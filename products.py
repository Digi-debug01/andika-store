# ─────────────────────────────────────────────
# DAFTAR PRODUK ANDIKA STORE
# Harga Bot = Modal + Rp1.000
# Harga Offline = Modal + Rp2.000
# ─────────────────────────────────────────────

PRODUCTS = {
    "pulsa": {
        "Telkomsel": [
            {"kode": "TSL5",   "nama": "Telkomsel 5.000",   "harga": 6200},
            {"kode": "TSL10",  "nama": "Telkomsel 10.000",  "harga": 11135},
            {"kode": "TSL15",  "nama": "Telkomsel 15.000",  "harga": 15900},
            {"kode": "TSL20",  "nama": "Telkomsel 20.000",  "harga": 20960},
            {"kode": "TSL25",  "nama": "Telkomsel 25.000",  "harga": 25685},
            {"kode": "TSL50",  "nama": "Telkomsel 50.000",  "harga": 51025},
            {"kode": "TSL100", "nama": "Telkomsel 100.000", "harga": 98020},
        ],
        "Indosat": [
            {"kode": "ISAT5",   "nama": "Indosat 5.000",   "harga": 7359},
            {"kode": "ISAT10",  "nama": "Indosat 10.000",  "harga": 12570},
            {"kode": "ISAT20",  "nama": "Indosat 20.000",  "harga": 21510},
            {"kode": "ISAT50",  "nama": "Indosat 50.000",  "harga": 50818},
            {"kode": "ISAT100", "nama": "Indosat 100.000", "harga": 100030},
        ],
        "XL": [
            {"kode": "XL5",   "nama": "XL 5.000",   "harga": 6933},
            {"kode": "XL10",  "nama": "XL 10.000",  "harga": 11855},
            {"kode": "XL15",  "nama": "XL 15.000",  "harga": 15994},
            {"kode": "XL25",  "nama": "XL 25.000",  "harga": 25975},
            {"kode": "XL50",  "nama": "XL 50.000",  "harga": 50935},
            {"kode": "XL100", "nama": "XL 100.000", "harga": 100820},
        ],
        "Tri": [
            {"kode": "TRI5",  "nama": "Tri 5.000",  "harga": 6110},
            {"kode": "TRI10", "nama": "Tri 10.000", "harga": 12655},
            {"kode": "TRI20", "nama": "Tri 20.000", "harga": 20620},
            {"kode": "TRI50", "nama": "Tri 50.000", "harga": 50020},
        ],
        "Axis": [
            {"kode": "AXS5",   "nama": "Axis 5.000",   "harga": 6848},
            {"kode": "AXS10",  "nama": "Axis 10.000",  "harga": 11895},
            {"kode": "AXS15",  "nama": "Axis 15.000",  "harga": 15994},
            {"kode": "AXS50",  "nama": "Axis 50.000",  "harga": 50935},
            {"kode": "AXS100", "nama": "Axis 100.000", "harga": 100820},
        ],
        "Smartfren": [
            {"kode": "SMT2",   "nama": "Smartfren 2.000",  "harga": 3009},
            {"kode": "SMT3",   "nama": "Smartfren 3.000",  "harga": 4006},
            {"kode": "SMT4",   "nama": "Smartfren 4.000",  "harga": 5003},
            {"kode": "SMT5",   "nama": "Smartfren 5.000",  "harga": 6205},
            {"kode": "SMT10",  "nama": "Smartfren 10.000", "harga": 11040},
            {"kode": "SMT15",  "nama": "Smartfren 15.000", "harga": 15980},
            {"kode": "SMT100", "nama": "Smartfren 50.000", "harga": 50855},
        ],
    },
    "data": {},   # Diisi nanti
    "game": {},   # Diisi nanti
}

# Mapping cepat kode → produk
SKU_MAP = {}
for kategori, operators in PRODUCTS.items():
    for operator, items in operators.items():
        for item in items:
            SKU_MAP[item["kode"]] = {**item, "operator": operator, "kategori": kategori}

# ─────────────────────────────────────────────
# DAFTAR HARGA OFFLINE (untuk referensi admin)
# Modal + Rp2.000
# ─────────────────────────────────────────────
HARGA_OFFLINE = {
    # Telkomsel
    "TSL5":   7200,   "TSL10":  12135,  "TSL15":  16900,
    "TSL20":  21960,  "TSL25":  26685,  "TSL50":  52025,  "TSL100": 99020,
    # Indosat
    "ISAT5":  8359,   "ISAT10": 13570,  "ISAT20": 22510,
    "ISAT50": 51818,  "ISAT100":101030,
    # XL
    "XL5":    7933,   "XL10":   12855,  "XL15":   16994,
    "XL25":   26975,  "XL50":   51935,  "XL100":  101820,
    # Tri
    "TRI5":   7110,   "TRI10":  13655,  "TRI20":  21620,  "TRI50":  51020,
    # Axis
    "AXS5":   7848,   "AXS10":  12895,  "AXS15":  16994,
    "AXS50":  51935,  "AXS100": 101820,
    # Smartfren
    "SMT2":   4009,   "SMT3":   5006,   "SMT4":   6003,
    "SMT5":   7205,   "SMT10":  12040,  "SMT15":  16980,  "SMT100": 51855,
}
