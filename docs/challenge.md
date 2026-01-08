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