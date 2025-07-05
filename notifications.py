import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

def send_slack_alert(title, message, color="danger", fields=None):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured")
        return False
    
    payload = {
        "text": f"ALERT:: {title}",
        "attachments": [
            {
                "color": color,
                "fields": fields or [
                    {
                        "title": title,
                        "value": message,
                        "short": False
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            logger.info("Slack notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Slack notification: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return False

def send_incident_alert(metrics, issues, log_analysis=""):
    fields = [
        {"title": "CPU Usage", "value": f"{metrics.get('cpu', 'N/A')}", "short": True},
        {"title": "Memory Usage", "value": f"{metrics.get('memory', 'N/A')}", "short": True},
        {"title": "Disk Usage", "value": f"{metrics.get('disk', 'N/A')}", "short": True},
        {"title": "Network Usage", "value": f"{metrics.get('network', 'N/A')}", "short": True},
        {"title": "Issues Detected", "value": ", ".join(issues), "short": False}
    ]
    
    if log_analysis:
        fields.append({"title": "Root Cause", "value": log_analysis[:500], "short": False})
    
    return send_slack_alert(
        "System Alert - Issues Detected",
        f"Detected {len(issues)} system issue(s) requiring attention",
        "danger",
        fields
    )

def send_remediation_alert(status, pre_metrics, post_metrics):
    fields = [
        {"title": "Remediation Status", "value": status, "short": True},
        {"title": "Pre-CPU", "value": f"{pre_metrics.get('cpu', 'N/A')}", "short": True},
        {"title": "Post-CPU", "value": f"{post_metrics.get('cpu', 'N/A')}", "short": True},
        {"title": "Pre-Memory", "value": f"{pre_metrics.get('memory', 'N/A')}", "short": True},
        {"title": "Post-Memory", "value": f"{post_metrics.get('memory', 'N/A')}", "short": True}
    ]
    
    color = "good" if "SUCCESS" in status else "warning"
    
    return send_slack_alert(
        "System Remediation Completed",
        f"Automatic remediation executed: {status}",
        color,
        fields
    )
