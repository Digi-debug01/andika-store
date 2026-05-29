import telebot
import requests
import hashlib
import os
from dotenv import load_dotenv
from telebot import types
from datetime import datetime
from products import PRODUCTS, SKU_MAP

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DIGI_USERNAME = os.getenv("DIGI_USERNAME", "")
DIGI_API_KEY = os.getenv("DIGI_API_KEY", "")
SANDBOX_MODE = True  # Ganti False setelah deposit saldo

DIGI_URL = "https://api.digiflazz.com/v1"

bot = telebot.TeleBot(BOT_TOKEN)

# ─────────────────────────────────────────────
# DATABASE SEMENTARA
# ─────────────────────────────────────────────
order_db = {}
user_db = {}
user_sessions = {}
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
        r = requests.post(f"{DIGI_URL}/cek-saldo", json=payload, timeout=10)
        return r.json().get("data", {}).get("deposit", 0)
    except:
        return None

def transaksi(ref_id, customer_no, buyer_sku_code):
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
    return f"AS{user_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

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
    operators = list(PRODUCTS["pulsa"].keys())
    for op in operators:
        markup.add(types.KeyboardButton(op))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

def menu_nominal(operator, kategori="pulsa"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    items = PRODUCTS[kategori].get(operator, [])
    for item in items:
        markup.add(types.KeyboardButton(
            f"{item['nama']} - {format_rupiah(item['harga'])}"
        ))
    markup.add(types.KeyboardButton("🔙 Kembali"))
    return markup

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

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_db[uid] = {
        "nama": message.from_user.first_name,
        "username": message.from_user.username or "-"
    }
    user_sessions[uid] = {}
    mode_text = "🧪 MODE TESTING" if SANDBOX_MODE else "🟢 LIVE"
    teks = (
        f"👋 Halo, *{message.from_user.first_name}*!\n\n"
        f"Selamat datang di *Andika Store* {mode_text}\n"
        f"🛒 Pulsa, Paket Data & Top Up Game!\n\n"
        f"Silakan pilih menu:"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())

# ─────────────────────────────────────────────
# MENU PULSA
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📱 Pulsa")
def menu_pulsa(message):
    uid = message.from_user.id
    user_sessions[uid] = {"tipe": "pulsa"}
    bot.send_message(
        message.chat.id,
        "📱 *Pulsa*\nPilih operator:",
        parse_mode="Markdown",
        reply_markup=menu_operator_pulsa()
    )

@bot.message_handler(func=lambda m: m.text in PRODUCTS["pulsa"].keys())
def pilih_operator_pulsa(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})
    if sesi.get("tipe") != "pulsa":
        return
    operator = message.text
    user_sessions[uid]["operator"] = operator
    user_sessions[uid]["step"] = "pilih_nominal"
    bot.send_message(
        message.chat.id,
        f"📱 *Pulsa {operator}*\nPilih nominal:",
        parse_mode="Markdown",
        reply_markup=menu_nominal(operator, "pulsa")
    )

# ─────────────────────────────────────────────
# HANDLER PILIH NOMINAL
# ─────────────────────────────────────────────

def get_produk_dari_teks(teks, operator, kategori):
    items = PRODUCTS[kategori].get(operator, [])
    for item in items:
        label = f"{item['nama']} - {format_rupiah(item['harga'])}"
        if teks == label:
            return item
    return None

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "pilih_nominal")
def pilih_nominal(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})
    operator = sesi.get("operator")
    kategori = sesi.get("tipe", "pulsa")

    if message.text == "🔙 Kembali":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "🏠 Menu utama.", reply_markup=menu_utama())
        return

    produk = get_produk_dari_teks(message.text, operator, kategori)
    if not produk:
        bot.send_message(message.chat.id, "❌ Produk tidak ditemukan, pilih dari menu.")
        return

    user_sessions[uid]["produk"] = produk
    user_sessions[uid]["step"] = "input_nomor"

    bot.send_message(
        message.chat.id,
        f"📱 *{produk['nama']}*\nHarga: *{format_rupiah(produk['harga'])}*\n\nMasukkan nomor HP tujuan:",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )

