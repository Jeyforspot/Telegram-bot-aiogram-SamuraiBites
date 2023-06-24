from create_bot import dp
from aiogram.utils import executor

from tgbot.handlers.client_handlers import register_handlers_client
from tgbot.infrastructure.db import sql_start
import logging


async def on_startup(_):
    sql_start()


def register_all_handlers(dp):
    register_handlers_client(dp)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)

register_all_handlers(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
