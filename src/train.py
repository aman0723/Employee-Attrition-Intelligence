"""Multi-model benchmarking, threshold calibration, and evaluation for employee attrition prediction."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, cross_val_predict
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, classification_report, roc_curve, precision_recall_curve
)

from src.data import (
    ROOT, TARGET, RAW_NUMERIC_FEATURES, RAW_CATEGORICAL_FEATURES,
    ENGINEERED_FEATURES, ALL_NUMERIC_FEATURES, ALL_CATEGORICAL_FEATURES,
    load_and_validate, engineer_features
)

SEED = 42


def build_pipeline(estimator):
    """Constructs a scikit-learn preprocessing and estimator pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]), ALL_NUMERIC_FEATURES),
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]), ALL_CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", estimator)])


def extract_feature_importance(pipeline, X_sample):
    """Extracts interpretable global feature importance scores from the pipeline."""
    prep = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["classifier"]
    
    # Extract feature names after encoding
    num_cols = ALL_NUMERIC_FEATURES
    cat_cols = list(prep.named_transformers_["categorical"].named_steps["encoder"].get_feature_names_out(ALL_CATEGORICAL_FEATURES))
    all_feature_names = num_cols + cat_cols

    raw_scores = {}
    if hasattr(model, "feature_importances_"):
        raw_scores = dict(zip(all_feature_names, model.feature_importances_))
    elif hasattr(model, "coef_"):
        raw_scores = dict(zip(all_feature_names, np.abs(model.coef_[0])))
    else:
        return {}

    # Aggregate one-hot encoded categories back to their parent features
    aggregated = {}
    for feat_name, score in raw_scores.items():
        matched_parent = None
        for orig in ALL_CATEGORICAL_FEATURES:
            if feat_name.startswith(orig + "_"):
                matched_parent = orig
                break
        if matched_parent:
            aggregated[matched_parent] = aggregated.get(matched_parent, 0.0) + float(score)
        else:
            aggregated[feat_name] = aggregated.get(feat_name, 0.0) + float(score)

    total = sum(aggregated.values()) or 1.0
    normalized = {k: float(v / total) for k, v in sorted(aggregated.items(), key=lambda x: x[1], reverse=True)}
    return normalized


