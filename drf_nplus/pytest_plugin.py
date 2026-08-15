"""
Pytest plugin — installed automatically as `drf_nplus` via the `pytest11`
entry point in pyproject.toml.

Two entry points for guarding tests:

- `@pytest.mark.no_nplus` (optionally `threshold=N`) on a single test.
- `--nplus-strict` command-line flag applies the guard to every test.

Both wrap the test body in `assert_no_nplus`, raising `NPlusOneDetected`
(an `AssertionError` subclass) on failure.
"""

import pytest

from .testing import assert_no_nplus


def pytest_addoption(parser):
    group = parser.getgroup("drf_nplus")
    group.addoption(
        "--nplus-strict",
        action="store_true",
        default=False,
        help="Fail any test that triggers a DRF N+1 query (as if every test "
        "had @pytest.mark.no_nplus).",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_nplus(threshold=2): fail the test if any serializer field fires "
        "`threshold` or more identical queries.",
    )


@pytest.fixture(autouse=True)
def _drf_nplus_guard(request):
    marker = request.node.get_closest_marker("no_nplus")
    strict = request.config.getoption("--nplus-strict")
    if not marker and not strict:
        yield
        return
    threshold = 2
    if marker and "threshold" in marker.kwargs:
        threshold = marker.kwargs["threshold"]
    with assert_no_nplus(threshold=threshold):
        yield
