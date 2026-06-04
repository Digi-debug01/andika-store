# ─────────────────────────────────────────────
# DATABASE HANDLER — Supabase
# ─────────────────────────────────────────────
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────

def save_user(user_id, nama, username):
    try:
        supabase.table("adk_users").upsert({
            "id": user_id,
            "nama": nama,
            "username": username or "-"
        }).execute()
    except Exception as e:
        print(f"Error save_user: {e}")

def get_all_users():
    try:
        res = supabase.table("adk_users").select("id").execute()
        return [u["id"] for u in res.data]
    except:
        return []

def count_users():
    try:
        res = supabase.table("adk_users").select("id", count="exact").execute()
        return res.count or 0
    except:
        return 0

# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────

def save_order(ref_id, user_id, nama, tipe, operator, produk, kode, nomor, harga):
    try:
        supabase.table("adk_orders").insert({
            "ref_id": ref_id,
            "user_id": user_id,
            "nama": nama,
            "tipe": tipe,
            "operator": operator,
            "produk": produk,
            "kode": kode,
            "nomor": nomor,
            "harga": harga,
            "status": "pending"
        }).execute()
        return True
    except Exception as e:
        print(f"Error save_order: {e}")
        return False

def get_order(ref_id):
    try:
        res = supabase.table("adk_orders").select("*").eq("ref_id", ref_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def update_order_status(ref_id, status):
    try:
        supabase.table("adk_orders").update({"status": status}).eq("ref_id", ref_id).execute()
        return True
    except Exception as e:
        print(f"Error update_order_status: {e}")
        return False

def get_recent_orders(limit=10):
    try:
        res = supabase.table("adk_orders").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data or []
    except:
        return []

def get_order_stats():
    try:
        res = supabase.table("adk_orders").select("status, harga").execute()
        data = res.data or []
        total = len(data)
        sukses = sum(1 for o in data if o["status"] == "sukses")
        pending = sum(1 for o in data if o["status"] == "pending")
        gagal = sum(1 for o in data if o["status"] == "gagal")
        diproses = sum(1 for o in data if o["status"] == "diproses")
        omzet = sum(o["harga"] for o in data if o["status"] == "sukses")
        return {
            "total": total,
            "sukses": sukses,
            "pending": pending,
            "gagal": gagal,
            "diproses": diproses,
            "omzet": omzet
        }
    except:
        return {"total": 0, "sukses": 0, "pending": 0, "gagal": 0, "diproses": 0, "omzet": 0}
