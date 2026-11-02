"""Production startup and delivery-token boundaries, using real settings and signatures."""

import secrets
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.report_orders import sign_token, verify_token


@pytest.mark.parametrize("secret", ["dev-report-secret-change-me", "short", "x" * 64])
def test_production_rejects_unsafe_signing_secrets(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_environment="production", report_secret=secret)


def test_production_accepts_independently_generated_secret():
    secret = secrets.token_hex(32)
    settings = Settings(_env_file=None, app_environment="production", report_secret=secret)
    assert settings.report_secret == secret


def test_signed_token_cannot_start_in_the_future():
    secret = secrets.token_hex(32)
    token = sign_token(secret, "r2", "test-order", datetime.now(timezone.utc) + timedelta(days=1))
    assert not verify_token(secret, "r2", "test-order", token, 168)
