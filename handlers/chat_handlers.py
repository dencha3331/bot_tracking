from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatMemberUpdated, Message

from logs import logger
from services import chat_hand_serv
from configs.config import bot
from db import crud
# from configs.config_bot import bot

chat_router: Router = Router()


# ______________________________________________________________
# ________ Бота сделали админом или удалили из админа __________
# ______________________________________________________________
@chat_router.my_chat_member()
async def add_chat(update: ChatMemberUpdated) -> None:
    """Обработка запроса вступления бота в группу или канал."""
    await chat_hand_serv.add_chat(update)


# ____________________________________________________________________
# _____________ Обработчик вступления пользователя в группу __________
# ____________________________________________________________________
@chat_router.chat_member()
async def chat_member_update(update: ChatMemberUpdated) -> None:
    """Обработка запроса при вступлении пользователя в группы."""
    await chat_hand_serv.chat_member_update(update)


# _______________________________________________________________________
# __________ Удаление сообщений о вступление/удалении пользователя ______
# _______________________________________________________________________
@chat_router.message(F.content_type.in_(['new_chat_members', 'left_chat_member']))
async def delete_mes(message: Message) -> None:
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logger.error(f"error in delete_mes in chat_handlers.py: {e}")


# _____________________________________________________________________
# ___________ Обработчик смены имени группы ___________________________
# _____________________________________________________________________
@chat_router.message(F.content_type.in_(['new_chat_title']))
async def new_chat_title(message: Message) -> None:
    """Сохраняю новое имя группы"""
    crud.update_group_by_id(message.chat.id, {'nickname': message.chat.title})
