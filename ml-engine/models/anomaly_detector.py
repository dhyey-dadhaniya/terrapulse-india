"""
Isolation Forest anomaly detection for regional climate readings.

An Isolation Forest builds random trees that keep splitting the feature space.
Unusual points tend to land in short paths (they get isolated quickly), while
typical points need more splits. That short-path signal becomes the anomaly
score — lower / more negative means more unusual.

We StandardScaler-normalize rainfall, temperature, and soil moisture before
fitting because they live on very different numeric scales (mm, °C, %). Without
scaling, the tree splits would be dominated by whichever feature has the
largest raw range.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_OUTPUT_CSV = _DATA_DIR / "synthetic_regions_climate.csv"

_REGIONS = [
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

_FEATURE_COLS = ["rainfall_mm", "temperature", "soil_moisture"]


def generate_synthetic_region_data(num_days: int = 180) -> pd.DataFrame:
    """
    Build monsoon-season climate rows for 10 Indian regions and save to CSV.

    Most days look normal. A small fraction get flood-like rain spikes, heat
    extremes, or drought / waterlogged soil moisture so the Isolation Forest
    has clear anomalies to learn from.
    """
    rng = np.random.default_rng(seed=42)
    rows: list[dict] = []

    for region in _REGIONS:
        for _ in range(num_days):
            # ~5% flood-triggering rainfall spikes
            if rng.random() < 0.05:
                rainfall = float(rng.uniform(150, 300))
            else:
                rainfall = float(rng.uniform(0, 40))

            # ~3% extreme heat spikes
            if rng.random() < 0.03:
                temperature = float(rng.uniform(45, 48))
            else:
                temperature = float(rng.uniform(22, 38))

            # ~3% drought-like lows or waterlogged highs
            if rng.random() < 0.03:
                soil_moisture = float(
                    rng.uniform(0, 5) if rng.random() < 0.5 else rng.uniform(95, 100)
                )
            else:
                soil_moisture = float(rng.uniform(20, 60))

            rows.append(
                {
                    "region": region,
                    "rainfall_mm": round(rainfall, 2),
                    "temperature": round(temperature, 2),
                    "soil_moisture": round(soil_moisture, 2),
                }
            )

    df = pd.DataFrame(rows, columns=["region", *_FEATURE_COLS])
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_OUTPUT_CSV, index=False)
    return df


def train_isolation_forest(
    df: pd.DataFrame,
) -> tuple[IsolationForest, StandardScaler]:
    """
    Fit an Isolation Forest on scaled climate features.

    Returns the fitted model and the StandardScaler so the same transform can
    be applied to new readings at detection time.
    """
    missing = [c for c in (["region", *_FEATURE_COLS]) if c not in df.columns]
    if missing:
        raise ValueError(f"df is missing required columns: {missing}")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[_FEATURE_COLS])

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(scaled)
    return model, scaler


def detect_anomalies(
    model: IsolationForest,
    scaler: StandardScaler,
    current_readings: pd.DataFrame,
) -> list[dict]:
    """
    Score each row as normal or anomalous using the fitted Isolation Forest.

    anomaly_score comes from decision_function (lower = more anomalous).
    is_anomaly is True when predict() returns -1.
    """
    missing = [c for c in (["region", *_FEATURE_COLS]) if c not in current_readings.columns]
    if missing:
        raise ValueError(f"current_readings is missing required columns: {missing}")

    scaled = scaler.transform(current_readings[_FEATURE_COLS])
    predictions = model.predict(scaled)
    scores = model.decision_function(scaled)

    results: list[dict] = []
    for region, score, pred in zip(
        current_readings["region"],
        scores,
        predictions,
        strict=True,
    ):
        results.append(
            {
                "region": str(region),
                "anomaly_score": round(float(score), 3),
                "is_anomaly": bool(pred == -1),
            }
        )
    return results


if __name__ == "__main__":
    data = generate_synthetic_region_data()
    print(f"Wrote {len(data)} rows to {_OUTPUT_CSV}")

    model, scaler = train_isolation_forest(data)

    # One reading per region from the last generated day
    last_day = data.groupby("region", sort=False).tail(1).reset_index(drop=True)
    results = detect_anomalies(model, scaler, last_day)
    results_sorted = sorted(results, key=lambda r: r["anomaly_score"])

    print("Last-day anomaly scores (most anomalous first):")
    for row in results_sorted:
        print(row)

    # Spot-check the strongest injected extremes (clearest anomalies)
    rain_extremes = (
        data[data["rainfall_mm"] > 150]
        .nlargest(4, "rainfall_mm")
        .reset_index(drop=True)
    )
    heat_extremes = (
        data[data["temperature"] > 45]
        .nlargest(4, "temperature")
        .reset_index(drop=True)
    )
    extreme_rows = pd.concat([rain_extremes, heat_extremes], ignore_index=True)
    extreme_results = detect_anomalies(model, scaler, extreme_rows)

    print("\nKnown extreme readings (should flag is_anomaly=True):")
    for reading, result in zip(
        extreme_rows.to_dict(orient="records"),
        extreme_results,
        strict=True,
    ):
        print(
            {
                **result,
                "rainfall_mm": reading["rainfall_mm"],
                "temperature": reading["temperature"],
                "soil_moisture": reading["soil_moisture"],
            }
        )
