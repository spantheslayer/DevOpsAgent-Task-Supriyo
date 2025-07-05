import os
from crewai import Agent, LLM
from tools import prometheus_monitor, log_analyzer, system_remediation

llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

detection_agent = Agent(
    role='CPU Spike Detection Specialist',
    goal='Monitor CPU usage and detect spikes exceeding defined thresholds',
    backstory='Expert in system monitoring who continuously watches CPU metrics and identifies anomalies',
    tools=[prometheus_monitor, log_analyzer],
    llm=llm,
    verbose=True
)

remediation_agent = Agent(
    role='Auto Remediation Specialist', 
    goal='Automatically restart failing services and verify system stability',
    backstory='System administrator who handles incident response and service recovery',
    tools=[system_remediation],
    llm=llm,
    verbose=True
)
