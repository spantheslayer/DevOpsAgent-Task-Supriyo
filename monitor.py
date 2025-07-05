import time
from datetime import datetime
from main import main as run_crew
from config import MONITORING_INTERVAL_SECONDS
from logging_config import setup_logger

logger = setup_logger('monitor')

def continuous_monitor():
   print(f"Starting continuous DevOps monitoring (every {MONITORING_INTERVAL_SECONDS} seconds)...")
   print("Press Ctrl+C to stop")
   
   logger.info("DevOps monitoring started", extra={'alert_type': 'system'})
   
   while True:
       try:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"\n[{timestamp}] Running system check...")

           logger.info("Starting system check", extra={'alert_type': 'monitoring'})
           result = run_crew()
           print(result)
           logger.info("System check completed", extra={'alert_type': 'monitoring'})
           
           print(f"[{timestamp}] Check completed")
           print("-" * 50)
           
           time.sleep(MONITORING_INTERVAL_SECONDS)
           
       except KeyboardInterrupt:
           print("\nMonitoring stopped by user")
           logger.info("Monitoring stopped by user", extra={'alert_type': 'system'})
           break
       except Exception as e:
           timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           print(f"[{timestamp}] Monitor error: {e}")
           print(f"Retrying in {MONITORING_INTERVAL_SECONDS} seconds...")
           logger.error(f"Monitor error: {e}", extra={'alert_type': 'error'})
           time.sleep(MONITORING_INTERVAL_SECONDS)

if __name__ == "__main__":
   continuous_monitor()

