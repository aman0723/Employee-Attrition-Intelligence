"""Data loading, validation, and domain-informed feature engineering pipeline."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
TARGET = "Attrition"

# Core raw features to be utilized by the ML model
RAW_NUMERIC_FEATURES = [
    "MonthlyIncome",
    "PercentSalaryHike",
    "StockOptionLevel",
    "JobLevel",
    "TotalWorkingYears",
    "YearsAtCompany",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
    "YearsInCurrentRole",
    "JobSatisfaction",
    "EnvironmentSatisfaction",
    "RelationshipSatisfaction",
    "WorkLifeBalance",
    "JobInvolvement",
    "PerformanceRating",
    "DistanceFromHome",
    "NumCompaniesWorked",
    "TrainingTimesLastYear",
]

RAW_CATEGORICAL_FEATURES = [
    "Department",
    "JobRole",
    "BusinessTravel",
    "OverTime",
]

# Engineered business features
ENGINEERED_FEATURES = [
    "TenurePromotionRatio",
    "ManagerStabilityRatio",
    "CompanyTenureRatio",
    "SatisfactionIndex",
    "PerformanceBenefitIndex",
    "IncomePerLevel",
]

ALL_NUMERIC_FEATURES = RAW_NUMERIC_FEATURES + ENGINEERED_FEATURES
ALL_CATEGORICAL_FEATURES = RAW_CATEGORICAL_FEATURES
ALL_FEATURES = ALL_NUMERIC_FEATURES + ALL_CATEGORICAL_FEATURES

EXCLUDED_COLUMNS = [
    "EmployeeNumber", "EmployeeCount", "Over18", "StandardHours",
    "DailyRate", "HourlyRate", "MonthlyRate", "Age", "Gender",
    "MaritalStatus", "Education", "EducationField",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds domain-informed HR analytics features."""
    data = df.copy()
    
    # 1. Career stagnation ratio: Years without promotion relative to company tenure
    data["TenurePromotionRatio"] = data["YearsSinceLastPromotion"] / (data["YearsAtCompany"] + 1.0)
    
    # 2. Manager stability ratio: Tenure with current manager relative to company tenure
    data["ManagerStabilityRatio"] = data["YearsWithCurrManager"] / (data["YearsAtCompany"] + 1.0)
    
    # 3. Company loyalty ratio: Portion of career spent at this single organization
    data["CompanyTenureRatio"] = data["YearsAtCompany"] / (data["TotalWorkingYears"] + 1.0)
    
    # 4. Composite employee satisfaction index (1 to 4 scale)
    data["SatisfactionIndex"] = (
        data["JobSatisfaction"] +
        data["EnvironmentSatisfaction"] +
        data["RelationshipSatisfaction"] +
        data["WorkLifeBalance"]
    ) / 4.0
    
    # 5. Employee Value/Benefit index: Combines performance rating with engagement involvement
    data["PerformanceBenefitIndex"] = data["PerformanceRating"] * data["JobInvolvement"]
    
    # 6. Internal pay equity indicator: Salary relative to seniority job level
    data["IncomePerLevel"] = data["MonthlyIncome"] / (data["JobLevel"].clip(lower=1))
    
    return data


def load_and_validate():
    """Loads raw dataset, validates schema, generates engineered features, and writes validation report."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    frame = pd.read_csv(DATA_PATH)
    
    required_raw = set(RAW_NUMERIC_FEATURES + RAW_CATEGORICAL_FEATURES + [TARGET])
    missing_columns = sorted(required_raw - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Required columns missing from raw dataset: {missing_columns}")

    if frame[TARGET].isna().any() or not set(frame[TARGET].unique()).issubset({"Yes", "No"}):
        raise ValueError("Target column 'Attrition' must contain only non-null 'Yes' or 'No' values")

    if frame.empty:
        raise ValueError("Dataset has no records")

    # Add engineered features
    enriched_df = engineer_features(frame)

    # Calculate summary metrics
    summary = {
        "file": str(DATA_PATH.relative_to(ROOT)),
        "rows": int(len(enriched_df)),
        "columns_raw": int(frame.shape[1]),
        "columns_enriched": int(enriched_df.shape[1]),
        "missing_cells": int(enriched_df.isna().sum().sum()),
        "duplicate_rows": int(enriched_df.duplicated().sum()),
        "target_counts": {str(k): int(v) for k, v in enriched_df[TARGET].value_counts().items()},
        "attrition_rate": float((enriched_df[TARGET] == "Yes").mean()),
        "features": {
            "numeric": ALL_NUMERIC_FEATURES,
            "categorical": ALL_CATEGORICAL_FEATURES,
            "engineered": ENGINEERED_FEATURES,
            "excluded": EXCLUDED_COLUMNS,
        },
        "department_distribution": enriched_df["Department"].value_counts().to_dict(),
        "attrition_by_department": enriched_df.groupby("Department")[TARGET].apply(
            lambda s: float((s == "Yes").mean())
        ).to_dict(),
    }

    out = ROOT / "reports" / "data_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return enriched_df, summary


if __name__ == "__main__":
    df, summary = load_and_validate()
    print(f"Dataset loaded successfully: {len(df)} rows, {df.shape[1]} columns")
    print(f"Attrition rate: {summary['attrition_rate']:.2%}")
    print(f"Engineered features added: {ENGINEERED_FEATURES}")
