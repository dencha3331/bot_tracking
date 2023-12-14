from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Chat, User, CallbackQuery

from db import crud
from db.models import Admin
from configs.config import env


class AdminMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        print("admin hand")
        chat: Chat = data['event_chat']
        if chat.type != 'private':
            print(chat.type)
            return
        # if not isinstance(event, CallbackQuery):
        #     return await handler(event, data)
        admin_data: User = data["event_from_user"]
        if admin_data.id == int(env('ADMIN')):
            print("admin cconst")
            data['admin'] = True
            return await handler(event, data)
        admin: Admin = crud.get_admin_by_id(admin_data.id)
        if not admin:
            return
        return await handler(event, data)
