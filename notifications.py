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
    
    if metrics.get('confidence'):
        fields.append({"title": "AI Confidence", "value": f"{metrics.get('confidence')} - {metrics.get('decision_reason', '')}", "short": True})
        fields.append({"title": "Auto-Remediate", "value": metrics.get('auto_remediate', 'Unknown'), "short": True})
    
    if log_analysis:
        fields.append({"title": "Root Cause Analysis", "value": log_analysis[:1000], "short": False})
    
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

def send_comprehensive_incident_alert(incident_metrics, issues, root_cause_analysis, remediation_status, pre_metrics, post_metrics, action_taken):
    fields = [
        {"title": "Incident Details", "value": f"Issues: {', '.join(issues)}", "short": False},
        {"title": "CPU (Incident)", "value": f"{incident_metrics.get('cpu', 'N/A')}", "short": True},
        {"title": "Memory (Incident)", "value": f"{incident_metrics.get('memory', 'N/A')}", "short": True},
        {"title": "Disk (Incident)", "value": f"{incident_metrics.get('disk', 'N/A')}", "short": True},
        {"title": "Network (Incident)", "value": f"{incident_metrics.get('network', 'N/A')}", "short": True},
    ]
    
    if incident_metrics.get('confidence'):
        fields.append({"title": "AI Confidence", "value": f"{incident_metrics.get('confidence')} - {incident_metrics.get('decision_reason', '')}", "short": False})
    
    fields.extend([
        {"title": "Root Cause Analysis", "value": root_cause_analysis[:800], "short": False},
        {"title": "Action Taken", "value": action_taken, "short": False},
        {"title": "Remediation Status", "value": remediation_status, "short": True},
        {"title": "Pre-Remediation", "value": f"CPU: {pre_metrics.get('cpu', 'N/A')}, Memory: {pre_metrics.get('memory', 'N/A')}", "short": True},
        {"title": "Post-Remediation", "value": f"CPU: {post_metrics.get('cpu', 'N/A')}, Memory: {post_metrics.get('memory', 'N/A')}", "short": True}
    ])
    
    color = "good" if "SUCCESS" in remediation_status else "warning"
    
    return send_slack_alert(
        "System Incident - Detected Issues Report",
        f"Incident detected, analyzed, {action_taken}, Status: {remediation_status}",
        color,
        fields
    )
