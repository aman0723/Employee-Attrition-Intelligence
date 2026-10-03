# RetentionIntel: Enterprise Employee Attrition & Flight Risk Intelligence System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3%2B-orange.svg)](https://scikit-learn.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://palletsprojects.com/p/flask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **An End-to-End Predictive Machine Learning & Decision-Support System designed to identify voluntary employee turnover risks, protect high-impact talent, and prevent six-figure replacement costs through prescriptive HR interventions.**

---

## 📌 Executive Summary & Business Problem

When a valued employee leaves unexpectedly, organizations incur severe business and operational damage:
1. **Replacement & Hiring Costs:** Replacing a mid-to-senior professional costs between **50% to 150% of their annual salary** in recruitment agency fees, advertising, onboarding, and signing bonuses.
2. **Operational Project Disruption:** Unplanned departures cause knowledge loss, stalled project roadmaps, and team overload.
3. **The "Regrettable vs. Non-Regrettable" Attrition Dilemma:** Traditional HR models treat all turnover equally. In reality, **a Star Performer leaving is a crisis ("Regrettable Loss")**, while an underperformer leaving can often be absorbed naturally.

**RetentionIntel** solves this by combining **calibrated machine learning**, **explainable root-cause diagnosis**, the **9-Box Talent Flight Matrix**, and a **"What-If" Retention Simulator** to help People Leaders intervene proactively *before* formal resignation.

---

## 🚀 Key System Architecture & Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                   RETENTIONINTEL SYSTEM ARCHITECTURE                   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     DATA & ML PIPELINE (src/)   │       │   DECISION INTELLIGENCE (UI)    │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ • IBM HR Dataset (1,470 records)│       │ • Executive Workforce KPIs      │
│ • Domain Feature Engineering:   │       │   (Turnover loss, dept rates)   │
│   - TenurePromotionRatio        │       │ • Interactive Flight Risk Engine│
│   - PerformanceBenefitIndex     │       │ • 9-Box Talent Flight Matrix    │
│   - SatisfactionIndex           │       │ • Root Causes & Retention Anchor│
│   - IncomePerLevel (Pay Equity) │       │ • Prescriptive Action Checklist │
│ • 5-Fold Stratified Benchmark   │       │ • Live "What-If" Counterfactual │
│ • Sigmoid Platt Calibration     │       │   Intervention Simulator        │
│ • Decision Threshold Tuning     │       │ • Department Analytics Tables   │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

### 1. Domain Feature Engineering
* **`TenurePromotionRatio`**: Measures career promotion stagnation relative to tenure.
* **`PerformanceBenefitIndex`**: Combines `PerformanceRating` $\times$ `JobInvolvement` to quantify organizational value.
* **`SatisfactionIndex`**: Holistic composite satisfaction across job, environment, relationship, and work-life balance surveys.
* **`IncomePerLevel`**: Internal pay equity metric measuring salary deviation from grade benchmark medians.

### 2. Multi-Model Benchmark & Calibration
We benchmarked 3 industry classifiers across 5-fold Stratified Cross-Validation on the 80% training partition:

| Model Architecture | 5-Fold CV ROC-AUC | 5-Fold CV PR-AUC | Holdout Precision | Holdout Recall | Holdout F1 | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Calibrated)** | **0.833** | **0.624** | **52.9%** | **57.4%** | **0.551** | 🏆 **Champion** |
| **Gradient Boosting Classifier** | 0.816 | 0.599 | 48.1% | 51.0% | 0.495 | Candidate |
| **Random Forest Classifier** | 0.813 | 0.567 | 46.8% | 53.2% | 0.498 | Candidate |

* **Calibrated Probabilities:** Uses Sigmoid Platt scaling to ensure predicted probabilities reflect true empirical odds.
* **Optimal Threshold Tuning:** Decision threshold tuned to **0.300** to balance high recall with low false alarms, doubling precision over baseline naive cutoffs.

### 3. Executive 9-Box Talent Flight Matrix
Classifies employees into 4 distinct retention quadrants based on **Employee Value (0-100)** vs **Flight Risk (0-100%)**:
* 🚨 **CRITICAL FLIGHT RISK:** High Impact Star + High Flight Risk *(Immediate C-suite & People Partner retention intervention)*.
* ⚠️ **PRIORITY RETENTION WATCH:** High Impact Star + Moderate Risk *(Compensation calibration & promotion path check)*.
* 🌟 **SAFE CORE CHAMPION:** High Impact Star + Low Risk *(Stable organizational pillar; leadership growth tracks)*.
* 🔄 **MANAGED TRANSITION:** Low Contributor + High Risk *(Non-regrettable attrition; allow natural exit without counter-offers)*.

### 4. Interactive "What-If" Counterfactual Simulator
Enables HR leaders to test retention hypotheses and quantify ROI before committing budgets:
* *"What if we eliminate overtime shifts?"*
* *"What if we offer a 15% salary correction?"*
* *"What if we fast-track promotion?"*
* **Output:** Quantifies the **Risk Reduction Percentage** and **Estimated Capital Loss Prevented ($)** in real time.

---

## 🛠️ Tech Stack & Requirements

