from be.model.buyer import Buyer
from be.model import store as model_store


def setup_function(fn):
    # Ensure a clean-ish DB state for each test by using the shared in-memory conn
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # clear relevant tables (keep schema)
    cur.execute("DELETE FROM new_order_detail;")
    cur.execute("DELETE FROM new_order;")
    cur.execute("DELETE FROM store;")
    cur.execute("DELETE FROM user_store;")
    cur.execute("DELETE FROM user;")
    conn.commit()


def test_new_order_non_exist_user():
    b = Buyer()
    code, msg, oid = b.new_order("no_user", "s1", [("b1", 1)])
    assert code == 511


def test_new_order_non_exist_store():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("u1", 0, "p"))
    conn.commit()

    b = Buyer()
    code, msg, oid = b.new_order("u1", "missing_store", [("b1", 1)])
    assert code == 513


def test_new_order_non_exist_book():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # insert buyer user
    cur.execute("INSERT INTO user (user_id, balance, password) VALUES (?, ?, ?)", ("u2", 1000, "p"))
    # insert a store mapping (store exists from buyer perspective) but no book records
    cur.execute("INSERT INTO user_store (store_id, user_id) VALUES (?, ?)", ("s2", "seller_x"))
    conn.commit()

    b = Buyer()
    code, msg, oid = b.new_order("u2", "s2", [("book_missing", 1)])
    assert code == 515


def test_cancel_order_authorization_and_status():
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # create an order owned by 'owner1'
    cur.execute("INSERT INTO new_order (order_id, store_id, user_id, status, create_time) VALUES (?, ?, ?, ?, ?)",
                ("o_auth", "sX", "owner1", "created", 1))
    conn.commit()

    b = Buyer()
    # authorization fail when different user cancels
    code, msg = b.cancel_order("other_user", "o_auth")
    assert code == 401

    # change order status to paid and attempt cancel by owner -> expect error 530
    cur.execute("UPDATE new_order SET user_id=?, status=? WHERE order_id=?", ("owner2", "paid", "o_auth"))
    conn.commit()
    code, msg = b.cancel_order("owner2", "o_auth")
    assert code == 530
