# Exploratory analysis findings

Run `python -m src.analyze` to recreate the JSON summary and plots in `reports/`. Rates below are historical proportions in the supplied fictional sample; they are descriptive associations, not employee-level forecasts or causal explanations.

- Overall, 237 of 1,470 rows (16.1%) carry the attrition label.
- Overtime group: 127/416 (30.5%) labeled attrition, compared with 110/1,054 (10.4%) without overtime.
- Job satisfaction: rates are 22.8% for score 1 (n=289), 16.4% for 2 (n=280), 16.5% for 3 (n=442), and 11.3% for 4 (n=459). This association is not a causal estimate.
- Work-life balance score 1 has 31.3% attrition (n=80); the small group size makes that estimate less stable. Scores 2, 3, and 4 are 16.9%, 14.2%, and 17.6%, so a simple monotonic points rule would misrepresent this sample.
- Tenure bands: 0–1 years 34.9% (n=215), 2–3 years 18.4% (n=255), 4–5 years 13.1% (n=306), 6–10 years 12.3% (n=448), and 11+ years 8.1% (n=246). The sample has no observation dates, so these are not survival or time-to-exit estimates.
- Role differences vary substantially and some roles have few records. Avoid treating group rates as individual reasons or comparing teams without context.

These patterns motivate checking combinations in a model, but do not validate interventions. The dataset does not measure lateness, work progress, business benefit, or employees' stated reasons for leaving.
