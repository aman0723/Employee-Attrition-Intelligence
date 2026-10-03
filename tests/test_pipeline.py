"""Automated test suite for data validation, feature engineering, and API endpoints."""
import unittest
import numpy as np
import pandas as pd

from src.data import load_and_validate, engineer_features, ALL_NUMERIC_FEATURES, ALL_CATEGORICAL_FEATURES
from src.app import app, compute_employee_value, evaluate_9box_matrix


class TestAttritionIntelligence(unittest.TestCase):

    def setUp(self):
        self.app_client = app.test_client()

    def test_data_loading_and_features(self):
        """Verifies dataset loads cleanly and engineered features are computed."""
        df, summary = load_and_validate()
        self.assertGreater(len(df), 1000)
        self.assertIn("TenurePromotionRatio", df.columns)
        self.assertIn("SatisfactionIndex", df.columns)
        self.assertIn("PerformanceBenefitIndex", df.columns)
        self.assertIn("IncomePerLevel", df.columns)
        self.assertFalse(df["TenurePromotionRatio"].isna().any())

    def test_employee_value_computation(self):
        """Tests the employee value / benefit scoring algorithm."""
        high_performer = {
            "PerformanceRating": 4,
            "JobInvolvement": 4,
            "JobLevel": 4,
            "TotalWorkingYears": 15,
        }
        val = compute_employee_value(high_performer)
        self.assertGreaterEqual(val["score"], 65.0)
        self.assertEqual(val["tier"], "High Impact (Star Talent)")

        low_performer = {
            "PerformanceRating": 3,
            "JobInvolvement": 1,
            "JobLevel": 1,
            "TotalWorkingYears": 1,
        }
        val_low = compute_employee_value(low_performer)
        self.assertLess(val_low["score"], 45.0)

    def test_9box_matrix_evaluation(self):
        """Tests talent matrix classification for critical vs non-regrettable attrition."""
        critical = evaluate_9box_matrix(value_score=75.0, risk_prob=0.68)
        self.assertEqual(critical["quadrant"], "CRITICAL FLIGHT RISK")

        safe = evaluate_9box_matrix(value_score=80.0, risk_prob=0.15)
        self.assertEqual(critical["urgency"], "High Priority")
        self.assertEqual(safe["quadrant"], "SAFE CORE CHAMPION")

    def test_api_summary_endpoint(self):
        """Verifies /api/summary returns 200 and expected schema."""
        res = self.app_client.get("/api/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("records", data)
        self.assertIn("overall_attrition_rate", data)
        self.assertIn("model_status", data)

    def test_api_predict_endpoint(self):
        """Verifies prediction endpoint returns calibrated probability and root causes."""
        sample_payload = {
            "Department": "Research & Development",
            "JobRole": "Research Scientist",
            "JobLevel": 3,
            "MonthlyIncome": 6500,
            "OverTime": "Yes",
            "PerformanceRating": 4,
            "JobInvolvement": 3,
            "JobSatisfaction": 2,
            "EnvironmentSatisfaction": 2,
            "RelationshipSatisfaction": 3,
            "WorkLifeBalance": 1,
            "YearsAtCompany": 6,
            "YearsSinceLastPromotion": 4,
            "YearsWithCurrManager": 2,
            "YearsInCurrentRole": 3,
            "TotalWorkingYears": 10,
            "PercentSalaryHike": 12,
            "StockOptionLevel": 0,
            "BusinessTravel": "Travel_Rarely",
            "DistanceFromHome": 10,
            "NumCompaniesWorked": 2,
            "TrainingTimesLastYear": 2,
        }
        res = self.app_client.post("/api/predict", json=sample_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("probability", data)
        self.assertIn("risk_tier", data)
        self.assertIn("root_causes", data)
        self.assertIn("recommended_actions", data)
        self.assertGreater(len(data["recommended_actions"]), 0)

    def test_api_simulate_endpoint(self):
        """Verifies what-if intervention simulator calculates risk delta."""
        record = {
            "Department": "Sales",
            "JobRole": "Sales Executive",
            "JobLevel": 2,
            "MonthlyIncome": 4500,
            "OverTime": "Yes",
            "PerformanceRating": 3,
            "JobInvolvement": 3,
            "JobSatisfaction": 2,
            "EnvironmentSatisfaction": 2,
            "RelationshipSatisfaction": 2,
            "WorkLifeBalance": 1,
            "YearsAtCompany": 5,
            "YearsSinceLastPromotion": 3,
            "YearsWithCurrManager": 1,
            "YearsInCurrentRole": 3,
            "TotalWorkingYears": 7,
            "PercentSalaryHike": 11,
            "StockOptionLevel": 0,
            "BusinessTravel": "Travel_Frequently",
            "DistanceFromHome": 15,
            "NumCompaniesWorked": 1,
            "TrainingTimesLastYear": 2,
        }
        res = self.app_client.post("/api/simulate", json={
            "record": record,
            "interventions": {
                "remove_overtime": True,
                "salary_hike_pct": 15,
                "promote_employee": True,
            }
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("simulated_probability", data)
        self.assertGreater(data["baseline_probability"], data["simulated_probability"])
        self.assertGreater(data["relative_risk_reduction_pct"], 0)


if __name__ == "__main__":
    unittest.main()
