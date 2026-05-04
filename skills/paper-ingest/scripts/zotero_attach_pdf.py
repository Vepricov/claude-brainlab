#!/usr/bin/env python3
import argparse
import hashlib
import os
import random
import shutil
import sqlite3
import string
import sys
import time


DB_PATH = os.path.expanduser("~/Zotero/zotero.sqlite")
STORAGE_DIR = os.path.expanduser("~/Zotero/storage")


def random_key(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def md5sum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def unique_key(cur):
    while True:
        k = random_key()
        cur.execute("SELECT 1 FROM items WHERE key=?", (k,))
        if not cur.fetchone():
            return k


def insert_value(cur, value):
    cur.execute("SELECT valueID FROM itemDataValues WHERE value=?", (value,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO itemDataValues (value) VALUES (?)", (value,))
    return cur.lastrowid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-key", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--title", default="PDF")
    args = parser.parse_args()

    pdf_path = os.path.abspath(os.path.expanduser(args.pdf))
    if not os.path.exists(pdf_path):
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT itemID, libraryID FROM items WHERE key=?", (args.parent_key,))
    row = cur.fetchone()
    if not row:
        print(f"ERROR: parent item not found: {args.parent_key}", file=sys.stderr)
        sys.exit(1)
    parent_item_id, library_id = row

    cur.execute(
        """
        SELECT i.key, ia.path
        FROM itemAttachments ia
        JOIN items i ON i.itemID = ia.itemID
        WHERE ia.parentItemID = ? AND ia.contentType = 'application/pdf'
        """,
        (parent_item_id,),
    )
    existing = cur.fetchall()
    if existing:
        print(f"EXISTS {existing[0][0]} {existing[0][1]}")
        return

    attachment_key = unique_key(cur)

    filename = os.path.basename(pdf_path)
    storage_subdir = os.path.join(STORAGE_DIR, attachment_key)
    os.makedirs(storage_subdir, exist_ok=True)
    dest_path = os.path.join(storage_subdir, filename)
    shutil.copy2(pdf_path, dest_path)

    file_md5 = md5sum(dest_path)
    mod_ms = int(os.path.getmtime(dest_path) * 1000)
    mod_s = int(os.path.getmtime(dest_path))
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    access_date = time.strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO items (itemTypeID, dateAdded, dateModified, clientDateModified, libraryID, key, version, synced)
        VALUES (3, ?, ?, ?, ?, ?, 0, 0)
        """,
        (now, now, now, library_id, attachment_key),
    )
    attachment_item_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO itemAttachments (itemID, parentItemID, linkMode, contentType, path, syncState, storageModTime, storageHash, lastProcessedModificationTime)
        VALUES (?, ?, 1, 'application/pdf', ?, 2, ?, ?, ?)
        """,
        (attachment_item_id, parent_item_id, f"storage:{filename}", mod_ms, file_md5, mod_s),
    )

    title_value_id = insert_value(cur, args.title)
    cur.execute("INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, 1, ?)", (attachment_item_id, title_value_id))

    if args.url:
        url_value_id = insert_value(cur, args.url)
        cur.execute("INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, 10, ?)", (attachment_item_id, url_value_id))

    access_value_id = insert_value(cur, access_date)
    cur.execute("INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, 11, ?)", (attachment_item_id, access_value_id))

    conn.commit()
    conn.close()
    print(f"CREATED {attachment_key} parent={args.parent_key} file={filename}")


if __name__ == "__main__":
    main()
