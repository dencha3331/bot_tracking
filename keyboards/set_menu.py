from aiogram import Bot
from aiogram.enums import BotCommandScopeType
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeAllPrivateChats
from lexicon import LEXICON

lexicon_menu: dict[str] = LEXICON['menu']


async def set_main_menu(bot: Bot):
    """Set list command menu button"""
    main_menu_commands = [
        BotCommand(command='/unblock',
                   description=lexicon_menu['unblock']),
        BotCommand(command='/list_group',
                   description=lexicon_menu['list_group']),
        BotCommand(command='/admin',
                   description=lexicon_menu['admin']),
        BotCommand(command='/cancel',
                   description=lexicon_menu['cancel']),
        BotCommand(command='/id',
                   description=lexicon_menu['id']),
        BotCommand(command='/help',
                   description=lexicon_menu['help']),
    ]

    await bot.set_my_commands(main_menu_commands, scope=BotCommandScopeAllPrivateChats())
