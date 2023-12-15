import time

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, ChatPermissions, FSInputFile
from environs import Env

from configs.config import bot
# from db.models import Admin, Chat, Settings
from db import crud
from db.models import Users, Groups
from logs import logger
from services.pyrogram_service import get_chat_members

env: Env = Env()
env.read_env()


async def unban_user(nickname: str) -> None:
    logger.debug("unban user_start")
    user: Users = crud.get_user_for_nickname(nickname)
    if not user:
        logger.debug("not user")
        crud.save_pay_user(nickname)
        return
    if user.pay:
        groups = crud.get_list_groups()
        for group in groups:
            await _unban_now(group, user)
    crud.unban_user(user.nickname)


async def _unban_now(group: Groups, user: Users):
    if not group.news_group or group.news_group:
        try:
            await bot.unban_chat_member(chat_id=group.id, user_id=user.tg_id, only_if_banned=True)
            logger.debug("unban complete")
        except TelegramBadRequest as e:
            logger.warning(e)
            logger.debug(e)
            logger.debug('lose first unban')
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            await bot.restrict_chat_member(chat_id=group.id, user_id=user.tg_id, permissions=permissions)
        except Exception as e:
            logger.error(e)
            logger.debug('not unban')
            logger.debug(e)


async def ban_user(nickname: str) -> None:
    logger.debug('pre ban user')
    user: Users = crud.get_user_for_nickname(nickname)
    logger.debug(user.nickname)
    if not user:
        logger.debug("not user")
        return
    if not user.tg_id:
        logger.debug("not id")
        crud.update_user(user_nick=nickname, pay=False)
        return
    if not user.pay:
        logger.debug("ban user")
        crud.ban_users(nickname)
        groups = crud.get_list_groups()
        for group in groups:
            if group.news_group:
                continue
            try:
                await bot.ban_chat_member(chat_id=group.id, user_id=user.tg_id)
            except TelegramForbiddenError as e:
                logger.error(e)


async def check_unpay_users_ban() -> FSInputFile:
    result = []
    groups = crud.get_list_groups()
    pay_users_fom_db = crud.get_pay_users()
    admins_ids = crud.get_list_admins() + [int(env('ADMIN')), bot.id]
    pay_users_id = [user.id for user in pay_users_fom_db if user.id]
    for group in groups:
        logger.info("start get group")
        list_user: list[int] = await get_chat_members(group.id)
        list_user_group_without_admin = [user_id for user_id in list_user if user_id not in admins_ids]
        for user_group_id in list_user_group_without_admin:
            if user_group_id not in pay_users_id:
                logger.info("user_group id", user_group_id)
                user = await bot.get_chat_member(chat_id=group.id, user_id=user_group_id)
                await bot.ban_chat_member(chat_id=group.id, user_id=user_group_id)
                result.append(f"{user.user.first_name}\t{user.user.username}\t{user_group_id} "
                              f"удален из всех групп")
        time.sleep(1)
    with open('delete_user.txt', "w") as file:
        file.write("\n".join(result))
    return FSInputFile('delete_user.txt')


def send_pay_user() -> None:
    users = crud.get_all_user()
    with open('pay_users.txt', "w") as file:
        file.write("\tUser name\tОплата\tБан\tuser id\n")
        for user in users:
            if user.pay:
                name = user.nickname
                pay = "оплачен" if user.pay else "нет"
                ban = "бан" if user.ban else "нет"
                user_id = str(user.tg_id)
                file.write(f"\t{name}\t{pay}\t{ban}\t{user_id}")
