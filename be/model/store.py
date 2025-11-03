# be/model/store.py
from pymongo import MongoClient
import threading


class Store:
    def __init__(self, db_url="mongodb://localhost:27017/", db_name="bookstore"):
        # connect with short timeout so tests don't hang if MongoDB is not running
        try:
            self.client = MongoClient(db_url, serverSelectionTimeoutMS=1000)
        except Exception:
            # fallback: create a client without blocking (may still fail later)
            self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        # try to initialize indexes/collections, but don't fail tests if Mongo isn't available
        try:
            self.init_collections()
        except Exception:
            # ignore index creation errors (e.g., no Mongo server)
            pass

    def init_collections(self):
        """初始化必要集合（相当于原SQLite中的表）"""
        # 创建索引保证唯一性
        self.db.users.create_index("user_id", unique=True)
        self.db.user_store.create_index([("store_id", 1), ("user_id", 1)], unique=True)
        self.db.store.create_index([("store_id", 1), ("book_id", 1)], unique=True)
        self.db.new_order.create_index("order_id", unique=True)
        self.db.new_order_detail.create_index([("order_id", 1), ("book_id", 1)], unique=True)

    def get_db(self):
        return self.db


# 全局数据库实例
database_instance: Store = None

# 初始化完成事件（供测试等待服务启动）
init_completed_event = threading.Event()


def init_database(base_path: str = None):
    """Initialize the global database instance.

    base_path is kept for compatibility with previous code that passed
    the project parent path; currently unused but accepted.
    """
    global database_instance
    if database_instance is None:
        database_instance = Store()


# For legacy sqlite-based DBConn compatibility in this project we provide
# a sqlite connection (in-memory by default) and a helper get_db_conn()
# so existing db_conn.DBConn code continues to work.
import sqlite3

_sqlite_conn = None


def get_db_conn():
    global _sqlite_conn
    if _sqlite_conn is None:
        # allow cross-thread usage (Flask tests run server in a thread)
        _sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        cur = _sqlite_conn.cursor()
        # create tables expected by the existing DBConn SQL code
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user (
                user_id TEXT PRIMARY KEY,
                password TEXT,
                balance INTEGER,
                token TEXT,
                terminal TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_store (
                store_id TEXT PRIMARY KEY,
                user_id TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS store (
                store_id TEXT,
                book_id TEXT,
                book_info TEXT,
                stock_level INTEGER,
                PRIMARY KEY(store_id, book_id)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS new_order (
                order_id TEXT PRIMARY KEY,
                store_id TEXT,
                user_id TEXT,
                status TEXT,
                create_time INTEGER,
                pay_time INTEGER,
                ship_time INTEGER,
                receive_time INTEGER
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS new_order_detail (
                order_id TEXT,
                book_id TEXT,
                count INTEGER,
                price INTEGER
            );
            """
        )
        _sqlite_conn.commit()
    return _sqlite_conn


def get_db():
    global database_instance
    if database_instance is None:
        init_database()
    return database_instance.get_db()
