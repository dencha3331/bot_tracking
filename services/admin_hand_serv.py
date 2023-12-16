import time

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, ChatPermissions, FSInputFile
from environs import Env
from pyrogram.types import ChatMember
from sqlalchemy import Sequence
from sqlalchemy.exc import PendingRollbackError, IntegrityError

from configs.config import bot
# from db.models import Admin, Chat, Settings
from db import crud
from db.models import Users, Groups
from logs import logger
from services.pyrogram_service import get_chat_members

env: Env = Env()
env.read_env()


async def unban_user(nickname: str) -> None:
    logger.debug(f"start unban user_start in admin_hand_serv.py user: {nickname}")
    user: Users = crud.get_user_for_nickname(nickname)
    if not user:
        logger.debug(f"if not user: call crud.save_pay_user({nickname})")
        crud.save_pay_user(nickname)
        logger.debug(f"end unban user_start in admin_hand_serv.py user: {nickname} "
                     f"return in if not user:")
        return
    groups = crud.get_list_groups()
    for group in groups:
        await _unban_now(group, user)
    crud.unban_user(user.nickname)
    logger.debug(f"end unban_user in admin_hand_serv.py user: {nickname}")


async def _unban_now(group: Groups, user: Users):
    logger.debug(f"start _unban_now in admin_hand_serv.py user: {user.nickname}")
    if not group.news_group:
        logger.debug(f"if not group.news_group:")
        try:
            logger.debug(f"try: ")
            await bot.unban_chat_member(chat_id=group.id, user_id=user.tg_id, only_if_banned=True)
            logger.debug(f"unban complete user {user.nickname} in try: ")
        except TelegramBadRequest as e:
            logger.debug(f"except TelegramBadRequest as e: user {user.nickname}")
            logger.warning(e)
            logger.debug(e)
            logger.debug(f'lose first unban user {user.nickname}')
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            await bot.restrict_chat_member(chat_id=group.id, user_id=user.tg_id, permissions=permissions)
        except Exception as e:
            logger.error(e)
            logger.debug(f'not unban user {user.nickname}')
            logger.debug(e)
    logger.debug(f"end _unban_now in admin_hand_serv.py user: {user.nickname}")


async def ban_user(nickname: str) -> None:
    logger.debug(f"start ban_user in admin_hand_serv.py user: {nickname}")
    user: Users = crud.get_user_for_nickname(nickname)
    logger.debug(f"user from db: {user.nickname}")
    if not user:
        user_link = f'https://t.me/{nickname}'
        user = Users(nickname=nickname, ban=True, user_link=user_link)
        crud.add_object(user)
        logger.debug(f"end ban_user in admin_hand_serv.py user: {nickname} "
                     f"because if not user:")
        return
    if not user.tg_id:
        logger.debug(f"if not user.tg_id: crud.delete_user_by_nicname({nickname})")
        crud.update_user_by_nickname(user_nick=nickname, pay=False)
        return
    logger.debug(f"bane_user in admin_hand_serv call crud.ban_users({nickname})")
    crud.update_user_by_nickname(nickname, pay=False, ban=True)
    groups = crud.get_list_groups()
    for group in groups:
        logger.debug(f"for group in groups: group: {group.nickname} id {group.id} "
                     f"news: {group.news_group} user: {user.nickname} user id: {user.tg_id}")
        if group.news_group:
            continue
        try:
            await bot.ban_chat_member(chat_id=group.id, user_id=user.tg_id)
        except TelegramForbiddenError as e:
            logger.debug(f"except TelegramForbiddenError as e: user {user.nickname}")
            logger.error(e)


async def check_group_not_pay_users_and_ban(group_id: int):
    ban_users_list = []
    logger.debug(f"start check_group_not_pay_users_and_ban in admin_hand_serv.py user")
    group: int = group_id
    admins_ids: list[int] = crud.get_list_admins() + [int(env('ADMIN')), bot.id]
    users_fom_db: list[Users] = [user for user in crud.get_all_user()]
    list_chat_member: list[ChatMember] = await get_chat_members(group)

    await _update_users_data_using_chat_member(users_fom_db, list_chat_member)

    list_member_without_admin = [member for member in list_chat_member
                                 if member.user.id not in admins_ids]
    list_ban_users: list[str] = await _ban_users(list_member_without_admin,
                                                 users_fom_db, group_id)
    ban_users_list += list_ban_users
    return save_and_return_file_delete_users(ban_users_list)


