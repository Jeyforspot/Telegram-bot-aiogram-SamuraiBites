from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from tgbot.middlewares.i18n import setup_middleware

from tgbot.config import load_config

config = load_config(".env")

bot = Bot(token=config.tg_bot.token)
dp = Dispatcher(bot)

i18n = setup_middleware(dp)
_ = i18n.gettext
