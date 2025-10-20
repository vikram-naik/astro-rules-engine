# 🌌 Astro Rules Engine

A modular, Python-based backend system to model **astrological transits and their effects on market sectors**.  
This project enables configuration of astrology-based rules (e.g., "Jupiter in Ketu Nakshatra → bearish for equities") via an API layer and evaluates them against market data.

---

## 🚀 Features

- **FastAPI backend** for managing and executing astro-market rules  
- **SQLite storage** (easy to migrate to PostgreSQL)  
- **Modular rule engine** with pluggable planetary data providers  
- **AstroProvider abstraction** — integrates with [`pyswisseph`](https://pypi.org/project/pyswisseph/) or [`skyfield`](https://rhodesmill.org/skyfield/)  
- **Declarative rule schema** via JSON or REST API  
- **Extensible** to sectors, outcomes, and live backtesting  
- **Unit tests** via `pytest`

---

## 🧩 Architecture Overview

```
backend/app/
├── main.py                # FastAPI entry point
├── api/
│   ├── routes_rules.py    # CRUD endpoints for rules
│   └── routes_eval.py     # Evaluate transits
├── core/
│   ├── config.py          # Environment config
│   ├── db.py              # SQLModel engine + session
│   ├── models.py          # DB models (RuleModel, Sector)
│   ├── schemas.py         # Pydantic models & enums
│   ├── astro_provider.py  # Planet longitude provider (stub or Swisseph)
│   └── rules_engine.py    # Core engine to evaluate rules
└── tests/
    └── test_rules_engine.py
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- pipenv or venv
- SQLite (default, file-based)

### Setup

```bash
# clone the repo
git clone https://github.com/vikram-naik/astro-rules-engine.git
cd astro-rules-engine/backend

# setup environment
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

---

## 🧠 Usage

### 1️⃣ Run the API Server

```bash
uvicorn app.main:app --reload
```

- Visit Swagger docs at: **http://127.0.0.1:8000/docs**
- Example endpoints:
  - `POST /rules` → create new rule  
  - `GET /rules` → list rules  
  - `POST /evaluate` → evaluate enabled rules over a date range

### 2️⃣ Example API Request

```bash
POST /evaluate
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-10"
}
```

Response:
```json
{
  "count": 5,
  "events": [
    {
      "rule_id": "R001",
      "date": "2025-01-02",
      "sector": "EQUITY",
      "effect": "Bearish",
      "confidence": 0.9
    }
  ]
}
```

---

## 🧪 Testing

Run unit tests:

```bash
pytest -q
```

Expected output:
```
.  [100%]
1 passed in 0.45s
```

---

## 🪐 Astro Data Provider

The system uses an abstract `AstroProvider` class with two implementations:

- **Stub (default)** — deterministic pseudo longitudes for testing.
- **Swiss Ephemeris** (`pyswisseph`) — accurate Vedic (Lahiri) planetary positions.
- **Skyfield** (optional fallback) — accurate JPL ephemerides (tropical).

You can swap implementations easily in `core/astro_provider.py`.

---

## 🏗 Future Roadmap

| Feature | Status | Notes |
|----------|---------|-------|
| Rule CRUD API | ✅ | Done |
| Rule evaluation engine | ✅ | Done |
| SQLite database | ✅ | File-based, `astro_rules.db` |
| Logging & tracing | 🔜 | Next layer |
| Market data integration | 🔜 | via `yfinance` |
| Frontend rule builder UI | 🔜 | React / Streamlit planned |
| Backtesting analytics | 🔜 | Pandas + charts layer |

---

## 🧑‍💻 Development Notes

- Environment variables loaded via `.env`
- Code formatted with `black` and `isort`
- Uses [SQLModel](https://sqlmodel.tiangolo.com/) for ORM and Pydantic schema alignment
- Default DB path: `backend/astro_rules.db`

---

## 📜 License

MIT License © 2025 Vikram Naik

---

## ✨ Acknowledgements
- Swiss Ephemeris (`pyswisseph`)
- Skyfield Ephemeris (`de421`)
- FastAPI & SQLModel by Sebastián Ramírez