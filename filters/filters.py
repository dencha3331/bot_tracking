from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from environs import Env

from configs.config import bot
# from db.models import Admin, Chat, Settings
from db import crud
from db.models import Users

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
        user_id: int = message.from_user.id
        if user_id != int(env('ADMIN')) or user_id != int(env('ADMIN')):
            print("zaebalo", user_id)
            print(user_id != int(env('ADMIN')), user_id != int(env('ADMIN')))
            return True
        await message.delete()
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
        user_nick: str = message.from_user.username
        user_id: int = message.from_user.id
        user: Users = crud.get_user_for_nickname(user_nick)
        if not user:
            return False
        if user and not user.tg_id:
            crud.update_user(user_nick, tg_id=user_id)
        if user.pay:
            return {"status": "user"}
        return False
