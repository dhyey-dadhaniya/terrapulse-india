# TerraPulse ML Engine

Python FastAPI service for machine learning workloads.

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The service starts at `http://localhost:8000`.

## Endpoints

| Method | Path     | Description        |
|--------|----------|--------------------|
| GET    | `/`      | Root health check  |
| GET    | `/health`| Health check       |
