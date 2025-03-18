"""
This module provides functionality to collect and report test execution results
to Qase TestOps and VictoriaMetrics.

It extracts test metadata, formats the results, and sends them to VictoriaMetrics
for further analysis in a Prometheus-compatible format.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
import requests
from _pytest.reports import TestReport
from _pytest.nodes import Item

# Environment variables
VICTORIA_URL: Optional[str] = os.environ.get("VICTORIA_URL")
RUN_ID: Optional[str] = os.environ.get("QASE_TESTOPS_RUN_ID")
PROJECT: Optional[str] = os.environ.get("QASE_TESTOPS_PROJECT")
PLATFORM: Optional[str] = os.environ.get("PLATFORM")
QASE_TOKEN: Optional[str] = os.environ.get("QASE_TESTOPS_API_TOKEN")
PUSH_TO_VICTORIA: Optional[str] = os.environ.get("PUSH_TO_VICTORIA")


class MetricsReport:
    """
    A class for collecting and reporting test execution results to Qase TestOps
    and VictoriaMetrics.

    Attributes:
        run_id (Optional[str]): The test run ID from Qase TestOps.
        platform (Optional[str]): The test execution platform.
        results (List[Dict[str, Any]]): Collected test results.
    """

    def __init__(
        self, run_id: Optional[str] = RUN_ID, platform: Optional[str] = PLATFORM
    ) -> None:
        """
        Initializes the MetricsReport instance.

        Args:
            run_id (Optional[str]): The test run ID from Qase TestOps.
            platform (Optional[str]): The test execution platform.
        """
        self.run_id: Optional[str] = run_id
        self.platform: Optional[str] = platform
        self.results: List[Dict[str, Any]] = []

    def collect_result(self, item: Item, report: TestReport) -> None:
        """
        Collects test execution results and stores them in `results`.

        Args:
            item (Item): The pytest test item.
            report (TestReport): The test execution report.
        """
        if report.when != "call":  # Avoid setup/teardown phases
            return

        case_id = getattr(item.function, "__custom_id_suite__", None)
        suite_title = getattr(item.function, "__custom_qase_suite__", None)
        case_title = getattr(item.function, "__custom_qase_title__", None)
        tags = getattr(item.function, "__custom_qase_tags__", None)

        # Ensure attributes are always lists
        if not isinstance(suite_title, list):
            suite_title = (
                [suite_title] if suite_title is not None else ["UNKNOWN SUITE TITLE"]
            )
        if not isinstance(case_id, list):
            case_id = [case_id] if case_id is not None else ["UNKNOWN CASE ID"]
        if not isinstance(case_title, list):
            case_title = (
                [case_title] if case_title is not None else ["UNKNOWN TESTCASE TITLE"]
            )

        duration = int(report.duration * 1000)
        error_message = None
        stacktrace = None

        if report.outcome == "failed":
            error_message = report.longreprtext.split("\n")[-1]
            stacktrace = report.longreprtext

        max_length = max(len(suite_title), len(case_title))

        for i in range(max_length):
            self.results.append(
                {
                    "run_id": self.run_id,
                    "case_id": (case_id[i] if i < len(case_id) else case_id[-1]),
                    "title": (case_title[i] if i < len(case_title) else case_title[-1]),
                    "suite_title": (
                        suite_title[i] if i < len(suite_title) else suite_title[-1]
                    ),
                    "status": report.outcome,
                    "time_spent_ms": duration,
                    "error": error_message,
                    "stacktrace": stacktrace,
                    "tags": tags,
                    "platform": self.platform,
                }
            )

    def save_to_temp_file(self, worker_id: str) -> None:
        """
        Save worker results to a temporary JSON file.

        Args:
            worker_id (str): The ID of the worker process.
        """
        if not self.results:
            return  # Avoid writing empty files

        filename = f"pytest_worker_{worker_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f)

    def load_and_merge_results(self) -> None:
        """
        Load results from temporary worker files and merge them into `results`.
        """
        for file in os.listdir():
            if file.startswith("pytest_worker_") and file.endswith(".json"):
                with open(file, "r", encoding="utf-8") as f:
                    worker_data = json.load(f)
                    if worker_data:
                        self.results.extend(worker_data)
                os.remove(file)  # Clean up temp file

    def sanitize_result(self) -> None:
        """
        Sanitizes `self.results` to keep only the latest test result per `case_id`.

        If a `case_id` has multiple results with different statuses, the latest "passed"
        result is prioritized over failed ones.

        Returns:
            None: Updates `self.results` in place.
        """
        latest_result: Dict[int, Dict[str, object]] = {}

        for result in self.results:
            case_id = result["case_id"]
            if case_id not in latest_result or result["status"] == "passed":
                latest_result[case_id] = result

        self.results = list(latest_result.values())

    def send_to_victoria_metrics(self) -> Optional[requests.Response]:
        """
        Sends collected test results to VictoriaMetrics in Prometheus format.

        Returns:
            Optional[requests.Response]: The response from the VictoriaMetrics API,
            or None if an error occurred.
        """
        if not self.results:
            print("No test results to send.")
            return None

        self.sanitize_result()

        metrics: List[str] = []
        timestamp = int(time.time())
        push_date = int(time.time() * 1000)

        def format_labels(result: Dict[str, Any]) -> str:
            """
            Formats test case metadata into a Prometheus-compatible label string.

            Args:
                result (Dict[str, Any]): The test execution result dictionary.

            Returns:
                str: A formatted string for Prometheus labels.
            """
            return (
                f'run_id="{result["run_id"]}", '
                f'suite_title="{result["suite_title"]}", '
                f'status="{result["status"]}", push_date="{push_date}", '
                f'title="{result["title"]}", tags="{result["tags"]}", '
                f'platform="{result["platform"]}", case_id="{result["case_id"]}"'
            )

        for result in self.results:
            status_value = "0" if result["status"] == "failed" else "1"
            error_message = result["error"] if result["error"] else "None"
            labels = format_labels(result)

            metrics.append(
                f'test_case_duration_ms{{{labels}}} {result["time_spent_ms"]} {timestamp}'
            )
            metrics.append(f"test_case_status{{{labels}}} {status_value} {timestamp}")

            if result["status"] == "failed":
                failure_labels = f'{labels}, error_message="{error_message}"'
                metrics.append(f"test_case_failures{{{failure_labels}}} 1 {timestamp}")

        payload = "\n".join(metrics)

        if PUSH_TO_VICTORIA == "true":
            try:
                response = payload
                response = requests.post(
                    VICTORIA_URL,
                    data=payload,
                    headers={"Content-Type": "text/plain"},
                    timeout=300,
                )
                print("Response:", response.status_code, response.text)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error sending data to VictoriaMetrics: {e}")
                return None

            return response
        else:
            print("Sending Metrics to Victoria is Disabled")
