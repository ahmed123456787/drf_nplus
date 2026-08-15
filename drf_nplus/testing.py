"""
Test helpers for asserting no N+1 queries fire during a block of code.

Usage in tests:

    from drf_nplus.testing import assert_no_nplus

    def test_post_list_is_efficient():
        with assert_no_nplus():
            PostSerializer(Post.objects.all(), many=True).data
"""

from collections import defaultdict
from contextlib import contextmanager

from django.db import connections

from . import context, patches


class NPlusOneDetected(AssertionError):
    pass


@contextmanager
def assert_no_nplus(threshold: int = 2):
    """
    Fail if any serializer field path fires the same SQL template
    `threshold` or more times.

    `threshold` is inclusive: threshold=2 means "two identical queries
    from the same field is a failure".
    """
    patches.install()

    by_path: dict[str | None, list[str]] = defaultdict(list)

    def tracker(execute, sql, params, many, ctx):
        by_path[context.current_path()].append(sql)
        return execute(sql, params, many, ctx)

    wrappers = [connections[alias].execute_wrapper(tracker) for alias in connections]
    for w in wrappers:
        w.__enter__()
    try:
        yield
    finally:
        for w in reversed(wrappers):
            w.__exit__(None, None, None)

    offenders = []
    for path, sqls in by_path.items():
        if path is None:
            continue
        counts: dict[str, int] = {}
        for sql in sqls:
            counts[sql] = counts.get(sql, 0) + 1
        for sql, n in counts.items():
            if n >= threshold:
                offenders.append((path, n, sql))

    if offenders:
        lines = ["N+1 detected:"]
        for path, n, sql in offenders:
            lines.append(f"  {path}: {n}× {sql[:80]}")
        raise NPlusOneDetected("\n".join(lines))
