from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.state import default_state
from aiogram import Router

from lexicon import LEXICON

clear_state_rout: Router = Router()
lexicon_clear: dict[str, str] = LEXICON['clear_state_hand']


@clear_state_rout.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message) -> None:
    """Command handler "/cancel" in default state"""
    await message.delete()
    await message.answer(lexicon_clear['nothing_cancel'])


@clear_state_rout.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext) -> None:
    """Handler of "/cancel" command in any states"""

    await message.delete()
    await message.answer(lexicon_clear['cancel'])
    await state.clear()

