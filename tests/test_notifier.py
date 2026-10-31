import pytest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.email_notifier import EmailNotifier

def test_notifier_init_defaults():
    notifier = EmailNotifier()
    assert notifier.enabled is False
    assert notifier.cooldown_seconds == 300
    assert notifier.score_threshold == 0.70
    assert notifier.last_alert_time == 0.0
    assert notifier.is_in_anomaly_state is False

def test_notifier_disabled():
    notifier = EmailNotifier(enabled=False)
    pred = {"anomaly_score": 0.95, "is_anomaly": True, "status": "ANOMALY"}
    metrics = {"cpu_usage": 95.0, "memory_usage": 90.0}
    # Disabled notifier should return False and not send
    assert notifier.notify_if_needed(pred, metrics) is False

@patch("smtplib.SMTP")
def test_notifier_send_alert_and_cooldown(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    notifier = EmailNotifier(
        enabled=True,
        sender_email="sentro@test.com",
        sender_password="dummy",
        recipient_email="admin@test.com",
        cooldown_seconds=60,
        score_threshold=0.70
    )

    pred_anomaly = {"anomaly_score": 0.88, "is_anomaly": True, "status": "ANOMALY"}
    metrics_anomaly = {"cpu_usage": 98.0, "memory_usage": 85.0}

    # 1. First trigger should send alert
    res1 = notifier.notify_if_needed(pred_anomaly, metrics_anomaly)
    assert res1 is True
    assert notifier.is_in_anomaly_state is True
    assert mock_server.sendmail.called
    assert mock_server.starttls.called

    # 2. Second trigger immediately after should be blocked by cooldown
    mock_server.reset_mock()
    res2 = notifier.notify_if_needed(pred_anomaly, metrics_anomaly)
    assert res2 is False
    assert not mock_server.sendmail.called

    # 3. Workload returns to normal -> triggers recovery email
    pred_normal = {"anomaly_score": 0.25, "is_anomaly": False, "status": "NORMAL"}
    metrics_normal = {"cpu_usage": 15.0, "memory_usage": 30.0}
    res3 = notifier.notify_if_needed(pred_normal, metrics_normal)
    assert res3 is True
    assert notifier.is_in_anomaly_state is False
    assert mock_server.sendmail.called
