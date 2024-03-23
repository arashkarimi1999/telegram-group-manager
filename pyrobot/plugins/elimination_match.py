import re
from pyrogram import Client, filters

from pyrobot.plugins.helper import is_admin, active_match_filter
# from pyrobot.db.mongo_handler import mongo
from pyrobot import bot


active_matches = {}


class EliminationMatch:
    def __init__(self, chat_id, max_error=3):
        self.chat_id = chat_id
        self.max_error = max_error
        self.admins = dict()
        self.players = dict()
        self.chat_blocked = False
        self.players_only = False

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
                "score": self.max_error, 
                "confirm": False
        }})

    def remove_player(self, user_id):
        del self.players[user_id]
    
    def is_player(self, user_id):
        if self.players.get(user_id):
            return True
        return False

    def confirm_player(self, user_id):
        player = self.players.get(user_id)
        player['confirm'] = True
        self.players[user_id] = player
        return player["score"]

    def sub_score(self, user_id):
        player = self.players.get(user_id)
        player['score'] -=  1
        self.players[user_id] = player
        return player["score"]

    def get_all_players(self):
        return [player for user_id, player in self.players.items()]
    
    def block_chat(self):
        self.chat_blocked = True
        self.players_only = False

    def make_players_only(self):
        self.chat_blocked = False
        self.players_only = True

    def unblock_chat(self):
        self.chat_blocked = False
        self.players_only = False

    def is_chat_blocked(self):
        return self.chat_blocked

    def is_players_only(self):
        return self.players_only
    
    def next(self):
        for player in self.get_all_players():
            if not player["confirm"]:
                score = self.sub_score(player["user_id"])
                if not score:
                    yield player
    
    def clear_confirm(self):
        for player in self.get_all_players():
            player['confirm'] = False
            user_id = player['user_id']
            self.players[user_id] = player

    def finish(self):
        self.players.clear()
        self.admins.clear()
        self.chat_blocked = False
        self.players_only = False


@bot.on_message(filters.command('start_elimination_match') & filters.group & filters.reply)
async def start_match(bot, update):
    """A command to start an elimination match."""
    if await is_admin(bot, update):
        if len(update.command) > 1:
            try:
                max_error = int(update.command[1])
            except ValueError:
                max_error = 3
        else:
            max_error = 3
        
        match = EliminationMatch(update.chat.id, max_error)
        active_matches[update.chat.id] = match

        match.add_admin(
            user_id=update.reply_to_message.from_user.id,
            name=update.reply_to_message.from_user.first_name
        )
        
        text = f"""elimination match started.
admin:[{update.reply_to_message.from_user.first_name}](tg://user?id={update.reply_to_message.from_user.id})
list of command:
    add: to add a player to the match
    +: to confirm a correct answer
    -: to subtract one score from a player
    results: to see the remaining players
    block: to block messaging for everyone
    players_only: to block messaging for everyone except match admins and players
    open: to open messaging for everyone
    next: to check this round and go to next
    /add_admin: to add an admin to the match (only group admins)
    /remove_admin: to remove an admin from the match (only group admins)
    /finish_match: to finish the match (only group admins)"""
        await bot.send_message(
            chat_id=update.chat.id,
            text=text,
            reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'add', re.IGNORECASE)) & filters.group & filters.reply)
async def add_player(bot, update):
    """A command to add a player to the elimination match."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.add_player(
                update.reply_to_message.from_user.id,
                update.reply_to_message.from_user.first_name
            )
            await bot.send_message(
                chat_id=update.chat.id,
                text="Player added successfully.",
                reply_to_message_id=update.id
            )


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'\+', re.IGNORECASE)) & filters.group & filters.reply)
async def add_score(bot, update):
    """A command to confirm a correct answer"""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            if match.is_player(update.reply_to_message.from_user.id):
                match.confirm_player(update.reply_to_message.from_user.id)
            else:
                await bot.send_message(
                    chat_id=update.chat.id,
                    text="user is not a player.",
                    reply_to_message_id=update.id
                )


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'-', re.IGNORECASE)) & filters.group & filters.reply)
async def sub_score(bot, update):
    """A command to subtract score from a player."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            if match.is_player(update.reply_to_message.from_user.id):
                score = match.sub_score(update.reply_to_message.from_user.id)
                if not score:
                    await bot.send_message(
                        chat_id=update.chat.id,
                        text=f"[{update.reply_to_message.from_user.first_name}](tg://user?id={update.reply_to_message.from_user.id}) ELEMINATED!"
                    )
                    match.remove_player(update.reply_to_message.from_user.id)
            else:
                await bot.send_message(
                    chat_id=update.chat.id,
                    text="user is not a player.",
                    reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'results', re.IGNORECASE)) & filters.group)
