from typing import Sequence

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, Document, User
from aiogram.fsm.state import default_state
from aiogram.types import FSInputFile

import keyboards.admin_hand_kb as keyboards
from configs.config import bot
from db.models import Groups
from filters.filters import AdminFilter, IsPrivateChat
from db import crud
from services import admin_hand_serv
from states.FSMStates import FSMAdminState
from keyboards import inline_kb

admin_router: Router = Router()


# @admin_router.message(F.content_type.in_(['new_chat_members', 'left_chat_member']))
# async def delete(message):
#     await bot.delete_message(message.chat.id, message.message_id)


@admin_router.message(IsPrivateChat(), CommandStart(), AdminFilter(), StateFilter(default_state))
async def command_start(message: Message) -> None:
    await message.answer("Вы админ воспользуйтесь кнопкой 'menu'")


@admin_router.message(IsPrivateChat(), Command('admin'), AdminFilter(), StateFilter(default_state))
async def add_users_start(message: Message, state: FSMContext) -> None:
    keyboard: InlineKeyboardMarkup = keyboards.menu_buttons()
    await message.delete()
    await message.answer(text="menu", reply_markup=keyboard)
    await state.set_state(FSMAdminState.menu)


@admin_router.message(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.menu))
async def negative_message(message: Message):
    await message.delete()


@admin_router.message(IsPrivateChat(), Command("id"))
async def get_id_user(message: Message) -> None:
    await message.delete()
    await message.answer(str(message.from_user.id))


@admin_router.callback_query(IsPrivateChat(), F.data == 'add_users',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def add_users_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Добавить юзера(ов)",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.add_user_confirm)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.add_user_confirm), AdminFilter())
async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == "yes":
        await callback.message.edit_text("Отправьте один NickName или список для добавления в оплаченные")
        await state.set_state(FSMAdminState.add_users)
    else:
        await callback.message.edit_text("Не добавляю")
        await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.add_users), AdminFilter())
async def save_users_end_unban(message: Message, state: FSMContext) -> None:
    users: list[str] = message.text.split('\n')
    res_list = []
    for nick_str in users:
        if '@' in nick_str:
            nick = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick = nick_str.split('/')[-1].strip()
        else:
            nick = nick_str.strip()
        # text_result = crud.add_users_by_nickname(nick)
        await admin_hand_serv.unban_user(nick)
        # res_list.append(text_result)
        res_list.append(f"{nick} добавлен в оплаченные")
    await message.answer("\n".join(res_list))

    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == 'del_users',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def del_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Удалить юзера(ов)",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.del_user_confirm)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.del_user_confirm), AdminFilter())
async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == "yes":
        await callback.message.edit_text("Отправьте один NickName или список для удаления")
        await state.set_state(FSMAdminState.del_users)
    else:
        await callback.message.edit_text("Не удаляю")
        await state.clear()


@admin_router.message(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.del_users))
async def del_user(message: Message, state: FSMContext) -> None:
    users: list[str] = message.text.split('\n')
    res_list = []
    for nick_str in users:
        if '@' in nick_str:
            nick = nick_str.replace('@', '').strip()
        elif '/' in nick_str:
            nick = nick_str.split('/')[-1].strip()
        else:
            nick = nick_str.strip()
        # text_result = crud.unpay_users_by_nickname(nick)
        await admin_hand_serv.ban_user(nick)
        # res_list.append(text_result)
        res_list.append(f"{nick} удален из оплаченных и из групп")
    await message.answer("\n".join(res_list))
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == 'change_link',
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text="Выберите группу", reply_markup=keyboard)
    await state.set_state(FSMAdminState.change_group_link_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.change_group_link_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
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
    await callback.message.edit_text("Не меняем")
    await state.clear()


@admin_router.message(IsPrivateChat(), AdminFilter(),
                      StateFilter(FSMAdminState.change_group_link))
async def change_group_link(message: Message, state: FSMContext) -> None:
    data: dict = await state.get_data()
    group_id: int = data['id']
    link: str = message.text
    save: bool = crud.update_group_link(group_id, link_chat=link)
    if save:
        await message.answer("Ссылка изменена")
    else:
        await message.answer("Не получилось!!! Попробуйте еще раз")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == "make_news_group",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    keyboard: InlineKeyboardMarkup = keyboards.change_link_group_keyboard()
    await callback.message.edit_text(text="Выберите группу", reply_markup=keyboard)
    await state.set_state(FSMAdminState.set_news_group_start)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group_start))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data: str = callback.data
    await state.update_data(id=int(data))
    await callback.message.edit_text(text="Сделать группу новостной (не удалять юзеров)?",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.set_news_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.set_news_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data: dict = await state.get_data()
    group_id: int = data['id']
    answer: str = callback.data
    if answer == "yes":
        crud.update_group_status(group_id)
        await callback.message.edit_text("Группа теперь новостная(пользователи не будут удаляться)")
    else:
        await callback.message.edit_text("Не меняю")

    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == "add_admin",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Отправьте id или список id по одному на строку "
                                     "кого надо сделать администратором",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, "Отмена"
                                     ))
    await state.set_state(FSMAdminState.add_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.add_admin), AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Не добавляю")
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.add_admin), AdminFilter())
async def save_admin(message: Message, state: FSMContext) -> None:
    admins: list[str] = message.text.replace("@", '').split('\n')
    for admin in admins:
        if not admin.isdigit():
            await message.answer(f"{admin} это не  похоже на id\n"
                                 f"id можно узнать по соответствующей кнопки в меню")
            return
        crud.add_admins_by_id(int(admin))
        await message.answer(f"id: {str(admin)} теперь админ")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == "del_admin",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def del_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Отправьте id или список id по одному на строку "
                                     "кого надо удалить с администраторов",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         1, "Отмена"
                                     ))
    await state.set_state(FSMAdminState.del_admin)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.del_admin), AdminFilter())
