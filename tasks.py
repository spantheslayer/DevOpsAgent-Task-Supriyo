from crewai import Task
from agents import detection_agent, remediation_agent
from config import CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD, NETWORK_THRESHOLD

system_monitoring_task = Task(
    description=f'Monitor system metrics using system_overview. Check CPU (>{CPU_THRESHOLD}%), Memory (>{MEMORY_THRESHOLD}%), Disk (>{DISK_THRESHOLD}%), and Network (>{NETWORK_THRESHOLD} Mbps) thresholds. If any metric exceeds threshold, retrieve system logs and analyze for root causes. Do not simulate issues.',
    agent=detection_agent,
    expected_output='Detection report with all system metrics, identifying any issues above thresholds with actual logs and root cause analysis. Report normal status if no issues detected.'
)

comprehensive_remediation_task = Task(
    description=f'Only execute if previous task detected actual issues above thresholds. Restart Docker service, verify all system metrics (CPU, memory, disk, network) returned to normal levels, and provide comprehensive verification report.',
    agent=remediation_agent,
    expected_output='Complete remediation report with restart status and verification of all system metrics returning to normal levels'
)
