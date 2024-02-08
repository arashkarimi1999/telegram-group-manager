import asyncio
import logging
from os import getenv
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

api_id = int(getenv("api_id"))
api_hash = getenv("api_hash")
bot_token = getenv("bot_token")
proxy = {
    "scheme": "socks5",
    "hostname": "127.0.0.1",
    "port": 10808
}

# # first time run to create session
# app = Client(
#     "groupe_manager",
#     api_id=api_id,
#     api_hash=api_hash,
#     bot_token=bot_token,
#     proxy=proxy)
# app.run()
