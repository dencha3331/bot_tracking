from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from environs import Env

from db import crud
from db.models import Users
from logs import logger

env: Env = Env()
env.read_env()


class AdminFilter(BaseFilter):
    """Фильтр проверки является ли пришедший Update от администратора бота"""
    async def __call__(self, message: Message) -> bool:
        user_id: int = message.from_user.id

        if user_id == int(env('ADMIN')) or user_id in crud.get_list_admins_ids():
            return True
        return False


class NotAdminFilter(BaseFilter):
    """Фильтр проверки является ли пришедший Update не от администратора бота"""
    async def __call__(self, message: Message) -> bool:
        logger.debug(f"start NotAdminFilter in filters.py user: {message.from_user.username}"
                     f" user id: {message.from_user.id}")
        user_id: int = message.from_user.id
        if user_id != int(env('ADMIN')) or user_id not in crud.get_list_admins_ids():
            logger.debug("zaebalo v filtrah")
            logger.debug(f"end NotAdminFilter in filters.py return True")
            return True
        await message.delete()
        logger.debug(f"end NotAdminFilter in filters.py return False")
        return False


class IsPrivateChat(BaseFilter):
    """Фильтр проверки Update что он пришел в частный чат боту"""
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, CallbackQuery):
            return True
        if message.chat.type == 'private':
            return True
        return False


class IsPayMember(BaseFilter):
    """Фильтр проверки является ли пришедший Update от оплаченного пользователя"""
    async def __call__(self, message: Message) -> bool:
        logger.debug(f"start IsPayMember in filters.py user: {message.from_user.username}"
                     f" user id: {message.from_user.id}")
        user_nick: str = message.from_user.username
        user: Users = crud.get_user_by_id_or_nick(nick=user_nick)
        if not user:
            logger.debug(f"end NotAdminFilter in filters.py because not user in db return False")
            return False
        if user.pay:
            logger.debug(f"end NotAdminFilter in filters.py user: {message.from_user.username} pay "
                         f"user id: {message.from_user.id} return True")
            return True
        logger.debug(f"end NotAdminFilter in filters.py {message.from_user.username} not pay "
                     f"user id: {message.from_user.id} return False")
        return False
