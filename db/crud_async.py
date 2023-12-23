from typing import Sequence, List

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import TextClause, text, create_engine, ScalarResult
from sqlalchemy import func, select, update, delete, Update, Select, or_
from sqlalchemy.exc import NoResultFound, IntegrityError, PendingRollbackError

from configs.config import env
from db.models import Admin, Groups, Users, Setting
from logs import logger


engine = create_async_engine(f"mysql+aiomysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
                             f"{env('DB_NAME')}?charset=utf8mb4", echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)




