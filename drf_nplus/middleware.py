"""
Per-request SQL query counter that attributes each query to the DRF
serializer field path that triggered it.

Pairs with `drf_nplus.patches`, which pushes the current field onto a
ContextVar stack while DRF resolves it. When a query fires, we snapshot the
stack — that's the field path we attribute it to.
"""

import logging
import time
from collections import Counter, defaultdict

from django.db import connections

from . import context, patches, settings as conf


class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = conf.get("ENABLED")
        self.threshold = conf.get("THRESHOLD")
        self.ignore_paths = tuple(conf.get("IGNORE_PATHS"))
        self.send_headers = conf.get("RESPONSE_HEADERS")
        self.logger = logging.getLogger(conf.get("LOGGER"))
        self.log_level = logging.getLevelName(conf.get("LOG_LEVEL"))
        if self.enabled:
            patches.install()

    def __call__(self, request):
        if not self.enabled or request.path.startswith(self.ignore_paths):
            return self.get_response(request)

        queries: list[tuple[str, str | None]] = []

        def tracker(execute, sql, params, many, ctx):
            queries.append((sql, context.current_path()))
            return execute(sql, params, many, ctx)

        start = time.perf_counter()
        with _wrap_all_connections(tracker):
            response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        offenders = self._offenders(queries)
        self._log(request, queries, elapsed_ms, offenders)

        if self.send_headers:
            response["X-DRF-Queries"] = str(len(queries))
            response["X-DRF-Query-Time-Ms"] = f"{elapsed_ms:.1f}"
            if offenders:
                response["X-DRF-NPlus-Fields"] = ",".join(p for p, _, _ in offenders)
        return response

    def _log(self, request, queries, elapsed_ms, offenders):
        header = (
            f"[drf-nplus] {request.method} {request.path} "
            f"→ {len(queries)} queries in {elapsed_ms:.1f}ms"
        )
        duplicates = self._count_duplicates(queries)
        if duplicates:
            header += f" | {duplicates} repeated SQL templates (possible N+1)"
        lines = [header] + [f"  {line}" for line in self._per_field_summary(queries)]
        self.logger.log(self.log_level, "\n".join(lines))

    def _offenders(self, queries):
        by_path: dict[str, list[str]] = defaultdict(list)
        for sql, path in queries:
            if path is None:
                continue
            by_path[path].append(sql)
        offenders = []
        for path, sqls in by_path.items():
            counts = Counter(sqls)
            for sql, n in counts.items():
                if n >= self.threshold:
                    offenders.append((path, n, sql))
        return offenders

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


class _wrap_all_connections:
    """Attach `tracker` to every configured database connection."""

    def __init__(self, tracker):
        self.tracker = tracker
        self._ctxs = []

    def __enter__(self):
        for alias in connections:
            ctx = connections[alias].execute_wrapper(self.tracker)
            ctx.__enter__()
            self._ctxs.append(ctx)
        return self

    def __exit__(self, exc_type, exc, tb):
        for ctx in reversed(self._ctxs):
            ctx.__exit__(exc_type, exc, tb)
