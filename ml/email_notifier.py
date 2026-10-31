import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

logger = logging.getLogger("ml-email-notifier")

class EmailNotifier:
    """
    Automated Email Alerting Dispatcher for Sentro ML Anomaly Detection.
    Features cooldown throttling and auto-recovery notifications.
    """
    def __init__(
        self,
        enabled: Optional[bool] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_email: Optional[str] = None,
        cooldown_seconds: Optional[int] = None,
        score_threshold: Optional[float] = None
    ):
        self.enabled = (
            enabled if enabled is not None
            else os.environ.get("ALERT_EMAIL_ENABLED", "false").lower() in ("true", "1", "yes")
        )
        self.smtp_server = smtp_server or os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.sender_email = sender_email or os.environ.get("ALERT_EMAIL_SENDER", "")
        self.sender_password = sender_password or os.environ.get("ALERT_EMAIL_PASSWORD", "")
        self.recipient_email = recipient_email or os.environ.get("ALERT_EMAIL_RECIPIENT", "")
        self.cooldown_seconds = cooldown_seconds or int(os.environ.get("ALERT_COOLDOWN_SECONDS", "300"))
        self.score_threshold = score_threshold or float(os.environ.get("ALERT_SCORE_THRESHOLD", "0.70"))

        self.last_alert_time: float = 0.0
        self.is_in_anomaly_state: bool = False

    def notify_if_needed(self, prediction: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """
        Coordinates alert dispatching and recovery notifications based on telemetry state.
        """
        score = prediction.get("anomaly_score", 0.0)
        is_anomaly = prediction.get("is_anomaly", False)

        # 1. Trigger Anomaly Alert if score breaches threshold or flagged anomalous
        if is_anomaly or score >= self.score_threshold:
            now = time.time()
            if now - self.last_alert_time >= self.cooldown_seconds:
                sent = self.send_alert_email(prediction, metrics)
                if sent:
                    self.last_alert_time = now
                    self.is_in_anomaly_state = True
                return sent
            else:
                remaining = int(self.cooldown_seconds - (now - self.last_alert_time))
                logger.info(f"Alert throttled by cooldown ({remaining}s remaining before next alert).")
                return False

        # 2. Trigger Auto-Recovery notification if previously in an anomaly state
        elif self.is_in_anomaly_state and score < 0.50:
            sent = self.send_recovery_email(prediction, metrics)
            if sent:
                self.is_in_anomaly_state = False
            return sent

        return False

    def send_alert_email(self, prediction: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """Sends a critical anomaly alert email."""
        if not self.enabled:
            logger.debug("Email alerts are disabled (ALERT_EMAIL_ENABLED=false).")
            return False

        if not self.sender_email or not self.recipient_email:
            logger.warning("Email alert skipped: sender or recipient email is not configured.")
            return False

        subject = f"🚨 [CRITICAL ALERT] Cloud Resource Anomaly Detected (Score: {prediction.get('anomaly_score'):.2f})"

        body_text = f"""
============================================================
🚨 SENTRO AIOPS ANOMALY NOTIFICATION
============================================================
Status:            CRITICAL ANOMALY DETECTED
Severity Score:    {prediction.get('anomaly_score', 0.0):.4f} / 1.00 (Threshold: {self.score_threshold})
Model Decision:    {prediction.get('status', 'ANOMALY')}
Timestamp:         {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

------------------------------------------------------------
Telemetric Breakdown at Trigger (12 Cloud Vectors):
------------------------------------------------------------
[Compute]
• CPU Utilization:     {metrics.get('cpu_usage', 'N/A')}%
• System Load (1m):    {metrics.get('system_load', 'N/A')}

[Memory & Storage]
• Memory Utilization:  {metrics.get('memory_usage', 'N/A')}%
• Disk Utilization:    {metrics.get('disk_usage', 'N/A')}%
• Disk Read Rate:      {metrics.get('disk_read_rate', 'N/A')} Bps
• Disk Write Rate:     {metrics.get('disk_write_rate', 'N/A')} Bps

[Network]
• Network Inbound:     {metrics.get('network_in_rate', 'N/A')} Bps
• Network Outbound:    {metrics.get('network_out_rate', 'N/A')} Bps
• Active TCP Sockets:  {metrics.get('tcp_connections', 'N/A')}

[Application Workload]
• App Request Rate:    {metrics.get('app_request_rate', 'N/A')} req/s
• App P95 Latency:     {metrics.get('app_p95_latency', 'N/A')} s
• App Error Rate:      {metrics.get('app_error_rate', 'N/A')} err/s

Model Algorithm: Isolation Forest (100 Estimators)
============================================================
Sent by Sentro Real-Time Cloud Resource Monitoring Platform
"""
        return self._send_smtp(subject, body_text)

    def send_recovery_email(self, prediction: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """Sends an issue resolved / recovery email."""
        if not self.enabled or not self.sender_email or not self.recipient_email:
            return False

        subject = f"✅ [RESOLVED] Cloud Workload Stabilized to Normal (Score: {prediction.get('anomaly_score'):.2f})"

        body_text = f"""
============================================================
✅ SENTRO AIOPS RECOVERY NOTIFICATION
============================================================
Status:            RESOLVED — WORKLOAD NORMALIZED
Severity Score:    {prediction.get('anomaly_score', 0.0):.4f} / 1.00
Timestamp:         {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

------------------------------------------------------------
Current Stabilized Telemetry:
------------------------------------------------------------
• CPU Utilization:     {metrics.get('cpu_usage', 'N/A')}%
• System Load (1m):    {metrics.get('system_load', 'N/A')}
• Memory Utilization:  {metrics.get('memory_usage', 'N/A')}%
• Disk Utilization:    {metrics.get('disk_usage', 'N/A')}%
• App Request Rate:    {metrics.get('app_request_rate', 'N/A')} req/s
• App P95 Latency:     {metrics.get('app_p95_latency', 'N/A')} s
• App Error Rate:      {metrics.get('app_error_rate', 'N/A')} err/s

The workload metrics have returned to safe operational baselines.
============================================================
Sent by Sentro Real-Time Cloud Resource Monitoring Platform
"""
        return self._send_smtp(subject, body_text)

    def _send_smtp(self, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            if self.sender_password:
                server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            server.quit()

            logger.info(f"Alert email successfully delivered to {self.recipient_email}!")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch alert email: {e}")
            return False
