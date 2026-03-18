from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.ml_model.feature_builder import (
    build_supervised_dataset,
    normalize_training_df,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

SUPERVISED_DATASET_PATH = DATA_DIR / "supervised_menu_dataset.csv"
MODEL_PATH = ARTIFACTS_DIR / "menu_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "menu_model_metadata.json"


FEATURE_COLUMNS = [
    "restaurant_id",
    "season_tag",
    "weekday",
    "category",
    "normalized_name",
    "avg_units_sold_hist",
    "avg_rating_hist",
    "times_used_hist",
    "total_units_sold_hist",
    "total_ratings_hist",
    "days_since_last_used",
    "used_prev_day",
    "used_7_days_ago",
    "used_14_days_ago",
    "times_used_same_weekday",
    "times_used_same_season",
    "usage_rate_global",
    "usage_rate_same_weekday",
    "usage_rate_same_season",
]


def build_model_pipeline(model_type: str = "rf") -> Pipeline:
    categorical_features = [
        "restaurant_id",
        "season_tag",
        "weekday",
        "category",
        "normalized_name",
    ]

    numeric_features = [
        "avg_units_sold_hist",
        "avg_rating_hist",
        "times_used_hist",
        "total_units_sold_hist",
        "total_ratings_hist",
        "days_since_last_used",
        "used_prev_day",
        "used_7_days_ago",
        "used_14_days_ago",
        "times_used_same_weekday",
        "times_used_same_season",
        "usage_rate_global",
        "usage_rate_same_weekday",
        "usage_rate_same_season",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
        ]
    )

    if model_type == "logreg":
        model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        )
    else:
        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def temporal_train_test_split(
    df: pd.DataFrame,
    test_days: int = 28,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = df.sort_values("menu_date").copy()

    max_date = data["menu_date"].max()
    cutoff = max_date - pd.Timedelta(days=test_days)

    train_df = data[data["menu_date"] <= cutoff].copy()
    test_df = data[data["menu_date"] > cutoff].copy()

    return train_df, test_df


def train_from_dataframe(
    training_df: pd.DataFrame,
    model_type: str = "rf",
    max_history_days: int | None = 120,
    test_days: int = 28,
    save_supervised_dataset: bool = True,
) -> dict:
    normalized_df = normalize_training_df(training_df)

    supervised_df = build_supervised_dataset(
        training_df=normalized_df,
        max_history_days=max_history_days,
    )

    if supervised_df.empty:
        raise ValueError("El dataset supervisado quedó vacío")

    if save_supervised_dataset:
        supervised_df.to_csv(SUPERVISED_DATASET_PATH, index=False)

    train_df, test_df = temporal_train_test_split(
        supervised_df,
        test_days=test_days,
    )

    if train_df.empty:
        raise ValueError("El split temporal dejó train vacío")
    if test_df.empty:
        raise ValueError("El split temporal dejó test vacío")

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["target_selected"].astype(int)

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["target_selected"].astype(int)

    pipeline = build_model_pipeline(model_type=model_type)
    pipeline.fit(X_train, y_train)

    test_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "positive_rate_train": float(y_train.mean()),
        "positive_rate_test": float(y_test.mean()),
        "avg_precision": float(average_precision_score(y_test, test_proba)),
        "roc_auc": (
            float(roc_auc_score(y_test, test_proba)) if y_test.nunique() > 1 else None
        ),
    }

    model_version = (
        "logreg_binary_candidate_ranker_v1"
        if model_type == "logreg"
        else "rf_binary_candidate_ranker_v1"
    )

    joblib.dump(pipeline, MODEL_PATH)

    metadata = {
        "model_version": model_version,
        "model_type": model_type,
        "feature_columns": FEATURE_COLUMNS,
        "max_history_days": max_history_days,
        "test_days": test_days,
        "metrics": metrics,
        "paths": {
            "supervised_dataset": str(SUPERVISED_DATASET_PATH),
            "model": str(MODEL_PATH),
            "metadata": str(METADATA_PATH),
        },
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return metadata


def train_from_csv(
    csv_path: str | Path,
    model_type: str = "rf",
    max_history_days: int | None = 120,
    test_days: int = 28,
) -> dict:
    df = pd.read_csv(csv_path)
    return train_from_dataframe(
        training_df=df,
        model_type=model_type,
        max_history_days=max_history_days,
        test_days=test_days,
    )


if __name__ == "__main__":
    input_csv = DATA_DIR / "raw" / "menu_items_training.csv"

    if not input_csv.exists():
        raise FileNotFoundError(
            f"No existe el CSV de entrada: {input_csv}. "
            "Genera antes el dataset base desde menu_items_training."
        )

    metadata = train_from_csv(
        csv_path=input_csv,
        model_type="rf",
        max_history_days=120,
        test_days=28,
    )

    print("Modelo entrenado correctamente")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
