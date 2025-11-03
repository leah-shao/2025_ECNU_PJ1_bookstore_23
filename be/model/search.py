"""Search helper that prefers MongoDB text search and falls back to SQLite LIKE.

Functions:
 - search_books(q, fields=None, store_id=None, page=1, page_size=10)

This module uses the MongoDB instance from `be.model.store.get_db()` when
available. If Mongo is not available or the `books` collection is missing,
falls back to SQLite queries against the `store` and `book` tables.
"""
from be.model import store as store_mod
from be.model import db_conn
import math


def _sqlite_search(q, fields, store_id, page, page_size):
    # Simple fallback: search book_info JSON in store table via LIKE
    conn = store_mod.get_db_conn()
    cur = conn.cursor()
    params = []
    where_clauses = []

    if store_id:
        where_clauses.append("store_id = ?")
        params.append(store_id)

    like_clause = ""
    if q:
        like_q = f"%{q}%"
        # search in book_info (json text), title, tags via LIKE
        like_sub = "(book_info LIKE ? OR book_info LIKE ? OR book_info LIKE ? )"
        # We attempt to match title/tags/content by checking JSON string
        where_clauses.append(like_sub)
        params.extend([like_q, like_q, like_q])

    where = "AND".join("(" + w + ")" for w in where_clauses) if where_clauses else "1=1"
    count_q = f"SELECT COUNT(*) FROM store WHERE {where}"
    cur.execute(count_q, tuple(params))
    total = cur.fetchone()[0]
    offset = (page - 1) * page_size
    qstr = f"SELECT book_info FROM store WHERE {where} LIMIT ? OFFSET ?"
    cur.execute(qstr, tuple(params) + (page_size, offset))
    rows = cur.fetchall()
    results = []
    for r in rows:
        try:
            import json

            book_info = json.loads(r[0])
        except Exception:
            book_info = {}
        results.append(book_info)

    return 200, "ok", results, total


def search_books(q: str, fields=None, store_id: str = None, page: int = 1, page_size: int = 10):
    """Search books.

    - q: keyword string
    - fields: list of fields to search (ignored for Mongo text search, used for projection in results)
    - store_id: if provided, restrict to books available in that store (uses sqlite store table)
    - page/page_size: pagination
    """
    # try MongoDB first
    try:
        db = store_mod.get_db()
        if db is None:
            raise Exception("no mongo db")
        books = db.books
        # build filter
        mongo_filter = {}
        if q:
            mongo_filter["$text"] = {"$search": q}
        if store_id:
            # find book ids in sqlite store for that store
            conn = store_mod.get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT book_id FROM store WHERE store_id = ?", (store_id,))
            ids = [r[0] for r in cur.fetchall()]
            if ids:
                mongo_filter["id"] = {"$in": ids}
            else:
                # no books in that store
                return 200, "ok", [], 0

        projection = None
        find_args = {}
        sort = None
        if q:
            # return text score if text search used
            projection = {"score": {"$meta": "textScore"}}
            sort = [("score", {"$meta": "textScore"})]

        total = books.count_documents(mongo_filter)
        cursor = books.find(mongo_filter, projection)
        if sort:
            # pymongo expects list of tuples for sort; but textScore meta needs special handling
            cursor = cursor.sort([("score", {"$meta": "textScore"})])

        cursor = cursor.skip((page - 1) * page_size).limit(page_size)
        results = []
        for d in cursor:
            # remove MongoDB _id for JSON response
            d.pop("_id", None)
            results.append(d)
        return 200, "ok", results, total

    except Exception:
        # fallback to SQLite LIKE search
        return _sqlite_search(q, fields, store_id, page, page_size)
