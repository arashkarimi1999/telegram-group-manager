from dotenv import load_dotenv
load_dotenv(dotenv_path="config.env")
from pyrobot import bot
import logging


logging.basicConfig(
#     filename="log.txt",
#     filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


if __name__ == "__main__":
    bot.run()