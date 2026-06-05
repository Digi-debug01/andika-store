import telebot
import requests
import threading
import hashlib
import os
from dotenv import load_dotenv
from telebot import types
from datetime import datetime
from products import PRODUCTS, SKU_MAP
from database import (save_user, get_all_users, count_users,
                      save_order, get_order, update_order_status,
                      get_recent_orders, get_order_stats, init_db)

load_dotenv()

BOT_TOKEN     = os.getenv("BOT_TOKEN")
ADMIN_ID      = int(os.getenv("ADMIN_ID"))
ADMIN_USERNAME= os.getenv("ADMIN_USERNAME", "admin")
ADMIN_WA = "wa.me/6285136080650"
MAINTENANCE_MODE = False  # Status maintenance
DIGI_USERNAME = os.getenv("DIGI_USERNAME", "")
DIGI_API_KEY  = os.getenv("DIGI_API_KEY", "")
SANDBOX_MODE  = os.getenv("SANDBOX_MODE", "True") == "True"
NAMA_REKENING = os.getenv("NAMA_REKENING", "Andika")
NO_REKENING   = os.getenv("NO_REKENING", "")
BANK_REKENING = os.getenv("BANK_REKENING", "BCA")

DIGI_URL   = "https://api.digiflazz.com/v1"
FIXIE_URL  = os.getenv("FIXIE_URL", "")  # Format: http://user:pass@fixie.usefixie.com:80

bot = telebot.TeleBot(BOT_TOKEN)

def get_proxies():
    """Kembalikan dict proxies jika FIXIE_URL tersedia, atau None jika tidak."""
    if FIXIE_URL:
        return {"http": FIXIE_URL, "https": FIXIE_URL}
    return None

user_sessions      = {}
broadcast_sessions = {}

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def digi_sign(username, api_key, ref_id=""):
    raw = username + api_key + ref_id
    return hashlib.md5(raw.encode()).hexdigest()

def cek_saldo():
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, "depo")
    payload = {"cmd": "deposit", "username": DIGI_USERNAME, "sign": sign}
    try:
        r = requests.post(f"{DIGI_URL}/cek-saldo", json=payload, timeout=10, proxies=get_proxies())
        return r.json().get("data", {}).get("deposit", 0)
    except:
        return None

def transaksi(ref_id, customer_no, buyer_sku_code):
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, ref_id)
    payload = {
        "username":       DIGI_USERNAME,
        "buyer_sku_code": buyer_sku_code,
        "customer_no":    customer_no,
        "ref_id":         ref_id,
        "sign":           sign,
        "testing":        SANDBOX_MODE
    }
    try:
        r = requests.post(f"{DIGI_URL}/transaction", json=payload, timeout=15, proxies=get_proxies())
        return r.json()
    except Exception as e:
        return {"data": {"rc": "ERROR", "message": str(e)}}

def cek_transaksi_digi(ref_id):
    """Cek status transaksi ke Digiflazz berdasarkan ref_id."""
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, ref_id)
    payload = {
        "username": DIGI_USERNAME,
        "buyer_sku_code": "",
        "customer_no": "",
        "ref_id": ref_id,
        "sign": sign,
        "testing": SANDBOX_MODE
    }
    try:
        r = requests.post(f"{DIGI_URL}/transaction", json=payload, timeout=15, proxies=get_proxies())
        return r.json()
    except Exception as e:
        return {"data": {"rc": "ERROR", "message": str(e)}}

def buat_ref_id(user_id):
    return f"AS{user_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

def validasi_nomor(nomor):
    """Validasi format nomor HP Indonesia, simpan dalam format 08."""
    nomor = nomor.strip().replace("-", "").replace(" ", "")
    if nomor.startswith("628"):
        nomor = "0" + nomor[2:]
    elif nomor.startswith("+628"):
        nomor = "0" + nomor[3:]
    elif nomor.startswith("+62"):
        nomor = "0" + nomor[3:]
    elif nomor.startswith("62"):
        nomor = "0" + nomor[2:]
    if not nomor.startswith("0"):
        return None
    if len(nomor) < 10 or len(nomor) > 13:
        return None
    if not nomor.isdigit():
        return None
    return nomor

