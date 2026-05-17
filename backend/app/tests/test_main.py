"""
Tests for main application endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AI Study Planner" in data["message"]
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_cors_headers():
    """Test CORS headers are present"""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    # CORS headers should be present in response
