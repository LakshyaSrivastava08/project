"""
kundli.py — Vedic astrology calculation module using pyswisseph.
Includes geocoding via Nominatim (OpenStreetMap).
"""

import swisseph as swe
from datetime import datetime
from functools import lru_cache
import requests

# ── Lookup tables ────────────────────────────────────────────────────────────

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    ("Ashwini",          "Ketu"),    ("Bharani",          "Venus"),
    ("Krittika",         "Sun"),     ("Rohini",           "Moon"),
    ("Mrigashira",       "Mars"),    ("Ardra",            "Rahu"),
    ("Punarvasu",        "Jupiter"), ("Pushya",           "Saturn"),
    ("Ashlesha",         "Mercury"), ("Magha",            "Ketu"),
    ("Purva Phalguni",   "Venus"),   ("Uttara Phalguni",  "Sun"),
    ("Hasta",            "Moon"),    ("Chitra",           "Mars"),
    ("Swati",            "Rahu"),    ("Vishakha",         "Jupiter"),
    ("Anuradha",         "Saturn"),  ("Jyeshtha",         "Mercury"),
    ("Mula",             "Ketu"),    ("Purva Ashadha",    "Venus"),
    ("Uttara Ashadha",   "Sun"),     ("Shravana",         "Moon"),
    ("Dhanishtha",       "Mars"),    ("Shatabhisha",      "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada","Saturn"),
    ("Revati",           "Mercury"),
]

PLANET_IDS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,
}

PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
    "Rahu": "Ra", "Ketu": "Ke", "Ascendant": "As"
}

# ── Geocoding ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=256)
def get_coordinates(place_name: str):
    """
    Convert place name to (latitude, longitude) via Nominatim.
    Cached with lru_cache to avoid repeat API calls.
    Returns None on failure.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "KundliApp/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[Geocoding] Error: {e}")
    return None


# ── Core helpers ──────────────────────────────────────────────────────────────

def get_julian_day(dob: str, tob: str) -> float:
    dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def longitude_to_sign(lon: float):
    idx = int(lon / 30) % 12
    return ZODIAC_SIGNS[idx], round(lon % 30, 4)


def longitude_to_nakshatra(lon: float):
    idx = int(lon / (360 / 27)) % 27
    return NAKSHATRAS[idx]  # (name, lord)


def get_nakshatra_pada(lon: float) -> int:
    """Each nakshatra = 13.333°, each pada = 3.333°"""
    nak_width = 360 / 27
    pada_width = nak_width / 4
    pos_in_nak = lon % nak_width
    return min(int(pos_in_nak / pada_width) + 1, 4)


def get_ascendant(jd: float, lat: float, lon: float) -> float:
    _, ascmc = swe.houses(jd, lat, lon, b'P')
    return ascmc[0]


def calc_house(planet_lon: float, asc_lon: float) -> int:
    return int(((planet_lon - asc_lon) % 360) / 30) + 1


# ── Main calculation ──────────────────────────────────────────────────────────

def calculate_kundli(dob: str, tob: str, lat: float, lon: float) -> dict:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = get_julian_day(dob, tob)
    asc_lon = get_ascendant(jd, lat, lon)
    asc_sign, asc_deg = longitude_to_sign(asc_lon)
    asc_nak, asc_nak_lord = longitude_to_nakshatra(asc_lon)

    result = {
        "Ascendant": {
            "longitude": round(asc_lon, 4),
            "sign":      asc_sign,
            "degree":    round(asc_deg, 2),
            "house":     1,
            "nakshatra": asc_nak,
            "nak_lord":  asc_nak_lord,
            "pada":      get_nakshatra_pada(asc_lon),
            "short":     "As",
        }
    }

    ketu_lon = None
    for pname, pid in PLANET_IDS.items():
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        pos, _ = swe.calc_ut(jd, pid, flags)
        p_lon = pos[0]

        if pname == "Rahu":
            ketu_lon = (p_lon + 180) % 360

        sign, deg = longitude_to_sign(p_lon)
        nak, nak_lord = longitude_to_nakshatra(p_lon)

        result[pname] = {
            "longitude": round(p_lon, 4),
            "sign":      sign,
            "degree":    round(deg, 2),
            "house":     calc_house(p_lon, asc_lon),
            "nakshatra": nak,
            "nak_lord":  nak_lord,
            "pada":      get_nakshatra_pada(p_lon),
            "short":     PLANET_SHORT[pname],
        }

    if ketu_lon is not None:
        ks, kd = longitude_to_sign(ketu_lon)
        kn, knl = longitude_to_nakshatra(ketu_lon)
        result["Ketu"] = {
            "longitude": round(ketu_lon, 4),
            "sign":      ks,
            "degree":    round(kd, 2),
            "house":     calc_house(ketu_lon, asc_lon),
            "nakshatra": kn,
            "nak_lord":  knl,
            "pada":      get_nakshatra_pada(ketu_lon),
            "short":     "Ke",
        }

    return result


# ── Dosha engine ──────────────────────────────────────────────────────────────

def check_kaal_sarp_dosh(planets: dict):
    rahu_lon = planets.get("Rahu", {}).get("longitude")
    ketu_lon = planets.get("Ketu", {}).get("longitude")
    if not rahu_lon or not ketu_lon:
        return None

    check_p = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    r, k = rahu_lon % 360, ketu_lon % 360

    def in_arc(lon):
        lon = lon % 360
        return (r <= lon <= k) if r < k else (lon >= r or lon <= k)

    if all(in_arc(planets[p]["longitude"]) for p in check_p if p in planets):
        return {
            "name": "Kaal Sarp Dosh",
            "severity": "high",
            "description": "All seven planets are hemmed between the Rahu–Ketu axis, indicating Kaal Sarp Dosh.",
            "disclaimer": "⚠️ Confirm with a qualified Vedic astrologer."
        }
    return None


def get_doshas(planets: dict) -> list:
    doshas = []
    d = check_kaal_sarp_dosh(planets)
    if d:
        doshas.append(d)
    # Add more check_* functions here
    return doshas


# ── Yoga detection ────────────────────────────────────────────────────────────

def get_yogas(planets: dict) -> list:
    yogas = [
        {"name": "Neecha Bhanga Raja Yoga",  "active": False},
        {"name": "Dharma Karmadhipati Yoga", "active": False},
        {"name": "Parivartana Yoga",         "active": False},
        {"name": "Adhi Yoga",                "active": False},
        {"name": "Vasumathi Yoga",           "active": False},
        {"name": "Vesi Yoga",                "active": False},
        {"name": "Budhaditya Yoga",          "active": False},
    ]
    # Budhaditya: Sun + Mercury in same sign
    if planets.get("Sun", {}).get("sign") == planets.get("Mercury", {}).get("sign"):
        next(y for y in yogas if y["name"] == "Budhaditya Yoga")["active"] = True

    return yogas