async def check_all_groups_not_pay_users_and_ban() -> FSInputFile:
    ban_users_list = []
    logger.debug(f"start check_all_groups_not_pay_users_and_ban in admin_hand_serv.py user")
    groups: list[Groups] = [group for group in crud.get_list_groups()]
    users_fom_db: list[Users] = [user for user in crud.get_all_user()]
    admins_ids: list[int] = crud.get_list_admins() + [int(env('ADMIN')), bot.id]
    for group in groups:
        group_id: int = group.id
        logger.debug(f"for group in groups: group: {group.nickname}, id: {group.id}")

        list_chat_member: list[ChatMember] = await get_chat_members(group_id)

        await _update_users_data_using_chat_member(users_fom_db, list_chat_member)
        if group.news_group:
            continue
        list_member_without_admin = [member for member in list_chat_member
                                     if member.user.id not in admins_ids]
        list_ban_users: list[str] = await _ban_users(list_member_without_admin,
                                                     users_fom_db, group_id)
        time.sleep(1)
        ban_users_list += list_ban_users
    return save_and_return_file_delete_users(ban_users_list)


async def _update_users_data_using_chat_member(list_db_users: list[Users],
                                               list_chat_member: list[ChatMember]) -> None:
    list_db_users = list_db_users[:]
    list_chat_member = list_chat_member[:]
    for chat_member in list_chat_member:
        for user_db in list_db_users:
            logger.debug(f"for user_db in users_fom_db: user_db: {user_db.nickname} "
                         f"chat_member: {chat_member.user.username} id: {chat_member.user.id}, "
                         f"user_db: {user_db.nickname}  id: {user_db.tg_id}")
            if chat_member.user.username == user_db.nickname and not user_db.tg_id:
                logger.debug(f"if chat_member.user.username == user_db and not user_db.tg_id:")
                await _update_db_user(chat_member, user_db)
                list_db_users.remove(user_db)


async def _update_db_user(chat_member: ChatMember, user_db: Users) -> None:
    user_link = f'https://t.me/{chat_member.user.username}' if chat_member.user.username else None
    try:
        logger.debug(f"try: crud.update_user: {chat_member.user.username} "
                     f"id: {chat_member.user.id}")
        crud.update_user_by_nickname(user_db.nickname, tg_id=chat_member.user.id, user_link=user_link,
                                     first_name=chat_member.user.first_name,
                                     last_name=chat_member.user.last_name)
    except (PendingRollbackError, IntegrityError):
        logger.debug(f"except: call crud.delete_user_by_id({chat_member.user.id}) and "
                     f"call crud.update_user({user_db.nickname})")
        user_from_db_without_nickname: Users = crud.get_user_by_id(chat_member.user.id)
        crud.delete_user_by_id(chat_member.user.id)
        crud.update_user_by_nickname(user_db.nickname, tg_id=chat_member.user.id,
                                     user_link=user_link,
                                     first_name=chat_member.user.first_name,
                                     last_name=chat_member.user.last_name,
                                     ban=user_from_db_without_nickname.ban, pay=user_db.pay)
        logger.debug(f"successful update user in except: user: {user_db.nickname}")


