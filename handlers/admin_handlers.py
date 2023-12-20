from typing import Sequence

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.state import default_state
from aiogram.types import FSInputFile
from pydantic import ValidationError

import keyboards.admin_hand_kb as keyboards
from configs.config import bot
# from configs.config_bot import bot

from db.models import Groups
from filters.filters import AdminFilter, IsPrivateChat
from db import crud
from services import admin_hand_serv
from states.FSMStates import FSMAdminState
from keyboards import inline_kb
from lexicon import LEXICON


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
# _________ кнопка в админ меню ________admin_____
# ________________________________________________
@admin_router.message(IsPrivateChat(), Command('admin'), AdminFilter(), StateFilter(default_state))
async def add_users_start(message: Message, state: FSMContext) -> None:
    keyboard: InlineKeyboardMarkup = keyboards.menu_buttons()
    await message.delete()
    await message.answer(text="menu", reply_markup=keyboard)
    await state.set_state(FSMAdminState.menu)


# ______________________________________________________
# _________ кнопка в админ меню ______id________________
# ______________________________________________________
@admin_router.message(IsPrivateChat(), Command("id"))
async def get_id_user(message: Message) -> None:
    await message.delete()
    await message.answer(str(message.from_user.id))


# ______________________________________________________________________
# ___________ кнопка в админ меню _________Добавить пользователей_______
# ______________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'add_users',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def add_users_start(callback: CallbackQuery, state: FSMContext) -> None:
    """При выборе возвращает клавиатуру с подтверждением добавить или нет пользователя"""
    await callback.message.edit_text(text=lexicon_admin["add_users"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
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
    res_list = []
    for nick_str in users:
        if '@' in nick_str:
            nick = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick = nick_str.split('/')[-1].strip()
        else:
            nick = nick_str.strip()
        await admin_hand_serv.unban_user(nick)
        res_list.append(f"{nick} добавлен в оплаченные")
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
                                         2, yes="Да", no="Нет"
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
    res_list = []
    for nick_str in users:
        if '@' in nick_str:
            nick = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick = nick_str.split('/')[-1].strip()
        else:
            nick = nick_str.strip()
        text = await admin_hand_serv.ban_user(nick)
        if text:
            res_list.append(text)
        else:
            res_list.append(f"{nick} удален из оплаченных")
    await message.answer("\n".join(res_list))
    await state.clear()


# _____________________________________________________________________________________________________
# ___________ кнопка в админ меню _________ Сменить пригласительную ссылку группы(в ручную в бд) _______
# __________________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'change_link',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext):
    """При выборе возвращает клавиатуру со всеми группами"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text="choose_group", reply_markup=keyboard)
    await state.set_state(FSMAdminState.change_group_link_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.change_group_link_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Переходит в режим ожидания ссылки или отмена"""
    await callback.answer()
    data = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text("Пришлите новую ссылку",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, "Отмена"
                                     ))
    await state.set_state(FSMAdminState.change_group_link)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.change_group_link))
async def cancel_change_link(callback: CallbackQuery, state: FSMContext) -> None:
    """При выборе отмены для замены ссылок"""
    await callback.message.edit_text("Не меняем")
    await state.clear()


@admin_router.message(IsPrivateChat(), AdminFilter(),
                      StateFilter(FSMAdminState.change_group_link))
async def change_group_link(message: Message, state: FSMContext) -> None:
    """Если отправили ссылку меняет ее в бд"""
    data: dict = await state.get_data()
    group_id: int = data['id']
    link: str = message.text
    save: bool = crud.update_group_link(group_id, link_chat=str(link))
    if save:
        await message.edit_text(f"Ссылка изменена на '{link}'")
    else:
        await message.edit_text("Не получилось!!! Попробуйте еще раз")
    await state.clear()


