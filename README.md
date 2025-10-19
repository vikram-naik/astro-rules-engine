# Astro Rules Engine

A Python-based backend rules engine for correlating astrological transits with market sector trends.

### Run locally

```bash
cd backend
uvicorn app.main:app --reload
```

Endpoints

POST /rules — create new rule

GET /rules — list rules

POST /evaluate — run all enabled rules on a date range