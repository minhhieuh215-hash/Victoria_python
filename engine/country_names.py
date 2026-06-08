"""
Load display names for country tags (Victoria 3 style English names).
Priority: NAME_OVERRIDES > # comment in definitions > capital > tag
"""
import json
import os
import re

# Vic3 / user list — always wins over auto-parsed names
NAME_OVERRIDES = {
    # Great powers
    "GBR": "Great Britain",
    "FRA": "France",
    "RUS": "Russia",
    "GER": "Germany",
    "AUS": "Austria",
    "PRU": "Prussia",
    "TUR": "Ottoman Empire",
    "USA": "United States",
    # Europe
    "NET": "Netherlands",
    "SPA": "Spain",
    "SWE": "Sweden",
    "CIR": "Circassia",
    "CHC": "Caucasian Imamate",
    "MON": "Montenegro",
    "SER": "Serbia",
    "GRE": "Greece",
    "CRO": "Croatia-Slavonia",
    "TRA": "Transylvania",
    "HUN": "Hungary",
    "ION": "Ionian Islands",
    "LUX": "Luxembourg",
    "BEL": "Belgium",
    "POR": "Portugal",
    "NOR": "Norway",
    "DEN": "Denmark",
    "FIN": "Grand Duchy of Finland",
    "SWI": "Switzerland",
    "ROM": "Romania",
    "WAL": "Wallachia",
    "MOL": "Moldavia",
    "KRA": "Krakow",
    "EST": "Estonia",
    "LIT": "Lithuania",
    "UBD": "United Baltic States",
    "SCA": "Scandinavia",
    "ITA": "Italy",
    "SAR": "Sardinia-Piedmont",
    "SIC": "Two Sicilies",
    "PAP": "Papal States",
    "TUS": "Tuscany",
    "BAV": "Bavaria",
    "HAN": "Hannover",
    "SAX": "Saxony",
    "WUR": "Württemberg",
    "BAD": "Baden",
    "HES": "Hesse",
    "NAS": "Nassau",
    "OLB": "Oldenburg",
    "MEC": "Mecklenburg",
    "POL": "Poland",
    "CZE": "Bohemia",
    "CRA": "Kraków",
    "LAT": "Latvia",
    "BYE": "Belarus",
    "UKR": "Ukraine",
    "BUL": "Bulgaria",
    "ALB": "Albania",
    "MAC": "Macedonia",
    "BOS": "Bosnia",
    "MNE": "Montenegro",
    "KOS": "Kosovo",
    "ICE": "Iceland",
    "IRE": "Ireland",
    "SCO": "Scotland",
    "WLS": "Wales",
    # Asia
    "JAP": "Tokugawa Shogunate",
    "RYU": "Ryukyu",
    "CHI": "Qing China",
    "KOR": "Korea",
    "PER": "Persia",
    "AFG": "Afghanistan",
    "BIC": "East India Company",
    "SIN": "Sindh",
    "CEY": "Ceylon",
    "KAL": "Kalat",
    "PAN": "Khalsa Raj",
    "MUG": "Mughal Empire",
    "DEI": "Dutch East Indies",
    "PHI": "Philippines",
    "DAI": "Dai Nam",
    "BUR": "Burma",
    "SIA": "Siam",
    "NEP": "Nepal",
    "BUK": "Bukhara",
    "KHI": "Khiva",
    "NEJ": "Nejd",
    "OMA": "Oman",
    "SIK": "Sikh Empire",
    "YEM": "Yemen",
    "HAD": "Hadhramaut",
    "KUW": "Kuwait",
    "BAH": "Bahrain",
    "QAT": "Qatar",
    "UAE": "Trucial States",
    "MUS": "Muscat",
    "KHO": "Khorasan",
    "AZE": "Azerbaijan",
    "ARM": "Armenia",
    "GEO": "Georgia",
    "KAZ": "Kazakhstan",
    "KYR": "Kyrgyzstan",
    "TAJ": "Tajikistan",
    "TUK": "Turkmenistan",
    "UZB": "Uzbekistan",
    "MOG": "Mogadishu",
    "TIB": "Tibet",
    "MOO": "Mughulistan",
    "CAS": "Kashgar",
    "XIN": "Xinjiang",
    "VIE": "Vietnam",
    "LAO": "Laos",
    "CAM": "Cambodia",
    "MAL": "Malaya",
    "SRI": "Sri Lanka",
    "BAN": "Bangladesh",
    "MYA": "Myanmar",
    "IND": "British India",
    "INS": "Indonesia",
    "BOR": "Brunei",
    "PNG": "Papua New Guinea",
    # Central Asia zhuz
    "KZH": "Kishi Zhuz",
    "OZH": "Orta Zhuz",
    "UZH": "Uly Zhuz",
    "KKL": "Khanate of Kokand",
    # Middle East
    "SYR": "Syria",
    "LEB": "Lebanon",
    "ISR": "Palestine",
    "JOR": "Jordan",
    "IRQ": "Iraq",
    "IRN": "Iran",
    "SAU": "Saudi Arabia",
    "EGY": "Egypt",

    # Americas
    "CLM": "Colombia",
    "VNZ": "Venezuela",
    "TEX": "Texas",
    "ARG": "Argentina",
    "CHL": "Chile",
    "PAR": "Parma",
    "BRZ": "Brazil",
    "RIO": "Republic of Rio Grande",
    "PNI": "Piratini",
    "PRG": "Paraguay",
    "PRA": "Grão-Pará",
    "URU": "Uruguay",
    "BOL": "Bolivia",
    "ECU": "Ecuador",
    "MEX": "Mexico",
    "HAI": "Haiti",
    "UCA": "Central America",
    "CUB": "Cuba",
    "HBC": "Hudson's Bay Company",
    "NPU": "North Peru",
    "SPU": "South Peru",
    "GUA": "Guatemala",
    "HON": "Honduras",
    "ELS": "El Salvador",
    "CRI": "Costa Rica",
    "DOM": "Dominican Republic",
    "JAM": "Jamaica",
    "NVS": "Nova Scotia",
    "NBS": "New Brunswick",
    "PCO": "Puerto Rico",
    "MSA": "Miskita",
    "MKT": "Miskitia",
    "IQU": "Iquicha",
    "ITR": "Indian Territory",
    # Formable in Americas
    "ATL": "Antillean Confederation",
    "CLI": "Carolina",
    "FSA": "Free State of America",
    "CAN": "Canada",
    "PND": "Federation of the Andes",
    "GCO": "Gran Colombia",
    "PLT": "Rio de la Plata",
    "PEU": "Peru",
    "TWU": "Tawantinsuyu",
    "WID": "West Indies",
    # Decentralized — Americas
    "ABS": "Absaroka",
    "APC": "Apache",
    "ARP": "Arapaho",
    "ATB": "Athabaska",
    "CAY": "Cayuga",
    "CCM": "Chinook",
    "CHK": "Cherokee",
    "CHW": "Cheyenne",
    "COM": "Comanche",
    "CSC": "Coast Salish",
    "CTF": "Iron Confederacy",
    "DAK": "Dakota",
    "DFT": "Driftwood",
    "DKT": "Dakota Territory",
    "GNI": "Guarani",
    "LKT": "Lakota",
    "MNC": "Mandan",
    "MRN": "Maroon",
    "NGA": "Niitsitapi",
    "NTO": "Natoo",
    "NTU": "Natuu",
    "NVJ": "Navajo",
    "OAX": "Oaxaca",
    "ORN": "Oregon Natives",
    "PAT": "Patagonia",
    "PWN": "Pawnee",
    "SKH": "Shoshone",
    "SLS": "Séliš",
    "SSU": "Sioux",
    "TRK": "Trekkers",
    "UTE": "Ute",
    "UYA": "Uyaya",
    "WTI": "Wind River",
    "WYU": "Wyoming Tribes",
    "YKA": "Yokuts",
    "SML": "Yat’siminoli",
    "SEL": "Selk'nam",
    "MAP": "Mapuche",
    # Release countries in Americas
    "NIC": "Nicaragua",

    # Africa
    "ETH": "Ethiopia",
    "MOR": "Morocco",
    "ZUL": "Zulu",
    "ASH": "Ashanti",
    "DAH": "Dahomey",
    "LIB": "Liberia",
    "SAF": "Cape Colony",
    "ALG": "Algeria",
    "TUN": "Tunisia",
    "LYB": "Libya",
    "MAD": "Madagascar",
    "SOM": "Somalia",
    "SUD": "Sudan",
    "ERI": "Eritrea",
    "DJI": "Djibouti",
    # Pacific
    "HAW": "Hawaii",
    "AST": "Australia",
    "NZL": "New Zealand",
    "MCH": "Manchuria",
    "FIJ": "Fiji",
    "SAM": "Samoa",
    "TON": "Tonga",
    # Micro-states / Other
    "VAT": "Vatican",
    "AND": "Andorra",
    "SMR": "San Marino",
    "LIE": "Liechtenstein",
    "MLT": "Malta",
    "CYP": "Cyprus",
    
    # Decentralized — Africa
    "ADG": "Adagh",
    "AHG": "Ahaggar",
    "AIR": "Aïr",
    "AYI": "Anyui",
    "BJA": "Beja",
    "BLA": "Balanta",
    "BLE": "Baoulé",
    "BLF": "Bafuliru",
    "BMB": "Bambara",
    "BMM": "Bamum",
    "BND": "Banda",
    "BNG": "Bangala",
    "PNK": "Pannakwati",
    "BOB": "Bobo",
    "BSS": "Barotse",
    "BST": "Basuto",
    "BTG": "Batonga",
    "DLA": "Dala",
    "DNK": "Dinka",
    "EQU": "Equateur",
    "EWE": "Ewe",
    "FNG": "Fang",
    "GAO": "Gao",
    "GGO": "Gogo",
    "GML": "Gambia",
    "HHE": "Hehe",
    "HLA": "Hlubi",
    "HMB": "Hemba",
    "HRO": "Herero",
    "IBL": "Ibibio",
    "IBO": "Igbo",
    "IRC": "Iron Cross",
    "JLF": "Jolof",
    "KBA": "Kuba",
    "KBD": "Kabinda",
    "KBU": "Kabubu",
    "KKI": "Kuki",
    "KKY": "Kakwa",
    "KNG": "Kongo",
    "KNK": "Kankan",
    "KRU": "Kru",
    "KSN": "Kasanje",
    "KSS": "Kasai",
    "KZM": "Kazembe",
    "LBA": "Luba",
    "LGA": "Loango",
    "LMW": "Lumwe",
    "LND": "Lunda",
    "LNG": "Lango",
    "LUO": "Luo",
    "LZO": "Lozi",
    "MCR": "Macri",
    "MDK": "Mandinka",
    "MGH": "Mangbetu",
    "MKU": "Makua",
    "MNB": "Manyika",
    "MOS": "Mossi",
    "MRV": "Maravi",
    "MSH": "Mashona",
    "MSI": "Masai",
    "MSK": "Miskito",
    "MTB": "Matabeleland",
    "MUI": "Mwui",
    "NAM": "Nama",
    "NBA": "Nbaka",
    "NNG": "Nkongo",
    "NUE": "Nuer",
    "NVL": "Neville",
    "NYM": "Nyamwezi",
    "NIM": "Nimíipuu",
    "OUA": "Oulata",
    "OVM": "Ovambo",
    "SAH": "Sahrawi",
    "SKM": "Sukuma",
    "SLK": "Selk’nam",
    "SLW": "Sulawesi",
    "SNA": "Sennar",
    "SNG": "Songwe",
    "SRA": "Sera",
    "SRR": "Serer",
    "TBI": "Tibesti",
    "THL": "Tehuelche",
    "TIP": "Tippu Tip",
    "TIR": "Tigray",
    "TIV": "Tiv",
    "TKE": "Teke",
    "TPI": "Toposa",
    "TPS": "Tupuri",
    "TRM": "Toromawa",
    "TRZ": "Tuareg",
    "TSW": "Tswana",
    "TUA": "Tuat",
    "ULR": "Uele River",
    "WBL": "Wabel",
    "XHO": "Xhosa",
    "ZND": "Zande",
    # Decentralized — Pacific & Asia
    "AIN": "Ainu",
    "FJI": "Fiji Islands",
    "MCO": "Micronesia",
    "NRU": "Nauru",
    "PPU": "Papua",
    "TNG": "Tonga Islands",
    "VNT": "Vanuatu",
}

