import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_slack_notification():
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not found in .env file")
        return False
    
    message = {
        "text": "DevOps AI Agent Test",
        "attachments": [
            {
                "color": "warning",
                "fields": [
                    {
                        "title": "Test Alert",
                        "value": "AIOPS monitoring test notification",
                        "short": False
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        if response.status_code == 200:
            print("Slack notification sent successfully")
            return True
        else:
            print(f"Failed to send Slack notification: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        return False

if __name__ == "__main__":
    test_slack_notification()
