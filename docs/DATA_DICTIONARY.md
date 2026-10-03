# Data dictionary and feature policy

## Target

`Attrition`: historical label (`Yes` / `No`). It identifies the outcome in the supplied sample. It does not encode why or when a person left.

## Model inputs shown in the dashboard

The model and estimator form use the same eight inputs. No hidden model inputs are silently filled with average or most-common values.

| Input | Dataset scale / meaning |
|---|---|
| `OverTime` | Whether overtime is recorded: Yes / No |
| `JobSatisfaction` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `WorkLifeBalance` | 1 Bad, 2 Good, 3 Better, 4 Best |
| `JobInvolvement` | 1 Low, 2 Medium, 3 High, 4 Very High |
| `YearsAtCompany` | Years at the company (sample range 0–37) |
| `YearsSinceLastPromotion` | Years since last promotion (sample range 0–15) |
| `MonthlyIncome` | Dataset income value (sample range 1,009–19,973; currency/unit unspecified) |
| `BusinessTravel` | Non-Travel, Travel_Rarely, Travel_Frequently; dashboard shows readable labels |

Numeric survey scales remain numeric inputs to the model but are displayed as their dataset labels. The backend requires all eight fields and checks values against training-sample ranges/categories.

## Available but not used as model inputs

The CSV also contains role, department, experience and other survey fields. This dashboard does not use them as hidden defaults: using only the fields HR sees makes each demonstrated prediction easier to reason about. Direct identifier (`EmployeeNumber`), constants (`EmployeeCount`, `Over18`, `StandardHours`), and demographic fields (`Age`, `Gender`, `MaritalStatus`, `Education`, `EducationField`) are also excluded.

## Not available in the data

No punctuality/late arrival, current task progress, documented business impact, exit interview, or employee-stated reason fields are present. Do not infer these values or treat performance ratings as a measure of company benefit.