async def save_users(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Не удаляю")
    await state.clear()


@admin_router.message(IsPrivateChat(), StateFilter(FSMAdminState.del_admin), AdminFilter())
async def del_admin(message: Message, state: FSMContext) -> None:
    admins: list[str] = message.text.split('\n')
    for admin in admins:
        if not admin.isdigit():
            await message.answer(f"{admin} это не  похоже на id\n"
                                 f"id можно узнать по соответствующей кнопки в меню")
            return
        crud.del_admins_by_id(int(admin))
        await message.answer(f"id: {str(admin)} теперь админ")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == "check_and_ban_unpay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def choice_group_for_check_pay_user(callback: CallbackQuery, state: FSMContext) -> None:
    list_group: Sequence[Groups] = crud.get_list_groups()
    buttons = {str(group.id): group.nickname for group in list_group}
    buttons.update(all="Проверить все группы")
    keyboard = inline_kb.create_inline_callback_data_kb(
        1, **buttons, last_btn={'cancel': "Отмена"}
    )
    await callback.message.edit_text("Выберите группу для проверки", reply_markup=keyboard)
    await state.set_state(FSMAdminState.choice_group_check)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             F.data == 'cancel', AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Не чего не делаю")
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             F.data == 'all', AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Подтвердите проверку по всем группам",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.check_unpay_users_all_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.check_unpay_users_all_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:

    processing_message = await callback.message.edit_text("Подождите запрос обрабатывается.....")
    answer: str = callback.data
    if answer == "yes":
        text: FSInputFile = await admin_hand_serv.check_all_groups_not_pay_users_and_ban()
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=text)
        except TelegramBadRequest:
            await callback.message.answer("Некого удалять")
    else:
        await callback.message.edit_text("Не чего не делаю")
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=processing_message.message_id)
    await state.clear()
    # await add_users_start(callback, state)


@admin_router.callback_query(IsPrivateChat(), StateFilter(FSMAdminState.choice_group_check),
                             AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(id=str(callback.data))
    await callback.message.edit_text("Подтвердите проверку по всем группам",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Да", no="Нет"
                                     ))
    await state.set_state(FSMAdminState.check_unpay_users_one_group)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(),
                             StateFilter(FSMAdminState.check_unpay_users_one_group))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
    processing_message = await callback.message.edit_text("Подождите запрос обрабатывается.....")
    answer: str = callback.data
    data: dict = await state.get_data()
    group_id: int = data['id']
    if answer == "yes":
        text: FSInputFile = await admin_hand_serv.check_group_not_pay_users_and_ban(int(group_id))
        try:
            await bot.send_document(chat_id=callback.message.chat.id, document=text)
        except TelegramBadRequest:
            await callback.message.answer("Некого удалять")
    else:
        await callback.message.edit_text("Не чего не делаю")
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=processing_message.message_id)
    await state.clear()


@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Подтвердите отправку оплаченных пользователей",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.send_file_pay_user))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
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


@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_not_pay_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Подтвердите отправку неоплаченных пользователей",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_not_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.send_file_not_pay_user))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
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


@admin_router.callback_query(IsPrivateChat(), F.data == "send_file_all_user",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Подтвердите отправку всех пользователей",
                                     reply_markup=inline_kb.create_inline_callback_data_kb(
                                         2, yes="Отправить", no="Не отправлять"
                                     ))
    await state.set_state(FSMAdminState.send_file_all_pay_user)


@admin_router.callback_query(IsPrivateChat(), AdminFilter(), StateFilter(FSMAdminState.send_file_all_pay_user))
async def change_group_link_start(callback: CallbackQuery, state: FSMContext) -> None:
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


@admin_router.callback_query(IsPrivateChat(), F.data == "help",
                             StateFilter(FSMAdminState.menu), AdminFilter())
async def change_group_link(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Пункт меню: Добавить юзеров в оплаченные.\n"
                                     "При добавление юзера происходит его разблокировка по всем группам."
                                     "(если юзер говорит что он не разблокирован пусть зайдет в бота и воспользуется "
                                     "командой: Список групп)\n"
                                     "Пункт меню: Удалить из оплаченных юзеров и из групп\n"
                                     "При выборе этого пункта происходит блокировка юзера по всем группам\n"
                                     "Пункт меню: Сменить пригласительную ссылку группы\n"
                                     "При выборе этого пункта выберите группу в которой хотите сменить ссылку и "
                                     "отправьте новую\n"
                                     "Пункт меню: Сделать новостной (не удалять юзеров, сбор зашедших)\n"
                                     "При выборе этого пункта не оплаченные пользователи не будут с нее удаляться, "
                                     "а так же все новые пользователи пришедшее в нее будут сохранятся в базу\n"
                                     "Пункты меню: Со скачиванием файлов отправят файлы в csv формате "
                                     "соответствующие названию пункта\n"
                                     "Пункт меню: Проверить безбилетников по группам и забанить\n"
                                     "При выборе этого пункта предложит на выбор какую группу проверить на "
                                     "неоплаченных пользователей(которых вы не внесли в базу) и всех кого нет"
                                     "забанит и выкинет из группы\n"
                                     "Пункты меню: Добавить и удалить админа бота\n"
                                     "При выборе этого пункта вам потребуется id того кого вы хотите добавить. "
                                     "Id можно получить по пункту 'Узнать id' по кнопки 'menu' в левом "
                                     "нижнем углу\n"

                                     )
    await state.clear()



@admin_router.message(IsPrivateChat(), ~StateFilter(default_state), AdminFilter())
async def del_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Воспользуйтесь кнопкой меню")
