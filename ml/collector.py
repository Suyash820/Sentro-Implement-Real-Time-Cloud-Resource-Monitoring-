import time
import logging
import requests
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Standard PromQL queries for Sentro Cloud Telemetry (12 Comprehensive Parameters)
METRIC_QUERIES = {
    # 1. Compute Tier
    "cpu_usage": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)',
    "system_load": 'node_load1',
    # 2. Memory Tier
    "memory_usage": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
    # 3. Storage & Disk Tier
    "disk_usage": '100 - ((node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"}) * 100)',
    "disk_read_rate": 'sum(rate(node_disk_read_bytes_total[1m]))',
    "disk_write_rate": 'sum(rate(node_disk_written_bytes_total[1m]))',
    # 4. Network Tier
    "network_in_rate": 'sum(rate(node_network_receive_bytes_total{device!~"lo|docker.*|veth.*"}[1m]))',
    "network_out_rate": 'sum(rate(node_network_transmit_bytes_total{device!~"lo|docker.*|veth.*"}[1m]))',
    "tcp_connections": 'node_sockstat_TCP_inuse',
    # 5. Application Workload Tier (Golden Signals)
    "app_request_rate": 'sum(rate(flask_http_request_total[1m]))',
    "app_p95_latency": 'histogram_quantile(0.95, sum by (le) (rate(flask_http_request_duration_seconds_bucket[1m])))',
    "app_error_rate": 'sum(rate(flask_http_request_total{status=~"[45].."}[1m]))'
}

DEFAULT_METRIC_VALUES = {
    "cpu_usage": 5.0,
    "system_load": 0.5,
    "memory_usage": 20.0,
    "disk_usage": 40.0,
    "disk_read_rate": 1024.0,
    "disk_write_rate": 2048.0,
    "network_in_rate": 1024.0,
    "network_out_rate": 512.0,
    "tcp_connections": 15.0,
    "app_request_rate": 0.0,
    "app_p95_latency": 0.005,
    "app_error_rate": 0.0
}

class MetricCollector:
    """
    Ingests live and historical telemetry metrics from the Prometheus HTTP API.
    """
    def __init__(self, prometheus_url: str = "http://localhost:9090", timeout: int = 5):
        self.prometheus_url = prometheus_url.rstrip("/")
        self.timeout = timeout

    def query_instant(self, query: str) -> Optional[float]:
        """
        Executes an instant PromQL query against Prometheus.
        Returns the parsed scalar float, or None if unavailable.
        """
        url = f"{self.prometheus_url}/api/v1/query"
        try:
            response = requests.get(url, params={"query": query}, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success" and data.get("data", {}).get("result"):
                results = data["data"]["result"]
                if results and "value" in results[0]:
                    raw_val = results[0]["value"][1]
                    val = float(raw_val)
                    return 0.0 if np.isnan(val) else val
            return None
        except Exception as e:
            logger.debug(f"PromQL query '{query}' failed: {e}")
            return None

    def query_range(self, query: str, start_time: float, end_time: float, step: str = "15s") -> pd.DataFrame:
        """
        Executes a range PromQL query. Returns a DataFrame with 'timestamp' and 'value'.
        """
        url = f"{self.prometheus_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start_time,
            "end": end_time,
            "step": step
        }
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success" and data.get("data", {}).get("result"):
                results = data["data"]["result"]
                if results and "values" in results[0]:
                    points = results[0]["values"]
                    df = pd.DataFrame(points, columns=["timestamp", "value"])
                    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="s")
                    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0)
                    return df
            return pd.DataFrame(columns=["timestamp", "value"])
        except Exception as e:
            logger.debug(f"PromQL range query '{query}' failed: {e}")
            return pd.DataFrame(columns=["timestamp", "value"])

    def get_latest_metrics_snapshot(self) -> Dict[str, float]:
        """
        Fetches an instant snapshot of all key operational metrics.
        Fills unrecorded metrics with safe default baseline values.
        """
        snapshot = {}
        for metric_name, query in METRIC_QUERIES.items():
            val = self.query_instant(query)
            if val is None or np.isnan(val):
                snapshot[metric_name] = DEFAULT_METRIC_VALUES.get(metric_name, 0.0)
            else:
                snapshot[metric_name] = round(val, 4)
        return snapshot

    def get_historical_dataframe(self, lookback_minutes: int = 30, step: str = "15s") -> pd.DataFrame:
        """
        Queries all metrics over a lookback window and merges them into a single DataFrame.
        """
        end_time = time.time()
        start_time = end_time - (lookback_minutes * 60)

        combined_df = None

        for metric_name, query in METRIC_QUERIES.items():
            df = self.query_range(query, start_time, end_time, step=step)
            if df.empty:
                continue
            df = df.rename(columns={"value": metric_name})
            if combined_df is None:
                combined_df = df
            else:
                combined_df = pd.merge(combined_df, df, on="timestamp", how="outer")

        if combined_df is None or combined_df.empty:
            return pd.DataFrame(columns=["timestamp"] + list(METRIC_QUERIES.keys()))

        combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)
        # Forward fill and default fill missing values
        for col in METRIC_QUERIES.keys():
            if col not in combined_df.columns:
                combined_df[col] = DEFAULT_METRIC_VALUES.get(col, 0.0)
            else:
                combined_df[col] = combined_df[col].ffill().bfill().fillna(DEFAULT_METRIC_VALUES.get(col, 0.0))

        return combined_df
