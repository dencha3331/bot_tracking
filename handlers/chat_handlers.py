from typing import Sequence

from aiogram import Router, F
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatMemberUpdated
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER
from sqlalchemy.exc import IntegrityError, PendingRollbackError

# from configs.config import bot, env
from configs.config import env
from configs.config_bot import bot

from db import crud

from db.models import Groups, Users
from logs import logger

chat_router: Router = Router()


@chat_router.my_chat_member()
async def add_chat(update: ChatMemberUpdated) -> None:
    """
    Обработка запроса вступления бота в группу или канал.
    Проверяю бота на админа. Формирую пригласительную ссылку, сохраняю в бд.
    При любом другом запросе удаляю группу с бд.
    :param update:
    :return:
    """
    logger.debug(f"{update.chat.type}")
    logger.debug("start add_chat in chat_handlers.py")
    print(update, "My.new")
    chat_id: int = update.chat.id
    name = update.chat.full_name
    # try:
    status = update.new_chat_member.status
    logger.debug(f"status bot in chat {status}")
    if status == ChatMemberStatus.ADMINISTRATOR:
        group_title: str = update.chat.title
        group_db = crud.get_group_by_title(group_title)
        if group_db:
            crud.del_group(group_db.id)
        try:
            link = await bot.create_chat_invite_link(chat_id)
            print(1)
        except TelegramBadRequest:
            print(2)
            link = await bot.get_chat(chat_id)
        linked = link.invite_link
        chat = Groups(id=chat_id, nickname=name, link_chat=str(linked))
        crud.add_object(chat)
        logger.debug("add bot because admin")
    # elif is_admin in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
    else:
        logger.debug("bot not admin status negative add")
        crud.del_group(chat_id)
    logger.debug(f"end add_chat in chat_handlers.py")


@chat_router.chat_member()
async def chat_member_update(update: ChatMemberUpdated) -> None:
    print(update, "member ")
    """
    Обработка запроса при вступлении в группы.
    Проверка на админа.
    Получаю с бд все объекты Group.
    Проверяю новостная группа или нет если да сохраняю пользователя в бд и пропускаю.
    Делаю запрос в бд для получения пользователя.
    Проверка если пользователя в бд и у него нет телеграм ид добавляю ему ид.
    Проверка если пользователь оплатил return.
    Если прошел далее значит безбилетник либо добавляю нового пользователя со всеми
    необходимыми данными либо обновляю существующего и в бан.
    :param update:
    :return:
    """
    # await bot.delete_message(chat_id=update.chat.id, message_id=update.)
    logger.debug(f"{update.from_user.bot} \n{update.bot.id} {bot.id}")
    # if update.bot.id == bot.id:
    #     return
    logger.debug('start chat_member_update in chat_handlers.py')
    group_user_id: int = update.from_user.id
    user_nickname: str = update.from_user.username
    if group_user_id == bot.id:
        return
    logger.debug(f'group name: {update.chat.title} user nick {user_nickname}')
    if group_user_id == int(env("ADMIN")) or group_user_id in crud.get_list_admins():
        logger.debug(f'end chat_member_update in chat_handlers.py because user'
                     f' is bot admin name: {user_nickname}')
        return
    user_by_nickname: Users = crud.get_user_for_nickname(user_nickname)
    groups: Sequence[Groups] = crud.get_list_groups()
    group_is_news: list[int] = [group.id for group in groups if group.news_group]
    if update.chat.id in group_is_news and not user_by_nickname.tg_id:
        await _add_new_user(update, user_by_nickname)
        logger.debug(f'end chat_member_update in chat_handlers.py because news group '
                     f'name: {update.chat.username} id: {update.chat.id}')
        return
    # await _user_without_tg_id_check(user_by_nickname, update)
    if user_by_nickname and user_by_nickname.pay:
        if not user_by_nickname.tg_id:
            await _add_new_user(update, user_by_nickname)
        logger.debug(f"end chat_member_update in chat_handlers.py because user save "
                     f"and pay user: {user_by_nickname.nickname} id {user_by_nickname.id}")
        return
    await _ban_user_by_groups(groups, update)
    logger.debug(f'ban in chat_member_update in chat_handlers.py user: {update.from_user.username}'
                 f' id user: {update.from_user.id} chat name {update.chat.username}')
    await _add_new_user(update, user_by_nickname)
    await _save_ban_user(user_by_nickname, update)
    logger.debug("end  chat_member_update in chat_handlers.py")
    # crud.update_user(user_nick=user_nickname, ban=True)


