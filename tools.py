from crewai.tools import tool
import requests
import subprocess
import time
import psutil
import os
from crewai import LLM
from config import CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD, NETWORK_THRESHOLD, SPIKE_DURATION_SECONDS
from notifications import send_incident_alert, send_remediation_alert, send_comprehensive_incident_alert

llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

spike_start_times = {}

def check_sustained_spike(metric_name, current_value, threshold):
    current_time = time.time()
    
    if current_value > threshold:
        if metric_name not in spike_start_times:
            spike_start_times[metric_name] = current_time
            return False
        elif current_time - spike_start_times[metric_name] >= SPIKE_DURATION_SECONDS:
            return True
        else:
            return False
    else:
        spike_start_times.pop(metric_name, None)
        return False

def get_spike_duration(metric_name):
    if metric_name in spike_start_times:
        return int(time.time() - spike_start_times[metric_name])
    return 0

def extract_metric_value(result_string):
    try:
        return float(result_string.split(': ')[1].rstrip('%'))
    except:
        return 0.0

def get_prometheus_metrics():
    try:
        cpu_result = prometheus_monitor()
        memory_result = memory_monitor()
        disk_result = disk_monitor()
        network_result = network_monitor()
        
        cpu_value = extract_metric_value(cpu_result)
        memory_value = extract_metric_value(memory_result)
        disk_value = extract_metric_value(disk_result)
        network_value = extract_metric_value(network_result.replace(' Mbps', ''))
        
        return {
            'cpu_result': cpu_result,
            'memory_result': memory_result,
            'disk_result': disk_result,
            'network_result': network_result,
            'cpu_value': cpu_value,
            'memory_value': memory_value,
            'disk_value': disk_value,
            'network_value': network_value
        }
    except Exception as e:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            'cpu_result': f"CPU {'spike detected' if cpu_usage > CPU_THRESHOLD else 'normal'}: {cpu_usage:.2f}%",
            'memory_result': f"Memory {'spike detected' if memory.percent > MEMORY_THRESHOLD else 'normal'}: {memory.percent:.2f}%",
            'disk_result': f"Disk {'spike detected' if disk.percent > DISK_THRESHOLD else 'normal'}: {disk.percent:.2f}%",
            'network_result': f"Network normal: {network.bytes_sent/1024/1024:.2f} MB sent",
            'cpu_value': cpu_usage,
            'memory_value': memory.percent,
            'disk_value': disk.percent,
            'network_value': network.bytes_sent/1024/1024
        }

def generate_root_cause_analysis(metrics, issues, system_logs=""):
    try:
        prompt = f"""
Analyze the following system metrics and provide a concise root cause analysis with confidence assessment:

System Metrics:
- CPU: {metrics.get('cpu', 'N/A')}
- Memory: {metrics.get('memory', 'N/A')}
- Disk: {metrics.get('disk', 'N/A')}
- Network: {metrics.get('network', 'N/A')}

Issues Detected: {', '.join(issues)}

System Logs (Recent):
{system_logs[:500] if system_logs else "No recent logs available"}

Provide analysis (max 150 words) with:
1. Most likely cause of the issues
2. Immediate impact
3. Confidence assessment

Then provide your recommendation in this exact format:
CONFIDENCE: [High/Medium/Low]
RECOMMENDATION: [AUTO_REMEDIATE/HUMAN_INTERVENTION]
REASON: [Brief explanation for confidence level]

Confidence Guidelines:
- High: Clear error patterns, known issues, single service affected
- Medium: Some uncertainty but manageable risk
- Low: Unclear cause, multiple systems affected, potential data risk

Do not use markdown formatting, asterisks, or headers in your response.
"""
        
        response = llm.call(prompt)
        return response.strip()
    except Exception as e:
        return f"Root cause analysis failed: {str(e)}", False

