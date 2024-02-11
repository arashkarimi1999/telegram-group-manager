from pyrogram import filters
from pyrogram.types import Message


def active_match_filter(active_matches):
    async def func(flt, _, m: Message):
        return m.chat.id in flt.data

    return filters.create(func, data=active_matches)


async def is_admin(bot, update):
    # Get the chat member information
    chat_member = await bot.get_chat_member(chat_id=update.chat.id, user_id=update.from_user.id)

    # Check if the user is an admin
    if chat_member.status.value in ['administrator', 'owner']:
        return True
    else:
        return False