# ─────────────────────────────────────────────
# INPUT NOMOR
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "input_nomor")
def input_nomor(message):
    uid = message.from_user.id
    if message.text == "🔙 Kembali":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "🏠 Menu utama.", reply_markup=menu_utama())
        return

    sesi = user_sessions.get(uid, {})
    produk = sesi.get("produk", {})
    nomor = message.text.strip()
    user_sessions[uid]["nomor"] = nomor
    user_sessions[uid]["step"] = "konfirmasi"

    teks = (
        f"📋 *Konfirmasi Order*\n\n"
        f"Produk : {produk['nama']}\n"
        f"Nomor  : `{nomor}`\n"
        f"Harga  : *{format_rupiah(produk['harga'])}*\n\n"
        f"⚠️ Pastikan nomor sudah benar!\n"
        f"Ketik *YA* untuk lanjut atau *BATAL*"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("YA"), types.KeyboardButton("BATAL"))
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=markup)

# ─────────────────────────────────────────────
# KONFIRMASI ORDER
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text in ["YA", "BATAL"] and user_sessions.get(m.from_user.id, {}).get("step") == "konfirmasi")
def konfirmasi_order(message):
    uid = message.from_user.id
    sesi = user_sessions.get(uid, {})

    if message.text == "BATAL":
        user_sessions[uid] = {}
        bot.send_message(message.chat.id, "❌ Order dibatalkan.", reply_markup=menu_utama())
        return

    produk = sesi.get("produk", {})
    nomor = sesi.get("nomor")
    ref_id = buat_ref_id(uid)
    user_sessions[uid]["ref_id"] = ref_id
    user_sessions[uid]["step"] = "menunggu_bayar"

    # Simpan ke order_db
    order_db[ref_id] = {
        "user_id": uid,
        "nama": message.from_user.first_name,
        "tipe": sesi.get("tipe"),
        "operator": sesi.get("operator", "-"),
        "produk": produk.get("nama"),
        "kode": produk.get("kode"),
        "nomor": nomor,
        "harga": produk.get("harga"),
        "status": "pending",
        "waktu": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    teks_bayar = (
        f"💳 *Informasi Pembayaran*\n\n"
        f"Produk : {produk['nama']}\n"
        f"Nomor  : `{nomor}`\n"
        f"Total  : *{format_rupiah(produk['harga'])}*\n"
        f"Ref ID : `{ref_id}`\n\n"
        f"Transfer ke:\n"
        f"🏦 *BCA* — 1234567890\n"
        f"👤 a.n. *Andika*\n\n"
        f"_Kirim bukti bayar ke admin setelah transfer._\n"
        f"/admin"
    )
    bot.send_message(message.chat.id, teks_bayar, parse_mode="Markdown", reply_markup=menu_kembali())

    # Notif admin
    notif = (
        f"🔔 *ORDER BARU!*\n\n"
        f"👤 {message.from_user.first_name} (@{message.from_user.username or '-'})\n"
        f"📦 {produk['nama']}\n"
        f"📞 Nomor: `{nomor}`\n"
        f"💰 Harga: {format_rupiah(produk['harga'])}\n"
        f"🧾 Ref ID: `{ref_id}`\n\n"
        f"Konfirmasi: /konfirmasi_{ref_id}"
    )
    try:
        bot.send_message(ADMIN_ID, notif, parse_mode="Markdown")
    except:
        pass

# ─────────────────────────────────────────────
# MENU LAINNYA
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📶 Paket Data")
def menu_paket(message):
    bot.send_message(
        message.chat.id,
        "📶 *Paket Data*\n\n_Segera hadir! Saat ini sedang dalam persiapan._\n\nUntuk sementara hubungi admin:",
        parse_mode="Markdown",
        reply_markup=menu_utama()
    )

@bot.message_handler(func=lambda m: m.text == "🎮 Top Up Game")
def menu_game(message):
    bot.send_message(
        message.chat.id,
        "🎮 *Top Up Game*\n\n_Segera hadir! Saat ini sedang dalam persiapan._\n\nUntuk sementara hubungi admin:",
        parse_mode="Markdown",
        reply_markup=menu_utama()
    )

@bot.message_handler(func=lambda m: m.text == "🔙 Kembali")
def kembali(message):
    user_sessions[message.from_user.id] = {}
    bot.send_message(message.chat.id, "🏠 Menu utama.", reply_markup=menu_utama())

@bot.message_handler(func=lambda m: m.text == "ℹ️ Info & Bantuan")
def info(message):
    teks = (
        "ℹ️ *Info Andika Store*\n\n"
        "🕐 Layanan: 24 Jam\n"
        "⚡ Proses: Otomatis & Cepat\n"
        "✅ Terpercaya & Aman\n\n"
        "📞 @Alfatih04\n"
        "/admin\n\n"
        "🌐 *Website:*\n"
        "https://digi-debug01.github.io/andika-store/"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())

@bot.message_handler(commands=["admin"])
def hubungi_admin(message):
    bot.send_message(message.chat.id, "📞 Silakan hubungi admin untuk bantuan.", reply_markup=menu_utama())

@bot.message_handler(func=lambda m: m.text == "💳 Cek Transaksi")
def cek_transaksi(message):
    bot.send_message(
        message.chat.id,
        "🔍 Masukkan *Ref ID* transaksi kamu:\n(contoh: AS1234567890)",
        parse_mode="Markdown",
        reply_markup=menu_kembali()
    )
    user_sessions[message.from_user.id] = {"step": "cek_transaksi"}

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("step") == "cek_transaksi")
def proses_cek_transaksi(message):
    if message.text == "🔙 Kembali":
        user_sessions[message.from_user.id] = {}
        bot.send_message(message.chat.id, "🏠 Menu utama.", reply_markup=menu_utama())
        return
    ref_id = message.text.strip()
    order = order_db.get(ref_id)
    if not order:
        bot.send_message(message.chat.id, "❌ Ref ID tidak ditemukan.", reply_markup=menu_utama())
        return
    status_icon = {"pending": "⏳", "sukses": "✅", "gagal": "❌", "diproses": "🔄"}.get(order["status"], "❓")
    teks = (
        f"🔍 *Status Transaksi*\n\n"
        f"Ref ID  : `{ref_id}`\n"
        f"Produk  : {order['produk']}\n"
        f"Nomor   : `{order['nomor']}`\n"
        f"Harga   : {format_rupiah(order['harga'])}\n"
        f"Status  : {status_icon} {order['status'].upper()}\n"
        f"Waktu   : {order['waktu']}"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_utama())
    user_sessions[message.from_user.id] = {}

