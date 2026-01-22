"""Tests for request validation logging.

These tests verify that 422 validation errors are logged with context.
"""

import logging

from fastapi.testclient import TestClient

from xscanner.server.server import app


def test_register_missing_extraction_id_logs_warning(caplog):
    client = TestClient(app)

    with caplog.at_level(logging.WARNING, logger="Server"):
        response = client.post(
            "/register",
            json={
                # Missing: extraction_id
                "structured_data": {
                    "SerialNumber": "123",
                    "Metal": "Gold",
                }
            },
        )

    assert response.status_code == 422

    messages = [record.getMessage() for record in caplog.records]
    assert any("Request validation failed (422)" in message for message in messages)
    assert any("POST /register" in message for message in messages)


def test_register_invalid_extraction_id_uuid_returns_422_and_logs_warning(caplog):
    client = TestClient(app)

    with caplog.at_level(logging.WARNING, logger="Server"):
        response = client.post(
            "/register",
            json={
                "extraction_id": "not-a-uuid",
                "structured_data": {
                    "SerialNumber": "123",
                    "Metal": "Gold",
                },
            },
        )

    assert response.status_code == 422

    messages = [record.getMessage() for record in caplog.records]
    assert any("Request validation failed (422)" in message for message in messages)
    assert any("POST /register" in message for message in messages)