* **Language & Core:** Python 3.10+
* **Data Processing & Feature Engineering:** `pandas`, `numpy`
* **Machine Learning & Evaluation:** `scikit-learn`, `joblib`
* **Backend API:** `Flask` (RESTful architecture)
* **Visualizations:** `matplotlib`, `seaborn`, `Chart.js`
* **Frontend:** Modern HTML5, Responsive CSS3 (Glassmorphism design system), Vanilla JavaScript (ES6+)
* **Testing:** `unittest` automated test suite

---

## 💻 How to Run Locally

### Option A: One-Click Windows Batch Runner (Recommended)
Double-click `RUN_ON_WINDOWS.bat` in the root folder. It will:
1. Initialize the Python virtual environment (`.venv`).
2. Install all required dependencies from `requirements.txt`.
3. Train and benchmark the machine learning models.
4. Generate analytical summaries and charts under `reports/`.
5. Launch the local Flask server and automatically open `http://127.0.0.1:5000` in your default browser.

### Option B: Manual Command Line Execution
```bash
# 1. Clone repository & create virtual environment
git clone https://github.com/your-username/Employee-Attrition-Intelligence.git
cd Employee-Attrition-Intelligence
python -m venv .venv

# 2. Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train model & generate reports
python -m src.train
python -m src.analyze

# 5. Run automated test suite
python -m unittest tests/test_pipeline.py

# 6. Launch web dashboard
python -m src.app
```
Now navigate to **`http://127.0.0.1:5000`** in your browser.

---

## 📂 Project Directory Structure

```
Employee-Attrition-Intelligence/
├── data/
│   └── raw/
│       └── WA_Fn-UseC_-HR-Employee-Attrition.csv  # 1,470 IBM HR benchmark rows
├── docs/
│   ├── DATA_DICTIONARY.md                         # Feature meanings & definitions
│   ├── DATA_SOURCE.md                             # Dataset provenance & license
│   ├── EDA_FINDINGS.md                            # Descriptive statistics summary
│   └── VALIDATION.md                              # Evaluation protocol documentation
├── frontend/
│   ├── index.html                                 # Executive dashboard UI
│   ├── styles.css                                 # Modern responsive design system
│   └── app.js                                     # Interactive charts & simulator logic
├── models/
│   └── attrition_model.joblib                     # Serialized champion pipeline bundle
├── reports/
│   ├── data_validation.json                       # Schema validation metadata
│   ├── eda_summary.json                           # Department & tenure distributions
│   ├── model_evaluation.json                      # Full cross-validation report
│   └── figures/                                   # High-resolution benchmark plots
│       ├── confusion_matrix.png
│       ├── feature_importance.png
│       ├── model_comparison.png
│       ├── attrition_by_department.png
│       └── attrition_by_overtime.png
├── src/
│   ├── __init__.py
│   ├── app.py                                     # Flask RESTful API & simulation engine
│   ├── data.py                                    # Data loader & domain feature engineering
│   ├── train.py                                   # Multi-model benchmarking & calibration
│   └── analyze.py                                 # Visualizations & EDA generator
├── tests/
│   └── test_pipeline.py                           # Automated unit & integration tests
├── requirements.txt                               # Pinned library dependencies
├── RUN_ON_WINDOWS.bat                             # 1-Click execution script
└── README.md                                      # Documentation & portfolio overview
```

---

## 📄 Resume Bullet Points (Copy & Paste for Placements & Internships)

You can feature this project on your resume under **Projects** using these impact-driven bullets:

* **Enterprise Employee Attrition & Retention Intelligence Suite** *(Python, Scikit-Learn, Pandas, Flask, Chart.js)*
  * Engineered an end-to-end predictive machine learning and decision-support pipeline on a 1,470-record enterprise workforce dataset to identify voluntary turnover flight risks.
  * Extracted domain-specific features (Career Stagnation Ratio, Pay Equity Index, Performance-Benefit Index) and benchmarked Logistic Regression, Random Forest, and Gradient Boosting via 5-Fold Stratified Cross-Validation.
  * Implemented Sigmoid probability calibration and cost-benefit threshold optimization, achieving **0.833 CV ROC-AUC** and **52.9% holdout precision**, reducing false positive alert fatigue by over 45%.
  * Built an executive Flask web dashboard featuring a **9-Box Talent Flight Matrix** to differentiate high-impact star talent from non-regrettable attrition and designed an interactive **"What-If" Counterfactual Simulator** that quantifies capital loss avoided through targeted HR interventions.
  * Achieved 100% test pass rate across data validation, scoring algorithms, and RESTful API endpoints using Python `unittest`.

---

## ⚖️ Ethical AI & Limitations Policy

* **Responsible AI:** Direct demographic attributes (`Age`, `Gender`, `MaritalStatus`) were intentionally excluded from the model feature vector to mitigate algorithmic bias and uphold EEOC compliance standards.
* **Decision Support, Not Automated Decisions:** This tool serves as an early-warning signal for human HR managers to initiate empathetic career conversations, not an automated employment termination or performance review mechanism.

---

## 📜 License
Distributed under the MIT License. Open for educational, academic, and portfolio demonstration use.
