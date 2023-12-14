from aiogram.types import InlineKeyboardMarkup

from keyboards import inline_kb
from db import crud

_buttons_menu = {
    "add_users": "Добавить юзеров в оплаченные",
    "del_users": "Удалить из оплаченных юзеров и из групп",
    "change_link": "Сменить пригласительную ссылку группы",
    "make_news_group": "сделать новостной (не удалять юзеров, сбор зашедших)",
    "add_admin": "Добавить админа бота",
    "del_admin": "удалить админа бот",
    # "send_file_pay_user": "Скачать файл с пользователями",
    "check_and_ban_unpay_user": "Проверить безбилетников по группам и забанить",
}


def change_link_group_keyboard() -> InlineKeyboardMarkup:
    all_groups: dict = crud.get_name_id_group()
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **all_groups
    )
    return keyboard


def menu_buttons() -> InlineKeyboardMarkup:
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **_buttons_menu
    )
    return keyboard
