from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from environs import Env


env: Env = Env()
env.read_env()


class AdminFilter(BaseFilter):
    """Фильтр проверки является ли пришедший Update от администратора бота"""
    async def __call__(self, message: Message, is_admin: bool) -> bool:
        return True if is_admin else False


class NotAdminFilter(BaseFilter):
    """Фильтр проверки является ли пришедший Update не от администратора бота"""
    async def __call__(self, message: Message, is_admin: bool) -> bool:
        return False if is_admin else True


class IsPrivateChat(BaseFilter):
    """Фильтр проверки Update что он пришел в частный чат боту"""
    async def __call__(self, message: Message | CallbackQuery, chat_type: bool) -> bool:
        return True if chat_type else False


class IsPayMember(BaseFilter):
    """Фильтр проверки является ли пришедший Update от оплаченного пользователя"""
    async def __call__(self, message: Message, pay: bool) -> bool:
        return True if pay else False
