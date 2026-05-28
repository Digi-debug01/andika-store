import telebot
import requests
import hashlib
import json
import os
from dotenv import load_dotenv
from telebot import types
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DIGI_USERNAME = os.getenv("DIGI_USERNAME", "")
DIGI_API_KEY = os.getenv("DIGI_API_KEY", "")

# Mode sandbox untuk testing (ganti ke False setelah verifikasi Digiflazz)
SANDBOX_MODE = True

DIGI_URL = "https://api.digiflazz.com/v1"

bot = telebot.TeleBot(BOT_TOKEN)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def digi_sign(username, api_key, ref_id=""):
    """Buat signature MD5 untuk Digiflazz"""
    raw = username + api_key + ref_id
    return hashlib.md5(raw.encode()).hexdigest()

def cek_saldo():
    """Cek saldo Digiflazz"""
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, "depo")
    payload = {
        "cmd": "deposit",
        "username": DIGI_USERNAME,
        "sign": sign
    }
    try:
        r = requests.post(f"{DIGI_URL}/cek-saldo", json=payload, timeout=10)
        data = r.json()
        return data.get("data", {}).get("deposit", 0)
    except:
        return None

def get_pricelist(category=""):
    """Ambil daftar produk dari Digiflazz"""
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, "pricelist")
    payload = {
        "cmd": "prepaid",
        "username": DIGI_USERNAME,
        "sign": sign
    }
    if SANDBOX_MODE:
        payload["testing"] = True
    try:
        r = requests.post(f"{DIGI_URL}/price-list", json=payload, timeout=15)
        data = r.json()
        products = data.get("data", [])
        if category:
            products = [p for p in products if category.lower() in p.get("category", "").lower()]
        return products
    except:
        return []

def transaksi(ref_id, customer_no, buyer_sku_code):
    """Proses transaksi ke Digiflazz"""
    sign = digi_sign(DIGI_USERNAME, DIGI_API_KEY, ref_id)
    payload = {
        "username": DIGI_USERNAME,
        "buyer_sku_code": buyer_sku_code,
        "customer_no": customer_no,
        "ref_id": ref_id,
        "sign": sign,
        "testing": SANDBOX_MODE
    }
    try:
        r = requests.post(f"{DIGI_URL}/transaction", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        return {"data": {"rc": "ERROR", "message": str(e)}}

def buat_ref_id(user_id):
    """Buat referensi ID unik"""
    return f"AS{user_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

# ─────────────────────────────────────────────
# PENYIMPANAN SESI ORDER (sementara di memori)
# ─────────────────────────────────────────────
user_sessions = {}

# ─────────────────────────────────────────────
# MENU UTAMA
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

def menu_operator():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        types.KeyboardButton("Telkomsel"),
        types.KeyboardButton("Indosat"),
        types.KeyboardButton("XL"),
        types.KeyboardButton("Tri"),
        types.KeyboardButton("Axis"),
        types.KeyboardButton("Smartfren"),
        types.KeyboardButton("🔙 Kembali")
    )
    return markup

def menu_game():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Mobile Legends"),
        types.KeyboardButton("Free Fire"),
        types.KeyboardButton("PUBG Mobile"),
        types.KeyboardButton("Genshin Impact"),
        types.KeyboardButton("Valorant"),
        types.KeyboardButton("🔙 Kembali")
    )
    return markup

def menu_kembali():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

# ─────────────────────────────────────────────
# HANDLER /start
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    nama = message.from_user.first_name
    mode_text = "🧪 MODE TESTING" if SANDBOX_MODE else "🟢 LIVE"
    teks = (
        f"👋 Halo, *{nama}*!\n\n"
        f"Selamat datang di *Andika Store* {mode_text}\n"
        f"🛒 Toko pulsa & top up game terpercaya!\n\n"
        f"Silakan pilih menu di bawah ini:"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())
    user_sessions[message.from_user.id] = {}

