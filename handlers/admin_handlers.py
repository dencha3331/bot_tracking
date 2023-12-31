from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ChatInviteLink
from aiogram.fsm.state import default_state
from aiogram.types import FSInputFile
from pyrogram.errors import FloodWait
from sqlalchemy.exc import IntegrityError

import keyboards.admin_hand_kb as keyboards
from db.models import Groups, Admin
from filters.filters import AdminFilter, IsPrivateChat
from db import crud
from services import admin_hand_serv
from states.FSMStates import FSMAdminState
from keyboards import inline_kb
from lexicon import LEXICON
from configs.config import bot


admin_router: Router = Router()
lexicon_admin: dict[str] = LEXICON['admin_handler']


# ____________________________________________________________________________________
# ______________ при вызове меню бот ожидает callback поэтому все сообщения удаляю ___
# ____________________________________________________________________________________
@admin_router.message(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.menu))
async def negative_message(message: Message):
    await message.delete()


# _________________________________________________
# _______menu______start___________________________
# _________________________________________________
@admin_router.message(IsPrivateChat(), CommandStart(), AdminFilter(), StateFilter(default_state))
async def command_start(message: Message) -> None:
    await message.answer(lexicon_admin["start"])


# _____________________________________________________
# _______ кнопка в админ меню ______unblock____________
# _____________________________________________________
@admin_router.message(IsPrivateChat(), AdminFilter(), Command('unblock'), StateFilter(default_state))
async def all_user(message: Message) -> None:
    await message.delete()
    await message.answer(lexicon_admin["unblock"])


# ________________________________________________
# _________ кнопка в меню ________admin_____
# ________________________________________________
@admin_router.message(IsPrivateChat(), Command('admin'), AdminFilter(), StateFilter(default_state))
async def add_users_start(message: Message, state: FSMContext) -> None:
    keyboard: InlineKeyboardMarkup = keyboards.menu_buttons()
    await message.delete()
    await message.answer(text="menu", reply_markup=keyboard)
    await state.set_state(FSMAdminState.menu)


# ______________________________________________________
# _________ кнопка в меню ______ id ______________________
# ______________________________________________________
@admin_router.message(IsPrivateChat(), Command("id"))
async def get_id_user(message: Message) -> None:
    await message.delete()
    await message.answer(str(message.from_user.id))


# ______________________________________________________
# _________ кнопка в меню ______ help ______________________
# ______________________________________________________
@admin_router.message(IsPrivateChat(), Command("help"), StateFilter(default_state), AdminFilter())
async def get_id_user(message: Message) -> None:
    await message.delete()
    await message.answer(lexicon_admin['help_menu'])


# ______________________________________________________________________
# ___________ кнопка в админ меню _________Добавить пользователей_______
# ______________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'add_users',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def add_users_start(callback: CallbackQuery, state: FSMContext) -> None:
    """При выборе возвращает клавиатуру с подтверждением добавить или нет пользователя"""
    await callback.message.edit_text(text=lexicon_admin["add_users"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.add_user_confirm)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.add_user_confirm), AdminFilter())
async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Отправка сообщения об ожидание ввода пользователей на добавление в оплаченные или отмена"""
    await callback.answer()
    if callback.data == "yes":
        await callback.message.edit_text(text=lexicon_admin["add_pay_user"])
        await state.set_state(FSMAdminState.add_users)
    else:
        await callback.message.edit_text(lexicon_admin["not_add"])
        await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.add_users), AdminFilter())
async def save_users_end_unban(message: Message, state: FSMContext) -> None:
    """Добавление пользователей в оплаченные и разблокировка по группам. Ожидает сообщение в формате:
    username, @username, или ссылка на пользователя"""
    users: list[str] = message.text.split('\n')
    res_list: list[str] = []
    for nick_str in users:
        if '@' in nick_str:
            nick = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick = nick_str.split('/')[-1].strip()
        else:
            nick = nick_str.strip()
        await admin_hand_serv.unban_user(nick)
        res_list.append(f"{nick} {lexicon_admin['added_in_pay_users']}")
    await message.answer("\n".join(res_list))

    await state.clear()


# _______________________________________________________________________________
# ___________кнопка в админ меню _________ Удалить пользователей_________________
# _______________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'del_users',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def del_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    """При выборе возвращает клавиатуру с подтверждением удалить или нет пользователя"""
    await callback.message.edit_text(text=lexicon_admin["del_users"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.del_user_confirm)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.del_user_confirm), AdminFilter())
async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Отправка сообщения об ожидание ввода пользователей на удаление из оплаченных или отмена"""
    await callback.answer()
    if callback.data == "yes":
        await callback.message.edit_text(lexicon_admin["del_not_pay_users"])
        await state.set_state(FSMAdminState.del_users)
    else:
        await callback.message.edit_text("not_del")
        await state.clear()


