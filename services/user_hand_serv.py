import time

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, ChatPermissions, FSInputFile
from environs import Env
from pyrogram.types import ChatMember
from sqlalchemy import Sequence
from sqlalchemy.exc import PendingRollbackError, IntegrityError

# from configs.config import bot
from configs.config_bot import bot

# from db.models import Admin, Chat, Settings
from db import crud
from db.models import Users, Groups
from logs import logger
from services import admin_hand_serv


async def unban_user_button(message: Message):
    logger.debug(f"start unban_user_button in user_hand_serv.py user: {message.from_user.username}"
                 f" user id: {message.from_user.id}")
    user_nick: str = message.from_user.username
    user: Users = crud.get_user_for_nickname(user_nick)
    # if not user:
    #     logger.debug(f"end NotAdminFilter in filters.py because not user in db return False")
    #     return False
    if user:
        if not user.tg_id:
            await _update_user(user, message)
        if user.pay:
            logger.debug(f"call admin_hand_serv.unban_user({user_nick}) in unban_user_button")
            await admin_hand_serv.unban_user(user_nick)
    # if user.pay:
    #     logger.debug(f"end NotAdminFilter in filters.py user: {message.from_user.username} pay "
    #                  f"user id: {message.from_user.id} return True")
    #     return {"status": "user"}
    # logger.debug(f"end NotAdminFilter in filters.py {message.from_user.username} not pay "
    #              f"user id: {message.from_user.id} return False")
    # return False


async def _update_user(user: Users, message: Message):
    user_id: int = message.from_user.id
    user_link = f'https://t.me/{message.from_user.username}' if message.from_user.username else None

    try:
        logger.debug(f"try: crud.update_user: {message.from_user.username} id: {message.from_user.id}")
        crud.update_user_by_nickname(message.from_user.username, tg_id=message.from_user.id,
                                     user_link=user_link, first_name=message.from_user.first_name,
                                     last_name=message.from_user.last_name)
    except (PendingRollbackError, IntegrityError):
        logger.debug(f"except: crud.delete_user_by_id({user_id}) and "
                     f"crud.update_user({message.from_user.username})")
        user_from_db: Users = crud.get_user_by_id(user_id)
        crud.delete_user_by_id(user_id)
        crud.update_user_by_nickname(message.from_user.username, tg_id=message.from_user.id,
                                     user_link=user_link, first_name=message.from_user.first_name,
                                     last_name=message.from_user.last_name,
                                     ban=user_from_db.ban, pay=user.pay)
        logger.debug(f"successful update user in except:")