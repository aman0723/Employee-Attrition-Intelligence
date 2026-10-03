"""Descriptive, domain-informed HR analytics summaries and visualization generator."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.data import ROOT, DATA_PATH, load_and_validate


def main():
    df, val_summary = load_and_validate()
    out = ROOT / "reports"
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette=["#0284c7", "#f43f5e"])

    df["AttritionFlag"] = (df["Attrition"] == "Yes").astype(int)

    summary = {
        "records": int(len(df)),
        "overall_attrition_rate": float(df["AttritionFlag"].mean()),
        "attrition_count": int(df["AttritionFlag"].sum()),
        "retained_count": int((df["AttritionFlag"] == 0).sum()),
        "categorical_rates": {},
        "department_analysis": {},
        "performance_breakdown": {},
    }

    # Analyze key categorical drivers
    columns_to_analyze = [
        "Department", "JobRole", "OverTime", "BusinessTravel",
        "JobSatisfaction", "WorkLifeBalance", "EnvironmentSatisfaction",
        "PerformanceRating", "JobInvolvement"
    ]

    for col in columns_to_analyze:
        grouped = df.groupby(col, observed=True)["AttritionFlag"].agg(["count", "mean"]).reset_index()
        grouped.columns = ["value", "count", "attrition_rate"]
        summary["categorical_rates"][col] = [
            {"value": str(r.value), "count": int(r.count), "attrition_rate": float(r.attrition_rate)}
            for r in grouped.itertuples(index=False)
        ]

    # Department analysis with avg salary & satisfaction
    dept_grp = df.groupby("Department").agg({
        "AttritionFlag": ["count", "mean"],
        "MonthlyIncome": "mean",
        "SatisfactionIndex": "mean",
        "PerformanceBenefitIndex": "mean"
    }).reset_index()
    
    summary["department_analysis"] = [
        {
            "department": str(row[("Department", "")]),
            "headcount": int(row[("AttritionFlag", "count")]),
            "attrition_rate": float(row[("AttritionFlag", "mean")]),
            "avg_salary": float(row[("MonthlyIncome", "mean")]),
            "avg_satisfaction": float(row[("SatisfactionIndex", "mean")]),
        }
        for _, row in dept_grp.iterrows()
    ]

    # Tenure Bands analysis
    df["TenureBand"] = pd.cut(
        df["YearsAtCompany"],
        bins=[-1, 1, 3, 5, 10, 50],
        labels=["0-1 yrs", "2-3 yrs", "4-5 yrs", "6-10 yrs", "11+ yrs"]
    )
    tenure_grp = df.groupby("TenureBand", observed=False)["AttritionFlag"].agg(["count", "mean"]).reset_index()
    summary["tenure_bands"] = [
        {"band": str(r.TenureBand), "count": int(r.count), "attrition_rate": float(r.mean)}
        for r in tenure_grp.itertuples(index=False) if r.count > 0
    ]

    (out / "eda_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Generate visual charts for report & dashboard
    chart_definitions = [
        ("Department", "Historical Attrition Rate by Department", "attrition_by_department.png", "#2563eb"),
        ("JobRole", "Historical Attrition Rate by Job Role", "attrition_by_role.png", "#7c3aed"),
        ("OverTime", "Attrition Rate: OverTime vs Regular Hours", "attrition_by_overtime.png", "#ef4444"),
        ("TenureBand", "Attrition Probability Across Company Tenure Bands", "attrition_by_tenure.png", "#059669"),
        ("JobSatisfaction", "Attrition Rate by Job Satisfaction Score", "attrition_by_satisfaction.png", "#0284c7"),
        ("WorkLifeBalance", "Attrition Rate by Work-Life Balance Rating", "attrition_by_work_life.png", "#d97706"),
    ]

    for col, title, fname, bar_color in chart_definitions:
        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        order = list(df[col].value_counts().index) if col != "TenureBand" else ["0-1 yrs", "2-3 yrs", "4-5 yrs", "6-10 yrs", "11+ yrs"]
        sns.barplot(data=df, x=col, y="AttritionFlag", order=order, color=bar_color, errorbar=None, ax=ax)
        ax.set(title=title, xlabel="", ylabel="Observed Attrition Rate")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        ax.tick_params(axis="x", labelrotation=25)
        fig.tight_layout()
        fig.savefig(figures / fname, dpi=160)
        plt.close(fig)

    print("[OK] EDA and Department analytics summaries successfully updated!")


if __name__ == "__main__":
    main()
