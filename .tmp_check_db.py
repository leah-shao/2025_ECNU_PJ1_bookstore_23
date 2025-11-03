#!/usr/bin/env python3
"""
Quick DB inspector for fe/data/book.db
Run from project root. Prints whether DB exists, tables, and book row count (if present).
"""
import os
import sqlite3

DB = os.path.join('fe', 'data', 'book.db')

def main():
    print('Checking', DB)
    if not os.path.exists(DB):
        print('NOT FOUND:', DB)
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('Tables:', tables)
    if 'book' in tables:
        try:
            cur.execute('SELECT COUNT(*) FROM book')
            cnt = cur.fetchone()[0]
            print('book rows:', cnt)
        except Exception as e:
            print('Error counting book rows:', e)
    conn.close()

if __name__ == '__main__':
    main()