def ambil_ref_id(text, prefix):
    """
    Ambil ref_id dari perintah admin.
    Support format: /prefix_REFID atau /prefix REFID
    """
    text = text.strip()
    if "@" in text.split()[0]:
        text = text.split()[0].split("@")[0] + " " + " ".join(text.split()[1:])
    if f"/{prefix}_" in text:
        return text.split(f"/{prefix}_", 1)[1].strip().split()[0]
    parts = text.split(None, 1)
    if len(parts) > 1:
        return parts[1].strip().split()[0]
    return None

# ─────────────────────────────────────────────
# KEYBOARD HELPERS
# ─────────────────────────────────────────────

def menu_utama():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📱 Pulsa"),
        types.KeyboardButton("📶 Paket Data"),
        types.KeyboardButton("🎮 Top Up Game"),
        types.KeyboardButton("💳 Cek Transaksi"),
        types.KeyboardButton("ℹ️ Info & Bantuan")
    )
    return markup

def menu_kembali():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

def menu_operator_pulsa():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    for op in PRODUCTS["pulsa"].keys():
        markup.add(types.KeyboardButton(op))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

def menu_nominal(operator, kategori="pulsa"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for item in PRODUCTS[kategori].get(operator, []):
        markup.add(types.KeyboardButton(f"{item['nama']} - {format_rupiah(item['harga'])}"))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

def menu_admin():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("💰 Cek Saldo"),
        types.KeyboardButton("📋 Daftar Order"),
        types.KeyboardButton("📊 Statistik"),
        types.KeyboardButton("📢 Broadcast"),
        types.KeyboardButton("🔙 Menu Utama")
    )
    return markup

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    save_user(uid, message.from_user.first_name, message.from_user.username)
    user_sessions[uid] = {}
    if MAINTENANCE_MODE and uid != ADMIN_ID:
        bot.send_message(
            uid,
            "🔧 ADK Store Sedang Maintenance\n\n"
            "Mohon maaf, layanan kami sedang dalam pemeliharaan.\n"
            "Silakan coba beberapa saat lagi 🙏\n\n"
            f"Info: Telegram @{ADMIN_USERNAME} | WhatsApp {ADMIN_WA}",
        )
        return
    mode_text = "🧪 MODE TESTING" if SANDBOX_MODE else "🟢 LIVE"
    teks = (
        f"👋 Halo, *{message.from_user.first_name}*!\n\n"
        f"Selamat datang di *Andika Store* {mode_text}\n"
        f"Pulsa, Paket Data & Top Up Game!\n\n"
        f"Silakan pilih menu:"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())

# ─────────────────────────────────────────────
# MENU PULSA
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📱 Pulsa")
def menu_pulsa(message):
    uid = message.from_user.id
    if MAINTENANCE_MODE and uid != ADMIN_ID:
        bot.send_message(uid, "🔧 Maaf, ADK Store sedang maintenance. Silakan coba beberapa saat lagi.")
        return
    user_sessions[uid] = {"tipe": "pulsa"}
    bot.send_message(message.chat.id, "📱 *Pulsa*\nPilih operator:", parse_mode="Markdown", reply_markup=menu_operator_pulsa())

@bot.message_handler(func=lambda m: m.text in PRODUCTS["pulsa"].keys())
def pilih_operator_pulsa(message):
    uid = message.from_user.id
    if user_sessions.get(uid, {}).get("tipe") != "pulsa":
        return
    user_sessions[uid]["operator"] = message.text
    user_sessions[uid]["step"] = "pilih_nominal"
    bot.send_message(message.chat.id, f"📱 *Pulsa {message.text}*\nPilih nominal:", parse_mode="Markdown", reply_markup=menu_nominal(message.text, "pulsa"))