# ─────────────────────────────────────────────
# HANDLER MENU
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📱 Pulsa")
def menu_pulsa(message):
    user_sessions[message.from_user.id] = {"tipe": "pulsa"}
    bot.send_message(
        message.chat.id,
        "📱 *Pulsa*\nPilih operator kamu:",
        parse_mode="Markdown",
        reply_markup=menu_operator()
    )

@bot.message_handler(func=lambda m: m.text == "📶 Paket Data")
def menu_paket(message):
    user_sessions[message.from_user.id] = {"tipe": "paket"}
    bot.send_message(
        message.chat.id,
        "📶 *Paket Data*\nPilih operator kamu:",
        parse_mode="Markdown",
        reply_markup=menu_operator()
    )

@bot.message_handler(func=lambda m: m.text == "🎮 Top Up Game")
def menu_topup_game(message):
    user_sessions[message.from_user.id] = {"tipe": "game"}
    bot.send_message(
        message.chat.id,
        "🎮 *Top Up Game*\nPilih game:",
        parse_mode="Markdown",
        reply_markup=menu_game()
    )

@bot.message_handler(func=lambda m: m.text == "🔙 Kembali")
def kembali(message):
    user_sessions[message.from_user.id] = {}
    bot.send_message(
        message.chat.id,
        "🏠 Kembali ke menu utama.",
        reply_markup=menu_utama()
    )

@bot.message_handler(func=lambda m: m.text == "ℹ️ Info & Bantuan")
def info(message):
    teks = (
        "ℹ️ *Info Andika Store*\n\n"
        "🕐 Layanan: 24 Jam\n"
        "⚡ Proses: Otomatis & Cepat\n"
        "✅ Terpercaya & Aman\n\n"
        "📞 *Hubungi Admin:*\n"
        "Ketik /admin jika butuh bantuan\n\n"
        "📋 *Cara Order:*\n"
        "1. Pilih menu produk\n"
        "2. Pilih operator/game\n"
        "3. Pilih nominal\n"
        "4. Masukkan nomor/ID\n"
        "5. Konfirmasi & bayar\n"
        "6. Produk langsung masuk otomatis!"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())

@bot.message_handler(commands=["admin"])
def hubungi_admin(message):
    bot.send_message(
        message.chat.id,
        f"📞 Hubungi admin:\nt.me/{bot.get_chat(ADMIN_ID).username or 'admin'}",
        reply_markup=menu_utama()
    )

# ─────────────────────────────────────────────
# HANDLER PILIH OPERATOR
# ─────────────────────────────────────────────

OPERATOR_LIST = ["Telkomsel", "Indosat", "XL", "Tri", "Axis", "Smartfren"]
GAME_LIST = ["Mobile Legends", "Free Fire", "PUBG Mobile", "Genshin Impact", "Valorant"]

OPERATOR_SKU_MAP = {
    "pulsa": {
        "Telkomsel": "XL",
        "Indosat": "IM3",
        "XL": "XL",
        "Tri": "THREE",
        "Axis": "AXIS",
        "Smartfren": "SF"
    },
    "paket": {
        "Telkomsel": "TSEL",
        "Indosat": "ISAT",
        "XL": "XL",
        "Tri": "THREE",
        "Axis": "AXIS",
        "Smartfren": "SF"
    }
}

NOMINAL_PULSA = ["5.000", "10.000", "15.000", "20.000", "25.000", "50.000", "100.000"]

def menu_nominal():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(n) for n in NOMINAL_PULSA]
    buttons.append(types.KeyboardButton("🔙 Kembali"))
    markup.add(*buttons)
    return markup

