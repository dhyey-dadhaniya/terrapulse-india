from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AQICurrentResponse,
    AnomaliesResponse,
    AnomalyRegionResult,
    ForecastPoint,
    ForecastResponse,
    HistoricalPoint,
    ModelMetricsResponse,
    RiskProbabilities,
    RiskResponse,
)
from data_fetchers.aqicn_fetcher import AQIFetchError, InvalidCityError, get_city_aqi
from models.anomaly_detector import (
    detect_anomalies,
    generate_synthetic_region_data,
    train_isolation_forest,
)
from models.aqi_forecaster import train_and_forecast
from models.risk_classifier import (
    generate_synthetic_risk_data,
    predict_risk,
    train_risk_model,
)
from sample_data_generator import generate_synthetic_aqi

# Canonical region names used by the climate anomaly / risk endpoints.
_KNOWN_REGIONS = [
    "Delhi",
    "Mumbai",
    "Chennai",
    "Bengaluru",
    "Kolkata",
    "Jaipur",
    "Nagpur",
    "Patna",
    "Lucknow",
    "Ahmedabad",
]
_RISK_LABELS = ["Low", "Medium", "High"]

# Trained once at startup and reused for fast API responses.
_anomaly_model = None
_anomaly_scaler = None
_risk_model = None
_risk_label_mapping: dict[int, str] | None = None
_risk_metrics: dict | None = None


def _as_date_str(value) -> str:
    """Normalize a date-like value to YYYY-MM-DD."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _resolve_region(region: str) -> str | None:
    """Return the canonical region name, or None if unknown."""
    lookup = {name.casefold(): name for name in _KNOWN_REGIONS}
    return lookup.get(region.casefold())


def _synthetic_risk_reading(region: str) -> dict:
    """
    Build one synthetic weather reading for a region.

    Uses the same value ranges as risk_classifier training data. The RNG is
    seeded from the region name so repeated calls for the same region are stable.
    """
    seed = abs(hash(region.casefold())) % (2**32)
    rng = np.random.default_rng(seed)
    return {
        "humidity": round(float(rng.uniform(20, 100)), 2),
        "temperature": round(float(rng.uniform(15, 48)), 2),
        "wind_speed": round(float(rng.uniform(0, 120)), 2),
        "historical_disaster_flag": int(rng.random() < 0.30),
    }


def _train_models_at_startup() -> None:
    """Fit anomaly + risk models once so request handlers stay fast."""
    global _anomaly_model, _anomaly_scaler
    global _risk_model, _risk_label_mapping, _risk_metrics

    region_df = generate_synthetic_region_data()
    _anomaly_model, _anomaly_scaler = train_isolation_forest(region_df)

    risk_df = generate_synthetic_risk_data()
    _risk_model, _risk_label_mapping, _risk_metrics = train_risk_model(risk_df)

    print(
        "Startup training complete: Isolation Forest + XGBoost risk classifier "
        "are loaded in memory."
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _train_models_at_startup()
    yield


app = FastAPI(title="TerraPulse ML Engine", lifespan=lifespan)

# Allow the Next.js frontend (browser) to call this API during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "healthy"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/aqi/current/{city}", response_model=AQICurrentResponse)
def get_current_aqi(city: str) -> AQICurrentResponse:
    """
    Return the latest live AQI snapshot for a city from AQICN.

    This is the real-time reading (PM2.5, PM10, NO2, overall AQI) for the
    requested feed. It does not include history — AQICN only exposes the
    current snapshot per city.
    """
    try:
        data = get_city_aqi(city)
    except InvalidCityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AQIFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AQICurrentResponse(**data)


@app.get("/api/aqi/forecast/{city}", response_model=ForecastResponse)
def get_aqi_forecast(
    city: str,
    days: int = Query(default=90),
) -> ForecastResponse:
    """
    Train Prophet on historical AQI and return a forward forecast.

    Historical series currently comes from synthetic Delhi-seasonal data, not
    live city history, because AQICN only provides the current reading and we
    are not yet storing daily snapshots. The city path param is echoed in the
    response for API shape, but does not change the training series yet.
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    # TODO: only Delhi-realistic synthetic pattern for now, replace with real
    # historical DB once we're collecting daily AQICN snapshots
    historical_df = generate_synthetic_aqi()
    forecast_df = train_and_forecast(historical_df, days_ahead=days)

    historical = [
        HistoricalPoint(date=_as_date_str(row["ds"]), aqi=float(row["y"]))
        for _, row in historical_df.iterrows()
    ]
    forecast = [
        ForecastPoint(
            date=_as_date_str(row["ds"]),
            yhat=float(row["yhat"]),
            yhat_lower=float(row["yhat_lower"]),
            yhat_upper=float(row["yhat_upper"]),
        )
        for _, row in forecast_df.iterrows()
    ]

    return ForecastResponse(
        city=city,
        generated_at=datetime.now(timezone.utc).isoformat(),
        historical=historical,
        forecast=forecast,
    )


@app.get("/api/climate/anomalies", response_model=AnomaliesResponse)
def get_climate_anomalies() -> AnomaliesResponse:
    """
    Score current climate readings for all known regions for anomalies.

    Uses the Isolation Forest trained once at startup (not per request) so
    responses stay fast. Current readings are a single synthetic day for each
    of the 10 regions.
    """
    if _anomaly_model is None or _anomaly_scaler is None:
        raise HTTPException(status_code=503, detail="Anomaly model is not ready yet.")

    # Last day across all regions from a fresh synthetic batch.
    current = (
        generate_synthetic_region_data()
        .groupby("region", sort=False)
        .tail(1)
        .reset_index(drop=True)
    )
    detected = detect_anomalies(_anomaly_model, _anomaly_scaler, current)

    return AnomaliesResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        results=[AnomalyRegionResult(**row) for row in detected],
    )


@app.get("/api/climate/risk/{region}", response_model=RiskResponse)
def get_climate_risk(region: str) -> RiskResponse:
    """
    Predict Low/Medium/High disaster risk for one region.

    Weather inputs are synthetic for now (same ranges as training). The XGBoost
    classifier is trained once at startup so each call only runs a quick predict.
    """
    if _risk_model is None or _risk_label_mapping is None:
        raise HTTPException(status_code=503, detail="Risk model is not ready yet.")

    canonical = _resolve_region(region)
    if canonical is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown region '{region}'. "
                f"Supported regions: {', '.join(_KNOWN_REGIONS)}."
            ),
        )

    features = _synthetic_risk_reading(canonical)
    prediction = predict_risk(_risk_model, _risk_label_mapping, features)

    return RiskResponse(
        region=canonical,
        risk_level=prediction["risk_level"],
        probabilities=RiskProbabilities(**prediction["probabilities"]),
    )


@app.get("/api/climate/model-metrics", response_model=ModelMetricsResponse)
def get_climate_model_metrics() -> ModelMetricsResponse:
    """
    Return the risk classifier's test metrics computed at startup.

    No retraining happens here — this just exposes accuracy, macro F1, and the
    confusion matrix so clients can inspect model quality without waiting.
    """
    if _risk_metrics is None:
        raise HTTPException(status_code=503, detail="Risk metrics are not ready yet.")

    return ModelMetricsResponse(
        accuracy=float(_risk_metrics["accuracy"]),
        f1_macro=float(_risk_metrics["f1_macro"]),
        confusion_matrix=_risk_metrics["confusion_matrix"],
        labels=list(_RISK_LABELS),
    )
