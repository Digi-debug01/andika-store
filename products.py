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

    # ─────────────────────────────────────────────
    # PAKET DATA
    # ─────────────────────────────────────────────
    "data": {
        "Telkomsel": [
            # Umum
            {"kode": "DTSL1G3H",       "nama": "Telkomsel 1GB 3 Hari",       "harga": 9555},
            {"kode": "DTSL2G3H",       "nama": "Telkomsel 2GB 3 Hari",       "harga": 11855},
            {"kode": "DTSL1G7H",       "nama": "Telkomsel 1GB 7 Hari",       "harga": 10655},
            {"kode": "DTSL1G15H",      "nama": "Telkomsel 1GB 15 Hari",      "harga": 11755},
            # Flash
            {"kode": "DTSLF1G30H",     "nama": "Telkomsel Flash 1GB 30 Hari",  "harga": 12385},
            {"kode": "DTSLF2G30H",     "nama": "Telkomsel Flash 2GB 30 Hari",  "harga": 24025},
            {"kode": "DTSLF3G30H",     "nama": "Telkomsel Flash 3GB 30 Hari",  "harga": 35190},
            # Combo Sakti
            {"kode": "DTSLCS1.5G30H",  "nama": "Telkomsel Combo Sakti 1.5GB 30 Hari", "harga": 22510},
            {"kode": "DTSLCS2.5G30H",  "nama": "Telkomsel Combo Sakti 2.5GB 30 Hari", "harga": 22775},
            {"kode": "DTSLCS3G30H",    "nama": "Telkomsel Combo Sakti 3GB 30 Hari",   "harga": 24525},
            {"kode": "DTSLCS4G30H",    "nama": "Telkomsel Combo Sakti 4GB 30 Hari",   "harga": 36125},
        ],
        "Indosat": [
            # Umum
            {"kode": "DISAT1G7H",      "nama": "Indosat 1GB 7 Hari",        "harga": 6700},
            {"kode": "DISAT1G3H",      "nama": "Indosat 1GB 3 Hari",        "harga": 6695},
            {"kode": "DISAT1G14H",     "nama": "Indosat 1GB 14 Hari",       "harga": 6805},
            # Yellow
            {"kode": "DISATY1G1H",     "nama": "Indosat Yellow 1GB 1 Hari", "harga": 6855},
            {"kode": "DISATY1G2H",     "nama": "Indosat Yellow 1GB 2 Hari", "harga": 6915},
            {"kode": "DISATY1G3H",     "nama": "Indosat Yellow 1GB 3 Hari", "harga": 7005},
            # Freedom Internet
            {"kode": "DISATF1.5G1H",   "nama": "Indosat Freedom 1.5GB 1 Hari",   "harga": 7865},
            {"kode": "DISATF5G1H",     "nama": "Indosat Freedom 5GB 1 Hari",     "harga": 7755},
            {"kode": "DISATF1G2H",     "nama": "Indosat Freedom 1GB 2 Hari",     "harga": 9910},
            {"kode": "DISATF1.5G3H",   "nama": "Indosat Freedom 1.5GB 3 Hari",   "harga": 12770},
            {"kode": "DISATF2.5G3H",   "nama": "Indosat Freedom 2.5GB 3 Hari",   "harga": 8000},
            {"kode": "DISATF3G3H",     "nama": "Indosat Freedom 3GB 3 Hari",     "harga": 12705},
            {"kode": "DISATF1.5G5H",   "nama": "Indosat Freedom 1.5GB 5 Hari",   "harga": 9945},
            {"kode": "DISATF2G5H",     "nama": "Indosat Freedom 2GB 5 Hari",     "harga": 13932},
            {"kode": "DISATF2.5G5H",   "nama": "Indosat Freedom 2.5GB 5 Hari",   "harga": 13920},
            {"kode": "DISATF10G5H",    "nama": "Indosat Freedom 10GB 5 Hari",    "harga": 13740},
            {"kode": "DISATF1.5G28H",  "nama": "Indosat Freedom 1.5GB 28 Hari",  "harga": 11030},
            {"kode": "DISATF2G15H",    "nama": "Indosat Freedom 2GB 15 Hari",    "harga": 12430},
            {"kode": "DISATF7G7H",     "nama": "Indosat Freedom 7GB 7 Hari",     "harga": 23435},
            {"kode": "DISATF3G28H",    "nama": "Indosat Freedom 3GB 28 Hari",    "harga": 26510},
            {"kode": "DISATF5.5G28H",  "nama": "Indosat Freedom 5.5GB 28 Hari",  "harga": 35545},
        ],
        "Axis": [
            # Aigo
            {"kode": "DAXSA1.5G3H",   "nama": "Axis Aigo 1.5GB 3 Hari",  "harga": 11803},
            {"kode": "DAXSA2.5G2H",   "nama": "Axis Aigo 2.5GB 2 Hari",  "harga": 11020},
            {"kode": "DAXSA2G3H",     "nama": "Axis Aigo 2GB 3 Hari",    "harga": 10630},
            {"kode": "DAXSA4G3H",     "nama": "Axis Aigo 4GB 3 Hari",    "harga": 13151},
            {"kode": "DAXSA2G5H",     "nama": "Axis Aigo 2GB 5 Hari",    "harga": 13780},
        ],
        "Smartfren": [
            # Unlimited
            {"kode": "DSMTU1G1H",     "nama": "Smartfren Unlimited 1GB 1 Hari",  "harga": 9969},
            {"kode": "DSMTU3G3H",     "nama": "Smartfren Unlimited 3GB 3 Hari",  "harga": 15400},
            {"kode": "DSMTU1G3H",     "nama": "Smartfren Unlimited 1GB 3 Hari",  "harga": 15695},
            {"kode": "DSMTU5G3H",     "nama": "Smartfren Unlimited 5GB 3 Hari",  "harga": 20160},
            {"kode": "DSMTU1G7H",     "nama": "Smartfren Unlimited 1GB 7 Hari",  "harga": 23210},
            {"kode": "DSMTU2G7H",     "nama": "Smartfren Unlimited 2GB 7 Hari",  "harga": 24400},
        ],
        "Tri": [
            # Happy
            {"kode": "DTRIH1.5G1H",   "nama": "Tri Happy 1.5GB 1 Hari",  "harga": 6195},
            {"kode": "DTRIH3G3H",     "nama": "Tri Happy 3GB 3 Hari",    "harga": 12662},
        ],
        "XL": [
            # Mini
            {"kode": "DXLM1G7H",      "nama": "XL Mini 1GB 7 Hari",    "harga": 10360},
            {"kode": "DXLM1.5G7H",    "nama": "XL Mini 1.5GB 7 Hari",  "harga": 11210},
            {"kode": "DXLM2.5G7H",    "nama": "XL Mini 2.5GB 7 Hari",  "harga": 16010},
            {"kode": "DXLM4G7H",      "nama": "XL Mini 4GB 7 Hari",    "harga": 19910},
            {"kode": "DXLM6G7H",      "nama": "XL Mini 6GB 7 Hari",    "harga": 25775},
        ],
    },

    "game": {},   # Diisi nanti
}

