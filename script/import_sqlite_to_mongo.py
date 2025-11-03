import sqlite3
from pymongo import MongoClient

sqlite_path = "./fe/data/book.db"
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["bookstore"]
books_col = db["books"]

# 读取 SQLite 数据
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM book")
columns = [desc[0] for desc in cursor.description]

for row in cursor.fetchall():
    doc = dict(zip(columns, row))
    books_col.insert_one(doc)

conn.close()
print("✅ 数据已导入 MongoDB！")
