from typing import Sequence
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramMigrateToChat
from aiogram.types import ChatPermissions, FSInputFile
from environs import Env
from pyrogram.types import ChatMember
from sqlalchemy.exc import PendingRollbackError, IntegrityError, OperationalError

from db import crud
from db.models import Users, Groups
from logs import logger
from services import pyrogram_service
from configs.config import bot

env: Env = Env()
env.read_env()


# _______________________________________________________________________________
# ___________кнопка в админ меню _________ Удалить пользователей_________________
# _______________________________________________________________________________
async def ban_user(nickname: str) -> None | str:
    """
    Запрашиваю пользователя с бд. Если его нет добавляю новую запись. Если есть, но нет
    telegram id ставлю пометку в бд, что не оплаченный. Далее запрашиваю список всех групп
    и передаю пользователя и группу на блокировку в _ban_user_in_group.
    """
    logger.debug(f"start ban_user in admin_hand_serv.py user: {nickname}")
    user: Users = crud.get_user_by_id_or_nick(nick=nickname)
    if not user:
        user_link = f'https://t.me/{nickname}'
        user: Users = Users(nickname=nickname, ban=True, user_link=user_link)
        crud.add_object(user)
        logger.debug(f"end ban_user in admin_hand_serv.py user: {nickname} "
                     f"because if not user:")
        return
    if not user.tg_id:
        logger.debug(f"user from db: {user.nickname}")
        logger.debug(f"if not user.tg_id: crud.delete_user_by_nicname({nickname})")
        crud.update_user_by_nickname(user_nick=nickname, pay=False)
        return
    logger.debug(f"bane_user in admin_hand_serv call crud.ban_users({nickname})")
    crud.update_user_by_nickname(nickname, pay=False, ban=True)
    groups: list[Groups] = crud.get_list_groups()
    res: list[str] = []
    for group in groups:
        text = await _ban_user_in_group(group, user)
        if text:
            res.append(text)

    return '\n'.join(res)


async def _ban_user_in_group(group: Groups, user: Users) -> str | None:
    """Блокировка пользователя для группы. Если группа новостная ничего не делаю"""
    logger.debug(f"for group in groups: group: {group.nickname} id {group.id} "
                 f"news: {group.news_group} user: {user.nickname} user id: {user.tg_id}")
    if group.news_group:
        return
    try:
        await bot.ban_chat_member(chat_id=group.id, user_id=user.tg_id)
        return f"{user.nickname} удален из {group.nickname}"
    except (TelegramForbiddenError, TelegramMigrateToChat, TelegramBadRequest) as e:
        logger.debug(f"except TelegramForbiddenError as e: user {user.nickname}")
        logger.error(e)
        return f"Не смог удалить  {user.nickname} для этой группы {group.nickname}"


# ______________________________________________________________________
# ___________ кнопка в админ меню _________Добавить пользователей_______
# ______________________________________________________________________
async def unban_user(nickname: str) -> None:
    """
    Разблокировка пользователя по telegram UserName.
    Получаю пользователя с бд, если такого нет создаю нового, выхожу.
    Если есть запрашиваю все группы с бд и вызываю unban_now для каждой группы,
    где разблокировал пользователя. Ставлю пометку в бд об этом.
    """
    logger.debug(f"start unban user_start in admin_hand_serv.py user: {nickname}")
    user: Users = crud.get_user_by_id_or_nick(nick=nickname)
    if not user:
        logger.debug(f"if not user: call crud.save_pay_user({nickname})")
        user_obj = Users(nickname=user, pay=True, user_link=f'https://t.me/{nickname}')
        crud.add_object(user_obj)
        logger.debug(f"end unban user_start in admin_hand_serv.py user: {nickname} "
                     f"return in if not user:")
        return
    groups: list[Groups] = crud.get_list_groups()
    for group in groups:
        await unban_now(group, user)
    crud.update_user_by_nickname(user.nickname, ban=False, pay=True)
    logger.debug(f"end unban_user in admin_hand_serv.py user: {nickname}")


