from aiogram import Router, F
from aiogram.filters import Command, CommandStart, or_f, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
# from magic_filter import F

from db import crud
from filters.filters import IsPrivateChat, IsPayMember, NotAdminFilter, AdminFilter
from services import user_hand_serv
from lexicon import LEXICON

user_router: Router = Router()
lexicon_user = LEXICON['user_handler']


# _____________ Заглушка для пользователей на кнопку админ ______________________
@user_router.message(IsPrivateChat(), StateFilter(default_state), Command('admin'), NotAdminFilter())
async def add_users_start(message: Message) -> None:
    """Блокировка для пользователей кнопки admin в меню"""
    await message.answer(f"Вы не админ!!!!!")


# _______________________________________
# __________ Start ______________________
# _______________________________________
@user_router.message(IsPrivateChat(), StateFilter(default_state), CommandStart(), IsPayMember())
async def command_start(message: Message) -> None:
    """Получает список групп из бд и отправляет сообщением"""
    text: str = crud.get_links_for_user()
    if not text:
        await message.answer("Пока нет групп")
        return
    await message.answer(text=text)
    await message.answer(lexicon_user['welcome'])


# ___________________________________________________________________
# ______________ Команда в меню list_group __________________________
# ___________________________________________________________________
@user_router.message(IsPrivateChat(), Command("list_group"), StateFilter(default_state),
                     or_f(AdminFilter(), IsPayMember()))
async def get_links(message: Message, status: str) -> None:
    """Получает список групп из бд и отправляет сообщением без превью. Разбил на несколько сообщений
    по 30 групп в сообщении т.к. телеграм не позволяет отправлять длинные сообщения"""
    text: str = crud.get_links_for_user()
    if not text:
        await message.answer("Пока нет групп")
        return
    if len(text.split("\n")) > 30:
        res = []
        text2 = text.split("\n", )
        for i in range(len(text2)):
            res.append(text2[i])
            if i == 30:
                await message.answer("\n".join(res), disable_web_page_preview=True)
                res = []
        if res:
            await message.answer("\n".join(res), disable_web_page_preview=True)
    else:
        await message.answer(text=text, disable_web_page_preview=True)
    if status != "admin":
        await message.answer(lexicon_user["info_list_group"])


# __________________________________________________________________
# ________________ Кнопка в меню unblock ___________________________
# __________________________________________________________________
@user_router.message(IsPrivateChat(), NotAdminFilter(), Command('unblock'),
                     StateFilter(default_state), IsPayMember())
async def all_user(message: Message) -> None:
    """При удачной проверки на оплату в фильтрах вызов вспомогательной функции из
    user_hand_serv для разблокировки вызывающего"""
    await user_hand_serv.unban_user_button(message)
    await message.answer(lexicon_user["success_unblock"])


@user_router.message(IsPrivateChat(), NotAdminFilter(), Command('unblock'), StateFilter(default_state))
async def all_user(message: Message) -> None:
    """Не прошел фильтр оплаты"""
    await message.answer(lexicon_user["failure_unblock_filter"])


# __________ Не прошел не один фильтр _____________________________
@user_router.message(IsPrivateChat(), StateFilter(default_state))
async def all_user(message: Message) -> None:
    await message.delete()
    await message.answer(lexicon_user["info_unpaid"])





