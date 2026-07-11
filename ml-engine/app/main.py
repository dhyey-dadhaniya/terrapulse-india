from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query

from app.schemas import (
    AQICurrentResponse,
    ForecastPoint,
    ForecastResponse,
    HistoricalPoint,
)
from data_fetchers.aqicn_fetcher import AQIFetchError, InvalidCityError, get_city_aqi
from models.aqi_forecaster import train_and_forecast
from sample_data_generator import generate_synthetic_aqi

app = FastAPI(title="TerraPulse ML Engine")


def _as_date_str(value) -> str:
    """Normalize a date-like value to YYYY-MM-DD."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


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
