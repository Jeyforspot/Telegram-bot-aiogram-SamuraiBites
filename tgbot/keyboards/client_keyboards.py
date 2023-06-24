import aiogram.utils.markdown as fmt
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.utils.callback_data import CallbackData
from babel import Locale
from create_bot import _
from tgbot.infrastructure.db import *

# TODO:
# try to add user_id in data
# delete "product_id"
# move func: make_menu_callback_data and make_add_to_basket_callback_data to another folder
menu_callback_data = CallbackData("menu_kb", "level", "category_id", "page", "product_id", "saved_page")
add_to_basket_callback_data = CallbackData("basket", "product_id")


def make_menu_callback_data(level, category_id=0, page=1, product_id=0, saved_page=1):
    return menu_callback_data.new(level=level, category_id=category_id, page=page, product_id=product_id,
                                  saved_page=saved_page)


def make_add_to_basket_callback_data(product_id):
    return add_to_basket_callback_data.new(product_id=product_id)


from tgbot.keyboards.client_paginator import InlineKeyboardPaginator


async def categories_keyboard(user_id):
    CURRENT_LEVEL = 0
    markup = InlineKeyboardMarkup(row_width=2)

    message_text = _("HI! I will take your order :) *I am a demo bot*")

    categories = get_categories(user_id)

    for category in categories:
        button_text = f'{category["category_emoji"]}{category["category_name"]}'

        callback_data = make_menu_callback_data(level=CURRENT_LEVEL + 1, category_id=category["category_id"])

        markup.insert(
            InlineKeyboardButton(text=button_text, callback_data=callback_data),
        )

    markup.row(
        await get_help_button(),
        await get_basket_button(),
        await get_about_button()
    )

    markup.row(
        await get_language_button()
    )

    return message_text, markup


async def help_keyboard():
    CURRENT_LEVEL = 0.5
    markup = InlineKeyboardMarkup()
    markup.insert(await get_menu_button())

    message_text = _(
        "If you stuck, the bot doesn't work or something is wrong, please write to a creator: {} or to our mail: {}").format(
        "@But_I_am_a_baka", "jeyforspot@gmail.com")

    return message_text, markup


async def about_keyboard():
    CURRENT_LEVEL = 0.6
    markup = InlineKeyboardMarkup()
    markup.insert(await get_menu_button())

    message_text = _("Hi, sweetie 💋💖{}").format(
        fmt.hide_link('https://i1.sndcdn.com/artworks-000360007827-0wcu9o-t500x500.jpg'))

    return message_text, markup


async def language_keyboard():
    CURRENT_LEVEL = 0.7
    markup = InlineKeyboardMarkup()

    languages = get_language()

    for language in languages:
        language_id = language["language_id"]

        lang_name = Locale.parse(language_id).get_display_name()

        markup.insert(InlineKeyboardButton(text=lang_name.title(), callback_data=f"language:{language_id}"))

    markup.row(await get_menu_button())

    message_text = _("Hello, please select the bot language")

    return message_text, markup


async def update_lang(user_id, language_code):
    sql_change_language(user_id, language_code)


async def products_keyboard(category_id, page, user_id):
    CURRENT_LEVEL = 1
    product = get_product(category_id, page, user_id)

    # form button_text for paginator
    message_text = _('{}\nComponent: {}\nWeight: {} gram\nCost: {}{} UAH').format(product["product_name"],
                                                                                  product["composition"],
                                                                                  product["gram"], product["price"],
                                                                                  fmt.hide_link(product["photos"]))

    # get product_id for "Add to basket" button
    product_id = product["product_id"]

    # get length of products from database depends on category_id
    # TODO:
    # try to change
    len_list_of_products = get_len_list_of_products(category_id)["count"]
    # TODO:
    # need to create or change these additional arguments
    # page_count get from function get_len_products
    markup = InlineKeyboardPaginator(
        page_count=len_list_of_products,
        current_page=page,
        level=CURRENT_LEVEL,
        category_id=category_id
    )

    markup.add_after(await get_basket_button(category_id=category_id, page=page),
                     await get_add_to_basket_button(product_id))
    markup.add_after(await get_menu_button())

    return markup.markup, message_text


async def basket_keyboard(user_id, category_id, page):
    CURRENT_LEVEL = 2

    markup = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(
            text=_("✏Change"),
            callback_data=make_menu_callback_data(level=CURRENT_LEVEL + 0.5,
                                                  category_id=category_id,
                                                  saved_page=page)),
            InlineKeyboardButton(
                text=_("✅Checkout"),
                callback_data=make_menu_callback_data(
                    level=CURRENT_LEVEL + 1,
                    page=page,
                    category_id=category_id))]
    ])

    # a small crutch to check if we execute "basket_keyboard" from menu but not from "products_keyboard"
    if int(category_id):
        markup.add(InlineKeyboardButton(text=_('↪Back'), callback_data=make_menu_callback_data(level=CURRENT_LEVEL - 1,
                                                                                               category_id=category_id,
                                                                                               page=page)))

    markup.add(await get_menu_button())

    basket = get_basket(user_id)

    message_text = _("Your order: ") + ("".join(
        _('\n\n{}({})\n{}pcs., {}UAH').format(product["product_name"], product["category_name"], product["amount"],
                                              product["price"]) for product in basket) or _("empty"))

    return message_text, markup


