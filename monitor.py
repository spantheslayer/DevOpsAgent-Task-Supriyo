import time
import threading
from main import main as run_crew
from tools import prometheus_monitor

def continuous_monitor():
   print("Starting continuous monitoring...")
   while True:
       try:
           cpu_result = prometheus_monitor()
           print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {cpu_result}")
           
           if "spike detected" in cpu_result.lower():
               print("CPU spike detected! Triggering AI agent...")
               run_crew()
           
           time.sleep(1)
       except KeyboardInterrupt:
           print("Monitoring stopped")
           break
       except Exception as e:
           print(f"Monitor error: {e}")
           time.sleep(1)

if __name__ == "__main__":
   continuous_monitor()
