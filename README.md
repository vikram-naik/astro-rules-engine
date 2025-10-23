# 🌌 Astro Rules Engine

A modular, Python-based backend to **model planetary transits and their correlation with market sectors**.  
It lets you define astrology-driven rules (e.g., *"Jupiter in Ketu Nakshatra → Bearish for equities"*) and evaluate them over date ranges or live data.

---

## 🚀 Key Features

- **FastAPI backend** for rule creation and event evaluation  
- **SQLModel ORM** with SQLite (migratable to PostgreSQL)  
- **Modular rule engine** with pluggable planetary providers  
- **Dual Astro Providers**  
  - `SwissEphemProvider` — accurate sidereal calculations using `pyswisseph`  
  - `SkyfieldProvider` — independent JPL-based ephemeris with native Lahiri ayanāṃśa  
- **Dynamic ayanāṃśa modes** via `.env`:  
  `tropical`, `lahiri`, `krishnamurti`, `raman`  
- **Provider-agnostic PlanetMapper** abstraction  
- **Comprehensive test suite** with parity checks across providers  

---

## 🧩 Architecture Overview

```
backend/app/
├── main.py                        # FastAPI entry point
├── api/
│   ├── routes_rules.py            # CRUD endpoints for rules
│   └── routes_eval.py             # Evaluate rules and events
├── core/
│   ├── common/
│   │   ├── config.py              # Environment / settings
│   │   └── enums.py               # Planet, Nakshatra, etc.
│   ├── astro/
│   │   ├── interfaces/
│   │   │   ├── i_astro_provider.py
│   │   │   └── i_planet_mapper.py
│   │   ├── providers/
│   │   │   ├── stub_provider.py
│   │   │   ├── swisseph_provider.py
│   │   │   └── skyfield_provider.py
│   │   └── provider_factory.py    # Creates provider from .env
│   ├── db.py                      # SQLModel session
│   ├── models.py                  # ORM models (Rule, Sector, Event)
│   └── event_generator.py         # Core engine to generate events
└── tests/
    ├── test_event_generator.py
    ├── test_provider_matrix.py    # Cross-provider precision tests
    └── test_rule_events_api.py
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 +
- SQLite (default local database)
- `pip` or `pipenv`

### Setup

```bash
git clone https://github.com/vikram-naik/astro-rules-engine.git
cd astro-rules-engine/backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` at the repo root:

```
LOG_LEVEL=INFO
DEFAULT_SECTOR_TICKER=^GSPC
ASTRO_PROVIDER=skyfield          # or swisseph
ASTRO_AYANAMSA_MODE=lahiri       # tropical | lahiri | krishnamurti | raman
ASTRO_SKYFIELD_EPHEMERIS=de440s.bsp
```

---

## 🧠 Usage

### Run the API Server
```bash
uvicorn app.main:app --reload
```

- Swagger docs → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Example Evaluation Request
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

Run all tests:

```bash
pytest -q
```

Expected:
```
13 passed in <1.0s
```

Includes:
- Cross-provider parity tests (`Skyfield` vs `SwissEphem`)
- Mode-switch regression tests for all four ayanāṃśa modes
- Event-generation engine validation

---

## 🪐 Astro Data Providers

| Provider | Source | Frame | Notes |
|-----------|---------|--------|-------|
| **SwissEphemProvider** | `pyswisseph` | Sidereal / Lahiri | Uses `swe.FLG_SIDEREAL` flag and dynamic mode handling |
| **SkyfieldProvider** | `skyfield` (`de440s.bsp`) | True Ecliptic of Date | Pure JPL computation, native ayanāṃśa polynomial (~24.206° @ 2025) |
| **StubProvider** | Built-in | Deterministic | For isolated rule testing |

Each provider implements the same `IAstroProvider` interface and uses its own `PlanetMapper` to resolve canonical `Planet` enums.

---

## 🧭 Ayanāṃśa Modes

Configured via environment variable:

| Mode | Description | Provider behavior |
|------|--------------|------------------|
| `tropical` | No sidereal correction | Returns raw tropical longitudes |
| `lahiri` | Default sidereal (Chitrapaksha) | Applies Lahiri ayanāṃśa (~24.2° @ 2025) |
| `krishnamurti` | Lahiri − 0.1° | For KP astrology |
| `raman` | Lahiri + 0.5° | Raman variant |

---

## 🏗 Future Roadmap

| Feature | Status | Notes |
|----------|---------|-------|
| Rule CRUD API | ✅ | Complete |
| Event generator | ✅ | Generates planetary transits |
| Dual astro providers | ✅ | Parity < 0.001° |
| Ayanāṃśa mode system | ✅ | Tested for 4 modes |
| Market correlation layer | 🔜 | Integrate with `yfinance` |
| Frontend visualization | 🔜 | React / Streamlit UI |
| Analytics & backtesting | 🔜 | Pandas + Plotly |

---

## 🧑‍💻 Development Notes

- Environment handled via `pydantic_settings`
- Formatted with `black` + `isort`
- Database: `backend/astro_rules.db`
- Typical debug trace shows:
  ```
  Longitude calc: planet=sun ... tropical=280.81 ay=24.206 sidereal=256.61
  ```
- Both providers log computed ayanāṃśa and mode at runtime.

---

## 📜 License

MIT License © 2025 Vikram Naik

---

## ✨ Acknowledgements
- [Swiss Ephemeris (`pyswisseph`)](https://pypi.org/project/pyswisseph/)
- [Skyfield (JPL DE440)](https://rhodesmill.org/skyfield/)
- [FastAPI & SQLModel](https://sqlmodel.tiangolo.com/)
- Thanks to the open-source community for precision astronomical libraries!
