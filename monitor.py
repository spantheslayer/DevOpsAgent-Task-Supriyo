import time
from datetime import datetime
from main import main as run_crew
from config import MONITORING_INTERVAL_SECONDS

def continuous_monitor():
   print(f"Starting continuous DevOps monitoring (every {MONITORING_INTERVAL_SECONDS} seconds)...")
   print("Press Ctrl+C to stop")
   
   while True:
       try:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"\n[{timestamp}] Running system check...")

           result = run_crew()
           print(result)
           
           print(f"[{timestamp}] Check completed")
           print("-" * 50)
           
           time.sleep(MONITORING_INTERVAL_SECONDS)
           
       except KeyboardInterrupt:
           print("\nMonitoring stopped by user")
           break
       except Exception as e:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"[{timestamp}] Monitor error: {e}")
           print(f"Retrying in {MONITORING_INTERVAL_SECONDS} seconds...")
           time.sleep(MONITORING_INTERVAL_SECONDS)

if __name__ == "__main__":
   continuous_monitor()