# ─────────────────────────────────────────────
# MENU PAKET DATA
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📶 Paket Data")
def menu_paket(message):
    uid = message.from_user.id
    user_sessions[uid] = {"tipe": "data"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for op in PRODUCTS["data"].keys():
        markup.add(types.KeyboardButton(f"📶 {op}"))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    bot.send_message(message.chat.id, "📶 *Paket Data*\nPilih operator:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in [f"📶 {op}" for op in PRODUCTS["data"].keys()])
def pilih_operator_data(message):
    uid = message.from_user.id
    if user_sessions.get(uid, {}).get("tipe") != "data":
        return
    operator = message.text.replace("📶 ", "")
    user_sessions[uid]["operator"] = operator
    user_sessions[uid]["step"] = "pilih_nominal"
    bot.send_message(message.chat.id, f"📶 *Paket Data {operator}*\nPilih paket:", parse_mode="Markdown", reply_markup=menu_nominal(operator, "data"))

# ─────────────────────────────────────────────
# MENU GAME
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "🎮 Top Up Game")
def menu_game(message):
uid = message.from_user.id
    user_sessions[uid] = {"tipe": "game"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for game in PRODUCTS["game"].keys():
        markup.add(types.KeyboardButton(f"🎮 {game}"))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    bot.send_message(message.chat.id, "Pilih game:", reply_markup=markup)
# ─────────────────────────────────────────────
# PILIH NOMINAL
# ─────────────────────────────────────────────

def get_produk_dari_teks(teks, operator, kategori):
    for item in PRODUCTS[kategori].get(operator, []):
        if teks == f"{item['nama']} - {format_rupiah(item['harga'])}":
            return item
    return None

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "pilih_nominal")
def pilih_nominal(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})
    if message.text == "🔙 Kembali":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())
        return
    produk = get_produk_dari_teks(message.text, sesi.get("operator"), sesi.get("tipe", "pulsa"))
    if not produk:
        bot.send_message(message.chat.id, "Pilih dari menu yang tersedia.")
        return
    user_sessions[uid]["produk"] = produk
    user_sessions[uid]["step"] = "input_nomor"
    bot.send_message(
        message.chat.id,
        f"*{produk['nama']}*\nHarga: *{format_rupiah(produk['harga'])}*\n\nMasukkan nomor HP tujuan:\n(contoh: 08123456789)",
        parse_mode="Markdown", reply_markup=menu_kembali()
    )

# ─────────────────────────────────────────────
# INPUT NOMOR
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "input_nomor")
def input_nomor(message):
    uid = message.from_user.id
    if message.text == "🔙 Kembali":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())
        return
    sesi   = user_sessions.get(uid, {})
    produk = sesi.get("produk", {})
    nomor  = validasi_nomor(message.text.strip())
    if not nomor:
        bot.send_message(
            message.chat.id,
            "❌ Format nomor tidak valid!\n\nMasukkan nomor HP yang benar:\n"
            "Contoh: 08123456789 atau 628123456789"
        )
        return
    user_sessions[uid]["nomor"] = nomor
    user_sessions[uid]["step"]  = "konfirmasi"
    teks = (
        f"📋 *Konfirmasi Order*\n\n"
        f"Produk : {produk['nama']}\n"
        f"Nomor  : `{nomor}`\n"
        f"Harga  : *{format_rupiah(produk['harga'])}*\n\n"
        f"Pastikan nomor sudah benar!\n"
        f"Ketik *YA* untuk lanjut atau *BATAL*"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("YA"), types.KeyboardButton("BATAL"))
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=markup)

# ─────────────────────────────────────────────
# KONFIRMASI ORDER
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "input_zone")
def input_zone(message):
    uid = message.from_user.id
    if message.text == "🔙 Kembali":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())
        return
    zone = message.text.strip()
    if not zone.isdigit():
        bot.send_message(message.chat.id, "Zone ID tidak valid. Masukkan angka saja. Contoh: 1234")
        return
    sesi   = user_sessions.get(uid, {})
    produk = sesi.get("produk", {})
    nomor  = sesi.get("nomor")
    user_sessions[uid]["zone_id"] = zone
    user_sessions[uid]["step"] = "konfirmasi"
    teks = (
        "Konfirmasi Order\n\n"
        + "Produk  : " + produk["nama"] + "\n"
        + "User ID : " + nomor + "\n"
        + "Zone ID : " + zone + "\n"
        + "Harga   : " + format_rupiah(produk["harga"]) + "\n\n"
        + "Pastikan User ID dan Zone ID sudah benar!\n"
        + "Ketik YA untuk lanjut atau BATAL"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("YA"), types.KeyboardButton("BATAL"))
    bot.send_message(message.chat.id, teks, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["YA", "BATAL"] and user_sessions.get(m.from_user.id, {}).get("step") == "konfirmasi")
