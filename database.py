import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import urllib.parse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    r = urllib.parse.urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=r.hostname,
        port=r.port or 5432,
        dbname=r.path.lstrip("/"),
        user=urllib.parse.unquote(r.username),
        password=urllib.parse.unquote(r.password),
        sslmode="require",
        connect_timeout=10
    )

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS adk_users (
            id          BIGINT PRIMARY KEY,
            nama        TEXT,
            username    TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS adk_orders (
            id          SERIAL PRIMARY KEY,
            ref_id      TEXT UNIQUE,
            user_id     BIGINT,
            nama        TEXT,
            tipe        TEXT,
            operator    TEXT,
            produk      TEXT,
            kode        TEXT,
            nomor       TEXT,
            harga       INTEGER,
            status      TEXT DEFAULT 'pending',
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database Andika Store siap.")

def save_user(user_id, nama, username):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO adk_users (id, nama, username) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET nama=%s, username=%s",
        (user_id, nama, username or "-", nama, username or "-")
    )
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM adk_users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def count_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM adk_users")
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def save_order(ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO adk_orders (ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga)
    )
    conn.commit()
    conn.close()

def get_order(ref_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga, status, created_at FROM adk_orders WHERE ref_id = %s", (ref_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "ref_id": row[0], "user_id": row[1], "nama": row[2],
        "tipe": row[3], "operator": row[4], "produk": row[5],
        "kode": row[6], "nomor": row[7], "harga": row[8],
        "status": row[9], "created_at": str(row[10])
    }

def update_order_status(ref_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE adk_orders SET status = %s WHERE ref_id = %s", (status, ref_id))
    conn.commit()
    conn.close()

def get_recent_orders(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga, status, created_at FROM adk_orders ORDER BY created_at DESC LIMIT %s", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"ref_id": r[0], "user_id": r[1], "nama": r[2], "tipe": r[3],
             "operator": r[4], "produk": r[5], "kode": r[6], "nomor": r[7],
             "harga": r[8], "status": r[9], "created_at": str(r[10])} for r in rows]

def get_order_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*), COALESCE(SUM(harga),0) FROM adk_orders GROUP BY status")
    rows = c.fetchall()
    conn.close()
    stats = {"total": 0, "sukses": 0, "pending": 0, "gagal": 0, "diproses": 0, "omzet": 0}
    for status, count, total in rows:
        stats["total"] += count
        if status in stats:
            stats[status] = count
        if status == "sukses":
            stats["omzet"] = total
    return stats