@admin_router.message(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.del_users))
async def del_user(message: Message, state: FSMContext) -> None:
    """Удаление пользователей из оплаченные и блокировка по группам. Ожидает сообщение в формате:
        username, @username, или ссылка на пользователя"""
    users: list[str] = message.text.split('\n')
    res_list: list[str] = []
    for nick_str in users:
        if '@' in nick_str:
            nick: str = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick: str = nick_str.split('/')[-1].strip()
        else:
            nick: str = nick_str.strip()
        text: str | None = await admin_hand_serv.ban_user(nick)
        if text:
            res_list.append(text)
        else:
            res_list.append(f"{nick} {lexicon_admin['deleted_from_pay_users']}")
    await message.answer("\n".join(res_list))
    await state.clear()


# _____________________________________________________________________________________________________
# ___________ кнопка в админ меню. _________ Сменить пригласительную ссылку группы(в ручную в бд) _______
# __________________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'change_link',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext):
    """При выборе возвращает клавиатуру со всеми группами"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text=lexicon_admin["choose_group"], reply_markup=keyboard)
    await state.set_state(FSMAdminState.change_group_link_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.change_group_link_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Переходит в режим ожидания ссылки или отмена"""
    await callback.answer()
    data: str = callback.data
    group: Groups = crud.get_group_by_title_or_id(group_id=int(data))
    link: str = group.link_chat
    await state.update_data(id=int(data))
    await callback.message.edit_text(f"{lexicon_admin['send_a_new_link_current']}: {link}",
                                     disable_web_page_preview=True,
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, lexicon_admin['cancel']
                                     ))
    await state.set_state(FSMAdminState.change_group_link)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.change_group_link))
async def cancel_change_link(callback: CallbackQuery, state: FSMContext) -> None:
    """При выборе отмены для замены ссылок"""
    await callback.message.edit_text(lexicon_admin['not_change'])
    await state.clear()


@admin_router.message(IsPrivateChat(), AdminFilter(),
                      StateFilter(FSMAdminState.change_group_link))
async def change_group_link(message: Message, state: FSMContext) -> None:
    """Если отправили ссылку меняет ее в бд"""
    data: dict = await state.get_data()
    group_id: int = data['id']
    link: str = message.text
    crud.update_group_by_id(group_id, {'link_chat': str(link)})
    await message.answer(f"{lexicon_admin['link_changed_to']}: {link}",
                         disable_web_page_preview=True)
    await state.clear()


# ___________________________________________________________________________________________
# ___________ кнопка меню. _________ Сгенерировать новую пригласительную ссылку группы _______
# ___________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'generate_new_link',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext):
    """Клавиатура с выбором какой группе сгенерировать ссылку"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text=lexicon_admin['choose_group'], reply_markup=keyboard)
    await state.set_state(FSMAdminState.generate_group_link_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.generate_group_link_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Ожидание подтверждения на генерацию ссылки """
    await callback.answer()
    data: str = callback.data
    group: Groups = crud.get_group_by_title_or_id(group_id=int(data))
    link: str = group.link_chat
    await state.update_data(id=int(data))
    await callback.message.edit_text(
                                     f"{lexicon_admin['should_i_generate_a_new_link_current']}: {link}",
                                     disable_web_page_preview=True,
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.generate_group_link_)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.generate_group_link_))
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Генерация ссылки при подтверждении или отмена"""
    if callback.data == "no":
        await callback.message.edit_text(lexicon_admin['not_change'])
        return
    data: dict = await state.get_data()
    group_id: int = data['id']
    await callback.answer()
    try:
        link: ChatInviteLink = await bot.create_chat_invite_link(group_id)
        linked: str = link.invite_link
        crud.update_group_by_id(group_id, {'link_chat': str(linked)})
        await callback.message.edit_text(f"{lexicon_admin['new_link']} {linked}",
                                         disable_web_page_preview=True)
    except TelegramBadRequest:
        await callback.message.edit_text(lexicon_admin["except_generate_link"])
    await state.clear()


# ____________________________________________________________________________________________
# ___________ кнопка меню _________ Сделать новостной (не удалять юзеров, сбор зашедших) _____
# ____________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "make_news_group",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """В ответ клавиатура с выбором группы какую сделать новостной или отмена """
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.make_news_link_group_keyboard(False)
    await callback.message.edit_text(text=lexicon_admin['choose_group'], reply_markup=keyboard)
    await state.set_state(FSMAdminState.set_news_group_start)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.set_news_group_start),
                             F.data == "cancel", AdminFilter())
async def cancel_news_group(callback: CallbackQuery, state: FSMContext) -> None:
    """Сообщение при отмене для сделать новостной сброс состояния"""
    await callback.message.edit_text(lexicon_admin['cancel'])
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.set_news_group_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение сделать группу новостной"""
    await callback.answer()
    data: str = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text(text=lexicon_admin["make_news_group?"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.set_news_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.set_news_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Смена группы с обычной на новостную(добавление соответствующего значения в бд)"""
    await callback.answer()
    data: dict = await state.get_data()
    group_id: int = data['id']
    answer: str = callback.data
    if answer == "yes":
        crud.update_group_by_id(group_id, {"news_group": True})
        await callback.message.edit_text(lexicon_admin["set_news_group"])
    else:
        await callback.message.edit_text(lexicon_admin['not_change'])

    await state.clear()


# ___________________________________________________________________________________
# ___________ кнопка меню. _________ Убрать из новостных (группа будет обычной) _______
# ___________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "unmake_news_group",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """В ответ отправляет клавиатуру со списком групп для выбора какую группу сделать обычной"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.make_news_link_group_keyboard(True)
    await callback.message.edit_text(text=lexicon_admin['choose_group'], reply_markup=keyboard)
    await state.set_state(FSMAdminState.set_news_group_cancel_start)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.set_news_group_cancel_start),
                             F.data == "cancel", AdminFilter())