COUNTRY_NAMES = dict(NAME_OVERRIDES)

_SKIP_COMMENT_PREFIXES = (
    "important note",
    "only use capital",
)


def _state_key_to_name(state_key: str) -> str:
    if not state_key:
        return ""
    name = state_key.replace("STATE_", "").replace("_", " ").strip()
    replacements = {
        "Irakajemi": "Persia",
        "Home Counties": "England",
        "Eastern Himalayas": "Sikh Empire",
        "Uzbekia": "Bukhara",
        "Rio De Janeiro": "Brazil",
        "Cundinamarca": "New Granada",
        "Montenegro": "Montenegro",
        "West Galicia": "Krakow",
    }
    titled = name.title()
    return replacements.get(titled, titled)


def _clean_file_comment(comment: str) -> str:
    if not comment:
        return ""
    c = comment.strip()
    if "/" in c:
        c = c.split("/")[0].strip()
    return c


def _parse_definitions_folder(folder: str) -> dict:
    """Parse country_definitions/*.txt -> {TAG: display_name}."""
    result = {}
    comments = {}
    if not os.path.isdir(folder):
        return result

    tag_re = re.compile(r"^([A-Z0-9]{2,4})\s*=\s*\{")
    capital_re = re.compile(r"capital\s*=\s*(STATE_[A-Z0-9_]+)")

    for fn in os.listdir(folder):
        if not fn.endswith(".txt"):
            continue
        path = os.path.join(folder, fn)
        current = None
        capital = None
        named_from_capital = False
        depth = 0
        pending_comment = None

        with open(path, "r", encoding="utf-8-sig") as f:
            for raw in f:
                stripped = raw.strip()
                if stripped.startswith("#") and depth == 0 and current is None:
                    body = stripped[1:].strip()
                    low = body.lower()
                    if body and not any(low.startswith(p) for p in _SKIP_COMMENT_PREFIXES):
                        pending_comment = _clean_file_comment(body)
                    continue

                line = raw.split("#")[0].strip()
                if not line:
                    continue

                m = tag_re.match(line)
                if m and depth == 0:
                    if current:
                        result[current] = _resolve_tag_name(
                            current, capital, named_from_capital, comments.get(current)
                        )
                    current = m.group(1)
                    capital = None
                    named_from_capital = False
                    if pending_comment:
                        comments[current] = pending_comment
                        pending_comment = None

                if current is None:
                    continue

                if "is_named_from_capital" in line:
                    named_from_capital = True
                cm = capital_re.search(line)
                if cm:
                    capital = cm.group(1)

                depth += line.count("{") - line.count("}")
                if depth <= 0 and current:
                    result[current] = _resolve_tag_name(
                        current, capital, named_from_capital, comments.get(current)
                    )
                    current = None
                    capital = None
                    named_from_capital = False
                    depth = 0

        if current:
            result[current] = _resolve_tag_name(
                current, capital, named_from_capital, comments.get(current)
            )

    return result


def _resolve_tag_name(tag, capital, named_from_capital, file_comment=None):
    if tag in NAME_OVERRIDES:
        return NAME_OVERRIDES[tag]
    if file_comment:
        return file_comment
    if named_from_capital and capital:
        return _state_key_to_name(capital)
    if capital:
        return _state_key_to_name(capital)
    return tag


def _load_json_names(base_dir: str) -> dict:
    path = os.path.join(base_dir, "data", "country_display_names.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {k.upper(): v for k, v in data.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def load_country_display_names(base_dir=None) -> dict:
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(base_dir, "data", "common", "country_definitions")
    parsed = _parse_definitions_folder(folder)
    names = dict(parsed)
    names.update(_load_json_names(base_dir))
    names.update(NAME_OVERRIDES)
    return names


def init_country_names(base_dir=None) -> dict:
    global COUNTRY_NAMES
    COUNTRY_NAMES = load_country_display_names(base_dir)
    return COUNTRY_NAMES


def get_country_display_name(tag, default=None) -> str:
    if not tag:
        return default or "?"
    return COUNTRY_NAMES.get(tag) or (default if default is not None else tag)
