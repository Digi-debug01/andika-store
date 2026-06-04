import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def db_get(table, filters=None, limit=None, order=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"select": "*"}
    if filters:
        params.update(filters)
    if limit:
        params["limit"] = limit
    if order:
        params["order"] = order
    try:
        r = httpx.get(url, headers=HEADERS, params=params, timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"DB GET error: {e}")
        return []

def db_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        r = httpx.post(url, headers=HEADERS, json=data, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"DB POST error: {e}")
        return False

def db_patch(table, data, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        r = httpx.patch(url, headers=HEADERS, json=data, params=filters, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"DB PATCH error: {e}")
        return False

def db_upsert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**HEADERS, "Prefer": "resolution=merge-duplicates"}
    try:
        r = httpx.post(url, headers=headers, json=data, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"DB UPSERT error: {e}")
        return False

def save_user(user_id, nama, username):
    return db_upsert("adk_users", {"id": user_id, "nama": nama, "username": username or "-"})

def get_all_users():
    data = db_get("adk_users")
    return [u["id"] for u in data] if data else []

def count_users():
    data = db_get("adk_users")
    return len(data) if data else 0

def save_order(ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga):
    return db_post("adk_orders", {
        "ref_id": ref_id, "user_id": user_id, "nama": nama,
        "tipe": tipe, "operator": operator, "produk": produk,
        "kode": kode, "nomor": nomor, "harga": harga, "status": "pending"
    })

def get_order(ref_id):
    data = db_get("adk_orders", filters={"ref_id": f"eq.{ref_id}"})
    return data[0] if data else None

def update_order_status(ref_id, status):
    return db_patch("adk_orders", {"status": status}, {"ref_id": f"eq.{ref_id}"})

def get_recent_orders(limit=10):
    return db_get("adk_orders", limit=limit, order="created_at.desc") or []

def get_order_stats():
    data = db_get("adk_orders") or []
    total = len(data)
    sukses = sum(1 for o in data if o["status"] == "sukses")
    pending = sum(1 for o in data if o["status"] == "pending")
    gagal = sum(1 for o in data if o["status"] == "gagal")
    diproses = sum(1 for o in data if o["status"] == "diproses")
    omzet = sum(o["harga"] for o in data if o["status"] == "sukses")
    return {"total": total, "sukses": sukses, "pending": pending, "gagal": gagal, "diproses": diproses, "omzet": omzet}
