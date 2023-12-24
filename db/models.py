from typing import Optional

from sqlalchemy import ForeignKey, JSON, create_engine, func
from sqlalchemy import String, BigInteger
from sqlalchemy.dialects.sqlite import json
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import datetime

from configs.config import env


class Base(DeclarativeBase):

    def get_dict(self) -> dict:
        res = self.__dict__
        del res['_sa_instance_state']
        return res


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50))
    create_date: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now())


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    tg_id: Mapped[Optional[BigInteger]] = mapped_column(BigInteger(), unique=True)
    pay: Mapped[bool] = mapped_column(default=False)
    ban: Mapped[bool] = mapped_column(default=False)
    user_link: Mapped[Optional[str]] = mapped_column(String(50))
    create_date: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now())
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))


class Groups(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(50))
    link_chat: Mapped[str] = mapped_column(String(50), unique=True)
    news_group: Mapped[bool] = mapped_column(default=False)
    create_date: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    bot_token: Mapped[str] = mapped_column(String(50))
    admin: Mapped[BigInteger] = mapped_column(BigInteger())
    pyrogram_api_id: Mapped[str] = mapped_column(String(50))
    pyrogram_api_hash: Mapped[str] = mapped_column(String(50))


engine = create_engine("sqlite+pysqlite:///bot_sqlite.db", echo=True)
# engine = create_engine(f"mysql+pymysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
#                        f"{env('DB_NAME')}?charset=utf8mb4")

Base.metadata.create_all(engine)
