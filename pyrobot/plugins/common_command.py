from pyrogram import Client, filters
from pyrobot import bot


@bot.on_message(filters.command('start'))
async def bot_message(bot, update):
    """Start the bot."""
    await bot.send_message(
        chat_id=update.chat.id,
        text="Hello there!\nI am Mr.Alderson, a group manager bot. I can help \
you in group managing and holding competitions. Just add me to your group and\
 you can use my abilities(/help).")


@bot.on_message(filters.command('help'))
async def delete_message(bot, update):
    """Get the command list."""
    await bot.send_message(
        chat_id=update.chat.id,
        text="""here is a list of commands:
/start - start the bot
/help - get the command list
/bot - check if bot is online (only admins)
/delete - delete the replied message (only admins)
/tag - <num=20> mentions recently active members
/start_elimination_match - starts an elimination match
/start_name_the_movie - starts name the movie match
/add_admin - add a user to the match admin list (only admins)
/remove_admin - remove a user from the match admin list (only admins)
/finish_match - finish the match (only admins))""")
