from pydantic import BaseModel


class AQICurrentResponse(BaseModel):
    city: str
    pm25: float | None
    pm10: float | None
    no2: float | None
    aqi: int | None
    timestamp: str


class HistoricalPoint(BaseModel):
    date: str
    aqi: float


class ForecastPoint(BaseModel):
    date: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastResponse(BaseModel):
    city: str
    generated_at: str
    historical: list[HistoricalPoint]
    forecast: list[ForecastPoint]
