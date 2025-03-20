import pytest
import os
from src.pytest_metrics.metrics import MetricsReport

qase_report = MetricsReport()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if call.when == "call":
        qase_report.collect_result(item, rep)
        item.test_result = rep


@pytest.hookimpl(trylast=True, hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    try:
        if worker_id:
            qase_report.save_to_temp_file(worker_id)
        else:
            qase_report.load_and_merge_results()
            qase_report.send_to_victoria_metrics()
    except Exception as e:
        session.config.pluginmanager.get_plugin("terminalreporter").write(
            f"\n[Metrics Report] Error: {e}\n"
        )
