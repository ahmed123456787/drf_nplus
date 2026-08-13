"""
Week 2: count SQL queries per request AND attribute each to the serializer
field path that triggered it.

Pairs with `drf_nplus.patches`, which pushes the current field onto a
ContextVar stack while DRF resolves it. When a query fires, we snapshot the
stack — that's the field path we attribute it to.
"""

import time
from collections import Counter, defaultdict

from django.db import connection

from . import context, patches


class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        patches.install()

    def __call__(self, request):
        queries = []

        def tracker(execute, sql, params, many, ctx):
            queries.append((sql, context.current_path()))
            return execute(sql, params, many, ctx)

        start = time.perf_counter()
        with connection.execute_wrapper(tracker):
            response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        header = (
            f"[drf-nplus] {request.method} {request.path} "
            f"→ {len(queries)} queries in {elapsed_ms:.1f}ms"
        )
        duplicates = self._count_duplicates(queries)
        if duplicates:
            header += f" | {duplicates} repeated SQL templates (possible N+1)"
        print(header, flush=True)

        for line in self._per_field_summary(queries):
            print(f"  {line}", flush=True)

        response["X-DRF-Queries"] = str(len(queries))
        return response

    @staticmethod
    def _count_duplicates(queries):
        counts = Counter(sql for sql, _ in queries)
        return sum(1 for _, n in counts.items() if n > 1)

    @staticmethod
    def _per_field_summary(queries):
        by_path = defaultdict(list)
        for sql, path in queries:
            by_path[path or "(unattributed)"].append(sql)

        lines = []
        for path, sqls in sorted(by_path.items(), key=lambda kv: -len(kv[1])):
            n = len(sqls)
            unique = len(set(sqls))
            marker = "  ← possible N+1" if n > 1 and unique == 1 else ""
            lines.append(f"{path}: {n} queries{marker}")
        return lines
