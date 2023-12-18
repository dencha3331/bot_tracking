from aiogram.types import InlineKeyboardMarkup

from keyboards import inline_kb
from db import crud

_buttons_menu = {
    "add_users": "Добавить юзера(ов) в оплаченные",
    "del_users": "Удалить юзера(ов) из оплаченных и из групп",
    "change_link": "Сменить пригласительную ссылку группы(в ручную в бд)",
    "generate_new_link": "Сгенерировать новую пригласительную ссылку группы",
    "make_news_group": "Сделать новостной (не удалять юзеров, сбор зашедших)",
    "unmake_news_group": "Убрать из новостных (группа будет обычной)",
    "send_file_pay_user": "Скачать файл с оплаченными пользователями",
    "send_file_not_pay_user": "Скачать файл с неоплаченными пользователями",
    "send_file_all_user": "Скачать файл со всеми пользователями",
    "check_and_ban_unpay_user": "Проверить безбилетников по группам и забанить",
    "add_admin": "Добавить админа бота",
    "del_admin": "Удалить админа бота",
    "help": "Справка по работе бота",

}


def change_link_group_keyboard() -> InlineKeyboardMarkup:
    all_groups: dict = crud.get_name_id_group()
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **all_groups
    )
    return keyboard


def make_news_link_group_keyboard(news: bool) -> InlineKeyboardMarkup:
    all_groups: dict = crud.news_or_not_group_id_name(news)
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **all_groups
    )
    return keyboard


def menu_buttons() -> InlineKeyboardMarkup:
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **_buttons_menu
    )
    return keyboard
