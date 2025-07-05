#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from crewai import Crew
from agents import detection_agent, remediation_agent
from tasks import cpu_monitoring_task, remediation_task

load_dotenv()

def main():
   crew = Crew(
       agents=[detection_agent, remediation_agent],
       tasks=[cpu_monitoring_task, remediation_task],
       verbose=True
   )
   
   result = crew.kickoff()
   print(f"Agent completed: {result}")

if __name__ == "__main__":
   main()
