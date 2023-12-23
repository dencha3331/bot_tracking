#!/usr/bin/env python3
from aiogram import Dispatcher
import asyncio

from aiogram.types import BotCommandScopeDefault
from redis.asyncio.client import Redis
from aiogram.fsm.storage.redis import RedisStorage

from handlers.clear_state_hand import clear_state_rout
from handlers.user_handlers import user_router
from handlers.admin_handlers import admin_router
from handlers.chat_handlers import chat_router
from keyboards.set_menu import set_main_menu
# from configs.config_bot import bot
from configs.config import bot
from logs import logger


async def main():
    redis: Redis = Redis(host='localhost')
    storage: RedisStorage = RedisStorage(redis=redis)

    dp: Dispatcher = Dispatcher(storage=storage)
    dp.include_router(clear_state_rout)
    dp.include_router(admin_router)

    # dp.update.outer_middleware(AdminMiddleware())
    # admin_router.callback_query.middleware(AdminMiddleware())
    # dp.update.outer_middleware(UserPermissionMiddleware())
    # user_router.message.middleware(UserPermissionMiddleware())

    dp.include_router(user_router)
    dp.include_router(chat_router)
    # await bot.delete_my_commands(scope=BotCommandScopeDefault())
    await set_main_menu(bot)
    logger.info("bot start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