@bot.message_handler(func=lambda m: m.text in OPERATOR_LIST)
def pilih_operator(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})
    tipe = sesi.get("tipe")

    if not tipe:
        bot.send_message(message.chat.id, "Silakan mulai dari menu utama.", reply_markup=menu_utama())
        return

    user_sessions[uid]["operator"] = message.text

    if tipe == "pulsa":
        bot.send_message(
            message.chat.id,
            f"📱 *Pulsa {message.text}*\nPilih nominal:",
            parse_mode="Markdown",
            reply_markup=menu_nominal()
        )
        user_sessions[uid]["step"] = "pilih_nominal"

    elif tipe == "paket":
        bot.send_message(
            message.chat.id,
            f"📶 *Paket Data {message.text}*\n\nMasukkan nomor HP tujuan:\n(contoh: 08123456789)",
            parse_mode="Markdown",
            reply_markup=menu_kembali()
        )
        user_sessions[uid]["step"] = "input_nomor_paket"

@bot.message_handler(func=lambda m: m.text in GAME_LIST)
def pilih_game(message):
    uid = message.from_user.id
    user_sessions[uid]["game"] = message.text
    user_sessions[uid]["step"] = "input_id_game"

    bot.send_message(
        message.chat.id,
        f"🎮 *{message.text}*\n\nMasukkan *ID Game* kamu:\n(untuk ML: ID + Server, contoh: 12345678 1234)",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )

# ─────────────────────────────────────────────
# HANDLER NOMINAL PULSA
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text in NOMINAL_PULSA)
def pilih_nominal(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})

    if sesi.get("step") != "pilih_nominal":
        return

    user_sessions[uid]["nominal"] = message.text
    user_sessions[uid]["step"] = "input_nomor"

    bot.send_message(
        message.chat.id,
        f"📱 *Pulsa {sesi['operator']} {message.text}*\n\nMasukkan nomor HP tujuan:\n(contoh: 08123456789)",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )

# ─────────────────────────────────────────────
# HANDLER INPUT NOMOR / ID
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") in ["input_nomor", "input_nomor_paket", "input_id_game"])
def input_nomor(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})
    step = sesi.get("step")
    nomor = message.text.strip()

    user_sessions[uid]["nomor"] = nomor

    if step == "input_nomor":
        operator = sesi.get("operator")
        nominal = sesi.get("nominal")
        teks = (
            f"📋 *Konfirmasi Order*\n\n"
            f"Produk : Pulsa {operator}\n"
            f"Nominal : Rp{nominal}\n"
            f"Nomor : {nomor}\n\n"
            f"⚠️ Pastikan nomor sudah benar!\n"
            f"Ketik *YA* untuk lanjut atau *BATAL* untuk membatalkan."
        )

    elif step == "input_nomor_paket":
        operator = sesi.get("operator")
        teks = (
            f"📋 *Konfirmasi Order*\n\n"
            f"Produk : Paket Data {operator}\n"
            f"Nomor : {nomor}\n\n"
            f"⚠️ Pastikan nomor sudah benar!\n"
            f"Ketik *YA* untuk lanjut atau *BATAL* untuk membatalkan."
        )

    elif step == "input_id_game":
        game = sesi.get("game")
        teks = (
            f"📋 *Konfirmasi Order*\n\n"
            f"Game : {game}\n"
            f"ID : {nomor}\n\n"
            f"⚠️ Pastikan ID sudah benar!\n"
            f"Ketik *YA* untuk lanjut atau *BATAL* untuk membatalkan."
        )

    user_sessions[uid]["step"] = "konfirmasi"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("YA"), types.KeyboardButton("BATAL"))
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=markup)

