from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated, Chat, ChatInviteLink
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from db import crud
from db.models import Groups, Users
from logs import logger
from configs.config import bot, env


# ______________________________________________________________
# ________ Бота сделали админом или удалили из админа __________
# ______________________________________________________________
async def add_chat(update: ChatMemberUpdated) -> None:
    """
    Обработка запроса вступления бота в группу или канал.
    Проверяю бота на админа. Формирую пригласительную ссылку, сохраняю в бд.
    При любом другом запросе удаляю группу с бд.
    """
    logger.debug(f"{update.chat.type}")
    logger.debug("start add_chat in chat_handlers.py")
    chat_id: int = update.chat.id
    name: str = update.chat.full_name
    status = update.old_chat_member.status
    logger.debug(f"status bot in chat before {status}")
    if status == ChatMemberStatus.ADMINISTRATOR:
        group_title: str = update.chat.title
        group_db: Groups = crud.get_group_by_title_or_id(group_title=group_title)
        if group_db:
            crud.del_group(group_db.id)
        try:
            link: ChatInviteLink = await bot.create_chat_invite_link(chat_id)
        except TelegramBadRequest:
            link: Chat = await bot.get_chat(chat_id)
        linked: str = link.invite_link
        chat = Groups(id=chat_id, nickname=name, link_chat=str(linked))
        crud.add_object(chat)
        logger.debug("add bot because admin")
    else:
        logger.debug("bot not admin status negative add")
        crud.del_group(chat_id)
    logger.debug(f"end add_chat in chat_handlers.py")


# ____________________________________________________________________
# _____________ Обработчик вступления пользователя в группу __________
# ____________________________________________________________________
async def chat_member_update(update: ChatMemberUpdated) -> None:
    """
    Обработка запроса при вступлении в группы.
    Проверяю являться пользователь самим ботом если да пропускаю.
    Проверка на админа.
    Делаю запрос в бд для получения пользователя.
    Получаю с бд все объекты Group.
    Вызываю _add_user в которой проверяю пользователя: есть ли такой в бд и менялись ли его данные
    если нет нечего не делаю, если да сохраняю.
    Проверяю новостная группа или нет если да сохраняю пользователя в бд и пропускаю.
    Проверка если пользователь оплатил return.
    Если прошел далее значит безбилетник отправляю в бан и делаю соответствующую пометку в бд.
    """
    logger.debug('start chat_member_update in chat_handlers.py')
    group_user_id: int = update.from_user.id
    user_nickname: str = update.from_user.username
    if group_user_id == bot.id:
        return
    logger.debug(f'group name: {update.chat.title} user nick {user_nickname}')
    if group_user_id == int(env("ADMIN")) or group_user_id in crud.get_list_admins_ids():
        logger.debug(f'end chat_member_update in chat_handlers.py because user'
                     f' is bot admin name: {user_nickname}')
        return
    user_from_db: Users = crud.get_user_by_id_or_nick(nick=user_nickname)
    groups: list[Groups] = crud.get_list_groups()
    group_is_news: list[int] = [group.id for group in groups if group.news_group]
    await _add_user(update, user_from_db)
    if update.chat.id in group_is_news:
        return
    if user_from_db and user_from_db.pay:
        logger.debug(f"end chat_member_update in chat_handlers.py because user save "
                     f"and pay user: {user_from_db.nickname} id {user_from_db.id}")
        return
    await bot.ban_chat_member(chat_id=update.chat.id, user_id=update.from_user.id)
    crud.update_user_by_nickname(update.from_user.username,  ban=True, pay=False)
    logger.debug("end  chat_member_update in chat_handlers.py")


async def _add_user(update: ChatMemberUpdated, user: Users) -> None:
    """
    Вспомогательная функция для chat_member_update.
    Проверяет если у пользователя с бд полученному по username нового пользователя группы есть
    telegram id и есть ли такой пользователь вообще в бд, если да return.
    Проверка есть ли у пользователя с бд telegram id если нет вызываю _update_user_without_tg_id.
    Проверка если такого пользователя нет в бд добавляем в _save_unknown_user.
    """
    logger.debug(f"start _add_new_user in chat_handler.py")
    user_link: str | None = f'https://t.me/{update.from_user.username}'\
        if update.from_user.username else None
    if user and user.tg_id:
        logger.debug(f"start _add_new_user in chat_handler.py because user and user.tg_id")
        return
    if user and not user.tg_id:
        await _update_user_without_tg_id(update, user_link)
        return
    if not user:
        await _save_unknown_user(update, user_link)
    logger.debug(f"end _add_new_user in chat_handler.py because not user and now user save or update "
                 f"user: {update.from_user.username} user id: {update.from_user.id} "
                 f"chat: {update.chat.username}")


async def _update_user_without_tg_id(update: ChatMemberUpdated, user_link: str) -> None:
    """Вспомогательная функция для _add_user если нет telegram id пытаюсь обновить его данные.
    Если возникает исключение значит такой пользователь уже есть в бд
    с такими данными(поля nickname и tg_id уникальные), удаляю старую запись, вношу новую."""
    try:
        crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
                                     user_link=user_link, first_name=update.from_user.first_name,
                                     last_name=update.from_user.last_name)
        logger.debug(f'successfully update user in try: in _update_user_without_tg_id')
    except (PendingRollbackError, IntegrityError) as e:
        crud.delete_user_by_id(update.from_user.id)
        crud.update_user_by_nickname(update.from_user.username, tg_id=update.from_user.id,
                                     user_link=user_link, first_name=update.from_user.first_name,
                                     last_name=update.from_user.last_name)
        logger.debug(f'successfully update user in except: in _update_user_without_tg_id'
                     f' exception: {e}')


async def _save_unknown_user(update: ChatMemberUpdated, user_link: str) -> None:
    """Вспомогательная функция для _add_user.
    Если пользователь не найден в бд по UserName пытаюсь создать нового.
    Если возникает исключение значит telegram id пользователя уже
    есть в бд(поля nickname и tg_id уникальные) удаляю старую запись, добавляю новую"""
    user_obj: Users = Users(nickname=update.from_user.username, tg_id=update.from_user.id,
                            user_link=user_link, first_name=update.from_user.first_name,
                            last_name=update.from_user.last_name)
    try:
        crud.add_object(user_obj)
        logger.debug(f"successfully in try: _save_unknown_user")
    except (PendingRollbackError, IntegrityError) as e:
        logger.debug(e)
        crud.delete_user_by_id(update.from_user.id)
        crud.add_object(user_obj)
        logger.debug(f"successfully in except: _save_unknown_user")

