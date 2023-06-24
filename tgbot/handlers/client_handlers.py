from contextlib import suppress
from random import choice
from sqlite3 import IntegrityError
from typing import Union

from aiogram import types, Dispatcher
from aiogram.types import ParseMode
from aiogram.types.message import ContentTypes
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound, BotBlocked

from create_bot import bot
from create_bot import i18n
from tgbot.config import load_config
from tgbot.keyboards.client_keyboards import *

config = load_config(".env")

emoji_list = ["😘", "💋", "💖", "🤩", "🤑", "❤️‍🔥", "👌"]


# /start command for describing all available commands in bot
# TODO: add list of commands such as: /help, /about
# add commands in BotFather
# move sql to client_kb
async def start_commands(message: types.Message):
    user_id = message.from_user.id

    with suppress(IntegrityError):
        await add_user(user_id)

    await list_categories(message)


async def list_categories(message: Union[types.Message, types.CallbackQuery], **kwargs):
    # create markup menu
    user_id = message.from_user.id
    message_text, markup = await categories_keyboard(user_id)

    # check which type of message we get
    if isinstance(message, types.Message):

        await delete_prev_message(user_id)

        msg = await message.answer(text=message_text, reply_markup=markup)

        message_id = msg.message_id

        await add_message(user_id, message_id)

    else:
        call = message
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=message_text,
                                    reply_markup=markup)


async def help_menu(callback_query: types.CallbackQuery, **kwargs):
    message_text, markup = await help_keyboard()

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=message_text, reply_markup=markup)


async def about_menu(callback_query: types.CallbackQuery, **kwargs):
    message_text, markup = await about_keyboard()

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=message_text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def language_menu(callback_query: types.CallbackQuery, **kwargs):
    message_text, markup = await language_keyboard()

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=message_text, reply_markup=markup)


# @dp.callback_query_handler(lambda c: c.data.startswith('language:'))
async def change_language(callback_query: types.CallbackQuery):
    language_code = callback_query.data.split(':')[1]

    user_id = callback_query.from_user.id

    await update_lang(user_id, language_code)

    await i18n.trigger("pre_process", {})

    await list_categories(callback_query)


# send available products from selected category
async def list_products(callback_query: types.CallbackQuery, category_id, page, **kwargs):
    user_id = callback_query.from_user.id

    markup, message_text = await products_keyboard(category_id, page, user_id)

    try:
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=message_text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except MessageNotModified:
        await callback_query.answer(choice(emoji_list))


async def list_basket(callback_query: types.CallbackQuery, category_id, page, **kwargs):
    user_id = callback_query.from_user.id
    message_text, markup = await basket_keyboard(user_id, category_id, page)

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=message_text, reply_markup=markup)


async def change_basket(callback_query: types.CallbackQuery, category_id, page, product_id, saved_page):
    user_id = callback_query.from_user.id
    message_text, markup = await change_basket_keyboard(user_id, category_id, page, product_id, saved_page)

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=message_text, reply_markup=markup, parse_mode='HTML')


async def checkout(callback_query: types.CallbackQuery, category_id, page, **kwargs):
    user_id = callback_query.from_user.id
    await delete_prev_message(user_id)
    await payment(callback_query, category_id, page)


async def payment(callback_query: types.CallbackQuery, category_id, page):
    user_id = callback_query.from_user.id

    message_text = await get_payment_info(user_id)
    if not message_text.get("prices"):
        await callback_query.answer(text=message_text["text"], show_alert=True)
        return await list_categories(callback_query)

    if config.tg_bot.pay_token.split(':')[1] == 'TEST':
        msg_text = await get_test_info()
        await callback_query.answer(text=msg_text, show_alert=True)

    msg = await bot.send_invoice(
        chat_id=callback_query.message.chat.id,
        title=message_text["title"],
        description=message_text["description"],
        payload='some-invoice-payload-for-our-internal-use',
        provider_token=config.tg_bot.pay_token,
        currency="UAH",
        prices=message_text["prices"],
        photo_url=r"https://cdn.dribbble.com/users/1461925/screenshots/11875449/media/4335f1de5128f56c95293ac343ea71d1.jpg",
        photo_width=512,
        photo_height=512,
        start_parameter='start_parameter',
        need_email=False,
        need_phone_number=False,
        is_flexible=True)

    message_text, markup = await get_payment_keyboard(category_id, page)

    msg = await bot.send_message(chat_id=callback_query.message.chat.id, text=message_text, reply_markup=markup,
                                 parse_mode=ParseMode.HTML)
    message_id = msg.message_id
    await add_message(user_id, message_id)