def konfirmasi_order(message):
    uid  = message.from_user.id
    sesi = user_sessions.get(uid, {})
    if message.text == "BATAL":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "Order dibatalkan.", reply_markup=menu_utama())
        return
    produk = sesi.get("produk", {})
    nomor  = sesi.get("nomor")
    ref_id = buat_ref_id(uid)
    user_sessions[uid]["ref_id"] = ref_id
    user_sessions[uid]["step"]   = "menunggu_bayar"

    save_order(
        ref_id=ref_id, user_id=uid,
        nama=message.from_user.first_name,
        tipe=sesi.get("tipe"), operator=sesi.get("operator", "-"),
        produk=produk.get("nama"), kode=produk.get("kode"),
        nomor=nomor, harga=produk.get("harga")
    )

    teks_bayar = (
        f"💳 *Informasi Pembayaran*\n\n"
        f"Produk : {produk['nama']}\n"
        f"Nomor  : `{nomor}`\n"
        f"Total  : *{format_rupiah(produk['harga'])}*\n"
        f"Ref ID : `{ref_id}`\n\n"
        f"Transfer ke:\n"
        f"{BANK_REKENING} — {NO_REKENING}\n"
        f"a.n. {NAMA_REKENING}\n\n"
        f"Kirim bukti bayar ke admin setelah transfer:\n"
        f"Telegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}"
    )
    bot.send_message(message.chat.id, teks_bayar, parse_mode="Markdown", reply_markup=menu_kembali())

    notif = (
        f"🔔 *ORDER BARU!*\n\n"
        f"👤 {message.from_user.first_name} (@{message.from_user.username or '-'})\n"
        f"📦 {produk['nama']}\n"
        f"📞 {nomor}\n"
        f"💰 {format_rupiah(produk['harga'])}\n"
        f"Ref ID: `{ref_id}`\n\n"
        f"Konfirmasi: /konfirmasi {ref_id}\n"
        f"Sukses: /sukses {ref_id}\n"
        f"Tolak: /tolak {ref_id}"
    )
    try:
        bot.send_message(ADMIN_ID, notif, parse_mode="Markdown")
    except:
        pass

# ─────────────────────────────────────────────
# CEK TRANSAKSI USER
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "💳 Cek Transaksi")
def cek_transaksi(message):
    bot.send_message(message.chat.id, "Masukkan Ref ID transaksi kamu:\n(contoh: AS1234567890)", reply_markup=menu_kembali())
    user_sessions[message.from_user.id] = {"step": "cek_transaksi"}

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "cek_transaksi")
def proses_cek_transaksi(message):
    if message.text == "🔙 Kembali":
        user_sessions[message.from_user.id] = {}
        bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())
        return
    order = get_order(message.text.strip())
    if not order:
        bot.send_message(message.chat.id, "Ref ID tidak ditemukan.", reply_markup=menu_utama())
        return
    icon = {"pending": "⏳", "sukses": "✅", "gagal": "❌", "diproses": "🔄"}.get(order["status"], "❓")
    teks = (
        f"Status Transaksi\n\n"
        f"Ref ID  : {order['ref_id']}\n"
        f"Produk  : {order['produk']}\n"
        f"Nomor   : {order['nomor']}\n"
        f"Harga   : {format_rupiah(order['harga'])}\n"
        f"Status  : {icon} {order['status'].upper()}\n"
        f"Waktu   : {order['created_at'][:16]}"
    )
    bot.send_message(message.chat.id, teks, reply_markup=menu_utama())
    user_sessions[message.from_user.id] = {}

# ─────────────────────────────────────────────
# INFO
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "ℹ️ Info & Bantuan")
def info(message):
    teks = (
        f"ℹ️ Info Andika Store\n\n"
        f"Layanan: 24 Jam\n"
        f"Proses: Cepat & Terpercaya\n\n"
        f"Tersedia:\n"
        f"📱 Pulsa semua operator\n"
        f"📶 Paket data\n"
        f"🎮 Top Up Game (Mobile Legends & lainnya)\n\n"
        f"Hubungi Admin:\n"
        f"Telegram : @{ADMIN_USERNAME}\n"
        f"WhatsApp : {ADMIN_WA}\n\n"
        f"Ref ID transaksi bisa dicek via:\n"
        f"💳 Cek Transaksi"
    )
    bot.send_message(message.chat.id, teks, reply_markup=menu_utama())

@bot.message_handler(commands=["admin"])
def hubungi_admin(message):
    bot.send_message(message.chat.id, f"Silakan hubungi admin:\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}", reply_markup=menu_utama())

@bot.message_handler(func=lambda m: m.text == "🔙 Kembali")
def kembali(message):
    user_sessions[message.from_user.id] = {}
    bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())

# ─────────────────────────────────────────────
# PANEL ADMIN
# ─────────────────────────────────────────────

