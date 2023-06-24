from tgbot.infrastructure.db import sql_get_lang
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types
from pathlib import Path
from typing import Tuple, Any

I18N_DOMAIN = 'mybot'
BASE_DIR = Path(__file__).parent
print(BASE_DIR)
LOCALES_DIR = BASE_DIR / 'locales'


async def get_lang(user_id):
    locale = sql_get_lang(user_id)
    if locale:
        return locale["location"]


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]):
        user = types.User.get_current()
        return await get_lang(user.id)


def setup_middleware(dp):
    global i18n
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
