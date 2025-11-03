import sqlite3
from flask import Flask
from be.view import debug
from be.model import store as model_store


def _make_app():
    app = Flask(__name__)
    app.register_blueprint(debug.bp_debug)
    return app


def setup_module(module):
    """Prepare an in-memory sqlite user row used by the debug endpoint tests."""
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    # ensure a known user exists for the happy-path test
    cur.execute(
        "INSERT OR REPLACE INTO user (user_id, balance) VALUES (?, ?)",
        ("test_user", 123),
    )
    conn.commit()


def test_user_balance_ok():
    app = _make_app()
    client = app.test_client()
    resp = client.get("/debug/user_balance", query_string={"user_id": "test_user"})
    assert resp.status_code == 200
    assert resp.get_json() == {"balance": 123}


def test_user_balance_missing_param():
    app = _make_app()
    client = app.test_client()
    resp = client.get("/debug/user_balance")
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "user_id required"


def test_user_not_found():
    app = _make_app()
    client = app.test_client()
    resp = client.get("/debug/user_balance", query_string={"user_id": "no_such_user"})
    assert resp.status_code == 404
    assert resp.get_json()["message"] == "user not found"
