"""
Week 1 MVP: count SQL queries per request and log the total.

This is the plumbing for the N+1 detector — no serializer awareness yet.
Week 2 will attach a serializer field-path stack so each query can be
attributed to the field that triggered it.
"""

import time
from collections import Counter

from django.db import connection


class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        queries = []

        def tracker(execute, sql, params, many, context):
            queries.append(sql)
            return execute(sql, params, many, context)

        start = time.perf_counter()
        with connection.execute_wrapper(tracker):
            response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        duplicates = self._count_duplicates(queries)
        summary = (
            f"[drf-nplus] {request.method} {request.path} "
            f"→ {len(queries)} queries in {elapsed_ms:.1f}ms"
        )
        if duplicates:
            summary += f" | {duplicates} repeated SQL templates (possible N+1)"
        print(summary)

        response["X-DRF-Queries"] = str(len(queries))
        return response

    @staticmethod
    def _count_duplicates(queries):
        """Rough duplicate detector: exact SQL match, ignoring parameter values."""
        counts = Counter(queries)
        return sum(1 for _, n in counts.items() if n > 1)
