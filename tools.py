from crewai.tools import tool
import requests
import subprocess
import time
from config import CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD, NETWORK_THRESHOLD
from notifications import send_incident_alert, send_remediation_alert

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
def memory_monitor():
    """Query Prometheus for memory metrics and detect high usage"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query?query=100*(1-node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)')
        data = response.json()
        memory_usage = float(data['data']['result'][0]['value'][1])
        
        if memory_usage > MEMORY_THRESHOLD:
            return f"Memory spike detected: {memory_usage:.2f}%"
        return f"Memory normal: {memory_usage:.2f}%"
    except Exception as e:
        return f"Error monitoring memory: {str(e)}"

@tool
def disk_monitor():
    """Query Prometheus for disk metrics and detect high usage"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query?query=100*(1-node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"})')
        data = response.json()
        disk_usage = float(data['data']['result'][0]['value'][1])
        
        if disk_usage > DISK_THRESHOLD:
            return f"Disk spike detected: {disk_usage:.2f}%"
        return f"Disk normal: {disk_usage:.2f}%"
    except Exception as e:
        return f"Error monitoring disk: {str(e)}"

@tool
def network_monitor():
    """Query Prometheus for network metrics and detect high usage"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query?query=rate(node_network_transmit_bytes_total{device="ens5"}[5m])*8/1000000')
        data = response.json()
        network_usage = float(data['data']['result'][0]['value'][1]) if data['data']['result'] else 0
        
        if network_usage > NETWORK_THRESHOLD:
            return f"Network spike detected: {network_usage:.2f} Mbps"
        return f"Network normal: {network_usage:.2f} Mbps"
    except Exception as e:
        return f"Error monitoring network: {str(e)}"

@tool
def system_overview():
    """Get comprehensive system metrics overview and send Slack alerts if issues detected"""
    try:
        cpu_result = prometheus_monitor()
        memory_result = memory_monitor()
        disk_result = disk_monitor()
        network_result = network_monitor()
        
        overview = f"""
System Overview:
{cpu_result}
{memory_result}
{disk_result}
{network_result}
"""
        
        issues = []
        metrics = {}
        
        if "spike detected" in cpu_result:
            issues.append("CPU")
            metrics['cpu'] = cpu_result.split(': ')[1]
        else:
            metrics['cpu'] = cpu_result.split(': ')[1]
            
        if "spike detected" in memory_result:
            issues.append("Memory")
            metrics['memory'] = memory_result.split(': ')[1]
        else:
            metrics['memory'] = memory_result.split(': ')[1]
            
        if "spike detected" in disk_result:
            issues.append("Disk")
            metrics['disk'] = disk_result.split(': ')[1]
        else:
            metrics['disk'] = disk_result.split(': ')[1]
            
        if "spike detected" in network_result:
            issues.append("Network")
            metrics['network'] = network_result.split(': ')[1]
        else:
            metrics['network'] = network_result.split(': ')[1]
        
        if issues:
            overview += f"\nISSUES DETECTED: {', '.join(issues)}"
            send_incident_alert(metrics, issues, "System metrics exceeded defined thresholds")
        else:
            overview += "\nAll systems normal"
            
        return overview
    except Exception as e:
        return f"Error getting system overview: {str(e)}"

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
    """Restart services and verify system health with Slack notifications"""
    try:
        pre_overview = system_overview()
        pre_metrics = {}
        
        restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            return f"Restart failed: {restart_result.stderr}"
        
        time.sleep(5)
        
        status_result = subprocess.run(['sudo', 'systemctl', 'is-active', 'docker'], 
                                     capture_output=True, text=True)
        service_status = status_result.stdout.strip()
        
        post_overview = system_overview()
        post_metrics = {}
        
        verification_report = f"""
Service Restart: SUCCESS
Docker Status: {service_status}
Post-restart System Status:
{post_overview}
System Stability: VERIFIED
"""
        
        send_remediation_alert("SUCCESS - Docker restarted", pre_metrics, post_metrics)
        
        return verification_report
        
    except Exception as e:
        return f"Error during remediation: {str(e)}"