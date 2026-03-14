"""Conformance test runner for XPR Python runtime."""

import os
import glob
import pytest
import yaml
from xpr import Xpr, XprError

CONFORMANCE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "conformance", "conformance"
)


def load_all_tests():
    cases = []
    pattern = os.path.join(CONFORMANCE_DIR, "*.yaml")
    for filepath in sorted(glob.glob(pattern)):
        with open(filepath, "r") as f:
            suite = yaml.safe_load(f)
        suite_name = suite.get("suite", os.path.basename(filepath))
        for test in suite.get("tests", []):
            cases.append((suite_name, test))
    return cases


def normalize(value):
    """Normalize numbers: convert int-valued floats to int for comparison."""
    if isinstance(value, float) and value == int(value) and abs(value) < 1e15:
        return int(value)
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    return value


ALL_TESTS = load_all_tests()
TEST_IDS = [f"{s}::{t['name']}" for s, t in ALL_TESTS]


@pytest.mark.parametrize("suite_name,test_case", ALL_TESTS, ids=TEST_IDS)
def test_conformance(suite_name, test_case):
    if test_case.get("skip"):
        pytest.skip(f"Skipped: {test_case['name']}")
    engine = Xpr()
    expression = test_case["expression"]
    context = test_case.get("context") or {}

    if "error" in test_case:
        # Expression should raise an exception
        with pytest.raises(Exception):
            engine.evaluate(expression, context)
    else:
        expected = test_case["expected"]
        result = engine.evaluate(expression, context)
        assert normalize(result) == normalize(expected), (
            f"[{suite_name}] {test_case['name']}\n"
            f"  expr:     {expression}\n"
            f"  expected: {expected!r}\n"
            f"  got:      {result!r}"
        )