# ─────────────────────────────────────────────
# HANDLER KONFIRMASI ORDER
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text in ["YA", "BATAL"] and user_sessions.get(m.from_user.id, {}).get("step") == "konfirmasi")
def konfirmasi_order(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})

    if message.text == "BATAL":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "❌ Order dibatalkan.", reply_markup=menu_utama())
        return

    # Lanjut ke pembayaran
    user_sessions[uid]["step"] = "menunggu_bayar"
    ref_id = buat_ref_id(uid)
    user_sessions[uid]["ref_id"] = ref_id

    teks_bayar = (
        f"💳 *Informasi Pembayaran*\n\n"
        f"Ref ID : `{ref_id}`\n\n"
        f"Transfer ke:\n"
        f"🏦 *BCA* — 1234567890\n"
        f"👤 a.n. *Andika*\n\n"
        f"Setelah transfer, kirim bukti bayar ke admin:\n"
        f"/admin\n\n"
        f"_Order akan diproses setelah pembayaran dikonfirmasi._"
    )

    bot.send_message(message.chat.id, teks_bayar, parse_mode="Markdown", reply_markup=menu_kembali())

    # Notifikasi ke admin
    tipe = sesi.get("tipe", "-")
    notif_admin = (
        f"🔔 *ORDER BARU!*\n\n"
        f"👤 User: {message.from_user.first_name} (@{message.from_user.username or '-'})\n"
        f"🆔 ID: {uid}\n"
        f"📦 Tipe: {tipe.upper()}\n"
        f"📱 Operator/Game: {sesi.get('operator') or sesi.get('game', '-')}\n"
        f"💰 Nominal: {sesi.get('nominal', '-')}\n"
        f"📞 Nomor/ID: {sesi.get('nomor', '-')}\n"
        f"🧾 Ref ID: `{ref_id}`\n\n"
        f"Gunakan /proses_{ref_id} untuk memproses order ini."
    )
    try:
        bot.send_message(ADMIN_ID, notif_admin, parse_mode="Markdown")
    except:
        pass

# ─────────────────────────────────────────────
# HANDLER CEK SALDO (ADMIN)
# ─────────────────────────────────────────────

@bot.message_handler(commands=["saldo"])
def cek_saldo_cmd(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Perintah ini hanya untuk admin.")
        return

    bot.send_message(message.chat.id, "⏳ Mengecek saldo...")
    saldo = cek_saldo()
    if saldo is not None:
        bot.send_message(message.chat.id, f"💰 Saldo Digiflazz kamu: *{format_rupiah(saldo)}*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Gagal cek saldo. Cek koneksi atau API Key kamu.")

# ─────────────────────────────────────────────
# HANDLER CEK TRANSAKSI
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "💳 Cek Transaksi")
def cek_transaksi(message):
    bot.send_message(
        message.chat.id,
        "🔍 Masukkan *Ref ID* transaksi kamu:\n(contoh: AS1234567890123456)",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )
    user_sessions[message.from_user.id] = {"step": "cek_transaksi"}

# ─────────────────────────────────────────────
# DATABASE ORDER (sementara di memori)
# ─────────────────────────────────────────────
# Format: { ref_id: { user_id, nama, tipe, operator/game, nominal, nomor, status, waktu } }
order_db = {}
user_db = {}  # { user_id: { nama, username } }

# ─────────────────────────────────────────────
# PANEL ADMIN — /admin
# ─────────────────────────────────────────────

def menu_admin():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📋 Daftar Order"),
        types.KeyboardButton("💰 Cek Saldo"),
        types.KeyboardButton("📊 Statistik"),
        types.KeyboardButton("📢 Broadcast"),
        types.KeyboardButton("🔙 Menu Utama")
    )
    return markup

