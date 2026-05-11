# db.py
import sqlite3
from datetime import datetime

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS intrusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            image_path TEXT,
            label TEXT,
            emailed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def log_intrusion(db_path, image_path, label="Unknown"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO intrusions (timestamp, image_path, label) VALUES (?, ?, ?)",
                (ts, image_path, label))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid

def update_label(db_path, intrusion_id, label):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE intrusions SET label=? WHERE id=?", (label, intrusion_id))
    conn.commit()
    conn.close()

def mark_emailed(db_path, intrusion_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE intrusions SET emailed=1 WHERE id=?", (intrusion_id,))
    conn.commit()
    conn.close()

def fetch_recent(db_path, limit=20):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id,timestamp,image_path,label,emailed FROM intrusions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
