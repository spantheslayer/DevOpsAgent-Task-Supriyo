import os
from crewai import Agent, LLM
from tools import prometheus_monitor, memory_monitor, disk_monitor, network_monitor, system_overview, log_analyzer, system_remediation, confidence_based_remediation

llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

detection_agent = Agent(
    role='System Monitoring Specialist',
    goal='Monitor CPU, memory, disk, and network usage and detect spikes exceeding defined thresholds',
    backstory='Expert in comprehensive system monitoring who watches all critical metrics and identifies performance anomalies',
    tools=[prometheus_monitor, memory_monitor, disk_monitor, network_monitor, system_overview, log_analyzer],
    llm=llm,
    verbose=True
)

remediation_agent = Agent(
    role='Auto Remediation Specialist', 
    goal='Assess AI confidence and automatically restart failing services only when confident, otherwise request human intervention',
    backstory='Experienced system administrator who prioritizes system stability and knows when to escalate to humans for complex issues',
    tools=[confidence_based_remediation, system_remediation, system_overview],
    llm=llm,
    verbose=True
)
