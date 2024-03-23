from pyrogram import Client, filters
from pyrobot.plugins.helper import is_admin
from pyrobot import bot


@bot.on_message(filters.command('bot') & filters.group)
async def bot_message(bot, update):
    """Dummy function to check admins or if the bot is online."""
    if await is_admin(bot, update):
        await bot.send_message(chat_id=update.chat.id, text="yes my master", reply_to_message_id=update.id)


@bot.on_message(filters.command('delete') & filters.group & filters.reply)
async def delete_message(bot, update):
    """Deletes a massage."""
    if await is_admin(bot, update):
        await bot.delete_messages(chat_id=update.chat.id, message_ids=[update.reply_to_message.id, update.id])


@bot.on_message(filters.command('tag') & filters.group)
async def tag(bot, update):
    """Mentions n recent participants in the group."""
    if await is_admin(bot, update):
        if len(update.command) > 1:
            try:
                num_to_tag = int(update.command[1])
            except ValueError:
                num_to_tag = 20
        else:
            num_to_tag = 20

        unique_users = []
        ids = [id for id in range(update.id, update.id-1000, -1)]
        messages = await bot.get_messages(chat_id=update.chat.id, message_ids=ids)
        for message in messages:
            if message.from_user and message.from_user not in unique_users and not message.from_user.is_bot:
                unique_users.append(message.from_user)
                if len(unique_users) >= num_to_tag:
                    break
        
        chunk_size = 4

        user_chunks = [unique_users[i:i + chunk_size] for i in range(0, len(unique_users), chunk_size)]
        for chunk in user_chunks:
            mention_list = ', '.join([f"[{user.first_name}](tg://user?id={user.id})" for user in chunk])
            await bot.send_message(chat_id=update.chat.id, text=f"Hello there {mention_list}!")