async def cancel_news_group(callback: CallbackQuery, state: FSMContext) -> None:
    """Сообщение при отмене для сделать новостной сброс состояния"""
    await callback.message.edit_text(lexicon_admin['cancel'])
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.set_news_group_cancel_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждения убрать из новостных"""
    await callback.answer()
    data: str = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text(text=lexicon_admin["del_news_group?"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.set_news_group_cancel)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.set_news_group_cancel))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Смена группы из новостных в обычную """
    await callback.answer()
    data: dict = await state.get_data()
    group_id: int = data['id']
    answer: str = callback.data
    if answer == "yes":
        crud.update_group_by_id(group_id, {"news_group": False})
        await callback.message.edit_text(lexicon_admin["set_simple_group"])
    else:
        await callback.message.edit_text(lexicon_admin['not_change'])
    await state.clear()


# _____________________________________________________________________________________________
# _______________ кнопка в админ меню. ___  Скачать файл с оплаченными пользователями __________
# _____________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с оплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_pay_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['send'],
                                         no=lexicon_admin['do_not_send']
                                     ))
    await state.set_state(FSMAdminState.send_file_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.send_file_pay_user))
async def send_file_pay_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла с оплаченными пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_users_data_file(pay=True,
                                                                 path="files/pay_users.csv")
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer(lexicon_admin['no_paid'])
    else:
        await callback.message.edit_text(lexicon_admin['i_do_not_send'])
    await callback.message.delete()
    await state.clear()


# __________________________________________________________________________________________
# ________ кнопка в админ меню. ________ Скачать файл с неоплаченными пользователями ________
# __________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_not_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с неоплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_not_pay_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['send'],
                                         no=lexicon_admin['do_not_send']
                                     ))
    await state.set_state(FSMAdminState.send_file_not_pay_user)


@admin_router.callback_query(StateFilter(FSMAdminState.send_file_not_pay_user),
                             IsPrivateChat(), AdminFilter())
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла с неоплаченными пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_users_data_file(pay=False,
                                                                 path="files/not_pay_users.csv")
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer(lexicon_admin['no_unpaid'])
    else:
        await callback.message.edit_text(lexicon_admin['i_do_not_send'])
    await callback.message.delete()
    await state.clear()


# ________________________________________________________________________________________
# ________ кнопка в админ меню. ______ Скачать файл со всеми пользователями _______________
# ________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_all_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с неоплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_all_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['send'],
                                         no=lexicon_admin['do_not_send']
                                     ))
    await state.set_state(FSMAdminState.send_file_all_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.send_file_all_pay_user))
async def send_file_with_all_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла со всеми пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_users_data_file()
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer(lexicon_admin['nobody_here'])
    else:
        await callback.message.edit_text(lexicon_admin['i_do_not_send'])
    await callback.message.delete()
    await state.clear()


