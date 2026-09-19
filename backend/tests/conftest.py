"""Shared pytest fixtures for the Destiny backend test suite."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient bound to the Destiny FastAPI application."""
    return TestClient(app)
