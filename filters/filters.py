from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from environs import Env
from sqlalchemy.exc import PendingRollbackError, IntegrityError

from configs.config import bot
# from db.models import Admin, Chat, Settings
from db import crud
from db.models import Users
from logs import logger
from services import admin_hand_serv

env: Env = Env()
env.read_env()


class AdminFilter(BaseFilter):

    async def __call__(self, message: Message) -> bool | dict:
        # return True
        user_id: int = message.from_user.id

        if user_id == int(env('ADMIN')) or user_id in crud.get_list_admins():
            return {"status": "admin"}
        return False


class NotAdminFilter(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        # return True
        logger.debug(f"start NotAdminFilter in filters.py user: {message.from_user.username}"
                     f" user id: {message.from_user.id}")
        user_id: int = message.from_user.id
        if user_id != int(env('ADMIN')) or user_id not in crud.get_list_admins():
            logger.debug("zaebalo v filtrah")
            logger.debug(f"end NotAdminFilter in filters.py return True")
            return True
        await message.delete()
        logger.debug(f"end NotAdminFilter in filters.py return False")
        return False


class IsPrivateChat(BaseFilter):
    async def __call__(self, message: Message | CallbackQuery):
        if isinstance(message, CallbackQuery):
            return True
        if message.chat.type == 'private':
            return True
        return False


class IsNoPayMember(BaseFilter):

    async def __call__(self, update: ChatMemberUpdated):
        user_nick: str = update.from_user.username
        user: Users = crud.get_user_for_nickname(user_nick)
        if user and user.pay:
            return True
        user_id: int = update.from_user.id
        chat_id: int = update.chat.id
        if not user or not user.pay:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return False


class IsPayMember(BaseFilter):

    async def __call__(self, message: Message):
        logger.debug(f"start IsPayMember in filters.py user: {message.from_user.username}"
                     f" user id: {message.from_user.id}")
        user_nick: str = message.from_user.username
        user_id: int = message.from_user.id
        user_link = f'https://t.me/{message.from_user.username}' if message.from_user.username else None
        user: Users = crud.get_user_for_nickname(user_nick)
        if not user:
            logger.debug(f"end NotAdminFilter in filters.py because not user in db return False")
            return False
        if user and not user.tg_id:
            logger.debug(f"if user and not user.tg_id:")
            try:
                logger.debug(f"try: crud.update_user: {message.from_user.username} id: {message.from_user.id}")
                crud.update_user(message.from_user.username, tg_id=message.from_user.id, user_link=user_link,
                                 first_name=message.from_user.first_name, last_name=message.from_user.last_name)
            except (PendingRollbackError, IntegrityError):
                logger.debug(f"except: crud.delete_user_by_id({user_id}) and "
                             f"crud.update_user({message.from_user.username})")
                user_from_db: Users = crud.get_user_by_id(user_id)
                crud.delete_user_by_id(user_id)
                crud.update_user(message.from_user.username, tg_id=message.from_user.id, user_link=user_link,
                                 first_name=message.from_user.first_name, last_name=message.from_user.last_name,
                                 ban=user_from_db.ban, pay=user.pay)
                logger.debug(f"successful update user in except:")
                if user_from_db.ban and user.pay:
                    logger.debug(f"call admin_hand_serv.unban_user({user_nick}) in NotAdminFilter")
                    await admin_hand_serv.unban_user(user_nick)

        if user.pay:
            logger.debug(f"end NotAdminFilter in filters.py user: {message.from_user.username} pay "
                         f"user id: {message.from_user.id} return True")
            return {"status": "user"}
        logger.debug(f"end NotAdminFilter in filters.py {message.from_user.username} not pay "
                     f"user id: {message.from_user.id} return False")
        return False