@bot.message_handler(commands=["panel"])
def panel_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Akses ditolak.")
        return

    mode_text = "🧪 SANDBOX" if SANDBOX_MODE else "🟢 PRODUCTION"
    teks = (
        f"🛠️ *PANEL ADMIN — Andika Store*\n"
        f"{'─' * 30}\n"
        f"Mode     : {mode_text}\n"
        f"Total Order : {len(order_db)} order\n"
        f"Total User  : {len(user_db)} user\n\n"
        f"Pilih menu di bawah:"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

# ─────────────────────────────────────────────
# DAFTAR ORDER
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📋 Daftar Order" and m.from_user.id == ADMIN_ID)
def daftar_order(message):
    if not order_db:
        bot.send_message(message.chat.id, "📭 Belum ada order masuk.", reply_markup=menu_admin())
        return

    teks = "📋 *DAFTAR ORDER*\n" + "─" * 30 + "\n\n"
    for ref, o in list(order_db.items())[-10:]:  # tampilkan 10 terakhir
        status_icon = {"pending": "⏳", "sukses": "✅", "gagal": "❌", "diproses": "🔄"}.get(o["status"], "❓")
        teks += (
            f"{status_icon} `{ref}`\n"
            f"👤 {o['nama']} | 📦 {o['tipe'].upper()}\n"
            f"📞 {o['nomor']} | 💰 {o.get('nominal', '-')}\n"
            f"🕐 {o['waktu']}\n\n"
        )

    teks += "_Gunakan /proses\\_{ref\\_id} untuk proses order_"
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

# ─────────────────────────────────────────────
# PROSES ORDER MANUAL
# ─────────────────────────────────────────────

@bot.message_handler(commands=["konfirmasi"])
def konfirmasi_bayar(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Akses ditolak.")
        return

    try:
        ref_id = message.text.split("_", 1)[1]
    except:
        bot.send_message(message.chat.id, "Format: /konfirmasi_REFID")
        return

    if ref_id not in order_db:
        bot.send_message(message.chat.id, f"❌ Order `{ref_id}` tidak ditemukan.", parse_mode="Markdown")
        return

    order = order_db[ref_id]
    order_db[ref_id]["status"] = "diproses"

    # Notif ke buyer
    try:
        bot.send_message(
            order["user_id"],
            f"✅ *Pembayaran Dikonfirmasi!*\n\n"
            f"Ref ID: `{ref_id}`\n"
            f"Order kamu sedang diproses...\n"
            f"Mohon tunggu sebentar 🙏",
            parse_mode="Markdown"
        )
    except:
        pass

    bot.send_message(
        message.chat.id,
        f"✅ Pembayaran order `{ref_id}` dikonfirmasi!\nOrder sedang diproses.",
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

@bot.message_handler(commands=["sukses"])
def order_sukses(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Akses ditolak.")
        return

    try:
        ref_id = message.text.split("_", 1)[1]
    except:
        bot.send_message(message.chat.id, "Format: /sukses_REFID")
        return

    if ref_id not in order_db:
        bot.send_message(message.chat.id, f"❌ Order `{ref_id}` tidak ditemukan.", parse_mode="Markdown")
        return

    order = order_db[ref_id]
    order_db[ref_id]["status"] = "sukses"

    # Notif ke buyer
    try:
        bot.send_message(
            order["user_id"],
            f"🎉 *Order Berhasil!*\n\n"
            f"Ref ID  : `{ref_id}`\n"
            f"Produk  : {order['tipe'].upper()} {order.get('operator') or order.get('game', '')}\n"
            f"Nomor   : {order['nomor']}\n"
            f"Status  : ✅ SUKSES\n\n"
            f"Terima kasih sudah belanja di *Andika Store*! 🙏\n"
            f"Simpan ref ID sebagai bukti transaksi.",
            parse_mode="Markdown"
        )
    except:
        pass

    bot.send_message(
        message.chat.id,
        f"✅ Order `{ref_id}` ditandai SUKSES & buyer sudah dinotifikasi.",
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

@bot.message_handler(commands=["tolak"])
def order_tolak(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Akses ditolak.")
        return

    try:
        parts = message.text.split("_", 2)
        ref_id = parts[1]
        alasan = parts[2] if len(parts) > 2 else "Pembayaran tidak diterima"
    except:
        bot.send_message(message.chat.id, "Format: /tolak_REFID_alasan")
        return

    if ref_id not in order_db:
        bot.send_message(message.chat.id, f"❌ Order `{ref_id}` tidak ditemukan.", parse_mode="Markdown")
        return

    order = order_db[ref_id]
    order_db[ref_id]["status"] = "gagal"

    # Notif ke buyer
    try:
        bot.send_message(
            order["user_id"],
            f"❌ *Order Ditolak*\n\n"
            f"Ref ID  : `{ref_id}`\n"
            f"Alasan  : {alasan}\n\n"
            f"Silakan hubungi admin jika ada pertanyaan:\n/admin",
            parse_mode="Markdown"
        )
    except:
        pass

    bot.send_message(
        message.chat.id,
        f"❌ Order `{ref_id}` ditolak & buyer sudah dinotifikasi.",
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

# ─────────────────────────────────────────────
# STATISTIK
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📊 Statistik" and m.from_user.id == ADMIN_ID)
def statistik(message):
    total = len(order_db)
    sukses = sum(1 for o in order_db.values() if o["status"] == "sukses")
    pending = sum(1 for o in order_db.values() if o["status"] == "pending")
    gagal = sum(1 for o in order_db.values() if o["status"] == "gagal")
    diproses = sum(1 for o in order_db.values() if o["status"] == "diproses")

    saldo = cek_saldo()
    saldo_text = format_rupiah(saldo) if saldo is not None else "Gagal ambil data"

    teks = (
        f"📊 *STATISTIK ANDIKA STORE*\n"
        f"{'─' * 30}\n\n"
        f"📦 Total Order  : {total}\n"
        f"✅ Sukses       : {sukses}\n"
        f"🔄 Diproses     : {diproses}\n"
        f"⏳ Pending      : {pending}\n"
        f"❌ Gagal/Tolak  : {gagal}\n\n"
        f"👥 Total User   : {len(user_db)}\n"
        f"💰 Saldo Digi   : {saldo_text}\n\n"
        f"🧪 Mode: {'SANDBOX' if SANDBOX_MODE else 'PRODUCTION'}"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

# ─────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────

broadcast_sessions = {}

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast_menu(message):
    broadcast_sessions[message.from_user.id] = True
    bot.send_message(
        message.chat.id,
        "📢 *Broadcast Pesan*\n\nKetik pesan yang ingin dikirim ke semua user:\n_(Ketik /batal untuk membatalkan)_",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )

@bot.message_handler(func=lambda m: broadcast_sessions.get(m.from_user.id) and m.from_user.id == ADMIN_ID)
def kirim_broadcast(message):
    if message.text == "/batal" or message.text == "🔙 Kembali":
        broadcast_sessions.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "❌ Broadcast dibatalkan.", reply_markup=menu_admin())
        return

    broadcast_sessions.pop(message.from_user.id, None)
    berhasil = 0
    gagal_kirim = 0

    for uid in user_db:
        try:
            bot.send_message(
                uid,
                f"📢 *INFO ANDIKA STORE*\n\n{message.text}",
                parse_mode="Markdown"
            )
            berhasil += 1
        except:
            gagal_kirim += 1

    bot.send_message(
        message.chat.id,
        f"📢 *Broadcast Selesai!*\n\n✅ Berhasil: {berhasil} user\n❌ Gagal: {gagal_kirim} user",
        parse_mode="Markdown",
        reply_markup=menu_admin()
    )

# ─────────────────────────────────────────────
# SIMPAN USER KE DATABASE
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def register_user(message):
    uid = message.from_user.id
    user_db[uid] = {
        "nama": message.from_user.first_name,
        "username": message.from_user.username or "-"
    }

# ─────────────────────────────────────────────
# BROADCAST (ADMIN)
# ─────────────────────────────────────────────

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Perintah ini hanya untuk admin.")
        return
    teks = message.text.replace("/broadcast ", "")
    bot.send_message(message.chat.id, f"📢 Broadcast: {teks}\n\n_(Fitur broadcast ke semua user akan diaktifkan setelah database ditambahkan)_")

# ─────────────────────────────────────────────
# JALANKAN BOT
# ─────────────────────────────────────────────

print("🚀 Andika Store Bot berjalan...")
print(f"🧪 Mode: {'SANDBOX/TESTING' if SANDBOX_MODE else 'PRODUCTION'}")
bot.infinity_polling()
