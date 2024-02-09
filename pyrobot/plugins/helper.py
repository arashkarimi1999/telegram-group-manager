

async def is_admin(bot, update):
    # Get the chat member information
    chat_member = await bot.get_chat_member(chat_id=update.chat.id, user_id=update.from_user.id)

    # Check if the user is an admin
    if chat_member.status.value in ['administrator', 'owner']:
        return True
    else:
        return False