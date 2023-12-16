from aiogram import Bot
from aiogram.enums import BotCommandScopeType
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeAllPrivateChats


async def set_main_menu(bot: Bot):
    """Set list command menu button"""
    main_menu_commands = [
        BotCommand(command='/list_group',
                   description='Список групп'),
        BotCommand(command='/admin',
                   description='Админ панель'),
        BotCommand(command='/cancel',
                   description='Отмена'),
        BotCommand(command='/id',
                   description='Узнать id'),
        # BotCommand(command='/help',
        #            description='Справка для администраторов'),
    ]

    await bot.set_my_commands(main_menu_commands, scope=BotCommandScopeAllPrivateChats())
