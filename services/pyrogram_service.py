from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMember

from configs.config import env
from logs import logger


bot_token = env('BOT_TOKEN')
api_id = int(env('PYROGRAM_API_ID'))
api_hash = env("PYROGRAM_API_HASH")


async def get_chat_members(chat_id) -> list[ChatMember] | None:
    logger.debug('start pyrogram')
    app = Client("EduardBot", api_id=api_id, api_hash=api_hash, bot_token=bot_token, in_memory=True)
    await app.start()

    try:
        chat_members = []
        async for member in app.get_chat_members(chat_id):
            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                continue
            chat_members = chat_members + [member]
        logger.debug("end pyrogram")
        return chat_members
    except ValueError as e:
        logger.error(e)
        return
    finally:
        await app.stop()