# ─────────────────────────────────────────────
# PANEL ADMIN
# ─────────────────────────────────────────────

@bot.message_handler(commands=["panel"])
def panel_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Akses ditolak.")
        return
    mode_text = "🧪 SANDBOX" if SANDBOX_MODE else "🟢 PRODUCTION"
    teks = (
        f"🛠️ *PANEL ADMIN — Andika Store*\n"
        f"{'─' * 28}\n"
        f"Mode        : {mode_text}\n"
        f"Total Order : {len(order_db)}\n"
        f"Total User  : {len(user_db)}\n\n"
        f"Pilih menu:"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "💰 Cek Saldo" and m.from_user.id == ADMIN_ID)
def cek_saldo_admin(message):
    bot.send_message(message.chat.id, "⏳ Mengecek saldo...")
    saldo = cek_saldo()
    if saldo is not None:
        bot.send_message(message.chat.id, f"💰 Saldo Digiflazz: *{format_rupiah(saldo)}*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Gagal cek saldo.")

@bot.message_handler(func=lambda m: m.text == "📋 Daftar Order" and m.from_user.id == ADMIN_ID)
def daftar_order(message):
    if not order_db:
        bot.send_message(message.chat.id, "📭 Belum ada order.", reply_markup=menu_admin())
        return
    teks = "📋 *DAFTAR ORDER* (10 terakhir)\n" + "─" * 28 + "\n\n"
    for ref, o in list(order_db.items())[-10:]:
        icon = {"pending": "⏳", "sukses": "✅", "gagal": "❌", "diproses": "🔄"}.get(o["status"], "❓")
        teks += f"{icon} `{ref}`\n👤 {o['nama']} | {o['produk']}\n📞 {o['nomor']} | {format_rupiah(o['harga'])}\n🕐 {o['waktu']}\n\n"
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "📊 Statistik" and m.from_user.id == ADMIN_ID)
def statistik(message):
    total = len(order_db)
    sukses = sum(1 for o in order_db.values() if o["status"] == "sukses")
    pending = sum(1 for o in order_db.values() if o["status"] == "pending")
    gagal = sum(1 for o in order_db.values() if o["status"] == "gagal")
    diproses = sum(1 for o in order_db.values() if o["status"] == "diproses")
    omzet = sum(o["harga"] for o in order_db.values() if o["status"] == "sukses")
    saldo = cek_saldo()
    teks = (
        f"📊 *STATISTIK ANDIKA STORE*\n"
        f"{'─' * 28}\n\n"
        f"📦 Total Order : {total}\n"
        f"✅ Sukses      : {sukses}\n"
        f"🔄 Diproses    : {diproses}\n"
        f"⏳ Pending     : {pending}\n"
        f"❌ Gagal       : {gagal}\n\n"
        f"💵 Total Omzet : {format_rupiah(omzet)}\n"
        f"👥 Total User  : {len(user_db)}\n"
        f"💰 Saldo Digi  : {format_rupiah(saldo) if saldo else 'Gagal ambil'}\n\n"
        f"Mode: {'🧪 SANDBOX' if SANDBOX_MODE else '🟢 PRODUCTION'}"
    )
    bot.send_message(message.chat.id, teks, parse_mode="Markdown", reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast_menu(message):
    broadcast_sessions[message.from_user.id] = True
    bot.send_message(message.chat.id, "📢 Ketik pesan broadcast:\n_(ketik /batal untuk membatalkan)_", parse_mode="Markdown", reply_markup=menu_kembali())

@bot.message_handler(func=lambda m: broadcast_sessions.get(m.from_user.id) and m.from_user.id == ADMIN_ID)
def kirim_broadcast(message):
    if message.text in ["/batal", "🔙 Kembali"]:
        broadcast_sessions.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "❌ Broadcast dibatalkan.", reply_markup=menu_admin())
        return
    broadcast_sessions.pop(message.from_user.id, None)
    berhasil = gagal_kirim = 0
    for uid in user_db:
        try:
            bot.send_message(uid, f"📢 *INFO ANDIKA STORE*\n\n{message.text}", parse_mode="Markdown")
            berhasil += 1
        except:
            gagal_kirim += 1
    bot.send_message(message.chat.id, f"📢 Broadcast selesai!\n✅ {berhasil} berhasil\n❌ {gagal_kirim} gagal", reply_markup=menu_admin())

