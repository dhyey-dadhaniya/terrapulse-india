"""
AQI forecaster using Facebook Prophet.

Prophet looks at past daily AQI, finds an overall trend plus a yearly
seasonal pattern (e.g. winter spikes vs monsoon dips), and projects that
pattern forward for the requested horizon.

Predicted values are clipped at 0 because AQI cannot be negative; Prophet's
uncertainty intervals can otherwise dip below zero on low-AQI stretches.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)

_REQUIRED_COLS = {"ds", "y"}


def train_and_forecast(
    historical_df: pd.DataFrame,
    days_ahead: int = 90,
) -> pd.DataFrame:
    """
    Fit Prophet on historical AQI and return only future predictions.

    Parameters
    ----------
    historical_df:
        Daily series with columns ['ds', 'y'].
    days_ahead:
        Number of days to forecast beyond the last historical date.

    Returns
    -------
    DataFrame with columns ['ds', 'yhat', 'yhat_lower', 'yhat_upper'] for
    future dates only (ds > last historical date). Values are clipped at 0
    and rounded to 2 decimal places.
    """
    if set(historical_df.columns) != _REQUIRED_COLS:
        raise ValueError(
            f"historical_df must have exactly columns ['ds', 'y'], "
            f"got {list(historical_df.columns)}"
        )

    df = historical_df.copy()
    df = df.dropna(subset=["y"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds").reset_index(drop=True)

    if len(df) < 365:
        logger.warning(
            "historical_df has only %d rows; yearly seasonality works best "
            "with at least 365 days of data. Proceeding anyway.",
            len(df),
        )

    last_date = df["ds"].iloc[-1]

    model = Prophet(yearly_seasonality=True)
    model.fit(df)

    future = model.make_future_dataframe(periods=days_ahead, freq="D")
    forecast = model.predict(future)

    future_only = forecast.loc[forecast["ds"] > last_date, [
        "ds",
        "yhat",
        "yhat_lower",
        "yhat_upper",
    ]].copy()

    for col in ("yhat", "yhat_lower", "yhat_upper"):
        future_only[col] = future_only[col].clip(lower=0).round(2)

    return future_only.reset_index(drop=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    csv_path = Path(__file__).resolve().parent.parent / "data" / "synthetic_delhi_aqi.csv"
    history = pd.read_csv(csv_path, parse_dates=["ds"])
    result = train_and_forecast(history, days_ahead=90)
    print(result.head())
