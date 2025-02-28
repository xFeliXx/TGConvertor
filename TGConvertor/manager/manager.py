from pathlib import Path
from typing import Type

from opentele.api import API, APIData

from .sessions.pyro import PyroSession
from .sessions.tele import TeleSession
from .sessions.tdata import TDataSession
from .exceptions import ValidationError


class SessionManager:
    def __init__(
        self,
        dc_id: int,
        auth_key: bytes,
        user_id: int = None,
        valid: bool = None,
        api: Type[APIData] = API.TelegramDesktop,
    ):
        self.dc_id = dc_id
        self.auth_key = auth_key
        self.user_id = user_id
        self.valid = valid
        self.api = api.copy()
        self.user = None
        self.client = None

    async def __aenter__(self):
        self.client = self.telethon_client()
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()
        self.client = None

    @property
    def auth_key_hex(self) -> str:
        return self.auth_key.hex()

    @classmethod
    async def from_telethon_file(cls, file: Path, api=API.TelegramDesktop):
        session = await TeleSession.from_file(file)
        return cls(
            dc_id=session.dc_id,
            auth_key=session.auth_key,
            api=api
        )

    @classmethod
    def from_telethon_string(cls, string: str, api=API.TelegramDesktop):
        session = TeleSession.from_string(string)
        return cls(
            dc_id=session.dc_id,
            auth_key=session.auth_key,
            api=api
        )

    @classmethod
    async def from_pyrogram_file(cls, file: Path, api=API.TelegramDesktop):
        session = await PyroSession.from_file(file)
        return cls(
            auth_key=session.auth_key,
            dc_id=session.dc_id,
            api=api,
            user_id=session.user_id,
        )

    @classmethod
    def from_pyrogram_string(cls, string: str, api=API.TelegramDesktop):
        session = PyroSession.from_string(string)
        return cls(
            auth_key=session.auth_key,
            dc_id=session.dc_id,
            api=api,
            user_id=session.user_id,
        )

    @classmethod
    def from_tdata_folder(cls, folder: Path):
        session = TDataSession.from_tdata(folder)
        return cls(
            auth_key=session.auth_key,
            dc_id=session.dc_id,
            api=session.api
        )

    async def to_pyrogram_file(self, path: Path):
        await self.pyrogram.to_file(path)

    def to_pyrogram_string(self) -> str:
        return self.pyrogram.to_string()

    async def to_telethon_file(self, path: Path):
        await self.telethon.to_file(path)

    def to_telethon_string(self) -> str:
        return self.telethon.to_string()

    async def to_tdata_folder(self, path: Path):
        await self.get_user_id()
        self.tdata.to_folder(path)

    @property
    def pyrogram(self) -> PyroSession:
        return PyroSession(
            dc_id=self.dc_id,
            auth_key=self.auth_key,
            user_id=self.user_id,
        )

    @property
    def telethon(self) -> TeleSession:
        return TeleSession(
            dc_id=self.dc_id,
            auth_key=self.auth_key,
        )

    @property
    def tdata(self) -> TDataSession:
        return TDataSession(
            dc_id=self.dc_id,
            auth_key=self.auth_key,
            api=self.api,
            user_id=self.user_id,
        )

    def pyrogram_client(self, proxy=None, no_updates=True):
        client = self.pyrogram.client(
            api=self.api,
            proxy=proxy,
            no_updates=no_updates,
        )
        return client

    def telethon_client(self, proxy=None, no_updates=True):
        client = self.telethon.client(
            api=self.api,
            proxy=proxy,
            no_updates=no_updates,
        )
        return client

    async def validate(self) -> bool:
        user = await self.get_user()
        self.valid = bool(user)
        return self.valid

    async def get_user_id(self):
        if self.user_id:
            return self.user_id

        user = await self.get_user()

        if user is None:
            raise ValidationError()

        return user.id

    async def get_user(self):
        async with self as client:
            self.user = await client.get_me()
            if self.user:
                self.user_id = self.user.id
        return self.user
