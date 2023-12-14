from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import TelegramObject, Chat, User

from configs.config import bot
from db import crud
from db.models import Users


# Мидлварь, которая достаёт внутренний айди юзера из какого-то стороннего сервиса
class UserPermissionMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        chat: Chat = data['event_chat']
        if chat.type != 'private':
            return
        return await handler(event, data)


        # user_data: User = data["event_from_user"]
        # user_nick: str = user_data.username
        # user: Users = crud.get_user_for_nickname(user_nick)
        # if not user:
        #     await event.bot.send_message(chat_id=chat.id,
        #                                  text="Чтобы получить доступ к ресурсам обратитесь к администратору")
        #     return
        # if user.pay:
        #     print('user pay')
        #     if user.ban:
        #         print("user ban")
        #         groups_ids: list[int] = crud.get_list_groups_ids()
        #         if groups_ids:
        #             for group_id in groups_ids:
        #                 await bot.unban_chat_member(chat_id=group_id, user_id=user.tg_id, only_if_banned=True)
        #     return await handler(event, data)
