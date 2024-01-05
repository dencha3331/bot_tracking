from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError, IntegrityError

from db import crud
from db.models import Users, Groups
from logs import logger
from services import admin_hand_serv


# __________________________________________________________________
# ________________ Кнопка в меню unblock ___________________________
# __________________________________________________________________
async def unban_user_button(message: Message):
    """
    Если у пользователя нет telegram id обновляю его данные, еще одна проверка на оплату
    далее вызов функции разблокировки admin_hand_serv.unban_user
    """
    logger.debug(f"start unban_user_button in user_hand_serv.py user: {message.from_user.username}"
                 f" user id: {message.from_user.id}")
    user_nick: str = message.from_user.username
    user: Users = crud.get_user_by_id_or_nick(nick=user_nick)
    if user:
        if not user.tg_id:
            await _update_user(user, message)
        if user.pay:
            logger.debug(f"call admin_hand_serv.unban_user({user_nick}) in unban_user_button")
            groups: list[Groups] = crud.get_list_groups()
            for group in groups:
                await admin_hand_serv.unban_now(group, user)


async def _update_user(user: Users, message: Message):
    """
    Пробую обновить данные если происходит исключение значит telegram id такой уже
    есть в бд удаляю старый, добавляю новый.
    """
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
        user_from_db: Users = crud.get_user_by_id_or_nick(tg_id=user_id)
        crud.delete_user_by_id(user_from_db.tg_id)
        crud.update_user_by_nickname(message.from_user.username, tg_id=message.from_user.id,
                                     user_link=user_link, first_name=message.from_user.first_name,
                                     last_name=message.from_user.last_name,
                                     ban=user_from_db.ban, pay=user.pay)
        logger.debug(f"successful update user in except:")
