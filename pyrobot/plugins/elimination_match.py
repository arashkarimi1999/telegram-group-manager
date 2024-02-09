import re
from pyrogram import Client, filters
# from pyrobot.db.mongo_handler import mongo
from pyrobot.plugins.helper import is_admin


active_matches = {}


class EliminationMatch:
    def __init__(self, chat_id, max_error=3):
        self.chat_id = chat_id
        self.max_error = max_error
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
                "score": self.max_error
        }})

    def remove_player(self, user_id):
        del self.players[user_id]
    
    def is_player(self, user_id):
        if self.players.get(user_id):
            return True
        return False
    
    def sub_score(self, user_id):
        player = self.players.get(user_id)
        player['score'] -=  1
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


@Client.on_message(filters.command('start_elimination_match') & filters.group & filters.reply)
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
    +: to add a player to the match
    -: to subtract one score from a player
    results: to see the remaining players
    block: to block messaging for everyone
    open: to open messaging for everyone
    /add_admin: to add an admin to the match (only group admins)
    /remove_admin: to remove an admin from the match (only group admins)
    /finish_match: to finish the match (only group admins)"""
        await bot.send_message(
            chat_id=update.chat.id,
            text=text,
            reply_to_message_id=update.id)


@Client.on_message(filters.regex(re.compile(r'\+', re.IGNORECASE)) & filters.group & filters.reply)
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


@Client.on_message(filters.regex(re.compile(r'-', re.IGNORECASE)) & filters.group & filters.reply)
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


@Client.on_message(filters.regex(re.compile(r'results', re.IGNORECASE)) & filters.group)
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
        

@Client.on_message(filters.regex(re.compile(r'block', re.IGNORECASE)) & filters.group)
async def block_chat(bot, update):
    """Block messaging for everyone except match admins."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.block_chat()


@Client.on_message(filters.regex(re.compile(r'open', re.IGNORECASE)) & filters.group)
async def unblock_chat(bot, update):
    """Unblock messaging for everyone."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_admin(update.from_user.id):
            match.unblock_chat()


@Client.on_message(filters.command('add_admin') & filters.group & filters.reply)
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


@Client.on_message(filters.command('remove_admin') & filters.group & filters.reply)
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


@Client.on_message(filters.command('finish_match') & filters.group)
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


@Client.on_message(filters.all & filters.group)
async def handle_all_messages(bot, update):
    """handle all messages."""
    match = active_matches.get(update.chat.id)
    if match:
        if match.is_chat_blocked() and not match.is_admin(update.from_user.id):
            await bot.delete_messages(chat_id=update.chat.id, message_ids=update.id)

        if not (match.is_admin(update.from_user.id) or match.is_player(update.from_user.id)):
            await bot.delete_messages(chat_id=update.chat.id, message_ids=update.id)

