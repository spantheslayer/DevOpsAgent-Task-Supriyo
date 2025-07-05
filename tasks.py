from crewai import Task
from agents import detection_agent, remediation_agent

cpu_monitoring_task = Task(
    description='Monitor current CPU usage using prometheus_monitor. Only proceed if CPU usage exceeds 30% threshold. If threshold is exceeded, retrieve system logs from the incident timeframe and analyze them for actual root causes. Do not simulate or assume CPU spikes that do not exist.',
    agent=detection_agent,
    expected_output='Detection report only if real CPU spike detected above 30%, with actual logs and genuine root cause analysis. If no spike detected, report normal status.'
)

remediation_task = Task(
    description='Only execute if previous task detected an actual CPU spike above 30%. Restart Docker service, verify system stability with real metrics, and confirm CPU levels returned to normal. Do not perform remediation unless there was a genuine detected issue.',
    agent=remediation_agent,
    expected_output='Remediation report with restart status and verification metrics only if remediation was actually needed and performed'
)
