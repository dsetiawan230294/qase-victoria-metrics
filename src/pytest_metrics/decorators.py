"""
This module provides decorators for integrating Qase TestOps with pytest.

The decorators allow adding metadata such as test IDs, titles, descriptions,
severities, and tags to test functions. Additionally, it supports conditionally
ignoring tests based on environment variables.
"""

import os
from typing import Callable, Union, List, Set
import allure
from qase.pytest import qase

# ENVIRONMENT VARIABLES
EXCLUDED_RUN_ID = os.environ.get("EXCLUDED_RUN_ID")


def qase_ignore() -> Callable:
    """
    Decorator to conditionally ignore a test case in Qase TestOps.

    The test will be ignored if the `QASE_TESTOPS_RUN_ID` environment variable
    is set to one of the predefined values.

    Returns:
        Callable: The wrapped function, potentially ignored in Qase.
    """

    def wrapper(func: Callable) -> Callable:
        if os.environ.get("QASE_TESTOPS_RUN_ID") == EXCLUDED_RUN_ID:
            func = qase.ignore()(func)
        return func

    return wrapper


def qase_id(ids: Union[int, List[int], Set[int]]) -> Callable:
    """
    Decorator to assign Qase TestOps test IDs to a test function.

    Args:
        ids (Union[int, List[int], Set[int]]): A single test ID or multiple test IDs.

    Returns:
        Callable: The wrapped function with assigned test IDs.
    """
    if not isinstance(ids, (list, tuple, set)):
        ids = [ids]

    def wrapper(func: Callable) -> Callable:
        func = qase.id(ids)(func)
        func.__custom_id_suite__ = ids
        return func

    return wrapper


def qase_suite(titles: Union[str, List[str], Set[str]]) -> Callable:
    """
    Decorator to assign a suite title (or multiple suite titles) to a test function.

    Args:
        titles (Union[str, List[str], Set[str]]): A single suite title or multiple titles.

    Returns:
        Callable: The wrapped function with assigned suite titles.
    """
    if not isinstance(titles, (list, tuple, set)):
        titles = [titles]

    def wrapper(func: Callable) -> Callable:
        for title in titles:
            func = qase.suite(title)(func)
        func.__custom_qase_suite__ = titles
        return func

    return wrapper


def qase_title(titles: Union[str, List[str], Set[str]]) -> Callable:
    """
    Decorator to assign a test case title (or multiple titles) to a test function.

    Args:
        titles (Union[str, List[str], Set[str]]): A single title or multiple titles.

    Returns:
        Callable: The wrapped function with assigned titles.
    """
    is_single_title = isinstance(titles, str)

    def wrapper(func: Callable) -> Callable:
        if is_single_title:
            func = allure.title(titles)(func)
            func = qase.title(titles)(func)
        else:
            for title in titles:
                func = qase.title(title)(func)

        func.__custom_qase_title__ = titles
        return func

    return wrapper


def qase_description(description: str) -> Callable:
    """
    Decorator to assign a test case description in Qase TestOps.

    Args:
        description (str): The test case description.

    Returns:
        Callable: The wrapped function with the assigned description.
    """

    def wrapper(func: Callable) -> Callable:
        func = qase.description(description)(func)
        func.__custom_qase_description__ = description
        return func

    return wrapper


def qase_severity(severity: str) -> Callable:
    """
    Decorator to assign a severity level to a test case.

    Args:
        severity (str): The severity level (e.g., "critical", "high", "medium", "low").

    Returns:
        Callable: The wrapped function with the assigned severity.
    """

    def wrapper(func: Callable) -> Callable:
        func = qase.severity(severity)(func)
        func.__custom_qase_severity__ = severity
        return func

    return wrapper


def qase_layer(layer: str) -> Callable:
    """
    Decorator to assign a test layer (e.g., UI, API, Integration) to a test function.

    Args:
        layer (str): The test layer.

    Returns:
        Callable: The wrapped function with the assigned test layer.
    """

    def wrapper(func: Callable) -> Callable:
        func = qase.layer(layer)(func)
        func.__custom_qase_layer__ = layer
        return func

    return wrapper


def qase_fields(fields: dict) -> Callable:
    """
    Decorator to assign custom fields to a test case.

    Args:
        fields (dict): Dictionary of custom fields.

    Returns:
        Callable: The wrapped function with assigned fields.
    """

    def wrapper(func: Callable) -> Callable:
        func = qase.fields(fields)(func)
        func.__custom_qase_fields__ = fields
        return func

    return wrapper


def qase_tags(tags: Union[str, List[str], Set[str]]) -> Callable:
    """
    Decorator to assign tags to a test function.

    Args:
        tags (Union[str, List[str], Set[str]]): A single tag or multiple tags.

    Returns:
        Callable: The wrapped function with assigned tags.
    """

    def wrapper(func: Callable) -> Callable:
        func.__custom_qase_tags__ = tags
        return func

    return wrapper


def qase_attach(file_path: str) -> None:
    """
    Function to attach a file to a Qase TestOps test case.

    Args:
        file_path (str): Path to the file to be attached.
    """
    qase.attach(file_path)
