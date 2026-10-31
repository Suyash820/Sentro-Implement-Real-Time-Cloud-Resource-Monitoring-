import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.detector_service import app, service

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_service_health_endpoint(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentro-ml-detector"
    assert data["model_trained"] is True

def test_service_status_endpoint(client):
    rv = client.get("/status")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "status" in data

from unittest.mock import patch

def test_service_evaluation_cycle(client):
    mock_metrics = {
        "cpu_usage": 15.0,
        "memory_usage": 25.0,
        "network_in_rate": 2000.0,
        "network_out_rate": 1000.0,
        "app_request_rate": 5.0,
        "app_p95_latency": 0.015
    }
    with patch.object(service.collector, "get_latest_metrics_snapshot", return_value=mock_metrics):
        res = service.evaluate_once()
        assert "status" in res
        assert "metrics" in res
        assert "prediction" in res
        assert res["status"] in ["NORMAL", "ANOMALY"]

    # Check metrics endpoint
    rv = client.get("/metrics")
    assert rv.status_code == 200
    assert b"sentro_anomaly_detected" in rv.data
    assert b"sentro_anomaly_score" in rv.data
    assert b"sentro_predictions_total" in rv.data
