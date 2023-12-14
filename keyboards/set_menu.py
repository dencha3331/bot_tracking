from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    """Set list command menu button"""
    main_menu_commands = [
        BotCommand(command='/list_group',
                   description='Список групп'),
        BotCommand(command='/admin',
                   description='Админ панель'),
        BotCommand(command='/cancel',
                   description='Отмена'),
        # BotCommand(command='/add_users',
        #            description='Добавить пользователей'),
        # BotCommand(command='/del_users',
        #            description='Удалить пользователей'),
        BotCommand(command='/id',
                   description='Узнать id'),
        # BotCommand(command='/change_link',
        #            description='Удалить пользователей'),
        # BotCommand(command='/get_all_users',
        #            description='Получить список пользователей'),
    ]
    await bot.set_my_commands(main_menu_commands)
