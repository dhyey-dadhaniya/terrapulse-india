# TerraPulse India — guided local startup (Windows)
# Prints the correct order. Open a new terminal for each long-running service.

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Step([string]$num, [string]$title) {
    Write-Host ""
    Write-Host "======== STEP $num: $title ========" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "TerraPulse India — local dev startup guide" -ForegroundColor Green
Write-Host "Project root: $Root"
Write-Host "Open a SEPARATE terminal for each long-running process (ML, backend, frontend, simulator)."
Write-Host ""

# ---------------------------------------------------------------------------
Step "1" "Kafka + Zookeeper (Docker)"
Write-Host "From the project root, start the brokers and wait until both are healthy:"
Write-Host ""
Write-Host '  cd "' -NoNewline; Write-Host $Root -NoNewline; Write-Host '"'
Write-Host "  docker compose up -d zookeeper kafka"
Write-Host "  docker compose ps"
Write-Host ""
Write-Host "Expect terrapulse-zookeeper and terrapulse-kafka to show (healthy)."
Write-Host "Do NOT start the optional postgres service unless you intentionally want Docker Postgres on port 5433."

# ---------------------------------------------------------------------------
Step "2" "Native PostgreSQL"
Write-Host "Confirm your HOST Postgres is running on localhost:5432."
Write-Host "Database terrapulse_db must exist (backend/application.properties default)."
Write-Host ""
Write-Host "  # Example check (adjust user if needed):"
Write-Host "  psql -h localhost -U postgres -d terrapulse_db -c '\conninfo'"
Write-Host ""
Write-Host "Ensure backend/.env has DB_USERNAME and DB_PASSWORD filled in."

# ---------------------------------------------------------------------------
Step "3" "ML engine (port 8000)"
Write-Host "New terminal:"
Write-Host ""
Write-Host '  cd "' -NoNewline; Write-Host (Join-Path $Root "ml-engine") -NoNewline; Write-Host '"'
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  # If venv missing: python -m venv .venv ; pip install -r requirements.txt"
Write-Host "  # Ensure ml-engine/.env has AQICN_API_TOKEN"
Write-Host "  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "Health: http://127.0.0.1:8000/health   Docs: http://127.0.0.1:8000/docs"
Write-Host "First start trains anomaly + risk models — wait for 'Startup training complete'."

# ---------------------------------------------------------------------------
Step "4" "Spring Boot backend (port 8080)"
Write-Host "New terminal:"
Write-Host ""
Write-Host '  cd "' -NoNewline; Write-Host (Join-Path $Root "backend") -NoNewline; Write-Host '"'
Write-Host "  mvn spring-boot:run"
Write-Host ""
Write-Host "Health: http://127.0.0.1:8080/health"
Write-Host "Needs Kafka healthy + Postgres reachable + ML engine up for risk refresh."

# ---------------------------------------------------------------------------
Step "5" "IoT simulator (optional — live alerts)"
Write-Host "Only needed for live fire alerts on the dashboard. New terminal:"
Write-Host ""
Write-Host '  cd "' -NoNewline; Write-Host (Join-Path $Root "ml-engine") -NoNewline; Write-Host '"'
Write-Host "  `$env:PYTHONUNBUFFERED='1'; `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe iot_simulator.py"
Write-Host ""
Write-Host "Publishes to Kafka topic iot-climate-stream. Stop with Ctrl+C."
Write-Host "Keep http://localhost:3000/dashboard open to see WebSocket alerts."

# ---------------------------------------------------------------------------
Step "6" "Next.js frontend (port 3000)"
Write-Host "New terminal:"
Write-Host ""
Write-Host '  cd "' -NoNewline; Write-Host (Join-Path $Root "frontend") -NoNewline; Write-Host '"'
Write-Host "  npm install   # first time only"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Uses frontend/.env.local (NEXT_PUBLIC_BACKEND_URL, NEXT_PUBLIC_ML_ENGINE_URL)."

# ---------------------------------------------------------------------------
Step "7" "Open the dashboard"
Write-Host "  http://localhost:3000/dashboard"
Write-Host ""
Write-Host "Landing page: http://localhost:3000  (View Dashboard button)"
Write-Host ""
Write-Host "Done. Follow the steps above in order for a full local stack." -ForegroundColor Green
Write-Host ""
