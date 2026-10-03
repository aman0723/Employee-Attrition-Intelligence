"""Enterprise HR Attrition Intelligence API & Decision Support Backend."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from src.data import (
    ROOT, DATA_PATH, TARGET, RAW_NUMERIC_FEATURES, RAW_CATEGORICAL_FEATURES,
    ALL_NUMERIC_FEATURES, ALL_CATEGORICAL_FEATURES, engineer_features
)

app = Flask(__name__, static_folder=str(ROOT / "frontend"), static_url_path="")
MODEL_PATH = ROOT / "models" / "attrition_model.joblib"
EVAL_PATH = ROOT / "reports" / "model_evaluation.json"
EDA_PATH = ROOT / "reports" / "eda_summary.json"


def load_model_bundle():
    """Loads trained model bundle, feature definitions, and thresholds."""
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


@app.get("/")
def index():
    return send_from_directory(ROOT / "frontend", "index.html")


@app.get("/figures/<path:filename>")
def serve_figure(filename):
    return send_from_directory(ROOT / "reports" / "figures", filename)


@app.get("/api/summary")
def get_summary():
    """Returns organizational EDA findings, department analytics, and champion ML metrics."""
    df = pd.read_csv(DATA_PATH)
    counts = df[TARGET].value_counts()
    
    eda_data = {}
    if EDA_PATH.exists():
        eda_data = json.loads(EDA_PATH.read_text(encoding="utf-8"))

    eval_data = {}
    if EVAL_PATH.exists():
        eval_data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))

    bundle = load_model_bundle()
    avg_annual_cost_per_exit = 28500  # Benchmark HR replacement cost estimate ($)

    return jsonify({
        "records": int(len(df)),
        "columns": int(df.shape[1]),
        "attrition_count": int(counts.get("Yes", 0)),
        "retained_count": int(counts.get("No", 0)),
        "overall_attrition_rate": float((df[TARGET] == "Yes").mean()),
        "estimated_turnover_loss": int(counts.get("Yes", 0) * avg_annual_cost_per_exit),
        "department_analysis": eda_data.get("department_analysis", []),
        "tenure_bands": eda_data.get("tenure_bands", []),
        "model_status": {
            "ready": bundle is not None,
            "champion_model": eval_data.get("champion_model", "Logistic Regression"),
            "roc_auc": eval_data.get("holdout_evaluation", {}).get("roc_auc", 0.788),
            "precision": eval_data.get("holdout_evaluation", {}).get("precision_attrition", 0.529),
            "recall": eval_data.get("holdout_evaluation", {}).get("recall_attrition", 0.574),
            "f1_score": eval_data.get("holdout_evaluation", {}).get("f1_attrition", 0.551),
            "alert_threshold": eval_data.get("optimal_threshold", 0.300),
        },
        "top_feature_drivers": eval_data.get("top_feature_importances", {}),
    })


def compute_employee_value(record: dict) -> dict:
    """Calculates multidimensional Employee Value/Benefit score (0-100) and tier."""
    perf = float(record.get("PerformanceRating", 3))  # 3 or 4
    involve = float(record.get("JobInvolvement", 2))  # 1 to 4
    job_level = float(record.get("JobLevel", 1))  # 1 to 5
    experience = float(record.get("TotalWorkingYears", 5))

    # Normalized components (0 to 1)
    # Note: IBM dataset only records ratings 3 ('High/Excellent') and 4 ('Outstanding')
    perf_norm = 0.65 if perf <= 3.0 else 1.0
    involve_norm = (involve - 1.0) / 3.0  # 0 to 1
    level_norm = min(job_level / 5.0, 1.0)  # 0 to 1
    exp_norm = min(experience / 25.0, 1.0)  # 0 to 1

    # Weighted composite score
    raw_score = (perf_norm * 35.0) + (involve_norm * 35.0) + (level_norm * 20.0) + (exp_norm * 10.0)
    score = round(max(5.0, min(100.0, raw_score)), 1)

    if score >= 65.0:
        tier = "High Impact (Star Talent)"
        badge_class = "star"
    elif score >= 40.0:
        tier = "Solid Core Contributor"
        badge_class = "solid"
    else:
        tier = "Developing / Low Contributor"
        badge_class = "low"

    return {"score": score, "tier": tier, "badge_class": badge_class}


def evaluate_9box_matrix(value_score: float, risk_prob: float) -> dict:
    """Classifies employee into the 9-Box Talent Flight Matrix."""
    high_value = value_score >= 55.0
    high_risk = risk_prob >= 0.50
    medium_risk = 0.25 <= risk_prob < 0.50

    if high_value and high_risk:
        return {
            "quadrant": "CRITICAL FLIGHT RISK",
            "urgency": "High Priority",
            "color": "danger",
            "description": "High business impact employee with severe turnover probability. Loss will cause severe project disruption and hiring replacement costs.",
            "recommended_stance": "Immediate retention outreach by Executive Leadership & People Partner.",
        }
    elif high_value and medium_risk:
        return {
            "quadrant": "PRIORITY RETENTION WATCH",
            "urgency": "Medium Priority",
            "color": "warning",
            "description": "Valuable contributor showing emerging disengagement or workload stress.",
            "recommended_stance": "Conduct proactive career trajectory and compensation alignment check.",
        }
    elif high_value and not (high_risk or medium_risk):
        return {
            "quadrant": "SAFE CORE CHAMPION",
            "urgency": "Stable",
            "color": "success",
            "description": "High value contributor with strong retention indicators and organizational commitment.",
            "recommended_stance": "Recognize achievements, provide leadership growth tracks, and maintain engagement.",
        }
    elif not high_value and high_risk:
        return {
            "quadrant": "MANAGED EXIT / NON-REGRETTABLE",
            "urgency": "Low Priority",
            "color": "info",
            "description": "Developing or low impact contributor likely to exit. Replacement cost impact is minimal.",
            "recommended_stance": "Evaluate role requirements; manage transition smoothly without costly counter-offers.",
        }
    else:
        return {
            "quadrant": "PERFORMANCE COACHING CANDIDATE",
            "urgency": "Internal Review",
            "color": "neutral",
            "description": "Stable retention risk but employee contribution requires performance development.",
            "recommended_stance": "Establish clear 90-day performance goals and skill enhancement roadmap.",
        }


def extract_root_causes_and_actions(record: dict, probability: float, bundle: dict) -> dict:
    """Generates explainable root causes, retention anchors, and actionable HR recommendations."""
    causes = []
    anchors = []
    recommendations = []

    # Overtime check
    if record.get("OverTime") == "Yes":
        causes.append({
            "factor": "Excessive Overtime Workload",
            "detail": "Consistently working overtime shifts (historically correlates with 3x attrition rate).",
            "severity": "High",
        })
        recommendations.append("Workload Rebalancing: Cap overtime hours and distribute critical deliverables across the team.")
    else:
        anchors.append({
            "factor": "Standard Working Hours",
            "detail": "Standard work schedule maintained without documented overtime burnout.",
        })

    # Career advancement / promotion check
    promo_years = float(record.get("YearsSinceLastPromotion", 0))
    tenure_years = float(record.get("YearsAtCompany", 0))
    if promo_years >= 4.0:
        causes.append({
            "factor": "Career Promotion Stagnation",
            "detail": f"{int(promo_years)} years elapsed without promotion recognition.",
            "severity": "High",
        })
        recommendations.append("Career Progression Review: Initiate fast-track appraisal review or define clear promotion criteria.")
    elif promo_years <= 1.0 and tenure_years > 2:
        anchors.append({
            "factor": "Recent Career Advancement",
            "detail": f"Promoted within the last year, supporting upward career momentum.",
        })

    # Compensation equity check
    income = float(record.get("MonthlyIncome", 5000))
    job_level = float(record.get("JobLevel", 1))
    level_medians = {1: 2800, 2: 5300, 3: 9800, 4: 15500, 5: 19000}
    expected_income = level_medians.get(int(job_level), 5000)
    if income < expected_income * 0.88:
        gap = expected_income - income
        causes.append({
            "factor": "Compensation Below Grade Midpoint",
            "detail": f"Current monthly salary (${int(income):,}) is ${int(gap):,} below benchmark median for Job Level {int(job_level)}.",
            "severity": "Medium",
        })
        recommendations.append(f"Compensation Calibration: Review off-cycle equity adjustment towards the ${int(expected_income):,} benchmark.")
    elif income >= expected_income:
        anchors.append({
            "factor": "Competitive Compensation",
            "detail": f"Salary (${int(income):,}) meets or exceeds grade level benchmark.",
        })

    # Satisfaction check
    job_sat = float(record.get("JobSatisfaction", 3))
    env_sat = float(record.get("EnvironmentSatisfaction", 3))
    if job_sat <= 2:
        causes.append({
            "factor": "Low Job & Role Satisfaction",
            "detail": "Survey indicates discontent with day-to-day role responsibilities and autonomy.",
            "severity": "Medium",
        })
        recommendations.append("Role Alignment Check-in: Schedule 1-on-1 to discuss project ownership and task preferences.")
    elif job_sat >= 3:
        anchors.append({
            "factor": "High Role Satisfaction",
            "detail": "Strong intrinsic engagement with daily tasks and responsibilities.",
        })

    # Work-life balance check
    wlb = float(record.get("WorkLifeBalance", 3))
    if wlb <= 2:
        causes.append({
            "factor": "Compromised Work-Life Harmony",
            "detail": "Reported poor work-life balance, increasing cumulative stress.",
            "severity": "Medium",
        })
        recommendations.append("Flexible Work Options: Offer hybrid/remote schedule options or core-hours flexibility.")

    # Business travel check
    if record.get("BusinessTravel") == "Travel_Frequently":
        causes.append({
            "factor": "High Travel Fatigue",
            "detail": "Frequent business travel schedule adding operational friction.",
            "severity": "Low",
        })
        recommendations.append("Travel Optimization: Shift routine status meetings to virtual conferences to reduce travel frequency.")

    # Stock options anchor
    stock = float(record.get("StockOptionLevel", 0))
    if stock >= 1:
        anchors.append({
            "factor": "Equity Incentive Lock-in",
            "detail": f"Level {int(stock)} stock option vesting creates positive financial retention inertia.",
        })

    # Manager relationship check
    mgr_years = float(record.get("YearsWithCurrManager", 2))
    if mgr_years >= 4:
        anchors.append({
            "factor": "Strong Managerial Continuity",
            "detail": f"{int(mgr_years)} years working under current supervisor fosters psychological safety.",
        })
    elif mgr_years <= 0 and tenure_years >= 2:
        causes.append({
            "factor": "Recent Management Transition",
            "detail": "New reporting relationship; manager changes often precede voluntary flight.",
            "severity": "Low",
        })
        recommendations.append("Manager Onboarding Support: Facilitate alignment check-ins with new reporting manager.")

    # If no specific cause was triggered, provide general guidance
    if not recommendations:
        recommendations.append("Routine Engagement: Continue bi-weekly 1-on-1s and provide recognition for ongoing contributions.")

    return {
        "causes": causes,
        "anchors": anchors,
        "recommendations": recommendations,
    }


def predict_single_record(record: dict, bundle: dict) -> dict:
    """Preprocesses a single record, generates engineered features, and predicts risk."""
    clean_record = {}
    for col in bundle["features"]["raw_numeric"]:
        val = record.get(col, bundle["numeric_medians"].get(col, 1.0))
        try:
            clean_record[col] = float(val)
        except (ValueError, TypeError):
            clean_record[col] = float(bundle["numeric_medians"].get(col, 1.0))

    for col in bundle["features"]["categorical"]:
        valid_vals = bundle["categorical_values"].get(col, [])
        given = record.get(col)
        clean_record[col] = given if given in valid_vals else (valid_vals[0] if valid_vals else "Unknown")

    df_single = pd.DataFrame([clean_record])
    enriched = engineer_features(df_single)
    
    # Predict calibrated probability
    model = bundle["model"]
    prob = float(model.predict_proba(enriched)[0, 1])
    threshold = float(bundle["threshold"])
    
    # Risk Tier classification
    if prob >= 0.60:
        risk_tier = "High"
    elif prob >= 0.30:
        risk_tier = "Medium"
    else:
        risk_tier = "Low"

    # Compute Value score and 9-box position
    val_data = compute_employee_value(clean_record)
    matrix_data = evaluate_9box_matrix(val_data["score"], prob)

    # Compute Root Causes and Actions
    explain_data = extract_root_causes_and_actions(clean_record, prob, bundle)

    # Replacement cost calculation (benchmark: 75% of annual salary)
    monthly_inc = float(clean_record.get("MonthlyIncome", 5000))
    replacement_cost = round(monthly_inc * 12.0 * 0.75)

    return {
        "probability": prob,
        "probability_percentage": round(prob * 100.0, 1),
        "risk_tier": risk_tier,
        "screening_alert": bool(prob >= threshold),
        "threshold": threshold,
        "employee_value": val_data,
        "matrix_evaluation": matrix_data,
        "estimated_replacement_cost": replacement_cost,
        "root_causes": explain_data["causes"],
        "retention_anchors": explain_data["anchors"],
        "recommended_actions": explain_data["recommendations"],
    }


@app.post("/api/predict")
def predict_employee():
    """Predicts attrition risk, talent value tier, root causes, and HR actions."""
    try:
        bundle = load_model_bundle()
        if bundle is None:
            return jsonify({"error": "Model artifact not found. Please run training script first."}), 503

        payload = request.get_json(silent=True) or {}
        result = predict_single_record(payload, bundle)
        result["input_snapshot"] = payload
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.post("/api/simulate")
def simulate_intervention():
    """Simulates the impact of HR retention interventions on attrition probability ('What-If' Analysis)."""
    try:
        bundle = load_model_bundle()
        if bundle is None:
            return jsonify({"error": "Model not available"}), 503

        data = request.get_json(silent=True) or {}
        record = data.get("record", {})
        interventions = data.get("interventions", {})

        # 1. Baseline prediction
        baseline = predict_single_record(record, bundle)

        # 2. Apply interventions
        simulated_record = dict(record)

        # Overtime elimination
        if interventions.get("remove_overtime", False):
            simulated_record["OverTime"] = "No"

        # Compensation hike (e.g. +10%, +15%)
        hike_pct = float(interventions.get("salary_hike_pct", 0.0))
        if hike_pct > 0:
            current_inc = float(simulated_record.get("MonthlyIncome", 5000))
            simulated_record["MonthlyIncome"] = current_inc * (1.0 + (hike_pct / 100.0))
            current_hike = float(simulated_record.get("PercentSalaryHike", 14))
            simulated_record["PercentSalaryHike"] = min(25.0, current_hike + (hike_pct / 2.0))

        # Promotion advancement
        if interventions.get("promote_employee", False):
            simulated_record["YearsSinceLastPromotion"] = 0.0
            current_level = float(simulated_record.get("JobLevel", 1))
            simulated_record["JobLevel"] = min(5.0, current_level + 1.0)

        # Work-life balance boost
        if interventions.get("improve_work_life", False):
            simulated_record["WorkLifeBalance"] = max(3.0, float(simulated_record.get("WorkLifeBalance", 2)) + 1.0)
            simulated_record["JobSatisfaction"] = max(3.0, float(simulated_record.get("JobSatisfaction", 2)) + 1.0)

        # 3. Predict on simulated state
        simulated = predict_single_record(simulated_record, bundle)

        prob_delta = baseline["probability"] - simulated["probability"]
        reduction_pct = (prob_delta / max(0.001, baseline["probability"])) * 100.0
        loss_saved = round(baseline["estimated_replacement_cost"] * max(0.0, prob_delta))

        return jsonify({
            "baseline_probability": baseline["probability"],
            "baseline_tier": baseline["risk_tier"],
            "simulated_probability": simulated["probability"],
            "simulated_tier": simulated["risk_tier"],
            "absolute_reduction_percentage": round(prob_delta * 100.0, 1),
            "relative_risk_reduction_pct": round(max(0.0, reduction_pct), 1),
            "financial_exposure_saved": loss_saved,
            "new_matrix_quadrant": simulated["matrix_evaluation"]["quadrant"],
            "applied_interventions": interventions,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.get("/api/sample_employees")
def sample_employees():
    """Provides pre-configured realistic employee profiles for 1-click interactive evaluation."""
    profiles = [
        {
            "id": "EMP-1042",
            "name": "Aarav Mehta",
            "title": "Senior R&D Research Scientist",
            "department": "Research & Development",
            "persona_summary": "High-Value Technical Star facing severe overtime and promotion bottleneck",
            "data": {
                "Department": "Research & Development",
                "JobRole": "Research Scientist",
                "JobLevel": 3,
                "MonthlyIncome": 6800,
                "OverTime": "Yes",
                "PerformanceRating": 4,
                "JobInvolvement": 3,
                "JobSatisfaction": 2,
                "EnvironmentSatisfaction": 3,
                "RelationshipSatisfaction": 3,
                "WorkLifeBalance": 1,
                "YearsAtCompany": 7,
                "YearsSinceLastPromotion": 5,
                "YearsWithCurrManager": 2,
                "YearsInCurrentRole": 4,
                "TotalWorkingYears": 11,
                "PercentSalaryHike": 12,
                "StockOptionLevel": 0,
                "BusinessTravel": "Travel_Rarely",
                "DistanceFromHome": 14,
                "NumCompaniesWorked": 2,
                "TrainingTimesLastYear": 2,
            }
        },
        {
            "id": "EMP-2108",
            "name": "Priya Sharma",
            "title": "Corporate Sales Executive",
            "department": "Sales",
            "persona_summary": "High Performer experiencing intense travel fatigue and compensation gap",
            "data": {
                "Department": "Sales",
                "JobRole": "Sales Executive",
                "JobLevel": 2,
                "MonthlyIncome": 4400,
                "OverTime": "Yes",
                "PerformanceRating": 3,
                "JobInvolvement": 3,
                "JobSatisfaction": 1,
                "EnvironmentSatisfaction": 2,
                "RelationshipSatisfaction": 2,
                "WorkLifeBalance": 2,
                "YearsAtCompany": 4,
                "YearsSinceLastPromotion": 3,
                "YearsWithCurrManager": 1,
                "YearsInCurrentRole": 3,
                "TotalWorkingYears": 6,
                "PercentSalaryHike": 11,
                "StockOptionLevel": 0,
                "BusinessTravel": "Travel_Frequently",
                "DistanceFromHome": 22,
                "NumCompaniesWorked": 1,
                "TrainingTimesLastYear": 3,
            }
        },
        {
            "id": "EMP-3045",
            "name": "Vikram Singh",
            "title": "Laboratory Technician",
            "department": "Research & Development",
            "persona_summary": "Developing Contributor with low engagement (Non-regrettable transition candidate)",
            "data": {
                "Department": "Research & Development",
                "JobRole": "Laboratory Technician",
                "JobLevel": 1,
                "MonthlyIncome": 2500,
                "OverTime": "Yes",
                "PerformanceRating": 3,
                "JobInvolvement": 1,
                "JobSatisfaction": 1,
                "EnvironmentSatisfaction": 1,
                "RelationshipSatisfaction": 2,
                "WorkLifeBalance": 2,
                "YearsAtCompany": 2,
                "YearsSinceLastPromotion": 1,
                "YearsWithCurrManager": 1,
                "YearsInCurrentRole": 1,
                "TotalWorkingYears": 3,
                "PercentSalaryHike": 13,
                "StockOptionLevel": 0,
                "BusinessTravel": "Non-Travel",
                "DistanceFromHome": 8,
                "NumCompaniesWorked": 3,
                "TrainingTimesLastYear": 1,
            }
        },
        {
            "id": "EMP-4190",
            "name": "Neha Patel",
            "title": "Senior HR Manager",
            "department": "Human Resources",
            "persona_summary": "Core Safe Champion with strong satisfaction, equity stake, and healthy balance",
            "data": {
                "Department": "Human Resources",
                "JobRole": "Human Resources",
                "JobLevel": 4,
                "MonthlyIncome": 14200,
                "OverTime": "No",
                "PerformanceRating": 4,
                "JobInvolvement": 4,
                "JobSatisfaction": 4,
                "EnvironmentSatisfaction": 4,
                "RelationshipSatisfaction": 4,
                "WorkLifeBalance": 3,
                "YearsAtCompany": 10,
                "YearsSinceLastPromotion": 1,
                "YearsWithCurrManager": 6,
                "YearsInCurrentRole": 5,
                "TotalWorkingYears": 16,
                "PercentSalaryHike": 19,
                "StockOptionLevel": 2,
                "BusinessTravel": "Travel_Rarely",
                "DistanceFromHome": 4,
                "NumCompaniesWorked": 1,
                "TrainingTimesLastYear": 4,
            }
        }
    ]
    return jsonify(profiles)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
