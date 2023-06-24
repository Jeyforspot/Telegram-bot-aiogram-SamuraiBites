import sqlite3 as sq
from tgbot.config import load_config

config = load_config(".env")


def sql_start():
    global base, cur
    base = sq.connect(config.db.database)
    base.row_factory = sq.Row
    cur = base.cursor()
    if base:
        print("Base is working well")


def sql_add_user(user_id):
    cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
    base.commit()


def sql_add_product_to_basket(user_id, product_id):
    cur.execute(
        "INSERT INTO cart (user_id, product_id) VALUES (?, ?)"
        "ON CONFLICT (user_id, product_id) DO UPDATE SET amount = amount + 1",
        (user_id, product_id))
    base.commit()


def get_categories(user_id):
    cur.execute("SELECT \
    c.category_id,\
    COALESCE(t.category_name, c.category_name) AS category_name,\
    c.category_emoji\
    FROM categories c\
    LEFT JOIN category_translations t ON c.category_id = t.category_id AND t.language_id = (SELECT location FROM users WHERE user_id = (?))",
    (user_id, ))
    return cur.fetchall()


def get_product(category_id, page, user_id):
    cur.execute("SELECT * FROM \
    (SELECT \
    p.product_id,\
    COALESCE(t.product_name, p.product_name) AS product_name,\
    COALESCE(t.composition, p.composition) AS composition,\
    p.category_id,\
    p.gram,\
    p.price,\
    p.photos\
    FROM products p\
    LEFT JOIN product_translations t ON p.product_id = t.product_id AND t.language_id = (SELECT location FROM users WHERE user_id = (?))\
        WHERE p.category_id = (?))\
        LIMIT 1 OFFSET (?)",
    (user_id, category_id, page - 1,))

    return cur.fetchone()


def get_len_list_of_products(category_id):
    cur.execute("SELECT \
    COUNT(product_id) AS count\
    FROM products\
    WHERE category_id = (?)",
    (category_id, ))
    return cur.fetchone()


def get_basket(user_id):
    cur.execute("SELECT \
    cart.product_id,\
    COALESCE(product_translations.product_name, products.product_name) AS product_name,\
    COALESCE(t.category_name, categories.category_name) AS category_name,\
    cart.amount,\
    products.price * cart.amount AS price,\
    products.photos\
    FROM cart\
        INNER JOIN products ON products.product_id = cart.product_id\
        LEFT JOIN product_translations ON products.product_id = product_translations.product_id AND product_translations.language_id = (SELECT location FROM users WHERE user_id = (?))\
        INNER JOIN categories ON categories.category_id = products.category_id\
        LEFT JOIN category_translations t ON categories.category_id = t.category_id AND t.language_id = (SELECT location FROM users WHERE user_id = (?))\
        WHERE user_id = (?)\
        ORDER BY cart.rowid",
    (user_id, user_id, user_id,))
    return cur.fetchall()


def delete_product(product_id, user_id):
    try:
        cur.execute("UPDATE cart\
        SET amount = amount - 1\
        WHERE product_id = (?) AND user_id = (?)", (product_id, user_id))
    except:
        cur.execute("DELETE FROM cart\
        WHERE product_id = (?) AND user_id = (?)", (product_id, user_id))
    base.commit()


def sql_add_message(user_id, message_id):
    cur.execute("UPDATE users SET message = (?) WHERE user_id = (?)", (message_id, user_id))
    base.commit()


def sql_get_message(user_id):
    cur.execute("SELECT message FROM users WHERE user_id = (?)", (user_id,))
    return cur.fetchone()


def sql_get_lang(user_id):
    cur.execute("SELECT location FROM users WHERE user_id = (?)", (user_id,))
    return cur.fetchone()


def get_language():
    cur.execute("SELECT language_id FROM languages")
    return cur.fetchall()


def sql_change_language(user_id, location):
    cur.execute("UPDATE users SET location = (?) WHERE user_id = (?)", (location, user_id,))
    base.commit()
