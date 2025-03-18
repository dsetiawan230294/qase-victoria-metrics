# Qase-Pytest Metrics Exporter

This project leverages the `qase-pytest` plugin to extract test result data, convert it into metrics, and push it to Victoria Metrics.

## Features
- Collects test execution results using `qase-pytest`
- Formats results into metrics
- Pushes the metrics to Victoria Metrics for monitoring and visualization

## Environment Variables

Before running the tests, set up the following environment variables:

| Variable Name          | Description                                      | Required |
|------------------------|--------------------------------------------------|----------|
| `VICTORIA_URL`        | URL of the Victoria Metrics instance             | Yes       |
| `QASE_TESTOPS_RUN_ID` | Qase TestOps Run ID                              | Yes      |
| `QASE_TESTOPS_PROJECT`| Qase project identifier                          | Yes      |
| `PLATFORM`            | Platform identifier (e.g., OS, environment)      | Yes       |
| `QASE_TESTOPS_API_TOKEN` | API token for Qase integration               | Yes      |
| `EXCLUDED_RUN_ID`     | Run ID to exclude from metrics                   | Yes       |
| `PUSH_TO_VICTORIA`     | Option to Push or Not Push the Result           | Yes       |

## Usage
On a testcase level, import this decators
```python
from pytest_metrics.decorators import qase_id, qase_title, qase_suite, qase_tags
```

To apply the decorators , follow this example :
```python
@qase_id(5189)
@qase_title("User success login, when input email, password, and gauth valid")
@qase_suite("PRO WEB.AUTH.LOGIN")
@qase_tags("ProSpot")
def test_1():
    var = False
    assert_that(var).is_true()
```

To exclude test case from being pushed to Excluded Run Id, follow this example :
```python
@qase_ignore()
```

Modify your `conftest.py` file to integrate with the metrics reporting system:

```python
from pytest_metrics.metrics import MetricsReport
import os

qase_report = MetricsReport()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if call.when == "call":
        qase_report.collect_result(item, rep)
        item.test_result = rep

def pytest_sessionfinish(session, exitstatus):
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    if worker_id:
        qase_report.save_to_temp_file(worker_id)
    else:
        qase_report.load_and_merge_results()
        qase_report.send_to_victoria_metrics()
```

## Installation
1. Install dependencies:
```
pip install qase-victoria-metrics
```
2. Set up the required environment variables.

3. Run your tests:
```
pytest /path/to/file
```

## How It Works
- During test execution, pytest_runtest_makereport collects test results.
- After the test session, results are either saved (for distributed runs) or aggregated.
- The final results are pushed to Victoria Metrics for monitoring.
