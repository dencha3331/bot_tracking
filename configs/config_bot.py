from aiogram import Bot

from db import crud


settings = crud.get_settings()


bot = Bot(token=str(settings.bot_token))