async def unban_now(group: Groups, user: Users) -> None:
    """Разблокировка пользователя в группе. Если группа не новостная пробую разблокировать
    методом unban_chat_member. В случая неудачи делаю еше попытку только методом restrict_chat_member"""

    logger.debug(f"start _unban_now in admin_hand_serv.py user: {user.nickname}")
    if not group.news_group:
        logger.debug(f"if not group.news_group:")
        try:
            logger.debug(f"try: ")
            await bot.unban_chat_member(chat_id=group.id, user_id=user.tg_id, only_if_banned=True)
            logger.debug(f"unban complete user {user.nickname} in try: ")
        except (TelegramBadRequest, TelegramMigrateToChat) as e:
            try:
                logger.debug(f"except TelegramBadRequest as e: lose first unban user {user.nickname}\n{e}")
                logger.warning(e)
                permissions = ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
                await bot.restrict_chat_member(chat_id=group.id, user_id=user.tg_id, permissions=permissions)
            except (TelegramBadRequest, TelegramMigrateToChat) as e:
                logger.error(e)
                logger.debug(f'not unban user {user.nickname}\n{e}')
    logger.debug(f"end _unban_now in admin_hand_serv.py user: {user.nickname}")


# __________________________________________________________________________________________
# __________ кнопка в админ меню. _______ Проверить безбилетников по группам и забанить _____
# __________________________________________________________________________________________
async def check_group_not_pay_users_and_ban(group: Groups) -> FSInputFile | None:
    """
    Проверка по группе неоплаченных пользователей.
    Запрашиваю с бд список telegram id админов бота и всех пользователей.
    Затем вызываю стороннее приложение c Pyrogram в pyrogram_service.get_chat_members
    для получения всех пользователей группы.
    Далее из полученных пользователей группы обновляю данные пользователей в бд в
    _update_users_data_using_chat_member.
    Проверка на новостную группу если да отмена.
    Фильтрую список пользователей группы от админов бота и группы, передаю на
    блокировку в _ban_users_by_chat_member которая возвращает список заблокированных пользователей.
    Передаю полученный список заблокированных в make_and_return_file_delete_users
    для формирования csv файла и возвращаю его.
    """

    logger.debug(f"start check_group_not_pay_users_and_ban in admin_hand_serv.py user")
    admins_ids: list[int] = crud.get_list_admins_ids() + [int(env('ADMIN')), bot.id]
    users_fom_db: list[Users] = [user for user in crud.get_all_user()]
    list_chat_member: list[ChatMember] = await pyrogram_service.get_chat_members(group.id)
    await _update_users_data_using_chat_member(list_chat_member)
    if group.news_group:
        return
    list_member_without_admin: list[ChatMember] = [member for member in list_chat_member
                                                   if member.status.MEMBER
                                                   and member.user.id not in admins_ids]
    list_ban_users: list[ChatMember] = []
    pay_users_name: list[str] = [user.nickname for user in users_fom_db if user.pay]
    for member in list_member_without_admin:
        if member.user.username not in pay_users_name:
            crud.update_user_by_id(member.user.id, ban=True, pay=False)
            try:
                await bot.ban_chat_member(chat_id=group.id, user_id=member.user.id)
                list_ban_users.append(member)
            except Exception as e:
                logger.error(f"Exception in check_group_not_pay_users_and_ban in admin_hand_serv.py: {e}")
    return make_and_return_file_delete_users(list_ban_users,
                                             f"files/delete_user_in_{group.nickname}.csv")


