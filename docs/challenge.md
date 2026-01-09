# Notes

# Part 1: Model Implementation

## 1.1) Fix Features Generation

### 1) get_period_day

**Why it needs improvement**

The original implementation contains edge case bugs at time boundaries (e.g. 05:00, 11:59, 12:00) and does not correctly handle the midnight crossing for the night period.
This may result in missing or incorrect period assignments for valid flight times.

**What was improved**

Fixed inclusive time boundaries and simplified the logic to correctly classify morning, afternoon, and night periods while preserving the original function signature and output values.

### 2) is_high_season

**Why it needs improvement**

While functionally correct, the original implementation relies on fragile string parsing and duplicated datetime conversions, reducing readability and maintainability.

**What was improved**

Refactored the internal logic to use explicit datetime ranges, improving clarity, robustness, and testability without changing the original behavior or outputs.

---
## 1.2) Why ROC Curve is applied

ROC AUC is used to evaluate the model's discriminative power independently of any specific decision threshold.
By comparing ROC AUC between training and test sets, we can detect overfitting or underfitting and assess whether the model generalizes well.
This comparison helps select the most suitable model for production deployment.

---
## 1.3) Production Readiness Evaluation
In addition to predictive performance, inference latency and model size were evaluated.
These metrics are relevant for production readiness, especially when deploying the model as an API.

In production environments, latency directly impacts user experience and system scalability.
Models with similar ROC AUC scores may not be equally viable if their inference times differ significantly.

Model size was also considered, as it affects cold start times, deployment speed, and infrastructure costs

---
## 1.4) Model Selection

The objective of this project is to predict the probability of flight delays for airport takeoffs and landings.
In this context, correctly identifying delayed flights (class 1) is more critical than maximizing overall accuracy, as false negatives may lead to operational and planning issues.

For this reason, recall for the delayed class and probabilistic discrimination (ROC AUC) were prioritized over accuracy.
Models achieving high accuracy but near-zero recall for delayed flights were discarded, as they fail to meet the business objective despite appearing performant.

Among the evaluated models, only those trained with class balancing and the top 10 most important features achieved a meaningful recall for delayed flights.

While both XGBoost and Logistic Regression achieved similar ROC AUC and recall scores, Logistic Regression was selected due to its significantly lower inference latency, smaller model size, and simpler operational footprint.

These characteristics make it more suitable for production deployment as an API, without sacrificing predictive performance.

| Metric                   | XGBoost (Top 10 + Balanced) | Logistic Regression (Top 10 + Balanced) |
| ------------------------ | --------------------------- | --------------------------------------- |
| Recall (Delay = 1)       | **0.69**                    | **0.69**                                |
| Precision (Delay = 1)    | 0.25                        | 0.25                                    |
| ROC AUC (Test)           | 0.643                       | 0.640                                   |
| Accuracy                 | 0.55                        | 0.55                                    |
| Inference Latency (mean) | 2.33 ms                     | **0.91 ms**                             |
| Model Size               | 0.24 MB                     | **0.0013 MB**                           |
| Interpretability         | Low                         | **High**                                |
| Operational Complexity   | Medium                      | **Low**                                 |
| Production Suitability   | Good                        | **Excellent**                           |

**Note:** When predictive performance is comparable, the simpler and more efficient model was preferred to reduce operational risk and infrastructure costs.

**Model selected: Logistic Regression with top 10 features and class balancing (Regression 2)**

---
## 1.5) Test Data Loading Strategy (test_model.py)

The dataset path is resolved dynamically based on the test file location to ensure portability across different execution environments. Additionally, all columns are loaded as strings (dtype=str) to avoid Pandas type inference issues and mixed-type warnings, keeping data loading deterministic and delegating all type handling to the preprocessing stage.

---
## 1.6) Model tests 

The `DelayModel` implementation has been validated using automated unit tests.

Run the model tests with:
```
make model-test
```

Results:
```
collected 4 items

tests/model/test_model.py ....                                                                                                             [100%]

--------------- generated xml file: /mnt/c/Users/Carlos/Documents/Option - Latam/airport-flight-delay-prediction/reports/junit.xml ---------------

---------- coverage: platform linux, python 3.10.12-final-0 ----------
Name                    Stmts   Miss  Cover
-------------------------------------------
challenge/__init__.py       2      0   100%
challenge/api.py            8      2    75%
challenge/model.py         58      3    95%
-------------------------------------------
TOTAL                      68      5    93%
Coverage HTML written to dir reports/html
Coverage XML written to file reports/coverage.xml
```

Test and coverage artifacts are generated under the reports/ directory (excluded from version control).

---

# Part 2: FastAPI API

## 2.1) Dependency compatibility

FastAPI 0.86 / Starlette 0.20 require AnyIO < 4.

The dependency is pinned explicitly to avoid runtime errors in TestClient.