# __________________________________________________________________________________________
# __________ кнопка в админ меню. _______ Проверить безбилетников по группам и забанить _____
# __________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "check_and_ban_unpay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def choice_group_for_check_pay_user(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает список группа для выбора какую группу проверить или отмена"""
    list_group: list[Groups] = crud.get_list_groups()
    buttons: dict[str, str] = {str(group.id): group.nickname for group in list_group}
    keyboard: InlineKeyboardMarkup = inline_kb.create_inline_callback_data_kb(
        1, **buttons, last_btn={'cancel': lexicon_admin['cancel']}
    )
    await callback.message.edit_text(lexicon_admin["choose_group"], reply_markup=keyboard)
    await state.set_state(FSMAdminState.choice_group_check)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             F.data == 'cancel', AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена проверки безбилетников сброс состояния"""
    await callback.message.edit_text(lexicon_admin['not_doing_anything'])
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение проверки безбилетников по выбранной группе"""
    await state.update_data(id=str(callback.data))
    await callback.message.edit_text(lexicon_admin["confirm_check_group"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes=lexicon_admin['yes'], no=lexicon_admin['no']
                                     ))
    await state.set_state(FSMAdminState.check_unpay_users_one_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.check_unpay_users_one_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Запуск проверки безбилетников по выбранной группе вызов вспомогательных функция из service"""
    processing_message: Message = await callback.message.edit_text(lexicon_admin["processing_message"])
    answer: str = callback.data
    data: dict = await state.get_data()
    group_id: int = int(data['id'])
    group: Groups = [group for group in crud.get_list_groups() if group.id == group_id][-1]
    if answer == "yes":
        try:
            doc: FSInputFile | None = await admin_hand_serv.check_group_not_pay_users_and_ban(group)
            if not doc:
                await callback.message.answer(lexicon_admin['group_is_news'])
            else:
                await bot.send_document(chat_id=callback.message.chat.id, document=doc)
        except TelegramBadRequest:
            await callback.message.edit_text(lexicon_admin['telegram_error'])
        except FloodWait as e:
            start = str(e).find("of ") + 2
            end = str(e).find(" seconds ")
            seconds = str(e)[start:end]
            await callback.message.answer(lexicon_admin['to_many_request_wait'].format(
                seconds=seconds
            ))

    else:
        await callback.message.edit_text(lexicon_admin['not_doing_anything'])
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=processing_message.message_id)
    await state.clear()


# _____________________________________________________________________
# ___________ кнопка меню _________ Добавить админа бота ______________
# _____________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "add_admin",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрашивает telegram id или отмену"""
    await callback.message.edit_text(lexicon_admin["get_id_for_add_admin"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, cancel=lexicon_admin['cancel']
                                     ))
    await state.set_state(FSMAdminState.add_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.add_admin),
                             F.data == "cancel", AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена добавления админа, сброс состояния"""
    await callback.message.edit_text(lexicon_admin['not_add'])
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.add_admin), AdminFilter())
async def save_admin(message: Message, state: FSMContext) -> None:
    """Добавление админа ожидает на вход целочисленные данные 10 значный id"""
    admins: list[str] = message.text.split('\n')
    for admin in admins:
        if not admin.isdigit() or not 6 <= len(admin) < 12:
            await message.answer(f"{admin} {lexicon_admin['is_not_id']}")
            return
        admin_obj: Admin = Admin(id=int(admin))
        try:
            crud.add_object(admin_obj)
            await message.answer(f"id: {str(admin)} {lexicon_admin['now_admin']}")
        except IntegrityError:
            await message.answer(f"id: {str(admin)} {lexicon_admin['already_an_admin']}")
    await state.clear()


# ____________________________________________________________________
# ___________ кнопка меню _________ Удаление админа бота _____________
# ____________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "del_admin",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def del_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрашивает telegram id или отмену"""
    await callback.message.edit_text(lexicon_admin["get_id_for_del_admin"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, cancel=lexicon_admin['cancel']
                                     ))
    await state.set_state(FSMAdminState.del_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.del_admin),
                             F.data == "cancel", AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена удаления админа, сброс состояния"""
    await callback.message.edit_text(lexicon_admin['not_del'])
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.del_admin), AdminFilter())
async def del_admin(message: Message, state: FSMContext) -> None:
    """Удаление админа ожидает на вход целочисленные данные 10 значный id"""
    admins: list[str] = message.text.split('\n')
    for admin in admins:
        if not admin.isdigit() or not 6 < len(admin) < 12:
            await message.answer(f"{admin} {lexicon_admin['is_not_id']}")
            return
        crud.del_admins_by_id(int(admin))
        await message.answer(f"id: {str(admin)} {lexicon_admin['now_not_admin']}")
    await state.clear()


# ____________________________________________________________________________
# _________ кнопка в админ меню __________ Справка по работе бота ____________
# ____________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "help",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(lexicon_admin['help'])


# _________________________________________________________________________
# _______ удаление сообщений для админов чтоб не захломлять чат ___________
@admin_router.message(IsPrivateChat(), AdminFilter(), ~StateFilter(default_state))
async def negative_message(message: Message):
    await message.delete()