# ___________________________________________________________________________________________
# ___________ кнопка меню _________ Сгенерировать новую пригласительную ссылку группы _______
# ___________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == 'generate_new_link',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext):
    """Клавиатура с выбором какой группе сгенерировать ссылку"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text="Выберите группу", reply_markup=keyboard)
    await state.set_state(FSMAdminState.generate_group_link_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.generate_group_link_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Ожидание подтверждения на генерацию ссылки """
    await callback.answer()
    data = callback.data
    print(data)
    await state.update_data(id=int(data))
    await callback.message.edit_text("Мне сгенерировать новую ссылку?",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.generate_group_link_)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.generate_group_link_))
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Генерация ссылки при подтверждении или отмена"""
    if callback.data == "no":
        await callback.message.edit_text("Не меняю")
        return
    data: dict = await state.get_data()
    group_id: int = data['id']
    await callback.answer()
    try:
        link = await bot.create_chat_invite_link(group_id)
        linked = link.invite_link
        crud.update_group_link(group_id, link_chat=str(linked))
        await callback.message.edit_text(f"Новая ссылка {linked}")
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
    await callback.message.edit_text(text="Выберите группу", reply_markup=keyboard)
    await state.set_state(FSMAdminState.set_news_group_start)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.set_news_group_start),
                             F.data == "cancel", AdminFilter())
async def cancel_news_group(callback: CallbackQuery, state: FSMContext) -> None:
    """Сообщение при отмене для сделать новостной сброс состояния"""
    await callback.message.edit_text("Отмена")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение сделать группу новостной"""
    await callback.answer()
    data: str = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text(text=lexicon_admin["make_news_group?"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.set_news_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Смена группы с обычной на новостную(добавление соответствующего значения в бд)"""
    await callback.answer()
    data: dict = await state.get_data()
    group_id: int = data['id']
    answer: str = callback.data
    if answer == "yes":
        crud.update_group_status(group_id, {"news_group": True})
        await callback.message.edit_text(lexicon_admin["set_news_group"])
    else:
        await callback.message.edit_text("Не меняю")

    await state.clear()


# ___________________________________________________________________________________
# ___________ кнопка меню_________ Убрать из новостных (группа будет обычной) _______
# ___________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "unmake_news_group",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """В ответ отправляет клавиатуру со списком групп для выбора какую группу сделать обычной"""
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.make_news_link_group_keyboard(True)
    await callback.message.edit_text(text="Выберите группу", reply_markup=keyboard)
    await state.set_state(FSMAdminState.set_news_group_cancel_start)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.set_news_group_cancel_start),
                             F.data == "cancel", AdminFilter())
async def cancel_news_group(callback: CallbackQuery, state: FSMContext) -> None:
    """Сообщение при отмене для сделать новостной сброс состояния"""
    await callback.message.edit_text("Отмена")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group_cancel_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждения убрать из новостных"""
    await callback.answer()
    data: str = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text(text=lexicon_admin["del_news_group?"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.set_news_group_cancel)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group_cancel))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Смена группы из новостных в обычную """
    await callback.answer()
    data: dict = await state.get_data()
    group_id: int = data['id']
    answer: str = callback.data
    if answer == "yes":
        crud.update_group_status(group_id, {"news_group": False})
        await callback.message.edit_text(lexicon_admin["set_simple_group"])
    else:
        await callback.message.edit_text("Не меняю")

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
                                         1, cancel="Отмена"
                                     ))
    await state.set_state(FSMAdminState.add_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.add_admin),
                             F.data == "cancel", AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена добавления админа, сброс состояния"""
    await callback.message.edit_text("Не добавляю")
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.add_admin), AdminFilter())
async def save_admin(message: Message, state: FSMContext) -> None:
    """Добавление админа ожидает на вход целочисленные данные 10 значный id"""
    admins: list[str] = message.text.split('\n')
    for admin in admins:
        if not admin.isdigit() or len(admin) != 10:
            await message.answer(f"{admin} {lexicon_admin['is_not_id']}")
            return
        crud.add_admins_by_id(int(admin))
        await message.answer(f"id: {str(admin)} теперь админ")
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
                                         1, cancel="Отмена"
                                     ))
    await state.set_state(FSMAdminState.del_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.del_admin),
                             F.data == "cancel", AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена удаления админа, сброс состояния"""
    await callback.message.edit_text("Не удаляю")
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.del_admin), AdminFilter())
async def del_admin(message: Message, state: FSMContext) -> None:
    """Удаление админа ожидает на вход целочисленные данные 10 значный id"""
    admins: list[str] = message.text.split('\n')
    for admin in admins:
        if not admin.isdigit():
            await message.answer(f"{admin} {lexicon_admin['is_not_id']}")
            return
        crud.del_admins_by_id(int(admin))
        await message.answer(f"id: {str(admin)} теперь не админ")
    await state.clear()


# __________________________________________________________________________________________
# __________ кнопка в админ меню _______ Проверить безбилетников по группам и забанить _____
# __________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "check_and_ban_unpay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def choice_group_for_check_pay_user(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает список группа для выбора какую группу проверить или отмена"""
    list_group: Sequence[Groups] = crud.get_list_groups()
    buttons = {str(group.id): group.nickname for group in list_group}
    # buttons.update(all="Проверить все группы")
    keyboard = inline_kb.create_inline_callback_data_kb(
        1, **buttons, last_btn={'cancel': "Отмена"}
    )
    await callback.message.edit_text(lexicon_admin["choose_group"], reply_markup=keyboard)
    await state.set_state(FSMAdminState.choice_group_check)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             F.data == 'cancel', AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена проверки безбилетников сброс состояния"""
    await callback.message.edit_text("Не чего не делаю")
    await state.clear()


# @admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
#                              F.data == 'all', AdminFilter())
# async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
#     """Подтверждение проверки по всем группам (сейчас не активна) надо решить проблему с блокировкой
#     телеграм из-за большого количества запросов пока убрал эту опцию"""
#     await callback.message.edit_text(lexicon_admin["confirm_check_all_groups"],
#                                      reply_markup=inline_kb.create_inline_callback_data_kb(
#                                          2, yes="Да", no="Нет"
#                                      ))
#     await state.set_state(FSMAdminState.check_unpay_users_all_group)
#
#
# @admin_router.callback_query(IsPrivateChat(), AdminFilter(),
#                              StateFilter(FSMAdminState.check_unpay_users_all_group))
# async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
#     """_____________Проверка безбилетников по всем группам_________
#     ____________________УБРАЛ ЭТУ ОПЦИЮ_________________________"""
#     processing_message = await callback.message.edit_text("Подождите запрос обрабатывается.....")
#     answer: str = callback.data
#     if answer == "yes":
#         text: FSInputFile = await admin_hand_serv.check_all_groups_not_pay_users_and_ban()
#         try:
#             await bot.send_document(chat_id=callback.message.chat.id, document=text)
#         except TelegramBadRequest:
#             await callback.message.answer("Некого удалять")
#     else:
#         await callback.message.edit_text("Не чего не делаю")
#     await bot.delete_message(chat_id=callback.message.chat.id,
#                              message_id=processing_message.message_id)
#     await state.clear()
#     # await add_users_start(callback, state)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение проверки безбилетников по выбранной группе"""
    await state.update_data(id=str(callback.data))
    await callback.message.edit_text(lexicon_admin["confirm_check_group"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.check_unpay_users_one_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.check_unpay_users_one_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Запуск проверки безбилетников по выбранной группе вызов вспомогательных функция из service"""
    processing_message = await callback.message.edit_text(lexicon_admin["processing_message"])
    answer: str = callback.data
    data: dict = await state.get_data()
    group_id: int = int(data['id'])
    group: Groups = [group for group in crud.get_list_groups() if group.id == group_id][-1]
    if answer == "yes":
        doc: FSInputFile = await admin_hand_serv.check_group_not_pay_users_and_ban(group)
        if isinstance(doc, FSInputFile) or doc is None:
            try:
                await bot.send_document(chat_id=callback.message.chat.id, document=doc)
            except TelegramBadRequest:
                await callback.message.edit_text("Некого удалять")
            except ValidationError:
                await callback.message.answer("Группа новостная")
        elif doc == "С группой что то не так.":
            await callback.message.answer("Не могу проверить группу")
        else:
            await callback.message.answer("Группа новостная")
    else:
        await callback.message.edit_text("Не чего не делаю")
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=processing_message.message_id)
    await state.clear()


# _____________________________________________________________________________________________
# _______________ кнопка в админ меню ___  Скачать файл с оплаченными пользователями __________
# _____________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с оплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_pay_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.send_file_pay_user))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла с оплаченными пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_pay_user()
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer("Нет оплаченных")
    else:
        await callback.message.edit_text("Не отправляю")
    await callback.message.delete()
    await state.clear()


# __________________________________________________________________________________________
# ________ кнопка в админ меню ________ Скачать файл с неоплаченными пользователями ________
# __________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_not_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с неоплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_not_pay_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_not_pay_user)


@admin_router.callback_query(StateFilter(FSMAdminState.send_file_not_pay_user),
                             IsPrivateChat(), AdminFilter())
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла с неоплаченными пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_not_pay_user()
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer("Нет неоплаченных")
    else:
        await callback.message.edit_text("Не отправляю")
    await callback.message.delete()
    await state.clear()


# ________________________________________________________________________________________
# ________ кнопка в админ меню ______ Скачать файл со всеми пользователями _______________
# ________________________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_all_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос подтверждения на отправку файла с неоплаченными пользователями"""
    await callback.message.edit_text(lexicon_admin["send_file_all_user"],
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_all_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.send_file_all_pay_user))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение данных с бд и отправка файла со всеми пользователями"""
    await callback.answer()
    answer: str = callback.data
    if answer == "yes":
        file: FSInputFile = admin_hand_serv.send_all_user()
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=file)
        except TelegramBadRequest:
            await callback.message.answer("Никого нет")
    else:
        await callback.message.edit_text("Не отправляю")
    await callback.message.delete()
    await state.clear()


# ____________________________________________________________________________
# _________ кнопка в админ меню __________ Справка по работе бота ____________
# ____________________________________________________________________________
@admin_router.callback_query(IsPrivateChat(), F.data == "help",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text()


# _________________________________________________________________________
# _______ удаление сообщений для админов чтоб не захломлять чат ___________
@admin_router.message(IsPrivateChat(), AdminFilter(), ~StateFilter(default_state))
async def negative_message(message: Message):
    await message.delete()
