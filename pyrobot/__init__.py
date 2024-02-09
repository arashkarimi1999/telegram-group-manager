from os import getenv
from pyrogram import Client
from dotenv import load_dotenv
load_dotenv()


api_id = int(getenv("api_id"))
api_hash = getenv("api_hash")
bot_token = getenv("bot_token")

if getenv("scheme"):
    proxy = {
        "scheme": getenv("scheme"),
        "hostname": getenv("hostname"),
        "port": int(getenv("port"))
    }
else:
    proxy = None


bot = Client(
    "groupe_manager",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    proxy=proxy, 
    plugins=dict(root=f"{__name__}/plugins"))