@bot.message_handler(func=lambda m: m.text == "🔙 Menu Utama" and m.from_user.id == ADMIN_ID)
def kembali_menu_utama_admin(message):
    bot.send_message(message.chat.id, "🏠 Menu utama.", reply_markup=menu_utama())

@bot.message_handler(commands=["konfirmasi"])
def konfirmasi_bayar(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        ref_id = message.text.split("_", 1)[1]
    except:
        bot.send_message(message.chat.id, "Format: /konfirmasi_REFID")
        return
    if ref_id not in order_db:
        bot.send_message(message.chat.id, f"❌ Order `{ref_id}` tidak ditemukan.", parse_mode="Markdown")
        return
    order_db[ref_id]["status"] = "diproses"
    try:
        bot.send_message(order_db[ref_id]["user_id"], f"✅ Pembayaran dikonfirmasi!\nRef ID: `{ref_id}`\nOrder sedang diproses... 🙏", parse_mode="Markdown")
    except:
        pass
    bot.send_message(message.chat.id, f"✅ Order `{ref_id}` dikonfirmasi!", parse_mode="Markdown", reply_markup=menu_admin())

@bot.message_handler(commands=["sukses"])
def order_sukses(message):
    if message.from_user.id != ADMIN_ID:
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
    try:
        bot.send_message(order["user_id"], f"🎉 *Order Berhasil!*\n\nRef ID : `{ref_id}`\nProduk : {order['produk']}\nNomor  : `{order['nomor']}`\nStatus : ✅ SUKSES\n\nTerima kasih sudah belanja di *Andika Store*! 🙏", parse_mode="Markdown")
    except:
        pass
    bot.send_message(message.chat.id, f"✅ Order `{ref_id}` ditandai SUKSES!", parse_mode="Markdown", reply_markup=menu_admin())

@bot.message_handler(commands=["tolak"])
def order_tolak(message):
    if message.from_user.id != ADMIN_ID:
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
    try:
        bot.send_message(order["user_id"], f"❌ *Order Ditolak*\n\nRef ID : `{ref_id}`\nAlasan : {alasan}\n\nHubungi admin: /admin", parse_mode="Markdown")
    except:
        pass
    bot.send_message(message.chat.id, f"❌ Order `{ref_id}` ditolak!", parse_mode="Markdown", reply_markup=menu_admin())

# ─────────────────────────────────────────────
# JALANKAN BOT
# ─────────────────────────────────────────────
print("🚀 Andika Store Bot berjalan...")
print(f"Mode: {'🧪 SANDBOX' if SANDBOX_MODE else '🟢 PRODUCTION'}")
print(f"Produk tersedia: {sum(len(v) for v in PRODUCTS['pulsa'].values())} pulsa")
bot.infinity_polling()
