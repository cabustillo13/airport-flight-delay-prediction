# Notes

# Part 1: Model Implementation

## Fix Features Generation

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