def main():
    print("=" * 60)
    print("EMPLOYEE ATTRITION INTELLIGENCE: MODEL TRAINING & BENCHMARK")
    print("=" * 60)
    
    df, validation = load_and_validate()
    X = df[ALL_NUMERIC_FEATURES + ALL_CATEGORICAL_FEATURES]
    y = (df[TARGET] == "Yes").astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )

    # 1. Define candidate algorithms for competitive benchmarking
    candidates = {
        "Logistic Regression": build_pipeline(
            LogisticRegression(class_weight="balanced", max_iter=2500, random_state=SEED)
        ),
        "Random Forest": build_pipeline(
            RandomForestClassifier(
                n_estimators=120, max_depth=10, min_samples_leaf=2,
                class_weight="balanced", random_state=SEED
            )
        ),
        "Gradient Boosting": build_pipeline(
            GradientBoostingClassifier(
                n_estimators=80, learning_rate=0.1, max_depth=3,
                subsample=0.9, random_state=SEED
            )
        ),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scoring_metrics = {
        "balanced_accuracy": "balanced_accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "average_precision": "average_precision",
    }

    print("\n[1/5] Running 5-Fold Stratified Cross-Validation Benchmark...", flush=True)
    benchmark_results = {}
    for name, pipe in candidates.items():
        # Using synchronous single job to ensure 100% stability on Windows Python 3.14
        scores = cross_validate(pipe, X_train, y_train, cv=cv, scoring=scoring_metrics, n_jobs=1)
        benchmark_results[name] = {
            m: {
                "mean": float(np.mean(scores[f"test_{m}"])),
                "std": float(np.std(scores[f"test_{m}"])),
            }
            for m in scoring_metrics
        }
        print(f" -> {name:20s} | ROC-AUC: {benchmark_results[name]['roc_auc']['mean']:.3f} | PR-AUC: {benchmark_results[name]['average_precision']['mean']:.3f} | F1: {benchmark_results[name]['f1']['mean']:.3f}", flush=True)

    # Select champion model based on combined ranking (ROC-AUC and Average Precision)
    champion_name = max(
        candidates.keys(),
        key=lambda k: benchmark_results[k]["roc_auc"]["mean"] + benchmark_results[k]["average_precision"]["mean"]
    )
    print(f"\n[2/5] Champion Model Selected: {champion_name}", flush=True)
    champion_pipeline = candidates[champion_name]

    # 2. Probability Calibration
    print("\n[3/5] Applying Isotonic/Sigmoid Probability Calibration...", flush=True)
    try:
        calibrated_model = CalibratedClassifierCV(estimator=champion_pipeline, method="sigmoid", cv=3)
    except TypeError:
        calibrated_model = CalibratedClassifierCV(base_estimator=champion_pipeline, method="sigmoid", cv=3)

    calibrated_model.fit(X_train, y_train)

    # 3. Optimal Threshold Selection on Calibrated Predictions
    train_cal_probs = calibrated_model.predict_proba(X_train)[:, 1]
    
    threshold_grid = np.linspace(0.12, 0.50, 77)
    best_threshold = 0.25
    best_f1 = -1.0
    
    for t in threshold_grid:
        preds = (train_cal_probs >= t).astype(int)
        rec = recall_score(y_train, preds, zero_division=0)
        prec = precision_score(y_train, preds, zero_division=0)
        # Target balanced F1 while maintaining solid retention detection (Recall >= 65%)
        if rec >= 0.65 and prec > 0:
            f1 = 2 * (prec * rec) / (prec + rec)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = float(t)

    print(f" -> Optimal Alert Threshold determined: {best_threshold:.3f} (Training F1: {best_f1:.3f})", flush=True)

    # 4. Fit Champion Pipeline on full training set and evaluate on Holdout
    print("\n[4/5] Evaluating on Untouched Holdout Test Set (20%)...", flush=True)
    champion_pipeline.fit(X_train, y_train)

    holdout_prob = calibrated_model.predict_proba(X_test)[:, 1]
    holdout_pred = (holdout_prob >= best_threshold).astype(int)

    holdout_metrics = {
        "test_rows": int(len(y_test)),
        "attrition_count": int(y_test.sum()),
        "threshold": float(best_threshold),
        "accuracy": float(accuracy_score(y_test, holdout_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, holdout_pred)),
        "precision_attrition": float(precision_score(y_test, holdout_pred, zero_division=0)),
        "recall_attrition": float(recall_score(y_test, holdout_pred, zero_division=0)),
        "f1_attrition": float(f1_score(y_test, holdout_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, holdout_prob)),
        "average_precision": float(average_precision_score(y_test, holdout_prob)),
        "brier_score": float(brier_score_loss(y_test, holdout_prob)),
        "confusion_matrix": confusion_matrix(y_test, holdout_pred).tolist(),
        "classification_report": classification_report(
            y_test, holdout_pred, target_names=["Stayed", "Left"], output_dict=True, zero_division=0
        ),
    }

    print(f" -> Holdout ROC-AUC: {holdout_metrics['roc_auc']:.3f}")
    print(f" -> Holdout Recall:  {holdout_metrics['recall_attrition']:.1%}")
    print(f" -> Holdout Precision: {holdout_metrics['precision_attrition']:.1%}")
    print(f" -> Holdout F1:      {holdout_metrics['f1_attrition']:.3f}")

    # Extract Feature Importances from Champion
    feature_importances = extract_feature_importance(champion_pipeline, X_train)

    # 5. Save Artifacts & Figures
    print("\n[5/5] Generating Visualizations & Persisting Model Bundle...")
    reports_dir = ROOT / "reports"
    figures_dir = reports_dir / "figures"
    models_dir = ROOT / "models"
    figures_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # Compute baseline training and test stats for UI
    bundle = {
        "model": calibrated_model,
        "champion_pipeline": champion_pipeline,
        "champion_name": champion_name,
        "features": {
            "all_numeric": ALL_NUMERIC_FEATURES,
            "raw_numeric": RAW_NUMERIC_FEATURES,
            "engineered": ENGINEERED_FEATURES,
            "categorical": ALL_CATEGORICAL_FEATURES,
        },
        "feature_importances": feature_importances,
        "numeric_ranges": {
            c: [float(X_train[c].min()), float(X_train[c].max())]
            for c in ALL_NUMERIC_FEATURES
        },
        "numeric_medians": {
            c: float(X_train[c].median())
            for c in ALL_NUMERIC_FEATURES
        },
        "categorical_values": {
            c: sorted(X_train[c].dropna().astype(str).unique().tolist())
            for c in ALL_CATEGORICAL_FEATURES
        },
        "baseline_rate": float(y_train.mean()),
        "threshold": float(best_threshold),
        "holdout_metrics": holdout_metrics,
    }
    joblib.dump(bundle, models_dir / "attrition_model.joblib")

    # Generate Figures
    sns.set_theme(style="whitegrid", font="sans-serif")

    # 1. Model Comparison Chart
    fig, ax = plt.subplots(figsize=(8, 4.5))
    comp_df = pd.DataFrame([
        {"Model": m, "ROC-AUC": res["roc_auc"]["mean"], "PR-AUC": res["average_precision"]["mean"], "F1": res["f1"]["mean"]}
        for m, res in benchmark_results.items()
    ])
    comp_melted = comp_df.melt(id_vars="Model", var_name="Metric", value_name="Score")
    sns.barplot(data=comp_melted, x="Model", y="Score", hue="Metric", palette=["#2563eb", "#0d9488", "#f59e0b"], ax=ax)
    ax.set(title="Model Benchmark: Cross-Validation Performance", ylabel="Metric Score (0-1.0)", ylim=(0, 1.0))
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(figures_dir / "model_comparison.png", dpi=160)
    plt.close(fig)

    # 2. Confusion Matrix Heatmap
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    cm = np.array(holdout_metrics["confusion_matrix"])
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Retained (Stayed)", "Attrition (Left)"],
                yticklabels=["Retained (Stayed)", "Attrition (Left)"], ax=ax)
    ax.set(xlabel="Predicted Label", ylabel="Actual Outcome", title=f"Holdout Confusion Matrix ({champion_name})")
    fig.tight_layout()
    fig.savefig(figures_dir / "confusion_matrix.png", dpi=160)
    plt.close(fig)

    # 3. Top Feature Importance Chart
    fig, ax = plt.subplots(figsize=(9, 5))
    top_feats = list(feature_importances.items())[:12]
    top_df = pd.DataFrame(top_feats, columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)
    ax.barh(top_df["Feature"], top_df["Importance"], color="#0284c7")
    ax.set(title="Top 12 Predictive Drivers of Employee Attrition", xlabel="Relative Importance")
    fig.tight_layout()
    fig.savefig(figures_dir / "feature_importance.png", dpi=160)
    plt.close(fig)

    # Save comprehensive evaluation JSON report
    report = {
        "champion_model": champion_name,
        "calibration": "Sigmoid (Platt Scaling)",
        "optimal_threshold": float(best_threshold),
        "cross_validation_benchmark": benchmark_results,
        "holdout_evaluation": holdout_metrics,
        "top_feature_importances": dict(list(feature_importances.items())[:15]),
        "data_validation": validation,
    }
    (reports_dir / "model_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n[OK] Model training and benchmarking completed successfully!")
    print("Artifacts saved to: models/attrition_model.joblib & reports/model_evaluation.json")


if __name__ == "__main__":
    main()
