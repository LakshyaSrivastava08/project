"""
kundli.py — Vedic astrology calculation module using pyswisseph (swisseph).
All functions are pure and modular — easy to extend.
"""

import swisseph as swe
from datetime import datetime

# ── Lookup tables ────────────────────────────────────────────────────────────

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_SIGNS_HI = [
    "मेष", "वृषभ", "मिथुन", "कर्क",
    "सिंह", "कन्या", "तुला", "वृश्चिक",
    "धनु", "मकर", "कुम्भ", "मीन"
]

NAKSHATRAS = [
    ("Ashwini",      "Ketu"),   ("Bharani",    "Venus"),  ("Krittika",   "Sun"),
    ("Rohini",       "Moon"),   ("Mrigashira", "Mars"),   ("Ardra",      "Rahu"),
    ("Punarvasu",    "Jupiter"),("Pushya",     "Saturn"), ("Ashlesha",   "Mercury"),
    ("Magha",        "Ketu"),   ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta",        "Moon"),   ("Chitra",     "Mars"),   ("Swati",      "Rahu"),
    ("Vishakha",     "Jupiter"),("Anuradha",   "Saturn"), ("Jyeshtha",   "Mercury"),
    ("Mula",         "Ketu"),   ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana",     "Moon"),   ("Dhanishtha", "Mars"),   ("Shatabhisha","Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]

PLANET_IDS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,   # North Node
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_julian_day(dob: str, tob: str) -> float:
    """Convert date/time strings to Julian Day (UT)."""
    dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day,
                    dt.hour + dt.minute / 60.0)
    return jd


def longitude_to_sign(lon: float) -> tuple[str, float]:
    """Return (zodiac_sign, degree_within_sign) for an ecliptic longitude."""
    sign_index = int(lon / 30) % 12
    degree = lon % 30
    return ZODIAC_SIGNS[sign_index], round(degree, 4)


def longitude_to_nakshatra(lon: float) -> tuple[str, str]:
    """Return (nakshatra_name, lord) for an ecliptic longitude."""
    nak_index = int(lon / (360 / 27)) % 27
    name, lord = NAKSHATRAS[nak_index]
    return name, lord


def get_ascendant(jd: float, lat: float, lon: float) -> float:
    """Return the Ascendant (Lagna) longitude."""
    houses, ascmc = swe.houses(jd, lat, lon, b'P')  # Placidus
    return ascmc[0]  # Ascendant longitude


def calc_house(planet_lon: float, asc_lon: float) -> int:
    """Simple whole-sign house calculation."""
    diff = (planet_lon - asc_lon) % 360
    return int(diff / 30) + 1

# ── Main calculation ─────────────────────────────────────────────────────────

def calculate_kundli(dob: str, tob: str, lat: float, lon: float) -> dict:
    """
    Calculate Vedic planetary positions.
    Returns a dict of planet data.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Lahiri ayanamsa (Vedic standard)

    jd = get_julian_day(dob, tob)
    asc_lon = get_ascendant(jd, lat, lon)
    asc_sign, asc_deg = longitude_to_sign(asc_lon)

    result = {
        "Ascendant": {
            "longitude": round(asc_lon, 4),
            "sign":      asc_sign,
            "degree":    asc_deg,
            "house":     1,
            "nakshatra": longitude_to_nakshatra(asc_lon)[0],
            "nak_lord":  longitude_to_nakshatra(asc_lon)[1],
        }
    }

    for planet_name, planet_id in PLANET_IDS.items():
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        pos, _ = swe.calc_ut(jd, planet_id, flags)
        p_lon = pos[0]

        # Ketu is exactly opposite Rahu
        if planet_name == "Rahu":
            ketu_lon = (p_lon + 180) % 360

        sign, deg = longitude_to_sign(p_lon)
        nak, nak_lord = longitude_to_nakshatra(p_lon)
        house = calc_house(p_lon, asc_lon)

        result[planet_name] = {
            "longitude": round(p_lon, 4),
            "sign":      sign,
            "degree":    round(deg, 2),
            "house":     house,
            "nakshatra": nak,
            "nak_lord":  nak_lord,
        }

    # Add Ketu
    ketu_sign, ketu_deg = longitude_to_sign(ketu_lon)
    ketu_nak, ketu_nak_lord = longitude_to_nakshatra(ketu_lon)
    result["Ketu"] = {
        "longitude": round(ketu_lon, 4),
        "sign":      ketu_sign,
        "degree":    round(ketu_deg, 2),
        "house":     calc_house(ketu_lon, asc_lon),
        "nakshatra": ketu_nak,
        "nak_lord":  ketu_nak_lord,
    }

    return result

# ── Dosha detection engine ───────────────────────────────────────────────────

def check_kaal_sarp_dosh(planets: dict) -> dict | None:
    """
    Kaal Sarp Dosh: all planets hemmed between Rahu and Ketu axis.
    Returns dosha dict if present, else None.
    """
    rahu_lon = planets.get("Rahu", {}).get("longitude")
    ketu_lon = planets.get("Ketu", {}).get("longitude")
    if rahu_lon is None or ketu_lon is None:
        return None

    check_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    rahu_lon = rahu_lon % 360
    ketu_lon = ketu_lon % 360

    def in_rahu_ketu_arc(lon):
        """Check if longitude is in the arc from Rahu to Ketu (going forward)."""
        lon = lon % 360
        if rahu_lon < ketu_lon:
            return rahu_lon <= lon <= ketu_lon
        else:
            return lon >= rahu_lon or lon <= ketu_lon

    all_in = all(in_rahu_ketu_arc(planets[p]["longitude"]) for p in check_planets if p in planets)

    if all_in:
        return {
            "name": "Kaal Sarp Dosh",
            "severity": "high",
            "description": (
                "All seven planets are hemmed between the Rahu–Ketu axis. "
                "This is known as Kaal Sarp Dosh and may cause delays, obstacles, "
                "and karmic challenges in life. Remedies include Kaal Sarp Dosh Puja "
                "at Trimbakeshwar or Ujjain."
            ),
            "disclaimer": (
                "⚠️ Disclaimer: This is an algorithmic detection. Kaal Sarp Dosh "
                "should be confirmed by a qualified Vedic astrologer, as exceptions "
                "and partial formations exist."
            )
        }
    return None


def get_doshas(planets: dict) -> list[dict]:
    """
    Run all dosha checks. Returns a list of detected doshas.
    Easy to extend — just add more check_* functions below.
    """
    doshas = []

    ksd = check_kaal_sarp_dosh(planets)
    if ksd:
        doshas.append(ksd)

    # ── Add more rules below ──────────────────────────────────────
    # Example:
    # mangal = check_mangal_dosh(planets)
    # if mangal: doshas.append(mangal)
    # ─────────────────────────────────────────────────────────────

    return doshas
