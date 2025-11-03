#!/usr/bin/env python3
"""
Quick DB inspector for fe/data/book_lx.db (large DB)
Run from project root. Prints whether DB exists and tables.
"""
import os
import sqlite3

DB = os.path.join('fe', 'data', 'book_lx.db')

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
    conn.close()

if __name__ == '__main__':
    main()
