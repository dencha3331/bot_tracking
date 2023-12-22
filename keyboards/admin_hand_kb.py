from aiogram.types import InlineKeyboardMarkup

from keyboards import inline_kb
from db import crud
from lexicon import LEXICON


lexicon_admin_kb = LEXICON['admin_hand_kb']


_buttons_menu = {
    "add_users": lexicon_admin_kb["add_users"],
    "del_users": lexicon_admin_kb["del_users"],
    "change_link": lexicon_admin_kb["change_link"],
    "generate_new_link": lexicon_admin_kb["generate_new_link"],
    "make_news_group": lexicon_admin_kb["make_news_group"],
    "unmake_news_group": lexicon_admin_kb["unmake_news_group"],
    "send_file_pay_user": lexicon_admin_kb["send_file_pay_user"],
    "send_file_not_pay_user": lexicon_admin_kb["send_file_not_pay_user"],
    "send_file_all_user": lexicon_admin_kb["send_file_all_user"],
    "check_and_ban_unpay_user": lexicon_admin_kb["check_and_ban_unpay_user"],
    "add_admin": lexicon_admin_kb["add_admin"],
    "del_admin": lexicon_admin_kb["del_admin"],
    "help": lexicon_admin_kb["help"],

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
        1, **all_groups, last_btn={"cancel": lexicon_admin_kb['cancel']}
    )
    return keyboard


def menu_buttons() -> InlineKeyboardMarkup:
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **_buttons_menu
    )
    return keyboard