# ─────────────────────────────────────────────
# MAPPING CEPAT KODE → PRODUK
# ─────────────────────────────────────────────
SKU_MAP = {}
for _kategori, _operators in PRODUCTS.items():
    for _operator, _items in _operators.items():
        for _item in _items:
            SKU_MAP[_item["kode"]] = {**_item, "operator": _operator, "kategori": _kategori}

# ─────────────────────────────────────────────
# DAFTAR HARGA OFFLINE (Modal + Rp2.000)
# ─────────────────────────────────────────────
HARGA_OFFLINE = {
    # Pulsa Telkomsel
    "TSL5": 7200, "TSL10": 12135, "TSL15": 16900,
    "TSL20": 21960, "TSL25": 26685, "TSL50": 52025, "TSL100": 99020,
    # Pulsa Indosat
    "ISAT5": 8359, "ISAT10": 13570, "ISAT20": 22510,
    "ISAT50": 51818, "ISAT100": 101030,
    # Pulsa XL
    "XL5": 7933, "XL10": 12855, "XL15": 16994,
    "XL25": 26975, "XL50": 51935, "XL100": 101820,
    # Pulsa Tri
    "TRI5": 7110, "TRI10": 13655, "TRI20": 21620, "TRI50": 51020,
    # Pulsa Axis
    "AXS5": 7848, "AXS10": 12895, "AXS15": 16994,
    "AXS50": 51935, "AXS100": 101820,
    # Pulsa Smartfren
    "SMT2": 4009, "SMT3": 5006, "SMT4": 6003,
    "SMT5": 7205, "SMT10": 12040, "SMT15": 16980, "SMT100": 51855,
    # Data Telkomsel Umum
    "DTSL1G3H": 10555, "DTSL2G3H": 12855, "DTSL1G7H": 11655, "DTSL1G15H": 12755,
    # Data Telkomsel Flash
    "DTSLF1G30H": 13385, "DTSLF2G30H": 25025, "DTSLF3G30H": 36190,
    # Data Telkomsel Combo Sakti
    "DTSLCS1.5G30H": 23510, "DTSLCS2.5G30H": 23775,
    "DTSLCS3G30H": 25525, "DTSLCS4G30H": 37125,
    # Data Indosat Umum
    "DISAT1G7H": 7700, "DISAT1G3H": 7695, "DISAT1G14H": 7805,
    # Data Indosat Yellow
    "DISATY1G1H": 7855, "DISATY1G2H": 7915, "DISATY1G3H": 8005,
    # Data Indosat Freedom
    "DISATF1.5G1H": 8865, "DISATF5G1H": 8755, "DISATF1G2H": 10910,
    "DISATF1.5G3H": 13770, "DISATF2.5G3H": 9000, "DISATF3G3H": 13705,
    "DISATF1.5G5H": 10945, "DISATF2G5H": 14932, "DISATF2.5G5H": 14920,
    "DISATF10G5H": 14740, "DISATF1.5G28H": 12030, "DISATF2G15H": 13430,
    "DISATF7G7H": 24435, "DISATF3G28H": 27510, "DISATF5.5G28H": 36545,
    # Data Axis Aigo
    "DAXSA1.5G3H": 12803, "DAXSA2.5G2H": 12020, "DAXSA2G3H": 11630,
    "DAXSA4G3H": 14151, "DAXSA2G5H": 14780,
    # Data Smartfren Unlimited
    "DSMTU1G1H": 10969, "DSMTU3G3H": 16400, "DSMTU1G3H": 16695,
    "DSMTU5G3H": 21160, "DSMTU1G7H": 24210, "DSMTU2G7H": 25400,
    # Data Tri Happy
    "DTRIH1.5G1H": 7195, "DTRIH3G3H": 13662,
    # Data XL Mini
    "DXLM1G7H": 11360, "DXLM1.5G7H": 12210, "DXLM2.5G7H": 17010,
    "DXLM4G7H": 20910, "DXLM6G7H": 26775,
}
