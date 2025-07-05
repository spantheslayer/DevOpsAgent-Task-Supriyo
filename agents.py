import os
from crewai import Agent, LLM
from tools import prometheus_monitor, memory_monitor, disk_monitor, network_monitor, system_overview, log_analyzer, system_remediation

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
    goal='Automatically restart failing services and verify comprehensive system stability',
    backstory='System administrator who handles incident response and ensures all system resources return to normal levels',
    tools=[system_remediation, system_overview],
    llm=llm,
    verbose=True
)
