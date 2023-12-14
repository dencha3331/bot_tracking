from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER

from configs.config import bot, env
from db import crud

from db.models import Groups, Users

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
    print("add_chat")
    chat_id: int = update.chat.id
    name = update.chat.full_name
    # try:

    is_admin = update.new_chat_member.status
    print(is_admin)
    if is_admin == ChatMemberStatus.ADMINISTRATOR:
        print("add is admin", chat_id)
        link = await bot.create_chat_invite_link(chat_id)
        linked = link.invite_link
        chat = Groups(id=chat_id, nickname=name, link_chat=str(linked))
        crud.add_object(chat)
    # elif is_admin in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
    else:
        print("add is admin none")
        crud.del_group(chat_id)


@chat_router.chat_member()
async def some_func(update: ChatMemberUpdated) -> None:
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
    user_id: int = update.from_user.id
    user_nickname = update.new_chat_member.user.username
    if user_id == int(env("ADMIN")) or user_id in crud.get_list_admins():
        return
    user: Users = crud.get_user_for_nickname(user_nickname)
    group_id = update.chat.id
    groups = crud.get_list_groups()
    group_is_news = [group.news_group for group in groups if group.id == group_id]
    chat_id = update.chat.id
    if chat_id in group_is_news:
        print('news group')
        await _add_new_user(update, user)
        return
    if user and not user.tg_id:
        print("not tg id")
        crud.update_user(user_nick=user_nickname, tg_id=user_id, first_name=update.from_user.first_name,
                         last_name=update.from_user.last_name)
    if user and user.pay:
        return
    if not user:
        user_obj: Users = Users(nickname=user_nickname, tg_id=user_id, pay=False, ban=True)
        crud.add_object(user_obj)

    print('ban')
    crud.update_user(user_nick=user_nickname, ban=True)

    for group in groups:
        if not group.news_group:
            try:
                print('popitka bana', group.id, update.chat.id)
                await bot.ban_chat_member(chat_id=group.id, user_id=user_id)
                print('udacha ban')
            except TelegramBadRequest as e:
                print(e)


async def _add_new_user(update: ChatMemberUpdated, user: Users) -> None:
    user_id: int = update.from_user.id
    user_nickname = update.new_chat_member.user.username
    if user and user.tg_id:
        return
    if user and not user.tg_id:
        crud.update_user(user_nickname, id=user_id)
        return
    if not user:
        user_obj = Users(nickname=user_nickname, tg_id=user_id)
        crud.add_object(user_obj)
        return

