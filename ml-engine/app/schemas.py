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


class AnomalyRegionResult(BaseModel):
    region: str
    anomaly_score: float
    is_anomaly: bool


class AnomaliesResponse(BaseModel):
    generated_at: str
    results: list[AnomalyRegionResult]


class RiskProbabilities(BaseModel):
    Low: float
    Medium: float
    High: float


class RiskResponse(BaseModel):
    region: str
    risk_level: str
    probabilities: RiskProbabilities


class ModelMetricsResponse(BaseModel):
    accuracy: float
    f1_macro: float
    confusion_matrix: list[list[int]]
    labels: list[str]
