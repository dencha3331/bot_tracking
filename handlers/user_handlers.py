from aiogram import Router, F
from aiogram.filters import Command, CommandStart, or_f, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
# from magic_filter import F

from db import crud
from filters.filters import IsPrivateChat, IsPayMember, NotAdminFilter, AdminFilter

user_router: Router = Router()


@user_router.message(IsPrivateChat(), StateFilter(default_state), Command('admin'), NotAdminFilter())
async def add_users_start(message: Message) -> None:
    await message.answer(f"Вы не админ!!!!!")


@user_router.message(IsPrivateChat(), StateFilter(default_state), CommandStart(), IsPayMember())
async def command_start(message: Message) -> None:

    text: str = crud.get_links_for_user()
    if not text:
        await message.answer("Пока нет групп")
        return
    await message.answer(text=text)
    await message.answer("Если ранее у вас был неоплаченный абонемент, то после новой оплаты "
                         "потребуется до 15 минут для автоматической разблокировки вашего аккаунта. "
                         "После этого вы сможете присоединиться к группам.")
    await message.answer(f"Добро пожаловать. Чтобы получить список ссылок  "
                         f"выберите нужный пункт по кнопки 'menu' в левом нижнем углу")


@user_router.message(IsPrivateChat(), Command("list_group"), StateFilter(default_state),
                     or_f(AdminFilter(), IsPayMember()))
async def get_links(message: Message, status: str) -> None:
    text: str = crud.get_links_for_user()
    if not text:
        await message.answer("Пока нет групп")
        return
    await message.answer(text=text, disable_web_page_preview=True)
    if status != "admin":
        # await message.answer("Если вы не можете перейти по ссылки значит ранее у вас был неоплаченный абонемент, "
        #                      "подождите до 15 минут для автоматической разблокировки вашего аккаунта. "
        #                      "После этого вы сможете присоединиться к группам.")
        await message.answer(f"Чтобы получить список ссылок повторно "
                             f"выберите нужный пункт по кнопки 'menu' в левом нижнем углу")


@user_router.message(IsPrivateChat(), NotAdminFilter())
async def all_user(message: Message) -> None:
    await message.delete()
    await message.answer(f"Чтобы получить доступ к ресурсам обратитесь к администратору")

