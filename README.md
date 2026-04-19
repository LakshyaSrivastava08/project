# ☽ Kundli App — Full Setup Guide

A Vedic astrology web app built with Flask + pyswisseph + Supabase.

---

## 📁 Folder Structure

```
kundli_app/
├── app.py              ← Flask routes
├── kundli.py           ← Planetary calculations (pyswisseph)
├── database.py         ← Supabase integration
├── requirements.txt
├── .env.example        ← Copy to .env and fill in your keys
└── templates/
    ├── base.html       ← Shared navbar, dark theme, search
    ├── index.html      ← Birth details form
    ├── result.html     ← Kundli result + save button
    ├── dashboard.html  ← All saved kundlis (tag cloud + cards)
    └── view_kundli.html← Individual kundli from database
```

---

## ⚙️ Step 1 — Python Environment

```bash
cd kundli_app
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

---

## 📦 Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note on pyswisseph**: on Windows you may need Visual C++ Build Tools.
> Alternatively install the pre-built wheel:
> ```
> pip install pyswisseph --only-binary=:all:
> ```

---

## 🗄️ Step 3 — Supabase Setup

1. Go to [https://app.supabase.com](https://app.supabase.com) and create a free project.
2. Open **SQL Editor** and run:

```sql
CREATE TABLE kundlis (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  dob         TEXT NOT NULL,
  tob         TEXT NOT NULL,
  lat         FLOAT,
  lon         FLOAT,
  planets     JSONB,
  doshas      JSONB,
  notes       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

3. Go to **Project Settings → API** and copy:
   - `Project URL`
   - `anon public` key

4. Create `.env` in your project root:

```bash
cp .env.example .env
# Edit .env and paste your Supabase URL and KEY
```

---

## 🔑 Step 4 — Environment Variables

Edit `.env`:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-anon-key
```

Then load them before running:

```bash
# Mac/Linux
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k,$v) }
```

Or use python-dotenv (already in requirements). Add this to top of `app.py` if needed:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## ▶️ Step 5 — Run the App

```bash
python app.py
```

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🌐 Features

| Feature | Status |
|---|---|
| Birth details form | ✅ |
| Planetary positions (Sun–Ketu) | ✅ |
| Nakshatra + Lord | ✅ |
| House calculation | ✅ |
| Kaal Sarp Dosh detection | ✅ |
| Global search (name/rashi/nakshatra) | ✅ |
| Supabase save + retrieve | ✅ |
| Dashboard with name tags | ✅ |
| Dark theme Bootstrap UI | ✅ |
| Mobile responsive | ✅ |

---

## ➕ Adding New Dosha Rules

Open `kundli.py` and add a new function:

```python
def check_mangal_dosh(planets: dict) -> dict | None:
    mars_house = planets.get("Mars", {}).get("house")
    if mars_house in [1, 4, 7, 8, 12]:
        return {
            "name": "Mangal Dosh",
            "severity": "medium",
            "description": "Mars is placed in house...",
            "disclaimer": "⚠️ Consult a qualified astrologer."
        }
    return None
```

Then in `get_doshas()`:

```python
mangal = check_mangal_dosh(planets)
if mangal:
    doshas.append(mangal)
```

---

## 🚀 Deployment (Optional)

**Railway / Render / Fly.io:**
1. Push code to GitHub
2. Connect repo to Railway/Render
3. Add environment variables in their dashboard
4. Deploy — it works out of the box!

**Gunicorn (production server):**
```bash
pip install gunicorn
gunicorn app:app
```

---

## 🙏 Credits

- [Swiss Ephemeris](https://www.astro.com/swisseph/) via pyswisseph
- [Supabase](https://supabase.com/) — open source Firebase alternative
- [Bootstrap 5](https://getbootstrap.com/)
