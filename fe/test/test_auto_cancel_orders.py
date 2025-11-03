import time
from be.model import buyer as buyer_mod
from be.model import store as model_store


def setup_function(fn):
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # clear tables
    cur.execute("DELETE FROM new_order_detail;")
    cur.execute("DELETE FROM new_order;")
    cur.execute("DELETE FROM store;")
    conn.commit()


def test_auto_cancel_unpaid_restores_stock():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # prepare store and inventory
    cur.execute(
        "INSERT INTO store(store_id, book_id, book_info, stock_level) VALUES (?, ?, ?, ?)",
        ("s_timeout", "b1", '{"price":10}', 5),
    )

    now = int(time.time())
    old_order_id = "o_old"
    new_order_id = "o_new"

    # old order: created 2 hours ago
    cur.execute(
        "INSERT INTO new_order(order_id, store_id, user_id, status, create_time) VALUES (?, ?, ?, ?, ?)",
        (old_order_id, "s_timeout", "u1", "created", now - 7200),
    )
    cur.execute(
        "INSERT INTO new_order_detail(order_id, book_id, count, price) VALUES (?, ?, ?, ?)",
        (old_order_id, "b1", 2, 10),
    )

    # new order: created now
    cur.execute(
        "INSERT INTO new_order(order_id, store_id, user_id, status, create_time) VALUES (?, ?, ?, ?, ?)",
        (new_order_id, "s_timeout", "u2", "created", now),
    )
    cur.execute(
        "INSERT INTO new_order_detail(order_id, book_id, count, price) VALUES (?, ?, ?, ?)",
        (new_order_id, "b1", 1, 10),
    )

    # decrement stock to reflect orders reserved (simulate previous reservation)
    cur.execute("UPDATE store SET stock_level = stock_level - ? WHERE store_id = ? AND book_id = ?", (3, "s_timeout", "b1"))
    conn.commit()

    b = buyer_mod.Buyer()
    code, msg, cancelled = b.auto_cancel_unpaid(3600)
    assert code == 200
    assert cancelled == 1

    # old order should be removed
    cur.execute("SELECT COUNT(1) FROM new_order WHERE order_id = ?", (old_order_id,))
    assert cur.fetchone()[0] == 0

    # new order should remain
    cur.execute("SELECT COUNT(1) FROM new_order WHERE order_id = ?", (new_order_id,))
    assert cur.fetchone()[0] == 1

    # stock should have been restored by 2 (old order had count 2). original 5 -3 =2 then +2 => 4
    cur.execute("SELECT stock_level FROM store WHERE store_id = ? AND book_id = ?", ("s_timeout", "b1"))
    stock = cur.fetchone()[0]
    assert stock == 4
