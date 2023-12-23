from environs import Env
from aiogram import Bot


env: Env = Env()
env.read_env()
bot = Bot(token=env('BOT_TOKEN'))



