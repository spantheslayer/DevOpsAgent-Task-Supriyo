import time
from datetime import datetime
from main import main as run_crew

def continuous_monitor():
   print("Starting continuous DevOps monitoring (every 60 seconds)...")
   print("Press Ctrl+C to stop")
   
   while True:
       try:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"\n[{timestamp}] Running system check...")
           
           result = run_crew()
           
           print(f"[{timestamp}] Check completed")
           print("-" * 50)
           
           time.sleep(60)
           
       except KeyboardInterrupt:
           print("\nMonitoring stopped by user")
           break
       except Exception as e:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"[{timestamp}] Monitor error: {e}")
           print("Retrying in 60 seconds...")
           time.sleep(60)

if __name__ == "__main__":
   continuous_monitor()

