from be.model.seller import Seller
from be.model import store as model_store


def setup_function(fn):
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # clear relevant tables
    cur.execute("DELETE FROM new_order_detail;")
    cur.execute("DELETE FROM new_order;")
    cur.execute("DELETE FROM store;")
    cur.execute("DELETE FROM user_store;")
    cur.execute("DELETE FROM user;")
    conn.commit()


def test_add_book_no_user():
    s = Seller()
    code, msg = s.add_book("no_user", "s1", "b1", "{}", 10)
    assert code == 511


def test_create_store_and_add_book_missing_store():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("u_seller", 0, "p"))
    conn.commit()

    s = Seller()
    # creating store should succeed
    code, msg = s.create_store("u_seller", "store_x")
    assert code == 200

    # add_book with existing user but no book should succeed (store exists)
    code, msg = s.add_book("u_seller", "store_x", "bk1", '{"price":10}', 5)
    assert code == 200


def test_add_book_already_exists():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("u2", 0, "p"))
    cur.execute("INSERT INTO user_store (store_id, user_id) VALUES (?, ?)", ("s2", "u2"))
    # insert an existing book
    cur.execute("INSERT INTO store (store_id, book_id, book_info, stock_level) VALUES (?, ?, ?, ?)",
                ("s2", "book1", '{"price":5}', 10))
    conn.commit()

    s = Seller()
    code, msg = s.add_book("u2", "s2", "book1", '{"price":5}', 10)
    assert code == 516


def test_ship_order_invalid_and_authorization_and_status():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # ensure seller user exists and a mapping exists
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("seller_owner", 0, "p"))
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("another", 0, "p"))
    cur.execute("INSERT INTO user_store (store_id, user_id) VALUES (?, ?)", ("store_ship", "seller_owner"))
    # create an order with created status
    cur.execute("INSERT INTO new_order (order_id, store_id, user_id, status, create_time) VALUES (?, ?, ?, ?, ?)",
                ("order_1", "store_ship", "buyer_x", "created", 1))
    conn.commit()

    s = Seller()
    # invalid order id
    code, msg = s.ship_order("seller_owner", "no_such")
    assert code == 518

    # auth fail when different user attempts shipping
    code, msg = s.ship_order("another", "order_1")
    assert code == 401

    # status not paid -> expect 530
    code, msg = s.ship_order("seller_owner", "order_1")
    assert code == 530
