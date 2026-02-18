"""API endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "veripost"


@pytest.mark.asyncio
async def test_list_posts_empty(client):
    response = await client.get("/api/v1/posts/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["posts"] == []