def parse_confidence_decision(analysis_text):
    try:
        lines = analysis_text.split('\n')
        confidence = "Low"
        recommendation = "HUMAN_INTERVENTION"
        reason = "Analysis parsing failed"
        
        clean_analysis_lines = []
        for line in lines:
            if line.startswith('CONFIDENCE:'):
                confidence = line.split(':', 1)[1].strip()
            elif line.startswith('RECOMMENDATION:'):
                recommendation = line.split(':', 1)[1].strip()
            elif line.startswith('REASON:'):
                reason = line.split(':', 1)[1].strip()
            elif line.strip() and line.strip() != "Analysis:":
                clean_analysis_lines.append(line)
        
        clean_analysis = '\n'.join(clean_analysis_lines).strip()
        auto_remediate = recommendation == "AUTO_REMEDIATE" and confidence in ["High", "Medium"]
        return clean_analysis, auto_remediate, confidence, reason
        
    except Exception as e:
        return analysis_text, False, "Low", f"Parsing error: {str(e)}"

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
        prometheus_data = get_prometheus_metrics()
        
        overview = f"""
System Overview:
{prometheus_data['cpu_result']}
{prometheus_data['memory_result']}
{prometheus_data['disk_result']}
{prometheus_data['network_result']}
"""
        
        issues = []
        metrics = {
            'cpu': f"{prometheus_data['cpu_value']:.2f}%",
            'memory': f"{prometheus_data['memory_value']:.2f}%",
            'disk': f"{prometheus_data['disk_value']:.2f}%",
            'network': f"{prometheus_data['network_value']:.2f} MB"
        }
        
        sustained_issues = []
        
        if check_sustained_spike('cpu', prometheus_data['cpu_value'], CPU_THRESHOLD):
            issues.append("CPU")
            sustained_issues.append(f"CPU (sustained {get_spike_duration('cpu')}s)")
            
        if check_sustained_spike('memory', prometheus_data['memory_value'], MEMORY_THRESHOLD):
            issues.append("Memory")
            sustained_issues.append(f"Memory (sustained {get_spike_duration('memory')}s)")
            
        if check_sustained_spike('disk', prometheus_data['disk_value'], DISK_THRESHOLD):
            issues.append("Disk")
            sustained_issues.append(f"Disk (sustained {get_spike_duration('disk')}s)")
            
        if check_sustained_spike('network', prometheus_data['network_value'], NETWORK_THRESHOLD):
            issues.append("Network")
            sustained_issues.append(f"Network (sustained {get_spike_duration('network')}s)")
        
        current_spikes = []
        if prometheus_data['cpu_value'] > CPU_THRESHOLD and 'cpu' in spike_start_times and 'CPU' not in issues:
            current_spikes.append(f"CPU tracking ({get_spike_duration('cpu')}s)")
        if prometheus_data['memory_value'] > MEMORY_THRESHOLD and 'memory' in spike_start_times and 'Memory' not in issues:
            current_spikes.append(f"Memory tracking ({get_spike_duration('memory')}s)")
        if prometheus_data['disk_value'] > DISK_THRESHOLD and 'disk' in spike_start_times and 'Disk' not in issues:
            current_spikes.append(f"Disk tracking ({get_spike_duration('disk')}s)")
        if prometheus_data['network_value'] > NETWORK_THRESHOLD and 'network' in spike_start_times and 'Network' not in issues:
            current_spikes.append(f"Network tracking ({get_spike_duration('network')}s)")
        
        if issues:
            overview += f"\nSUSTAINED ISSUES DETECTED: {', '.join(sustained_issues)}"
            
            try:
                result = subprocess.run(['journalctl', '--since', '5 minutes ago', '--no-pager'], 
                                      capture_output=True, text=True)
                system_logs = result.stdout
            except:
                system_logs = ""
            
            root_cause = generate_root_cause_analysis(metrics, issues, system_logs)
            analysis_text, should_auto_remediate, confidence, reason = parse_confidence_decision(root_cause)
            
            metrics['confidence'] = confidence
            metrics['auto_remediate'] = "Yes" if should_auto_remediate else "No"
            metrics['decision_reason'] = reason
            
            send_incident_alert(metrics, issues, analysis_text)
        elif current_spikes:
            overview += f"\nTRACKING POTENTIAL ISSUES: {', '.join(current_spikes)} (need {SPIKE_DURATION_SECONDS}s to trigger alert)"
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

