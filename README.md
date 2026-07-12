# TerraPulse India

TerraPulse India is a local-first climate intelligence platform for Indian cities. It combines AQI forecasting, climate anomaly detection, and disaster-risk classification with a live IoT-style fire-alert pipeline — so operators can see regional risk on a map, inspect air-quality forecasts, and watch high-severity alerts arrive in real time.

## Architecture

```
IoT simulator (Python)
        │
        ▼  Kafka topic: iot-climate-stream
Spring Boot backend  ←→  PostgreSQL (regions, sensor_readings, alert_logs)
        │                       ▲
        │ REST + WebSocket      │ JPA
        ▼                       │
Next.js dashboard (Leaflet map, Recharts, live alerts)
        ▲
        │ REST
Python FastAPI ML engine (Prophet AQI forecast, Isolation Forest, XGBoost risk)
```

- **ml-engine** — FastAPI models + AQICN live AQI fetch  
- **backend** — Spring Boot API, Kafka consumer, scheduled risk refresh, WebSocket `/topic/alerts`  
- **frontend** — Next.js dashboard at `/dashboard`  
- **Kafka + Zookeeper** — local Docker Compose (optional Postgres container on port 5433)

## Tech stack

- **ML:** Python, FastAPI, Prophet, XGBoost, scikit-learn, kafka-python  
- **Backend:** Spring Boot, PostgreSQL, Spring Kafka, STOMP WebSocket  
- **Frontend:** Next.js 14, Leaflet/OpenStreetMap, Recharts, SockJS + STOMP  
- **Infra (local):** Docker Compose (Kafka/Zookeeper; optional Postgres)

## Prerequisites

- Python 3.10+  
- Java 17+ and Maven 3.8+  
- Node.js 18+  
- Docker Desktop  
- Native PostgreSQL 16+ (default; database `terrapulse_db` on `localhost:5432`)  
- AQICN API token ([aqicn.org/data-platform/token](https://aqicn.org/data-platform/token/)) for live AQI

## Setup

```powershell
git clone <repo-url> terrapulse-india
cd terrapulse-india
```

### 1. Environment files

Copy each example and fill real values (never commit real `.env` files):

```powershell
Copy-Item ml-engine\.env.example ml-engine\.env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
# Optional — only if you use Docker Postgres later:
Copy-Item .env.example .env
```

| File | Keys |
|------|------|
| `ml-engine/.env` | `AQICN_API_TOKEN` |
| `backend/.env` | `DB_USERNAME`, `DB_PASSWORD` |
| `frontend/.env.local` | `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_ML_ENGINE_URL` |
| `.env` (root, optional) | `DB_PASSWORD` for compose Postgres |

### 2. Install dependencies

```powershell
# ML engine
cd ml-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# Backend — Maven resolves deps on first run
# Frontend
cd frontend
npm install
cd ..
```

### 3. Database

With native Postgres running, create the DB once:

```sql
CREATE DATABASE terrapulse_db;
```

Spring Boot (`ddl-auto=update`) creates tables on first start. Seed regions via `POST /api/regions` or the dashboard’s backend after startup (10 cities are expected for the full demo).

> **Docker Postgres (optional):** compose exposes Postgres on **localhost:5433** so it does not conflict with native `:5432`. Default backend config still points at `:5432`. See comments in `docker-compose.yml`.

## Running locally

Use the guided helper (prints steps; open separate terminals as directed):

```powershell
.\start-dev.ps1
```

**Startup order (summary):**

1. `docker compose up -d zookeeper kafka` — wait until healthy  
2. Confirm native PostgreSQL + `terrapulse_db`  
3. ML engine: `uvicorn app.main:app --reload` → `:8000`  
4. Backend: `mvn spring-boot:run` → `:8080`  
5. (Optional) IoT simulator: `python iot_simulator.py` for live fire alerts  
6. Frontend: `npm run dev` → `:3000`  
7. Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

Useful URLs:

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000/dashboard |
| Backend health | http://localhost:8080/health |
| ML docs | http://localhost:8000/docs |
| Alert WS test page | http://localhost:8080/alert-ws-test.html |

## Known limitations

- AQI **forecast** currently trains on **Delhi-pattern synthetic** history for every city (city selector is demo-shaped).  
- Only **10 seeded regions** (not full India coverage).  
- Historical AQI for forecasting is **not** from a long-term AQICN archive (AQICN is current-snapshot oriented).  
- Kafka / WebSocket setup is **local demo only** — no auth, TLS, or production hardening.  
- Live alert UI holds alerts in **browser memory**; refresh clears the feed (rows remain in `alert_logs`).  
- Risk refresh scheduler runs every **30 minutes**; use `POST /api/regions/refresh-risk` for an on-demand pull.

## Project layout

```
terrapulse-india/
├── ml-engine/          # FastAPI + models + iot_simulator.py
├── backend/            # Spring Boot API + Kafka consumer
├── frontend/           # Next.js dashboard
├── docker-compose.yml  # Zookeeper, Kafka, optional Postgres
├── start-dev.ps1       # Guided local startup
└── README.md
```