async def show_remaining_players(bot, update):
    """A command to see the remaining players."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            players = match.get_all_players()
            text = ''
            for player in players:
                text += f"[{player['name']}](tg://user?id={player['user_id']}) {player['score']}\n"
            await bot.send_message(
                chat_id=update.chat.id,
                text=text)
        

@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'block', re.IGNORECASE)) & filters.group)
async def block_chat(bot, update):
    """Block messaging for everyone except match admins."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.block_chat()


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'players_only', re.IGNORECASE)) & filters.group)
async def players_only(bot, update):
    """Block messaging for everyone except match admins and players."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.make_players_only()


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'open', re.IGNORECASE)) & filters.group)
async def unblock_chat(bot, update):
    """Unblock messaging for everyone."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.unblock_chat()


@bot.on_message(active_match_filter(active_matches) & filters.regex(re.compile(r'next', re.IGNORECASE)) & filters.group)
async def next(bot, update):
    """A coomand to check this round and go to next"""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            text = ''
            for player in match.next():
                text += f"[{player['name']}](tg://user?id={player['user_id']}) ELEMINATED!\n"
                match.remove_player(player['user_id'])

                await bot.send_message(
                    chat_id=update.chat.id,
                    text = text
                )

            match.clear_confirm()


@bot.on_message(active_match_filter(active_matches) & filters.command('add_admin') & filters.group & filters.reply)
async def add_admin(bot, update):
    """Add a user to the match admin list."""
    match = active_matches.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            match.add_admin(
                user_id=update.reply_to_message.from_user.id,
                name=update.reply_to_message.from_user.first_name
            )
            text = f"[{update.reply_to_message.from_user.first_name}](tg://user?id={update.reply_to_message.from_user.id}) added to the match admins."
            await bot.send_message(
                chat_id=update.chat.id,
                text=text,
                reply_to_message_id=update.id)
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text="No active match found.",
                reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_matches) & filters.command('remove_admin') & filters.group & filters.reply)
async def remove_admin(bot, update):
    """Remove a user from the match admin list."""
    match = active_matches.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            if match.is_admin(update.reply_to_message.from_user.id):
                match.remove_admin(user_id=update.reply_to_message.from_user.id)
                text = f"[{update.reply_to_message.from_user.first_name}](tg://user?id={update.reply_to_message.from_user.id}) removed from the match admins."
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


@bot.on_message(active_match_filter(active_matches) & filters.command('finish_match') & filters.group)
async def finish_match(bot, update):
    """Finish the match."""
    match = active_matches.get(update.chat.id)
    if await is_admin(bot, update):
        if match:
            match.finish()
            del active_matches[update.chat.id]
            await bot.send_message(
                chat_id=update.chat.id,
                text="The match has been finished.",
                reply_to_message_id=update.id)
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text="No active match found.",
                reply_to_message_id=update.id)


@bot.on_message(active_match_filter(active_matches) & filters.all & filters.group)
async def handle_all_messages(bot, update):
    """handle all messages."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_chat_blocked() and not match.is_admin(update.from_user.id):
            await bot.delete_messages(chat_id=update.chat.id, message_ids=update.id)

        if match.is_players_only() and not (match.is_admin(update.from_user.id) or match.is_player(update.from_user.id)):
            await bot.delete_messages(chat_id=update.chat.id, message_ids=update.id)

