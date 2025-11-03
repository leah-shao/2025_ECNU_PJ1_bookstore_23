# db_handler.py
from pymongo import MongoClient

def get_db():
    """
    获取MongoDB数据库连接
    """
    client = MongoClient("mongodb://localhost:27017/")
    db = client["bookstore"]
    return db
