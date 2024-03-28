import re
from os import getenv
from pyrogram import Client, filters

from pyrobot.plugins.helper import is_admin, active_match_filter
# from pyrobot.db.mongo_handler import mongo
from pyrobot import bot


active_games = {}


class NameTheMovie:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.admins = dict()
        self.players = dict()
        self.chat_blocked = False

    def add_admin(self, user_id, name):
        self.admins.update({
            user_id:{
                "user_id": user_id,
                "name": name,
        }})

    def remove_admin(self, user_id):
        del self.admins[user_id]

    def is_admin(self, user_id):
        if self.admins.get(user_id):
            return True
        return False

    def add_player(self, user_id, name):
        self.players.update({
            user_id:{
                "user_id": user_id,
                "name": name,
                "score": 0
        }})
    
    def is_player(self, user_id):
        if self.players.get(user_id):
            return True
        return False
    
    def add_score(self, user_id, score=10):
        player = self.players.get(user_id)
        player['score'] +=  score
        self.players[user_id] = player
        return player["score"]

    def sub_score(self, user_id, score=5):
        player = self.players.get(user_id)
        player['score'] -=  score
        self.players[user_id] = player
        return player["score"]

    def get_all_players(self):
        return [player for user_id, player in self.players.items()]
    
    def block_chat(self):
        self.chat_blocked = True

    def unblock_chat(self):
        self.chat_blocked = False

    def is_chat_blocked(self):
        return self.chat_blocked
    
    def finish(self):
        self.players.clear()
        self.admins.clear()
        self.chat_blocked = False


@bot.on_message(filters.command('start_name_the_movie') & filters.group & filters.reply)
async def start_match(bot, update):
    """A command to start name the movie match."""
    if getenv("debug") == 'True':
        print("start_name_the_movie")

    if await is_admin(bot, update):
        
        match = NameTheMovie(update.chat.id)
        active_games[update.chat.id] = match

        match.add_admin(
            user_id=update.reply_to_message.from_user.id,
            name=update.reply_to_message.from_user.first_name
        )
        
        text = f"""name the movie match started.
admin:{update.reply_to_message.from_user.mention()}
list of command:
    + <num=10>: to add score to a player

    - <num=5>: to subtract score from a player

    results: to see the results

    block: to block messaging for everyone

    open: to open messaging for everyone

    /add_admin: to add an admin to the match (only group admins)

    /remove_admin: to remove an admin from the match (only group admins)

    /finish_match: to finish the match (only group admins)"""
        await bot.send_message(
            chat_id=update.chat.id,
            text=text,
            reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_games) & filters.regex(re.compile(r'^\+\s*(\d+)?$', re.IGNORECASE)) & filters.group & filters.reply)
async def add_score(bot, update):
    """A command to add score to a player."""
    if getenv("debug") == 'True':
        print("+")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):

            command = re.match(r'^\+\s*(\d+)?$', update.text)
            if command and command.group(1):
                try:
                    score = int(command.group(1))
                except ValueError:
                    score = 10
            else:
                score = 10

            if not match.is_player(update.reply_to_message.from_user.id):
                match.add_player(
                    update.reply_to_message.from_user.id,
                    update.reply_to_message.from_user.first_name
                )

            match.add_score(update.reply_to_message.from_user.id, score)


@bot.on_message(active_match_filter(active_games) & filters.regex(re.compile(r'^-\s*(\d+)?$', re.IGNORECASE)) & filters.group & filters.reply)
async def sub_score(bot, update):
    """A command to subtract score from a player."""
    if getenv("debug") == 'True':
        print("-")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):

            command = re.match(r'^-\s*(\d+)?$', update.text)
            if command and command.group(1):
                try:
                    score = int(command.group(1))
                except ValueError:
                    score = 5
            else:
                score = 5

            if not match.is_player(update.reply_to_message.from_user.id):
                match.add_player(
                    update.reply_to_message.from_user.id,
                    update.reply_to_message.from_user.first_name
                )
            match.sub_score(update.reply_to_message.from_user.id, score)


