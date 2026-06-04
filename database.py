import os
import pg8000.native
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    r = urllib.parse.urlparse(DATABASE_URL)
    username = urllib.parse.unquote(r.username) if r.username else ""
    password = urllib.parse.unquote(r.password) if r.password else ""
    host     = r.hostname
    port     = r.port or 5432
    dbname   = r.path.lstrip("/")

    return pg8000.native.Connection(
        user=username,
        password=password,
        host=host,
        port=port,
        database=dbname,
        ssl_context=True,
        timeout=15,
    )


def init_db():
    conn = get_conn()
    try:
        conn.run("""
            CREATE TABLE IF NOT EXISTS adk_users (
                id          BIGINT PRIMARY KEY,
                nama        TEXT,
                username    TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.run("""
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
        print("✅ Database Andika Store siap.")
    except Exception as e:
        print(f"❌ Gagal init_db: {e}")
        raise
    finally:
        conn.close()


def save_user(user_id, nama, username):
    conn = get_conn()
    try:
        conn.run(
            "INSERT INTO adk_users (id, nama, username) VALUES (:id, :nama, :username) ON CONFLICT (id) DO UPDATE SET nama=:nama, username=:username",
            id=user_id, nama=nama, username=username or "-"
        )
    finally:
        conn.close()


def get_all_users():
    conn = get_conn()
    try:
        rows = conn.run("SELECT id FROM adk_users")
        return [r[0] for r in rows]
    finally:
        conn.close()


def count_users():
    conn = get_conn()
    try:
        rows = conn.run("SELECT COUNT(*) FROM adk_users")
        return rows[0][0] if rows else 0
    finally:
        conn.close()


def save_order(ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga):
    conn = get_conn()
    try:
        conn.run(
            "INSERT INTO adk_orders (ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga) VALUES (:ref_id, :user_id, :nama, :tipe, :operator, :produk, :kode, :nomor, :harga)",
            ref_id=ref_id, user_id=user_id, nama=nama, tipe=tipe,
            operator=operator, produk=produk, kode=kode, nomor=nomor, harga=harga
        )
    finally:
        conn.close()


def get_order(ref_id):
    conn = get_conn()
    try:
        rows = conn.run(
            "SELECT ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga, status, created_at FROM adk_orders WHERE ref_id = :ref_id",
            ref_id=ref_id
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "ref_id": r[0], "user_id": r[1], "nama": r[2],
            "tipe": r[3], "operator": r[4], "produk": r[5],
            "kode": r[6], "nomor": r[7], "harga": r[8],
            "status": r[9], "created_at": str(r[10])
        }
    finally:
        conn.close()


def update_order_status(ref_id, status):
    conn = get_conn()
    try:
        conn.run(
            "UPDATE adk_orders SET status = :status WHERE ref_id = :ref_id",
            status=status, ref_id=ref_id
        )
    finally:
        conn.close()


def get_recent_orders(limit=10):
    conn = get_conn()
    try:
        rows = conn.run(
            "SELECT ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga, status, created_at FROM adk_orders ORDER BY created_at DESC LIMIT :limit",
            limit=limit
        )
        return [
            {"ref_id": r[0], "user_id": r[1], "nama": r[2], "tipe": r[3],
             "operator": r[4], "produk": r[5], "kode": r[6], "nomor": r[7],
             "harga": r[8], "status": r[9], "created_at": str(r[10])}
            for r in rows
        ]
    finally:
        conn.close()


def get_order_stats():
    conn = get_conn()
    try:
        rows = conn.run(
            "SELECT status, COUNT(*), COALESCE(SUM(harga), 0) FROM adk_orders GROUP BY status"
        )
        stats = {"total": 0, "sukses": 0, "pending": 0, "gagal": 0, "diproses": 0, "omzet": 0}
        for status, count, total in rows:
            stats["total"] += count
            if status in stats:
                stats[status] = count
            if status == "sukses":
                stats["omzet"] = int(total)
        return stats
    finally:
        conn.close()