async def _update_users_data_using_chat_member(list_chat_member: list[ChatMember]) -> None:
    """
    Обновление или добавление пользователей по списку объектов ChatMember.
    Сначала пробу insert если такой пользователь есть пробую обновить по nickname(уникальное значение в бд)
    если ошибка значит такой tg_id(уникальное значение в бд) есть уже в бд, такое возможно если пользователь
    не имел nickname в телеграмме на момент первого взаимодействия с ботом(например был забанен и после его
    добавили по nickname в оплаченные). В таком случае удаляю запись с бд по tg_id и обновляю данные по nickname
    """
    list_chat_member: list[ChatMember] = list_chat_member[:]
    for chat_member in list_chat_member:
        user_link = f'https://t.me/{chat_member.user.username}' if chat_member.user.username else None
        try:
            user_obj: Users = Users(nickname=chat_member.user.username, tg_id=chat_member.user.id,
                                    user_link=user_link, first_name=chat_member.user.first_name,
                                    last_name=chat_member.user.last_name)
            crud.add_object(user_obj)
        except (PendingRollbackError, IntegrityError):
            crud.update_user_by_id(chat_member.user.id, nickname=chat_member.user.username,
                                   user_link=user_link, first_name=chat_member.user.first_name,
                                   last_name=chat_member.user.last_name)
        except (PendingRollbackError, IntegrityError):
            crud.update_user_by_nickname(chat_member.user.username, tg_id=chat_member.user.id,
                                         user_link=user_link, first_name=chat_member.user.first_name,
                                         last_name=chat_member.user.last_name)
        except (PendingRollbackError, IntegrityError):
            crud.delete_user_by_id(chat_member.user.id)
            crud.update_user_by_nickname(chat_member.user.username, tg_id=chat_member.user.id,
                                         user_link=user_link, first_name=chat_member.user.first_name,
                                         last_name=chat_member.user.last_name)
        except OperationalError as e:
            logger.error(f"Error in _update_users_data_using_chat_member admin_hand_serv.py: {e}")
            continue


def make_and_return_file_delete_users(list_users: list[ChatMember], path=None) -> FSInputFile:
    """Формирование файла с пользователями из списка с объектами ChatMember."""
    path = 'files/ban_user_for_all_group.csv' if not path else path
    with open(path, "w", encoding='utf-8-sig') as file:
        file.write(f"Никнейм; Телеграм id; ссылка; Имя; Фамилия;\n")
        for member in list_users:
            text: str = make_str_for_member(member)
            file.write(text)
    return FSInputFile(path)


def make_str_for_member(member: ChatMember) -> str:
    """Формирование строки из объекта ChatMember с nickname, telegram id, ссылки, имени и фамилии """
    name: str = member.user.username if member.user.username else "нет UserName"
    user_id: str = str(member.user.id)
    link: str = f"https://t.me/{member.user.username}" if member.user.username else "нет ссылки"
    first: str = member.user.first_name if member.user.first_name else "нет first name"
    last: str = member.user.last_name if member.user.first_name else "нет last name"
    return f"{name}; {user_id}; {link}; {first}; {last};\n"


# _____________________________________________________________________________________________
# _______________ кнопка в админ меню ___  Скачать файлы с пользователями __________
# _____________________________________________________________________________________________
def send_users_data_file(pay: bool = None, path: str = None) -> FSInputFile:
    """Формирование файла с пользователями. Если pay True формируется файл с оплаченными пользователями.
    Если pay False с неоплаченными. Если pay не указан при вызове со всеми пользователями"""
    users_db: Sequence[Users] = crud.get_all_user()
    path: str = 'files/all_users.csv' if not path else path
    if pay is None:
        users: list[Users] = [user for user in users_db]
    elif pay:
        users: list[Users] = [user for user in users_db if user.pay]
    else:
        users: list[Users] = [user for user in users_db if not user.pay]
    with open(path, "w", encoding='utf-8-sig') as file:
        file.write(f"Никнайм; Статус оплаты; Ранее удален; Телеграм id; ссылка; Имя; Фамилия; Добавлена;\n")
        for user in users:
            text = make_str_for_user(user)
            file.write(text)
    return FSInputFile(path)


def make_str_for_user(user: Users) -> str:
    """Формирование строки из объекта Users с nickname, статусом оплаты, был ли забанен,
    telegram id, ссылки, имени, фамилии и даты создание записи в бд"""
    name: str = user.nickname if user.nickname else "нет UserName"
    pay: str = "оплачен" if user.pay else "не оплачен"
    ban: str = "бан" if user.ban else "не забанен"
    user_id: str = str(user.tg_id) if user.tg_id else "нет id"
    link: str = user.user_link
    first: str = user.first_name if user.first_name else "нет first name"
    last: str = user.last_name if user.first_name else "нет last name"
    date_create: str = str(user.create_date)
    return f"{name}; {pay}; {ban}; {user_id}; {link}; {first}; {last}; {date_create};\n"
