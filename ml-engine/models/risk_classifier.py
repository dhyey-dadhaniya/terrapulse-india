"""
Disaster risk classification with XGBoost.

XGBoost here builds many small decision trees in sequence: each new tree
focuses on the mistakes of the ones before it, and their votes are combined
into one stronger Low / Medium / High prediction.

After training we report:
- accuracy: share of test rows the model got exactly right
- F1 (macro): balances precision and recall, averaged evenly across the three
  risk classes (so a rare High class is not ignored)
- confusion matrix: rows = true labels, columns = predicted labels — shows
  which classes get mixed up

Synthetic labels include ~5% adjacent-level noise because real-world disaster
labels are rarely perfectly clean; a little noise keeps the task realistic
instead of trivially separable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_OUTPUT_CSV = _DATA_DIR / "synthetic_risk_training.csv"

_FEATURE_COLS = [
    "humidity",
    "temperature",
    "wind_speed",
    "historical_disaster_flag",
]
_RISK_LEVELS = ["Low", "Medium", "High"]
_LABEL_TO_INT = {name: idx for idx, name in enumerate(_RISK_LEVELS)}
_INT_TO_LABEL = {idx: name for idx, name in enumerate(_RISK_LEVELS)}


def _base_risk_level(
    humidity: float,
    temperature: float,
    wind_speed: float,
    historical_disaster_flag: int,
) -> str:
    """Assign High / Medium / Low from weather + history rules."""
    if (
        wind_speed > 80
        or (temperature > 42 and humidity < 30)
        or (historical_disaster_flag == 1 and wind_speed > 60)
    ):
        return "High"

    if (
        40 <= wind_speed <= 80
        or 35 <= temperature <= 42
        or historical_disaster_flag == 1
    ):
        return "Medium"

    return "Low"


def _flip_adjacent(level: str, rng: np.random.Generator) -> str:
    """Flip a risk label to a neighboring level (Low↔Medium↔High)."""
    if level == "Low":
        return "Medium"
    if level == "High":
        return "Medium"
    return "Low" if rng.random() < 0.5 else "High"


def generate_synthetic_risk_data(num_samples: int = 2000) -> pd.DataFrame:
    """
    Build synthetic weather + history rows with Low/Medium/High risk labels.

    Labels follow simple physical rules, then ~5% are flipped to an adjacent
    risk level so the classifier faces noisy, real-world-like targets.
    """
    rng = np.random.default_rng(seed=42)
    rows: list[dict] = []

    for _ in range(num_samples):
        humidity = float(rng.uniform(20, 100))
        temperature = float(rng.uniform(15, 48))
        wind_speed = float(rng.uniform(0, 120))
        historical_disaster_flag = int(rng.random() < 0.30)

        risk_level = _base_risk_level(
            humidity, temperature, wind_speed, historical_disaster_flag
        )
        if rng.random() < 0.05:
            risk_level = _flip_adjacent(risk_level, rng)

        rows.append(
            {
                "humidity": round(humidity, 2),
                "temperature": round(temperature, 2),
                "wind_speed": round(wind_speed, 2),
                "historical_disaster_flag": historical_disaster_flag,
                "risk_level": risk_level,
            }
        )

    df = pd.DataFrame(rows, columns=[*_FEATURE_COLS, "risk_level"])
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_OUTPUT_CSV, index=False)
    return df


def train_risk_model(df: pd.DataFrame) -> tuple[XGBClassifier, dict[int, str], dict]:
    """
    Train an XGBoost multi-class risk classifier and score it on a held-out test set.

    Returns the fitted model, an int→label mapping for decoding predictions,
    and a metrics dict (accuracy, f1_macro, confusion_matrix).
    """
    required = [*_FEATURE_COLS, "risk_level"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"df is missing required columns: {missing}")

    x = df[_FEATURE_COLS]
    y = df["risk_level"].map(_LABEL_TO_INT)
    if y.isna().any():
        raise ValueError("risk_level must be one of Low, Medium, High")

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=len(_RISK_LEVELS),
        random_state=42,
        eval_metric="mlogloss",
    )
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    f1_macro = float(f1_score(y_test, y_pred, average="macro"))
    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=list(range(len(_RISK_LEVELS))),
    )
    cm_list = cm.tolist()

    print(f"accuracy: {accuracy:.4f}")
    print(f"f1_macro: {f1_macro:.4f}")
    print(f"confusion_matrix (rows=true Low/Med/High, cols=pred): {cm_list}")

    metrics = {
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "confusion_matrix": cm_list,
    }
    label_mapping = dict(_INT_TO_LABEL)
    return model, label_mapping, metrics


def predict_risk(
    model: XGBClassifier,
    label_mapping: dict[int, str],
    input_features: dict,
) -> dict:
    """
    Predict risk level and class probabilities for one weather reading.

    Probabilities come from softprob (one value per class, summing to ~1.0).
    """
    row = pd.DataFrame(
        [
            {
                "humidity": float(input_features["humidity"]),
                "temperature": float(input_features["temperature"]),
                "wind_speed": float(input_features["wind_speed"]),
                "historical_disaster_flag": int(
                    input_features["historical_disaster_flag"]
                ),
            }
        ],
        columns=_FEATURE_COLS,
    )

    pred_idx = int(model.predict(row)[0])
    proba = model.predict_proba(row)[0]

    probabilities = {
        label_mapping[i]: round(float(proba[i]), 3)
        for i in range(len(proba))
    }
    return {
        "risk_level": label_mapping[pred_idx],
        "probabilities": probabilities,
    }


if __name__ == "__main__":
    data = generate_synthetic_risk_data()
    print(f"Wrote {len(data)} rows to {_OUTPUT_CSV}")
    print(data["risk_level"].value_counts().to_dict())

    model, label_mapping, metrics = train_risk_model(data)
    print("metrics:", metrics)

    examples = [
        {
            "name": "clearly low risk",
            "features": {
                "humidity": 65.0,
                "temperature": 24.0,
                "wind_speed": 12.0,
                "historical_disaster_flag": 0,
            },
        },
        {
            "name": "borderline medium risk",
            "features": {
                "humidity": 55.0,
                "temperature": 37.0,
                "wind_speed": 50.0,
                "historical_disaster_flag": 0,
            },
        },
        {
            "name": "clearly high risk",
            "features": {
                "humidity": 25.0,
                "temperature": 45.0,
                "wind_speed": 95.0,
                "historical_disaster_flag": 1,
            },
        },
    ]

    print("\nHand-picked predictions:")
    for example in examples:
        result = predict_risk(model, label_mapping, example["features"])
        print(f"{example['name']}: {result}")
