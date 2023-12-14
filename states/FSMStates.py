from aiogram.filters.state import State, StatesGroup


class FSMAdminState(StatesGroup):
    menu = State()
    add_users = State()
    add_user_confirm = State()
    del_users = State()
    del_user_confirm = State()
    change_group_link_start = State()
    change_group_link = State()
    set_news_group_start = State()
    set_news_group = State()
    add_admin = State()
    del_admin = State()
    check_unpay_users = State()
    send_file_pay_user = State()
