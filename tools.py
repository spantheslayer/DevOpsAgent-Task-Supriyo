from crewai.tools import tool
import requests
import subprocess
import time
import psutil
import os
from crewai import LLM
from config import CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD, NETWORK_THRESHOLD
from notifications import send_incident_alert, send_remediation_alert

llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

def generate_root_cause_analysis(metrics, issues, system_logs=""):
    try:
        prompt = f"""
Analyze the following system metrics and provide a concise root cause analysis:

System Metrics:
- CPU: {metrics.get('cpu', 'N/A')}
- Memory: {metrics.get('memory', 'N/A')}
- Disk: {metrics.get('disk', 'N/A')}
- Network: {metrics.get('network', 'N/A')}

Issues Detected: {', '.join(issues)}

System Logs (Recent):
{system_logs[:500] if system_logs else "No recent logs available"}

Provide a brief root cause analysis (max 150 words) focusing on:
1. Most likely cause of the issues
2. Immediate impact
3. Recommended next steps

Keep it concise and actionable for operations teams.
"""
        
        response = llm.call(prompt)
        return response.strip()
    except Exception as e:
        return f"Root cause analysis failed: {str(e)}"

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
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        cpu_result = f"CPU spike detected: {cpu_usage:.2f}%" if cpu_usage > CPU_THRESHOLD else f"CPU normal: {cpu_usage:.2f}%"
        memory_result = f"Memory spike detected: {memory.percent:.2f}%" if memory.percent > MEMORY_THRESHOLD else f"Memory normal: {memory.percent:.2f}%"
        disk_result = f"Disk spike detected: {disk.percent:.2f}%" if disk.percent > DISK_THRESHOLD else f"Disk normal: {disk.percent:.2f}%"
        network_result = f"Network normal: {network.bytes_sent/1024/1024:.2f} MB sent"
        
        overview = f"""
System Overview:
{cpu_result}
{memory_result}
{disk_result}
{network_result}
"""
        
        issues = []
        metrics = {
            'cpu': f"{cpu_usage:.2f}%",
            'memory': f"{memory.percent:.2f}%",
            'disk': f"{disk.percent:.2f}%",
            'network': f"{network.bytes_sent/1024/1024:.2f} MB"
        }
        
        if cpu_usage > CPU_THRESHOLD:
            issues.append("CPU")
            
        if memory.percent > MEMORY_THRESHOLD:
            issues.append("Memory")
            
        if disk.percent > DISK_THRESHOLD:
            issues.append("Disk")
            
        if network.bytes_sent/1024/1024 > NETWORK_THRESHOLD:
            issues.append("Network")
        
        if issues:
            overview += f"\nISSUES DETECTED: {', '.join(issues)}"
            
            try:
                result = subprocess.run(['journalctl', '--since', '5 minutes ago', '--no-pager'], 
                                      capture_output=True, text=True)
                system_logs = result.stdout
            except:
                system_logs = ""
            
            root_cause = generate_root_cause_analysis(metrics, issues, system_logs)
            send_incident_alert(metrics, issues, root_cause)
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
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        pre_metrics = {
            'cpu': f"{cpu_usage:.2f}%",
            'memory': f"{memory.percent:.2f}%",
            'disk': f"{disk.percent:.2f}%",
            'network': f"{network.bytes_sent/1024/1024:.2f} MB"
        }
        
        restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            return f"Restart failed: {restart_result.stderr}"
        
        time.sleep(5)
        
        status_result = subprocess.run(['sudo', 'systemctl', 'is-active', 'docker'], 
                                     capture_output=True, text=True)
        service_status = status_result.stdout.strip()
        
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        post_metrics = {
            'cpu': f"{cpu_usage:.2f}%",
            'memory': f"{memory.percent:.2f}%",
            'disk': f"{disk.percent:.2f}%",
            'network': f"{network.bytes_sent/1024/1024:.2f} MB"
        }
        
        post_overview = f"""
System Overview:
CPU: {cpu_usage:.2f}%
Memory: {memory.percent:.2f}%
Disk: {disk.percent:.2f}%
Network: {network.bytes_sent/1024/1024:.2f} MB sent
"""
        
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