from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from typing import Any, Callable, Dict, Awaitable
from configs.config import env
from db import crud
from db.models import Users


class UserStatusMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if data['event_chat'].type == 'private':
            data['chat_type'] = True
            user: User = data['event_from_user']
            admin_ids: list[int] = crud.get_list_admins_ids()
            if user.id == int(env('ADMIN')) or user.id in admin_ids:
                data['is_admin'] = True
            elif user.id != int(env('ADMIN')) or user.id not in admin_ids:
                data['is_admin'] = False
                if user.username:
                    user_db: Users = crud.get_user_by_id_or_nick(nick=user.username)
                    data['pay'] = True if user_db.pay else False
                else:
                    data['pay'] = False
        if data['event_chat'].type != 'private':
            data['chat_type'] = False
        return await handler(event, data)
