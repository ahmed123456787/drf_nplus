import logging

import pytest
from django.test import Client


@pytest.mark.django_db
def test_unoptimized_endpoint_reports_nplus_queries(seeded_blog):
    client = Client()
    response = client.get("/posts/")
    assert response.status_code == 200
    # 1 SELECT for posts + 1 per author (5) + 1 per tags prefetch-miss (5) = 11
    n_queries = int(response["X-DRF-Queries"])
    assert n_queries >= 11
    assert "PostSerializer.author" in response["X-DRF-NPlus-Fields"]


@pytest.mark.django_db
def test_optimized_endpoint_stays_flat(seeded_blog):
    client = Client()
    response = client.get("/posts-optimized/")
    assert response.status_code == 200
    n_queries = int(response["X-DRF-Queries"])
    # posts + prefetch tags = 2; select_related author folds into posts SELECT
    assert n_queries <= 3
    assert "X-DRF-NPlus-Fields" not in response


@pytest.mark.django_db
def test_middleware_attribution_flows_to_field_paths(seeded_blog, caplog):
    with caplog.at_level(logging.WARNING, logger="drf_nplus"):
        Client().get("/posts/")
    message = "\n".join(r.getMessage() for r in caplog.records)
    assert "PostSerializer.author" in message
    assert "PostSerializer.tags" in message
    assert "possible N+1" in message