async def change_basket_keyboard(user_id, category_id, page, product_id, saved_page):
    CURRENT_LEVEL = 2.5
    # print(page, saved_page)

    if product_id:
        delete_product(product_id, user_id)

    basket = get_basket(user_id)

    if not basket:
        markup = InlineKeyboardMarkup(row_width=1)

        markup.add(InlineKeyboardButton(text=_('↪Back'),
                                        callback_data=make_menu_callback_data(level=2,
                                                                              category_id=category_id,
                                                                              page=saved_page)),
                   await get_menu_button())
        message_text = _("Your basket is empty")
        return message_text, markup

    # len_list_of_products = get_len_list_of_products(category_id)["count"]
    # TODO:
    # need to create or change these additional arguments
    # page_count get from function get_len_products

    markup = InlineKeyboardPaginator(
        page_count=len(basket),
        current_page=page,
        level=CURRENT_LEVEL,
        category_id=category_id,
        saved_page=saved_page

    )

    page = markup.current_page
    message_text = ""

    for value, product in enumerate(basket, start=1):
        if value == page:
            message_text = _('{}({})\n{}pcs., {}UAH, {}').format(product["product_name"], product["category_name"],
                                                                 product["amount"], product["price"],
                                                                 fmt.hide_link(product["photos"]))
            product_id = product["product_id"]

    markup.add_after(await get_delete_button(CURRENT_LEVEL, category_id, page, product_id, saved_page),
                     InlineKeyboardButton(text=_('↪Back'),
                                          callback_data=make_menu_callback_data(level=2, category_id=category_id,
                                                                                page=saved_page)))
    markup.add_after(await get_menu_button())
    return message_text, markup.markup


async def get_test_info():
    message_text = _(
        "Don't worry. It`s a test payment. Use: \nCard number: 4242 4242 4242 4242 \nExpiration data: 04/24 \nCVC code: 242")

    return message_text


async def get_payment_info(user_id):
    CURRENT_LEVEL = 3

    PRICE = []

    basket = get_basket(user_id)

    for product in basket:
        PRICE.append(LabeledPrice(
            label=_('\n\n{}({})\n{}pcs.').format(product["product_name"], product["category_name"], product["amount"]),
            amount=product["price"]))

    if PRICE:
        message_text = {"title": _("PAYMENT"), "description": _("YOUR ORDER"), "prices": PRICE}
    else:
        message_text = {"text": _("Your basket is empty!")}

    return message_text


async def get_payment_keyboard(category_id, page):
    CURRENT_LEVEL = 3

    message_text = _("Available options:")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text=_('↪Back'), callback_data=make_menu_callback_data(CURRENT_LEVEL - 1, page=page,
                                                                                           category_id=category_id)),
               await get_menu_button())

    return message_text, markup


async def get_add_to_basket_button(product_id):
    return InlineKeyboardButton(text=_('💢Add to basket'),
                                callback_data=make_add_to_basket_callback_data(product_id=product_id))


async def get_delete_button(CURRENT_LEVEL, category_id, page, product_id, saved_page):
    return InlineKeyboardButton(text=_('❌Delete'),
                                callback_data=make_menu_callback_data(level=CURRENT_LEVEL, category_id=category_id,
                                                                      page=page, product_id=product_id,
                                                                      saved_page=saved_page))


async def get_basket_button(**kwargs):
    if kwargs:
        return InlineKeyboardButton(text=_('🛒Basket'),
                                    callback_data=make_menu_callback_data(level=2, category_id=kwargs["category_id"],
                                                                          page=kwargs["page"]))
    else:
        return InlineKeyboardButton(text=_('🛒Basket'), callback_data=make_menu_callback_data(level=2))


async def get_help_button():
    return InlineKeyboardButton(text=_('❓Help'), callback_data=make_menu_callback_data(level=0.5))


async def get_about_button():
    return InlineKeyboardButton(text=_('📃About'), callback_data=make_menu_callback_data(level=0.6))


async def get_language_button():
    return InlineKeyboardButton(text=_('🌐Language'), callback_data=make_menu_callback_data(level=0.7))


async def get_menu_button():
    return InlineKeyboardButton(text=_('🛎Menu'), callback_data=make_menu_callback_data(level=0))


# async def get_back_button(CURRENT_LEVEL, **kwargs):
# if kwargs:
# 	return InlineKeyboardButton(text='Back', callback_data=make_menu_callback_data(level=CURRENT_LEVEL-1, category_id=kwargs["category_id"], page=kwargs["page"]))
# else:
# 	return InlineKeyboardButton(text='basket', callback_data=make_menu_callback_data(level=CURRENT_LEVEL-1))
# 	return InlineKeyboardButton(text='Back', callback_data=make_menu_callback_data(level=CURRENT_LEVEL-1, category_id=kwargs["category_id"], page=kwargs["page"]))


async def product_to_basket(user_id, product_id):
    sql_add_product_to_basket(user_id, product_id)


async def get_payment_button():
    return InlineKeyboardButton(text='', pay=True)


async def add_message(user_id, message_id):
    sql_add_message(user_id, message_id)


async def get_message(user_id):
    return sql_get_message(user_id)


async def add_user(user_id):
    return sql_add_user(user_id)
