"""
database.py — Supabase integration for saving and retrieving Kundli data.
"""

import os
import json
from supabase import create_client, Client

# ── Supabase client ───────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── SQL to create the table (run once in Supabase SQL editor) ─────────────────
#
# CREATE TABLE kundlis (
#   id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   name        TEXT NOT NULL,
#   dob         TEXT NOT NULL,
#   tob         TEXT NOT NULL,
#   lat         FLOAT,
#   lon         FLOAT,
#   planets     JSONB,
#   doshas      JSONB,
#   notes       TEXT,
#   created_at  TIMESTAMPTZ DEFAULT NOW()
# );
#
# ─────────────────────────────────────────────────────────────────────────────

def save_kundli(data: dict) -> str | None:
    """Insert a kundli record. Returns the new record ID or None on failure."""
    try:
        client = get_client()
        payload = {
            "name":    data.get("name"),
            "dob":     data.get("dob"),
            "tob":     data.get("tob"),
            "lat":     data.get("lat"),
            "lon":     data.get("lon"),
            "planets": data.get("planets"),
            "doshas":  data.get("doshas"),
            "notes":   data.get("notes", ""),
        }
        response = client.table("kundlis").insert(payload).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"[DB] save_kundli error: {e}")
        return None


def get_all_kundlis() -> list[dict]:
    """Fetch all kundli summaries (id, name, dob, created_at)."""
    try:
        client = get_client()
        response = (
            client.table("kundlis")
            .select("id, name, dob, tob, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB] get_all_kundlis error: {e}")
        return []


def get_kundli_by_id(kundli_id: str) -> dict | None:
    """Fetch a single full kundli record by UUID."""
    try:
        client = get_client()
        response = (
            client.table("kundlis")
            .select("*")
            .eq("id", kundli_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[DB] get_kundli_by_id error: {e}")
        return None


def search_kundlis(query: str = "", planet: str = "", rashi: str = "", nakshatra: str = "") -> list[dict]:
    """
    Search kundlis by name (text search) or filter by planet/rashi/nakshatra inside the planets JSONB.
    Returns lightweight summary list.
    """
    try:
        client = get_client()
        q = client.table("kundlis").select("id, name, dob, planets, doshas")

        if query:
            q = q.ilike("name", f"%{query}%")

        response = q.execute()
        results = response.data or []

        # Filter in Python for planet/rashi/nakshatra combinations
        if planet or rashi or nakshatra:
            filtered = []
            for row in results:
                p_data = row.get("planets") or {}
                match = False
                for pname, pinfo in p_data.items():
                    p_ok  = (not planet    or pname.lower() == planet.lower())
                    r_ok  = (not rashi     or pinfo.get("sign", "").lower() == rashi.lower())
                    n_ok  = (not nakshatra or pinfo.get("nakshatra", "").lower() == nakshatra.lower())
                    if p_ok and r_ok and n_ok:
                        match = True
                        break
                if match:
                    filtered.append(row)
            results = filtered

        return results
    except Exception as e:
        print(f"[DB] search_kundlis error: {e}")
        return []
