import pytest
import sys
import os
import requests
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.collector import MetricCollector, METRIC_QUERIES, DEFAULT_METRIC_VALUES

def test_collector_init():
    collector = MetricCollector(prometheus_url="http://prometheus:9090", timeout=3)
    assert collector.prometheus_url == "http://prometheus:9090"
    assert collector.timeout == 3

@patch("requests.get")
def test_query_instant_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {},
                    "value": [1700000000.0, "42.5"]
                }
            ]
        }
    }
    mock_get.return_value = mock_resp

    collector = MetricCollector()
    val = collector.query_instant("up")
    assert val == 42.5

@patch("requests.get")
def test_query_instant_failure_fallback(mock_get):
    mock_get.side_effect = requests.RequestException("Connection refused")
    collector = MetricCollector()
    val = collector.query_instant("up")
    assert val is None

@patch("requests.get")
def test_get_latest_metrics_snapshot(mock_get):
    # Simulate Prometheus returning None for all queries, triggering fallbacks
    mock_get.side_effect = requests.RequestException("Timeout")
    collector = MetricCollector()
    snapshot = collector.get_latest_metrics_snapshot()

    assert isinstance(snapshot, dict)
    assert len(snapshot) == 12
    for key in METRIC_QUERIES.keys():
        assert key in snapshot
        assert isinstance(snapshot[key], (int, float))

@patch("requests.get")
def test_query_range_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {},
                    "values": [
                        [1700000000, "10.0"],
                        [1700000015, "15.5"],
                        [1700000030, "20.2"]
                    ]
                }
            ]
        }
    }
    mock_get.return_value = mock_resp

    collector = MetricCollector()
    df = collector.query_range("cpu_usage", 1700000000, 1700000030)
    assert len(df) == 3
    assert "timestamp" in df.columns
    assert "value" in df.columns
    assert df["value"].iloc[0] == 10.0
