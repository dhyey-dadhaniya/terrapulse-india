"""
Generate a synthetic daily AQI series for model training and demos.

Real historical AQI is hard to get from AQICN (current-only feeds), so we
simulate Delhi-like seasons instead:

- Nov–Jan: high AQI (roughly 300–450) from stubble burning and winter inversion
- Jul–Sep: low AQI (roughly 50–120) during the monsoon washout
- Other months: mid-range AQI (roughly 150–250) in the transition seasons

A little Gaussian noise is added each day so the series is not perfectly smooth.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent / "data"
_OUTPUT_CSV = _DATA_DIR / "synthetic_delhi_aqi.csv"


def _seasonal_base(month: int, rng: np.random.Generator) -> float:
    if month in (11, 12, 1):
        return float(rng.uniform(300, 450))
    if month in (7, 8, 9):
        return float(rng.uniform(50, 120))
    return float(rng.uniform(150, 250))


def generate_synthetic_aqi(city: str = "Delhi", years: int = 2) -> pd.DataFrame:
    """
    Build a daily AQI DataFrame with columns ['ds', 'y'] and write it to CSV.

    Parameters
    ----------
    city:
        Label for the series (currently only used for documentation; output
        path remains synthetic_delhi_aqi.csv as specified).
    years:
        Number of calendar years of daily rows to generate ending today.
    """
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=years) + pd.Timedelta(days=1)
    dates = pd.date_range(start=start, end=end, freq="D")

    rng = np.random.default_rng(seed=42)
    values: list[float] = []
    for ts in dates:
        base = _seasonal_base(int(ts.month), rng)
        noisy = base + float(rng.normal(0, 8))
        values.append(max(0.0, noisy))

    df = pd.DataFrame({"ds": dates, "y": values})
    # Keep y as a float AQI reading suitable for forecasting libs (Prophet-style).
    df["y"] = df["y"].round(2)

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_OUTPUT_CSV, index=False)

    _ = city  # reserved for multi-city outputs later
    return df


if __name__ == "__main__":
    frame = generate_synthetic_aqi()
    print(f"Wrote {len(frame)} rows to {_OUTPUT_CSV}")
    print(frame.head())
    print(frame.tail())
