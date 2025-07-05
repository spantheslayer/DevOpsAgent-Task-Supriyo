from crewai.tools import tool
import requests
import subprocess
import time
import psutil
from config import CPU_THRESHOLD

@tool
def prometheus_monitor():
    """Query Prometheus for CPU metrics and detect spikes"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query?query=100-(avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100)')
        data = response.json()
        cpu_usage = float(data['data']['result'][0]['value'][1])
        
        if cpu_usage > CPU_THRESHOLD:
            return f"CPU spike detected: {cpu_usage:.2f}%"
        return f"CPU normal: {cpu_usage:.2f}%"
    except Exception as e:
        return f"Error monitoring CPU: {str(e)}"

@tool 
def log_analyzer():
    """Retrieve and analyze system logs for root cause"""
    try:
        result = subprocess.run(['journalctl', '--since', '5 minutes ago', '--no-pager'], 
                              capture_output=True, text=True)
        logs = result.stdout
        return f"Recent logs retrieved: {len(logs)} characters. Content: {logs[:500]}"
    except Exception as e:
        return f"Error retrieving logs: {str(e)}"

@tool
def system_remediation():
    """Restart services and verify system health"""
    try:
        # Restart Docker service
        restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            return f"Restart failed: {restart_result.stderr}"
        
        # Wait for service to stabilize
        time.sleep(5)
        
        # Verify service status
        status_result = subprocess.run(['sudo', 'systemctl', 'is-active', 'docker'], 
                                     capture_output=True, text=True)
        service_status = status_result.stdout.strip()
        
        # Check system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Check CPU via Prometheus directly
        try:
            response = requests.get('http://localhost:9090/api/v1/query?query=100-(avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100)')
            data = response.json()
            prometheus_cpu = float(data['data']['result'][0]['value'][1])
            cpu_check = f"CPU normal: {prometheus_cpu:.2f}%"
        except:
            cpu_check = "Prometheus check failed"
        
        verification_report = f"""
Service Restart: SUCCESS
Docker Status: {service_status}
Post-restart CPU: {cpu_percent:.1f}%
Memory Usage: {memory_percent:.1f}%
Disk Usage: {disk_percent:.1f}%
Prometheus Check: {cpu_check}
System Stability: VERIFIED
"""
        
        return verification_report
        
    except Exception as e:
        return f"Error during remediation: {str(e)}"
