"""Import books from fe/data/book.db into local MongoDB and create text index.

Usage (PowerShell):
    python fe/data/import_books_mongo.py --mongo-url mongodb://localhost:27017/ --db bookstore --sqlite-file fe/data/book.db

This script will read the `book` table from the sqlite DB and insert documents
into the `books` collection. It will then create a text index on title, tags,
book_intro and content for full-text search.
"""
import argparse
import sqlite3
from pymongo import MongoClient, ASCENDING, TEXT


def import_books(sqlite_file, mongo_url="mongodb://localhost:27017/", mongo_db="bookstore"):
    conn = sqlite3.connect(sqlite_file)
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags FROM book")

    client = MongoClient(mongo_url)
    db = client[mongo_db]
    books = db.books
    # Optional: remove existing to reimport
    books.delete_many({})

    rows = cur.fetchall()
    docs = []
    for r in rows:
        doc = {
            "id": r[0],
            "title": r[1],
            "author": r[2],
            "publisher": r[3],
            "original_title": r[4],
            "translator": r[5],
            "pub_year": r[6],
            "pages": r[7],
            "price": r[8],
            "currency_unit": r[9],
            "binding": r[10],
            "isbn": r[11],
            "author_intro": r[12],
            "book_intro": r[13],
            "content": r[14],
            "tags": r[15],
        }
        docs.append(doc)

    if docs:
        books.insert_many(docs)

    # create text index across several fields; weight title higher
    try:
        books.create_index(
            [("title", TEXT), ("tags", TEXT), ("book_intro", TEXT), ("content", TEXT), ("author_intro", TEXT)],
            name="text_index",
            default_language="english",
            weights={"title": 10, "tags": 5, "book_intro": 2, "content": 1},
        )
    except Exception as e:
        print("Warning: could not create text index:", e)

    print(f"Imported {len(docs)} books into MongoDB {mongo_db}.books")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default="mongodb://localhost:27017/")
    parser.add_argument("--db", default="bookstore")
    parser.add_argument("--sqlite-file", default="fe/data/book.db")
    args = parser.parse_args()
    import_books(args.sqlite_file, args.mongo_url, args.db)


if __name__ == "__main__":
    main()
