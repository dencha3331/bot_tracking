from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.state import default_state
from aiogram import Router, F


clear_state_rout: Router = Router()


@clear_state_rout.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message) -> None:
    """Command handler "/cancel" in default state"""
    await message.delete()
    await message.answer("Отменять нечего")


@clear_state_rout.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext) -> None:
    """Handler of "/cancel" command in any states"""

    await message.delete()
    await message.answer("Отмена")
    await state.clear()