@bot.on_message(active_match_filter(active_games) & filters.regex(re.compile(r'results', re.IGNORECASE)) & filters.group)
async def show_results(bot, update):
    """A command to see the results."""
    if getenv("debug") == 'True':
        print("results")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            players = match.get_all_players()
            if players:
                sorted_players = sorted(players, key=lambda x: x['score'], reverse=True)
                text = ''
                for i, player in enumerate(sorted_players):
                    if i == 0:
                        text += f"🥇[{player['name']}](tg://user?id={player['user_id']}) - {player['score']}\n"
                    elif i == 1:
                        text += f"🥈[{player['name']}](tg://user?id={player['user_id']}) - {player['score']}\n"
                    elif i == 2:
                        text += f"🥉[{player['name']}](tg://user?id={player['user_id']}) - {player['score']}\n"
                    else:
                        text += f"🏅[{player['name']}](tg://user?id={player['user_id']}) - {player['score']}\n"

                await bot.send_message(
                    chat_id=update.chat.id,
                    text=text)
            

@bot.on_message(active_match_filter(active_games) & filters.regex(re.compile(r'block', re.IGNORECASE)) & filters.group)
async def block_chat(bot, update):
    """Block messaging for everyone except match admins."""
    if getenv("debug") == 'True':
        print("block")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.block_chat()


@bot.on_message(active_match_filter(active_games) & filters.regex(re.compile(r'open', re.IGNORECASE)) & filters.group)
async def unblock_chat(bot, update):
    """Unblock messaging for everyone."""
    if getenv("debug") == 'True':
        print("open")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.unblock_chat()


@bot.on_message(active_match_filter(active_games) & filters.command('add_admin') & filters.group & filters.reply)
async def add_admin(bot, update):
    """Add a user to the match admin list."""
    if getenv("debug") == 'True':
        print("add_admin")

    match = active_games.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            match.add_admin(
                user_id=update.reply_to_message.from_user.id,
                name=update.reply_to_message.from_user.first_name
            )
            text = f"{update.reply_to_message.from_user.mention()} added to the match admins."
            await bot.send_message(
                chat_id=update.chat.id,
                text=text,
                reply_to_message_id=update.id)
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text="No active match found.",
                reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_games) & filters.command('remove_admin') & filters.group & filters.reply)
async def remove_admin(bot, update):
    """Remove a user from the match admin list."""
    if getenv("debug") == 'True':
        print("remove_admin")

    match = active_games.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            if match.is_admin(update.reply_to_message.from_user.id):
                match.remove_admin(user_id=update.reply_to_message.from_user.id)
                text = f"{update.reply_to_message.from_user.mention()} removed from the match admins."
                await bot.send_message(
                    chat_id=update.chat.id,
                    text=text,
                    reply_to_message_id=update.id)
            else:
                await bot.send_message(
                    chat_id=update.chat.id,
                    text="User is not an admin.",
                    reply_to_message_id=update.id)
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text="No active match found.",
                reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_games) & filters.command('finish_match') & filters.group)
async def finish_match(bot, update):
    """Finish the match."""
    if getenv("debug") == 'True':
        print("finish_match")

    match = active_games.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            match.finish()
            del active_games[update.chat.id]
            await bot.send_message(
                chat_id=update.chat.id,
                text="The match has been finished.",
                reply_to_message_id=update.id)
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text="No active match found.",
                reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_games) & filters.all & filters.group)
async def handle_all_messages(bot, update):
    """handle all messages."""
    if getenv("debug") == 'True':
        print("handle_all_messages")

    match = active_games.get(update.chat.id)
    if match:
        if match.is_chat_blocked() and not match.is_admin(update.from_user.id):
            await bot.delete_messages(chat_id=update.chat.id, message_ids=update.id)

