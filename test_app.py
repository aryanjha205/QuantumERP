import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.endpoints.signup import pending_signups

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_signup_otp_request_validation():
    # Test signup with invalid request payload schema
    payload = {
        "email": "invalid-email-format",
        "password": "pass",
        "full_name": "Test User",
        "role": "Employee"
    }
    response = client.post("/api/v1/signup/request-otp", json=payload)
    assert response.status_code == 422  # Pydantic validation error

def test_signup_otp_verify_invalid():
    # Test verification with non-existent OTP
    response = client.post("/api/v1/signup/verify-otp?otp=999999")
    assert response.status_code == 400
    assert "Invalid or expired OTP" in response.json()["detail"]