@bot.message_handler(commands=["panel"])
def panel_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Akses ditolak.")
        return
    stats     = get_order_stats()
    mode_text = "SANDBOX" if SANDBOX_MODE else "PRODUCTION"
    teks = (
        f"PANEL ADMIN — Andika Store\n"
        f"Mode        : {mode_text}\n"
        f"Total Order : {stats['total']}\n"
        f"Total User  : {count_users()}\n\n"
        f"Perintah tersedia:\n"
        f"/konfirmasi REFID — konfirmasi bayar\n"
        f"/sukses REFID     — proses transaksi\n"
        f"/cekstatus REFID  — cek status ke Digi\n"
        f"/tolak REFID alasan\n"
        f"/refund REFID     — tandai refund selesai\n\n"
        f"Pilih menu:"
    )
    bot.send_message(message.chat.id, teks, reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "💰 Cek Saldo" and m.from_user.id == ADMIN_ID)
def cek_saldo_admin(message):
    saldo = cek_saldo()
    if saldo is not None:
        bot.send_message(message.chat.id, f"Saldo Digiflazz: {format_rupiah(saldo)}")
    else:
        bot.send_message(message.chat.id, "Gagal cek saldo.")

@bot.message_handler(func=lambda m: m.text == "📋 Daftar Order" and m.from_user.id == ADMIN_ID)
def daftar_order(message):
    orders = get_recent_orders(10)
    if not orders:
        bot.send_message(message.chat.id, "Belum ada order.", reply_markup=menu_admin())
        return
    teks = "DAFTAR ORDER (10 terakhir)\n\n"
    for o in orders:
        icon  = {"pending": "⏳", "sukses": "✅", "gagal": "❌", "diproses": "🔄"}.get(o["status"], "❓")
        teks += f"{icon} {o['ref_id']}\n{o['nama']} | {o['produk']}\n{o['nomor']} | {format_rupiah(o['harga'])}\n\n"
    bot.send_message(message.chat.id, teks, reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "📊 Statistik" and m.from_user.id == ADMIN_ID)
