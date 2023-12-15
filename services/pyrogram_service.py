from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMember

from configs.config import env, bot
from db import crud

api_id = int(env('PYROGRAM_API_ID'))
api_hash = env("PYROGRAM_API_HASH")
bot_token = env('BOT_TOKEN')


async def get_chat_members(chat_id) -> list[ChatMember]:
    print('start payogram')
    app = Client("EduardBot", api_id=api_id, api_hash=api_hash, bot_token=bot_token, in_memory=True)
    chat_members = []
    chat_members_nick = []
    await app.start()
    async for member in app.get_chat_members(chat_id):
        # print(member)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            continue
        chat_members = chat_members + [member]
        # chat_members_nick = chat_members_nick + [member.user.id]
    await app.stop()
    return chat_members