# @dp.shipping_query_handler(lambda query: True)
async def process_shipping_query(shipping_query: types.ShippingQuery):
    # print(shipping_query.shipping_address)

    if not shipping_query.shipping_address.country_code == 'UA':
        return await bot.answer_shipping_query(
            shipping_query_id=shipping_query.id,
            ok=False,
            error_message="Our product is available only in Ukraine"
        )
    elif shipping_query.shipping_address.city not in ["Рокитне", "Нововолинськ"]:
        return await bot.answer_shipping_query(
            shipping_query_id=shipping_query.id,
            ok=False,
            error_message="Our product is available only in Рокитне and Нововолинськ"
        )

    BOLT_SHIPPING_OPTION = types.ShippingOption(
        id="Bolt_delivery",
        title="Bolt delivery"
    ).add(types.LabeledPrice("Bolt delivery", 20))

    UKRAINE_POST_SHIPPING_OPTION = types.ShippingOption(
        id="Nova_Poshta",
        title="Nova Poshta"
    ).add(types.LabeledPrice("Nova Poshta", 40))

    PICKUP_SHIPPING_OPTION = types.ShippingOption(
        id="Self-delivery",
        title="Self-delivery"
    ).add(types.LabeledPrice("Self-delivery", 0))

    shipping_options = [BOLT_SHIPPING_OPTION, UKRAINE_POST_SHIPPING_OPTION, PICKUP_SHIPPING_OPTION]
    # shipping_options.insert(BOLT_SHIPPING_OPTION, UKRAINE_POST_SHIPPING_OPTION, PICKUP_SHIPPING_OPTION)
    # print(shipping_options)

    await bot.answer_shipping_query(
        shipping_query_id=shipping_query.id,
        ok=True,
        shipping_options=shipping_options
    )


# @dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    # print('order_info:')
    # print(pre_checkout_query.order_info)
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# @dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    await list_categories(message)


# print('successful_payment:')
# pmnt = message.successful_payment.to_python()
# for key, val in pmnt.items():
# 	print(f'{key} = {val}')
# await bot.send_message(
#     message.chat.id,
#     MESSAGES['successful_payment'].format(
#         total_amount=message.successful_payment.total_amount // 100,
#         currency=message.successful_payment.currency
#     )
# )

# filter all callback_queries
# @dp.callback_query_handler(menu_callback_data.filter())
async def menu_filter(call: types.CallbackQuery, callback_data: dict):
    current_level = callback_data.get("level")
    category_id = callback_data.get("category_id")
    page = callback_data.get("page")
    product_id = callback_data.get("product_id")
    saved_page = callback_data.get("saved_page")

    # TODO: add more level such as: checkout,
    levels = {
        "0": list_categories,
        "0.5": help_menu,
        "0.6": about_menu,
        "0.7": language_menu,
        "1": list_products,
        "2": list_basket,
        "2.5": change_basket,
        "3": checkout
    }

    current_level_function = levels[current_level]

    await current_level_function(
        call,
        category_id=category_id,
        page=int(page),
        product_id=product_id,
        saved_page=int(saved_page)
    )


async def add_to_basket(call: types.CallbackQuery, product_id):  # **kwargs possible

    user_id = call.from_user.id
    await product_to_basket(user_id, product_id)
    await call.answer("ASS WE CAN")


# @dp.callback_query_handler(add_to_basket_callback_data.filter())
async def basket_filter(call: types.CallbackQuery, callback_data: dict):
    product_id = callback_data.get("product_id")

    await add_to_basket(call, product_id)


async def trash(message: types.Message):
    user_id = message.from_user.id
    await delete_prev_message(user_id)

    await list_categories(message)


async def delete_prev_message(user_id):
    with suppress(MessageNotModified, MessageToEditNotFound):
        msg = await get_message(user_id)

        markup = types.InlineKeyboardMarkup()
        markup.insert(
            types.InlineKeyboardButton(text="-", callback_data="NONE")
        )
        await bot.edit_message_text(chat_id=user_id, message_id=msg["message"], text=choice(emoji_list))


# @dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    print(f"Opss")
    return True


# register handlers from top to bottom
def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start_commands, commands=["start"])
    dp.register_callback_query_handler(menu_filter, menu_callback_data.filter())
    dp.register_callback_query_handler(basket_filter, add_to_basket_callback_data.filter())
    dp.register_callback_query_handler(change_language, lambda c: c.data.startswith('language:'))
    dp.register_shipping_query_handler(process_shipping_query, lambda query: True)
    dp.register_pre_checkout_query_handler(process_pre_checkout_query, lambda query: True)
    dp.register_message_handler(process_successful_payment, content_types=ContentTypes.SUCCESSFUL_PAYMENT)
    dp.register_message_handler(trash, content_types=ContentTypes.ANY)
    dp.register_errors_handler(error_bot_blocked, exception=BotBlocked)