def statistik(message):
    stats = get_order_stats()
    saldo = cek_saldo()
    teks  = (
        f"STATISTIK ANDIKA STORE\n\n"
        f"Total Order : {stats['total']}\n"
        f"Sukses      : {stats['sukses']}\n"
        f"Diproses    : {stats['diproses']}\n"
        f"Pending     : {stats['pending']}\n"
        f"Gagal       : {stats['gagal']}\n\n"
        f"Total Omzet : {format_rupiah(stats['omzet'])}\n"
        f"Total User  : {count_users()}\n"
        f"Saldo Digi  : {format_rupiah(saldo) if saldo else 'Gagal ambil'}\n\n"
        f"Mode: {'SANDBOX' if SANDBOX_MODE else 'PRODUCTION'}"
    )
    bot.send_message(message.chat.id, teks, reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast_menu(message):
    broadcast_sessions[message.from_user.id] = True
    bot.send_message(message.chat.id, "Ketik pesan broadcast:\n(ketik /batal untuk membatalkan)", reply_markup=menu_kembali())

@bot.message_handler(func=lambda m: broadcast_sessions.get(m.from_user.id) and m.from_user.id == ADMIN_ID)
def kirim_broadcast(message):
    if message.text in ["/batal", "🔙 Kembali"]:
        broadcast_sessions.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Broadcast dibatalkan.", reply_markup=menu_admin())
        return
    broadcast_sessions.pop(message.from_user.id, None)
    users    = get_all_users()
    berhasil = gagal_kirim = 0
    for uid in users:
        try:
            bot.send_message(uid, f"INFO ANDIKA STORE\n\n{message.text}")
            berhasil += 1
        except:
            gagal_kirim += 1
    bot.send_message(message.chat.id, f"Broadcast selesai!\nBerhasil: {berhasil}\nGagal: {gagal_kirim}", reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "🔙 Menu Utama" and m.from_user.id == ADMIN_ID)
def kembali_admin(message):
    bot.send_message(message.chat.id, "Menu utama.", reply_markup=menu_utama())

@bot.message_handler(commands=["konfirmasi"])
def konfirmasi_bayar(message):
    if message.from_user.id != ADMIN_ID:
        return
    ref_id = ambil_ref_id(message.text, "konfirmasi")
    if not ref_id:
        bot.send_message(message.chat.id, "Format: /konfirmasi REFID")
        return
    order = get_order(ref_id)
    if not order:
        bot.send_message(message.chat.id, f"Order {ref_id} tidak ditemukan.")
        return
    update_order_status(ref_id, "diproses")
    try:
        bot.send_message(order["user_id"], f"✅ Pembayaran dikonfirmasi!\nRef ID: {ref_id}\nOrder sedang diproses...")
    except:
        pass
    bot.send_message(message.chat.id, f"Order {ref_id} dikonfirmasi!", reply_markup=menu_admin())

@bot.message_handler(commands=["sukses"])
def order_sukses(message):
    if message.from_user.id != ADMIN_ID:
        return
    ref_id = ambil_ref_id(message.text, "sukses")
    if not ref_id:
        bot.send_message(message.chat.id, "Format: /sukses REFID")
        return
    order = get_order(ref_id)
    if not order:
        bot.send_message(message.chat.id, f"Order {ref_id} tidak ditemukan.")
        return


    # Cegah double transaksi jika sudah sukses
    if order.get("status") == "sukses":
        bot.send_message(
            message.chat.id,
            f"⚠️ Order {ref_id} sudah berstatus SUKSES sebelumnya.\n"
            f"Tidak bisa diproses ulang untuk menghindari double transaksi.",
            reply_markup=menu_admin()
        )
        return

    hasil = transaksi(ref_id, order["nomor"], order["kode"])
    data  = hasil.get("data", {})
    rc    = data.get("rc", "")
    pesan = data.get("message", "")

    if rc == "00":
        update_order_status(ref_id, "sukses")
        # Notif ke pembeli
        try:
            bot.send_message(
                order["user_id"],
                f"✅ *Order Berhasil!*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n"
                f"Nomor  : {order['nomor']}\n"
                f"Status : SUKSES ✅\n\n"
                f"Terima kasih sudah belanja di Andika Store! 🙏",
                parse_mode="Markdown"
            )
        except:
            pass
        bot.send_message(message.chat.id, f"✅ Order {ref_id} berhasil diproses!", reply_markup=menu_admin())

    elif rc == "03":
        update_order_status(ref_id, "diproses")
        # Notif ke pembeli bahwa sedang diproses / pending
        try:
            bot.send_message(
                order["user_id"],
                f"⏳ *Order Sedang Diproses*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n"
                f"Nomor  : {order['nomor']}\n\n"
                f"Transaksi sedang diproses oleh provider.\n"
                f"Kamu akan mendapat notifikasi segera setelah selesai.\n\n"
                f"Ada pertanyaan?\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
                parse_mode="Markdown"
            )
        except:
            pass
        bot.send_message(
            message.chat.id,
            f"⏳ Transaksi pending di Digiflazz!\n"
            f"Ref ID: {ref_id}\n\n"
            f"Pembeli sudah dinotifikasi.\n"
            f"Cek status dengan: /cekstatus {ref_id}",
            reply_markup=menu_admin()
        )

    else:
        update_order_status(ref_id, "gagal")
        # Notif ke pembeli bahwa order gagal + info refund
        try:
            bot.send_message(
                order["user_id"],
                f"❌ *Order Gagal*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n"
                f"Nomor  : {order['nomor']}\n"
                f"Harga  : {format_rupiah(order['harga'])}\n\n"
                f"Maaf, transaksi kamu tidak berhasil diproses.\n"
                f"Admin sedang menangani, mohon tunggu info selanjutnya.\n\n"
                f"Hubungi admin:\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
                parse_mode="Markdown"
            )
        except:
            pass
        # Admin bisa pilih: coba ulang atau refund
        bot.send_message(
            message.chat.id,
            f"❌ Transaksi gagal!\n"
            f"RC: {rc} | Pesan: {pesan}\n\n"
            f"Pilihan admin:\n"
            f"🔄 Coba ulang : /sukses {ref_id}\n"
            f"💸 Refund     : /refund {ref_id}\n"
            f"❌ Tolak      : /tolak {ref_id} alasan",
            reply_markup=menu_admin()
        )

@bot.message_handler(commands=["cekstatus"])
def cek_status_digi(message):
    if message.from_user.id != ADMIN_ID:
        return
    ref_id = ambil_ref_id(message.text, "cekstatus")
    if not ref_id:
        bot.send_message(message.chat.id, "Format: /cekstatus REFID")
        return
    order = get_order(ref_id)
    if not order:
        bot.send_message(message.chat.id, f"Order {ref_id} tidak ditemukan di database.")
        return

    bot.send_message(message.chat.id, f"🔍 Mengecek status ke Digiflazz...")
    hasil = cek_transaksi_digi(ref_id)
    data  = hasil.get("data", {})
    rc    = data.get("rc", "")
    pesan = data.get("message", "")
    status_digi = data.get("status", "")

    if rc == "00" or status_digi == "Sukses":
        update_order_status(ref_id, "sukses")
        try:
            bot.send_message(
                order["user_id"],
                f"✅ *Order Berhasil!*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n"
                f"Nomor  : {order['nomor']}\n"
                f"Status : SUKSES ✅\n\n"
                f"Terima kasih sudah belanja di Andika Store! 🙏",
                parse_mode="Markdown"
            )
        except:
            pass
        bot.send_message(message.chat.id, f"✅ Status diupdate: SUKSES\nPembeli sudah dinotifikasi!", reply_markup=menu_admin())

    elif rc == "03" or status_digi == "Pending":
        # Pembeli diinfokan masih pending
        try:
            bot.send_message(
                order["user_id"],
                f"⏳ *Update Order*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n\n"
                f"Transaksi masih dalam antrian provider.\n"
                f"Mohon tunggu, kamu akan dinotifikasi jika sudah selesai.\n\n"
                f"Pertanyaan?\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
                parse_mode="Markdown"
            )
        except:
            pass
        bot.send_message(
            message.chat.id,
            f"⏳ Masih pending di Digiflazz.\n"
            f"Pembeli sudah dinotifikasi.\n"
            f"Coba cek lagi beberapa menit.",
            reply_markup=menu_admin()
        )

    else:
        update_order_status(ref_id, "gagal")
        # Notif ke pembeli bahwa order gagal + info refund
        try:
            bot.send_message(
                order["user_id"],
                f"❌ *Order Gagal*\n\n"
                f"Ref ID : `{ref_id}`\n"
                f"Produk : {order['produk']}\n"
                f"Nomor  : {order['nomor']}\n"
                f"Harga  : {format_rupiah(order['harga'])}\n\n"
                f"Maaf, transaksi kamu tidak berhasil diproses.\n"
                f"Dana kamu akan dikembalikan (refund) oleh admin.\n\n"
                f"Hubungi admin untuk konfirmasi refund:\n"
                f"Telegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
                parse_mode="Markdown"
            )
        except:
            pass
        # Ingatkan admin soal refund
        bot.send_message(
            message.chat.id,
            f"❌ Status: GAGAL\nRC: {rc} | Pesan: {pesan}\n\n"
            f"⚠️ PERLU REFUND:\n"
            f"Pembeli: {order['nama']}\n"
            f"Ref ID: {ref_id}\n"
            f"Nominal: {format_rupiah(order['harga'])}\n\n"
            f"Pembeli sudah dinotifikasi untuk menghubungi admin.",
            reply_markup=menu_admin()
        )

@bot.message_handler(commands=["tolak"])
def order_tolak(message):
    if message.from_user.id != ADMIN_ID:
        return
    ref_id = ambil_ref_id(message.text, "tolak")
    if not ref_id:
        bot.send_message(message.chat.id, "Format: /tolak REFID alasan")
        return
    try:
        teks = message.text.strip()
        setelah_refid = teks.split(ref_id, 1)[1].strip()
        alasan = setelah_refid if setelah_refid else "Pembayaran tidak diterima"
    except:
        alasan = "Pembayaran tidak diterima"

    order = get_order(ref_id)
    if not order:
        bot.send_message(message.chat.id, f"Order {ref_id} tidak ditemukan.")
        return
    update_order_status(ref_id, "gagal")
    try:
        bot.send_message(
            order["user_id"],
            f"❌ *Order Ditolak*\n\n"
            f"Ref ID : `{ref_id}`\n"
            f"Produk : {order['produk']}\n"
            f"Harga  : {format_rupiah(order['harga'])}\n"
            f"Alasan : {alasan}\n\n"
            f"Dana kamu akan dikembalikan oleh admin.\n"
            f"Hubungi admin:\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
            parse_mode="Markdown"
        )
    except:
        pass
    bot.send_message(
        message.chat.id,
        f"✅ Order {ref_id} ditolak.\n\n"
        f"⚠️ *PERLU REFUND:*\n"
        f"Pembeli : {order['nama']}\n"
        f"Nominal : {format_rupiah(order['harga'])}\n"
        f"Ref ID  : `{ref_id}`\n\n"
        f"Tandai sudah direfund: /refund {ref_id}",
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

@bot.message_handler(commands=["refund"])
def order_refund(message):
    if message.from_user.id != ADMIN_ID:
        return
    ref_id = ambil_ref_id(message.text, "refund")
    if not ref_id:
        bot.send_message(message.chat.id, "Format: /refund REFID")
        return
    order = get_order(ref_id)
    if not order:
        bot.send_message(message.chat.id, f"Order {ref_id} tidak ditemukan.")
        return
    # Notif ke pembeli bahwa refund sudah dikirim
    try:
        bot.send_message(
            order["user_id"],
            f"💸 *Refund Berhasil*\n\n"
            f"Ref ID : `{ref_id}`\n"
            f"Produk : {order['produk']}\n"
            f"Nominal: {format_rupiah(order['harga'])}\n\n"
            f"Dana sudah dikembalikan oleh admin.\n"
            f"Terima kasih atas pengertiannya 🙏\n\n"
            f"Butuh bantuan?\nTelegram : @{ADMIN_USERNAME}\nWhatsApp : {ADMIN_WA}",
            parse_mode="Markdown"
        )
    except:
        pass
    bot.send_message(
        message.chat.id,
        f"✅ Refund {ref_id} sudah ditandai!\n"
        f"Pembeli ({order['nama']}) sudah dinotifikasi.",
        reply_markup=menu_admin()
    )

# ─────────────────────────────────────────────
# CEK IP
# ─────────────────────────────────────────────

def get_ip_railway():
    """Ambil IP publik Railway saat ini."""
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        return r.text.strip()
    except:
        try:
            r = requests.get("https://ifconfig.me/ip", timeout=5)
            return r.text.strip()
        except:
            return "Gagal ambil IP"

@bot.message_handler(commands=["cekip"])
def cek_ip(message):
    if message.from_user.id != ADMIN_ID:
        return
    ip = get_ip_railway()
    teks = (
        "\U0001f310 *IP Railway Saat Ini*\n\n"
        + f"`{ip}`"
        + "\n\nPastikan IP ini sudah ada di whitelist Digiflazz."
    )
    bot.send_message(
        message.chat.id,
        teks,
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

# ─────────────────────────────────────────────
# JALANKAN BOT
# ─────────────────────────────────────────────
init_db()
print("Andika Store Bot berjalan...")
print(f"Mode        : {'SANDBOX' if SANDBOX_MODE else 'PRODUCTION'}")
print(f"Digi User   : {DIGI_USERNAME}")
print(f"Digi Key    : {DIGI_API_KEY[:6]}... (sensor)")
print(f"Proxy       : {FIXIE_URL[:20] + '...' if FIXIE_URL else 'Tidak ada (direct)'}")
print(f"Produk      : {sum(len(v) for v in PRODUCTS['pulsa'].values())} pulsa, {sum(len(v) for v in PRODUCTS['data'].values())} data")

# Notif ke admin saat bot online + kirim IP Railway
def notif_online():
    try:
        ip = get_ip_railway()
        mode = "SANDBOX" if SANDBOX_MODE else "PRODUCTION"
        teks = "Bot Andika Store Online!\n\n"
        teks += "IP Railway : " + ip + "\n"
        teks += "Mode       : " + mode + "\n\n"
        teks += "Cek whitelist Digiflazz jika IP berubah."
        bot.send_message(ADMIN_ID, teks)
    except:
        pass

# Notif maintenance ke semua user saat bot baru online
def notif_maintenance_selesai():
    import time
    time.sleep(3)  # tunggu bot siap dulu
    users = get_all_users()
    berhasil = 0
    for uid in users:
        if uid == ADMIN_ID:
            continue
        try:
            bot.send_message(
                uid,
                "Andika Store\n\n"
                "Bot kembali online setelah maintenance.\n"
                "Silakan lanjutkan transaksi kamu. \U0001f44b"
            )
            berhasil += 1
            time.sleep(0.05)  # hindari flood Telegram
        except:
            pass
    # Laporan ke admin
    try:
        bot.send_message(
            ADMIN_ID,
            "Notif maintenance terkirim ke " + str(berhasil) + " user."
        )
    except:
        pass

threading.Thread(target=notif_online, daemon=True).start()
threading.Thread(target=notif_maintenance_selesai, daemon=True).start()

bot.infinity_polling()
