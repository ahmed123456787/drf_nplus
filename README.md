# drf-nplus

A DRF serializer-aware N+1 query detector for Django.

Unlike a generic query counter, `drf-nplus` attributes each SQL query to the
serializer field that triggered it *and suggests the ORM fix*:

```
[drf-nplus] GET /posts/ → 201 queries in 340.2ms | 2 repeated SQL templates (possible N+1)
  PostSerializer.author: 100 queries  ← possible N+1 — add .select_related("author")
  PostSerializer.tags: 100 queries  ← possible N+1 — add .prefetch_related("tags")
  PostSerializer: 1 queries
```

## Install

```bash
pip install drf-nplus
```

## Integrate

Add the middleware to your Django `settings.py`:

```python
MIDDLEWARE = [
    # ...
    "drf_nplus.QueryCountMiddleware",
]
```

That's it. On every request the middleware logs a per-field query report and
sets these response headers:

- `X-DRF-Queries` — total query count
- `X-DRF-Query-Time-Ms` — wall time spent in `get_response`
- `X-DRF-NPlus-Fields` — comma-joined serializer field paths flagged as N+1

## Configure

All settings are optional. Defaults shown:

```python
DRF_NPLUS = {
    "ENABLED": True,             # gate the middleware; typically set to DEBUG
    "LOGGER": "drf_nplus",       # standard `logging` logger name
    "LOG_LEVEL": "WARNING",      # level used to emit the report
    "THRESHOLD": 2,              # ≥ N identical queries from one field = N+1
    "IGNORE_PATHS": (),          # prefixes to skip, e.g. ("/admin/", "/static/")
    "RESPONSE_HEADERS": True,    # set the X-DRF-* headers
}
```

Wire the logger through your `LOGGING` config to route reports wherever you
already send logs:

```python
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "drf_nplus": {"handlers": ["console"], "level": "WARNING"},
    },
}
```

## Use in tests

Installing `drf-nplus` auto-registers a pytest plugin. Two ways to guard tests:

**Per-test marker:**

```python
import pytest

@pytest.mark.no_nplus
def test_post_list_is_efficient(db):
    client.get("/posts/")

# Or with a custom threshold
@pytest.mark.no_nplus(threshold=5)
def test_moderate(db): ...
```

**Suite-wide:** `pytest --nplus-strict` (applies the guard to every test).

**Manual context manager** (for finer control):

```python
from drf_nplus.testing import assert_no_nplus
from blog.serializers import PostSerializer
from blog.models import Post

def test_post_list_is_efficient(db):
    qs = Post.objects.select_related("author").prefetch_related("tags")
    with assert_no_nplus():
        PostSerializer(qs, many=True).data
```

All three raise `drf_nplus.NPlusOneDetected` (an `AssertionError` subclass)
with the offending field paths, SQL, and suggested fix.

## How it works

- `patches.install()` wraps `rest_framework.serializers.Serializer.to_representation`
  to push the current field name onto a `ContextVar` stack for the duration
  of `get_attribute` / `to_representation`.
- The middleware attaches an `execute_wrapper` to every configured database
  connection. When a query fires, the current stack path is snapshotted and
  attributed to that field.
- `ContextVar` (not `threading.local`) so it behaves correctly under async
  views.

## Example project

This repo ships a `blog/` app that demonstrates the problem:

```bash
python manage.py migrate
python manage.py shell < seed.py
python manage.py runserver

# Unoptimized — ~201 queries
curl -s http://127.0.0.1:8000/posts/ > /dev/null
# Optimized — ~3 queries
curl -s http://127.0.0.1:8000/posts-optimized/ > /dev/null
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