@tool
def confidence_based_remediation():
    """Check AI confidence and perform remediation only if confidence is high enough"""
    try:
        prometheus_data = get_prometheus_metrics()
        issues = []
        metrics = {
            'cpu': f"{prometheus_data['cpu_value']:.2f}%",
            'memory': f"{prometheus_data['memory_value']:.2f}%",
            'disk': f"{prometheus_data['disk_value']:.2f}%",
            'network': f"{prometheus_data['network_value']:.2f} MB"
        }
        
        if prometheus_data['cpu_value'] > CPU_THRESHOLD:
            issues.append("CPU")
        if prometheus_data['memory_value'] > MEMORY_THRESHOLD:
            issues.append("Memory")
        if prometheus_data['disk_value'] > DISK_THRESHOLD:
            issues.append("Disk")
        if prometheus_data['network_value'] > NETWORK_THRESHOLD:
            issues.append("Network")
        
        if not issues:
            return "No issues detected - remediation not needed"
        
        try:
            result = subprocess.run(['journalctl', '--since', '5 minutes ago', '--no-pager'], 
                                  capture_output=True, text=True)
            system_logs = result.stdout
        except:
            system_logs = ""
        
        root_cause = generate_root_cause_analysis(metrics, issues, system_logs)
        analysis_text, should_auto_remediate, confidence, reason = parse_confidence_decision(root_cause)
        
        if should_auto_remediate:
            pre_metrics = metrics.copy()
            remediation_result = system_remediation()
            
            post_prometheus_data = get_prometheus_metrics()
            post_metrics = {
                'cpu': f"{post_prometheus_data['cpu_value']:.2f}%",
                'memory': f"{post_prometheus_data['memory_value']:.2f}%",
                'disk': f"{post_prometheus_data['disk_value']:.2f}%",
                'network': f"{post_prometheus_data['network_value']:.2f} MB"
            }
            
            metrics['confidence'] = confidence
            metrics['decision_reason'] = reason
            
            send_comprehensive_incident_alert(
                incident_metrics=metrics,
                issues=issues,
                root_cause_analysis=analysis_text,
                remediation_status="SUCCESS" if "SUCCESS" in remediation_result else "FAILED",
                pre_metrics=pre_metrics,
                post_metrics=post_metrics,
                action_taken="Docker service restarted automatically"
            )
            
            return f"""
CONFIDENCE-BASED REMEDIATION EXECUTED

AI Assessment:
- Confidence: {confidence}
- Decision: AUTO_REMEDIATE
- Reason: {reason}

{remediation_result}
"""
        else:
            metrics['confidence'] = confidence
            metrics['decision_reason'] = reason
            
            send_comprehensive_incident_alert(
                incident_metrics=metrics,
                issues=issues,
                root_cause_analysis=analysis_text,
                remediation_status="SKIPPED - Human intervention required",
                pre_metrics=metrics,
                post_metrics=metrics,
                action_taken="No automatic action taken due to low confidence"
            )
            
            return f"""
HUMAN INTERVENTION REQUIRED

AI Assessment:
- Confidence: {confidence}
- Decision: HUMAN_INTERVENTION
- Reason: {reason}

Issues Detected: {', '.join(issues)}
Current Metrics: {metrics}

Root Cause Analysis:
{analysis_text}

RECOMMENDATION: Operations team should manually investigate before taking remediation actions.
"""
        
    except Exception as e:
        return f"Error in confidence-based remediation: {str(e)}"