async def _add_new_user(update: ChatMemberUpdated, user: Users) -> None:
    logger.debug(f"start _add_new_user in chat_handler.py")
    user_link = f'https://t.me/{update.from_user.username}' if update.from_user.username else None
    if user and user.tg_id:
        logger.debug(f"start _add_new_user in chat_handler.py because user and user.tg_id")
        return
    if user and not user.tg_id:
        try:
            crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
                                         user_link=user_link, first_name=update.from_user.first_name,
                                         last_name=update.from_user.last_name)
        except (PendingRollbackError, IntegrityError):
            crud.delete_user_by_id(update.from_user.id)
            crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
                                         user_link=user_link, first_name=update.from_user.first_name,
                                         last_name=update.from_user.last_name)
        logger.debug(f"start _add_new_user in chat_handler.py because user save or update "
                     f"in if user and not user.tg_id:user: {update.from_user.username} "
                     f"user id: {update.from_user.id} "
                     f"chat: {update.chat.username}")
        return
    if not user:
        try:
            user_obj = Users(nickname=update.from_user.username, tg_id=update.from_user.id,
                             user_link=user_link, first_name=update.from_user.first_name,
                             last_name=update.from_user.last_name)
            crud.add_object(user_obj)
        except (PendingRollbackError, IntegrityError):
            crud.delete_user_by_id(update.from_user.id)
            crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id, user_link=user_link,
                                         first_name=update.from_user.first_name, last_name=update.from_user.last_name)
    logger.debug(f"end _add_new_user in chat_handler.py because not user and now user save or update "
                 f"user: {update.from_user.username} user id: {update.from_user.id} "
                 f"chat: {update.chat.username}")


# async def _user_without_tg_id_check(user: Users, update: ChatMemberUpdated) -> None:
#     logger.debug(f"start _user_without_tg_id_check in chat_handler.py")
#     user_link = f'https://t.me/{update.from_user.username}' if update.from_user.username else None
#     if user and not user.tg_id:
#         logger.debug("not tg id")
#         try:
#             crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
#                                          user_link=user_link, first_name=update.from_user.first_name,
#                                          last_name=update.from_user.last_name)
#         except (PendingRollbackError, IntegrityError):
#             crud.delete_user_by_id(update.from_user.id)
#             crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
#                                          user_link=user_link, first_name=update.from_user.first_name,
#                                          last_name=update.from_user.last_name)
#     logger.debug(f"end _user_without_tg_id_check in chat_handler.py")


async def _save_ban_user(user: Users, update: ChatMemberUpdated) -> None:
    logger.debug(f"start _save_ban_user in chat_handler.py")
    user_link = f'https://t.me/{update.from_user.username}' if update.from_user.username else None
    if not user:
        user_obj = Users(nickname=update.from_user.username, tg_id=update.from_user.id,
                         user_link=user_link, first_name=update.from_user.first_name,
                         last_name=update.from_user.last_name, ban=True)
        try:
            crud.add_object(user_obj)
        except (PendingRollbackError, IntegrityError):
            crud.delete_user_by_id(update.from_user.id)
            crud.add_object(user_obj)
    elif user and not user.ban:
        crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
                                     user_link=user_link, first_name=update.from_user.first_name,
                                     last_name=update.from_user.last_name, ban=True, pay=False)
    logger.debug(f"end _save_ban_user in chat_handler.py")


async def _ban_user_by_groups(groups: Sequence[Groups], update: ChatMemberUpdated) -> None:
    logger.debug(f"start _ban_user_by_groups in chat_handler.py")

    for group in groups:
        if not group.news_group:
            try:
                logger.debug(f'popitka bana {group.nickname} {update.from_user.id} {update.from_user.username}')
                await bot.ban_chat_member(chat_id=group.id, user_id=update.from_user.id)
                logger.debug('udacha ban')
            except TelegramBadRequest as e:
                logger.debug(f"negative ban {group.nickname} {update.from_user.id} {update.from_user.username}")
                logger.warning(e)
    logger.debug(f"end _ban_user_by_groups in chat_handler.py")


@chat_router.message(F.content_type.in_(['new_chat_members', 'left_chat_member']))
async def delete(message):
    print(message.content_type, "del")
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


@chat_router.message(F.content_type.in_(['new_chat_members', 'left_chat_member']))
async def delete(message):
    print(message.content_type, "all")
# MIGRATE_TO_CHAT_ID
#ChatMemberStatus.KICKED: 'kicked
#