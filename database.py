import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    """
    Koneksi ke Supabase via Session Pooler.
    Mendukung URL dengan karakter khusus di password.
    """
    r = urllib.parse.urlparse(DATABASE_URL)

    # Decode username & password yang mungkin mengandung karakter khusus
    username = urllib.parse.unquote(r.username) if r.username else ""
    password = urllib.parse.unquote(r.password) if r.password else ""
    host     = r.hostname
    port     = r.port or 5432
    dbname   = r.path.lstrip("/")

    # Ambil options tambahan dari query string jika ada (misal: ?pgbouncer=true)
    query_params = urllib.parse.parse_qs(r.query)
    options = query_params.get("options", [None])[0]

    conn_kwargs = dict(
        host=host,
        port=port,
        dbname=dbname,
        user=username,
        password=password,
        sslmode="require",
        connect_timeout=15,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )

    if options:
        conn_kwargs["options"] = options

    return psycopg2.connect(**conn_kwargs)


def with_conn(fn):
    """Decorator: buka koneksi → jalankan fn(conn) → tutup."""
    def wrapper(*args, **kwargs):
        conn = get_conn()
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    return wrapper


def init_db():
    conn = get_conn()
    try:
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
        print("✅ Database Andika Store siap.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Gagal init_db: {e}")
        raise
    finally:
        conn.close()


def save_user(user_id, nama, username):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO adk_users (id, nama, username)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET nama=%s, username=%s
            """,
            (user_id, nama, username or "-", nama, username or "-")
        )
        conn.commit()
    finally:
        conn.close()


def get_all_users():
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM adk_users")
        return [r[0] for r in c.fetchall()]
    finally:
        conn.close()


def count_users():
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM adk_users")
        row = c.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def save_order(ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO adk_orders
                (ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga)
        )
        conn.commit()
    finally:
        conn.close()


def get_order(ref_id):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT ref_id, user_id, nama, tipe, operator, produk,
                   kode, nomor, harga, status, created_at
            FROM adk_orders WHERE ref_id = %s
            """,
            (ref_id,)
        )
        row = c.fetchone()
        if not row:
            return None
        return {
            "ref_id": row[0], "user_id": row[1], "nama": row[2],
            "tipe": row[3], "operator": row[4], "produk": row[5],
            "kode": row[6], "nomor": row[7], "harga": row[8],
            "status": row[9], "created_at": str(row[10])
        }
    finally:
        conn.close()


def update_order_status(ref_id, status):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "UPDATE adk_orders SET status = %s WHERE ref_id = %s",
            (status, ref_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_orders(limit=10):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT ref_id, user_id, nama, tipe, operator, produk,
                   kode, nomor, harga, status, created_at
            FROM adk_orders ORDER BY created_at DESC LIMIT %s
            """,
            (limit,)
        )
        return [
            {
                "ref_id": r[0], "user_id": r[1], "nama": r[2],
                "tipe": r[3], "operator": r[4], "produk": r[5],
                "kode": r[6], "nomor": r[7], "harga": r[8],
                "status": r[9], "created_at": str(r[10])
            }
            for r in c.fetchall()
        ]
    finally:
        conn.close()


def get_order_stats():
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT status, COUNT(*), COALESCE(SUM(harga), 0) FROM adk_orders GROUP BY status"
        )
        rows = c.fetchall()
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
