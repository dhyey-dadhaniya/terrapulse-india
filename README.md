# TerraPulse India

Monorepo for the TerraPulse India platform, containing the ML engine, backend API, and frontend application.

## Project Structure

```
terrapulse-india/
├── ml-engine/    # Python FastAPI ML service
├── backend/      # Spring Boot REST API
└── frontend/     # Next.js web application
```

## Prerequisites

- Python 3.10+
- Java 17+
- Maven 3.8+
- Node.js 18+

## ML Engine

```bash
cd ml-engine
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The ML engine runs at `http://localhost:8000`.

## Backend

```bash
cd backend
mvn spring-boot:run
```

The backend runs at `http://localhost:8080`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`.