async def _ban_users(list_member: list[ChatMember],
                     list_db_users: list[Users],
                     group: int) -> list[str]:
    result = []
    users_fom_db = list_db_users[:]
    pay_users_name = [user.nickname for user in users_fom_db if user.pay]
    users_name = [user.nickname for user in users_fom_db]
    list_member_without_admin: list[ChatMember] = list_member[:]
    for member in list_member_without_admin:
        logger.debug(f'for member in list_member_without_admin: member: {member.user.username}')
        chat_member = await bot.get_chat_member(chat_id=group, user_id=member.user.id)
        if chat_member.user.username not in users_name:
            logger.debug(f"if chat_member.user.username not in users_name: "
                         f"call crud.insert_user{chat_member.user.username})")
            # user_link = f'https://t.me/{chat_member.user.username}' if chat_member.user.username else None
            # try:
            #     crud.insert_user(
            #         nickname=chat_member.user.username, tg_id=chat_member.user.id,
            #         user_link=user_link, first_name=chat_member.user.first_name,
            #         last_name=chat_member.user.last_name, ban=True
            #     )
            # except IntegrityError:
            #     crud.update_user(chat_member.user.username, tg_id=chat_member.user.id,
            #                      user_link=user_link, first_name=chat_member.user.first_name,
            #                      last_name=chat_member.user.last_name, ban=True)
        if chat_member.user.username not in pay_users_name:
            logger.debug(f"if chat_member.user.username not in pay_users_name:"
                         f" chat_member: {chat_member.user.username} "
                         f"call bot.ban_chat_member(chat_id={group}, user_id={member.user.id})")
            crud.update_user_by_id(chat_member.user.id, ban=True)
            await bot.ban_chat_member(chat_id=group, user_id=member.user.id)
            result.append(f"{member.user.first_name}; {member.user.username}; {member.user.id}; "
                          f"удален из всех групп;")
    return result


def save_and_return_file_delete_users(list_str_users: list[str], path=None) -> FSInputFile:
    path = path if path else 'delete_user.csv'
    with open(path, "w") as file:
        file.write("\n".join(list_str_users))
    logger.debug(f"end check_unpay_users_ban in admin_hand_serv.py"
                 f" return FSInputFile('delete_user.txt')")
    return FSInputFile(path)


def send_pay_user() -> FSInputFile:
    users = crud.get_all_user()
    path = 'pay_users.csv'
    with open(path, "w") as file:
        # file.write("\tUser name\tОплата\tБан\tuser id\n")
        for user in users:
            if user.pay:
                name = user.nickname if user.nickname else "нет"
                pay = "оплачен" if user.pay else "не оплачен"
                ban = "бан" if user.ban else "не забанен"
                user_id = str(user.tg_id) if user.tg_id else "нет"
                first = user.first_name if user.first_name else "нет"
                last = user.last_name if user.first_name else "нет"
                date_create = str(user.create_date)
                updated_date = user.updated_date
                file.write(f"{name}; {pay}; {ban}; {user_id}; {first}; "
                           f"{last}; {date_create}; {updated_date};")
    return FSInputFile(path)


def send_not_pay_user() -> FSInputFile:
    users = crud.get_all_user()
    path = 'not_pay_users.csv'
    with open(path, "w") as file:
        # file.write("\tUser name\tОплата\tБан\tuser id\n")
        for user in users:
            if not user.pay:
                name = user.nickname if user.nickname else "нет"
                pay = "оплачен" if user.pay else "не оплачен"
                ban = "бан" if user.ban else "не забанен"
                user_id = str(user.tg_id) if user.tg_id else "нет"
                first = user.first_name if user.first_name else "нет"
                last = user.last_name if user.first_name else "нет"
                date_create = str(user.create_date)
                updated_date = user.updated_date
                file.write(f"{name}; {pay}; {ban}; {user_id}; {first}; "
                           f"{last}; {date_create}; {updated_date};")
    return FSInputFile(path)


def send_all_user() -> FSInputFile:
    users = crud.get_all_user()
    path = 'all_users.csv'
    with open(path, "w") as file:
        # file.write("\tUser name\tОплата\tБан\tuser id\n")
        for user in users:
            name = user.nickname if user.nickname else "нет"
            pay = "оплачен" if user.pay else "не оплачен"
            ban = "бан" if user.ban else "не забанен"
            user_id = str(user.tg_id) if user.tg_id else "нет"
            first = user.first_name if user.first_name else "нет"
            last = user.last_name if user.first_name else "нет"
            date_create = str(user.create_date)
            updated_date = user.updated_date
            file.write(f"{name}; {pay}; {ban}; {user_id}; {first}; "
                       f"{last}; {date_create}; {updated_date};")
    return FSInputFile(path)
