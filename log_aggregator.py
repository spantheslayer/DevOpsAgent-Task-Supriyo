import json
import glob
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class LogAggregator:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        
    def get_log_files(self) -> List[str]:
        pattern = os.path.join(self.log_dir, "devops-agent.log*")
        return sorted(glob.glob(pattern), reverse=True)
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        try:
            return json.loads(line.strip())
        except:
            return None
    
    def search_logs(self, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   level: Optional[str] = None,
                   alert_type: Optional[str] = None,
                   search_text: Optional[str] = None,
                   limit: int = 1000) -> List[Dict]:
        
        results = []
        count = 0
        
        for log_file in self.get_log_files():
            if count >= limit:
                break
                
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if count >= limit:
                            break
                            
                        log_entry = self.parse_log_line(line)
                        if not log_entry:
                            continue
                        
                        if start_time:
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            if log_time < start_time:
                                continue
                        
                        if end_time:
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            if log_time > end_time:
                                continue
                        
                        if level and log_entry.get('level') != level:
                            continue
                            
                        if alert_type and log_entry.get('alert_type') != alert_type:
                            continue
                            
                        if search_text and search_text.lower() not in log_entry.get('message', '').lower():
                            continue
                        
                        results.append(log_entry)
                        count += 1
            except Exception as e:
                continue
        
        return results
    
    def get_recent_incidents(self, hours: int = 24) -> List[Dict]:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self.search_logs(
            start_time=start_time,
            alert_type="incident"
        )
    
    def get_system_metrics(self, hours: int = 1) -> List[Dict]:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self.search_logs(
            start_time=start_time,
            search_text="metrics"
        )

if __name__ == "__main__":
    aggregator = LogAggregator()
    
    print("Recent incidents (last 24h):")
    incidents = aggregator.get_recent_incidents()
    for incident in incidents[:5]:
        print(f"  {incident['timestamp']} - {incident['message']}")
    
    print(f"\nTotal incidents: {len(incidents)}")
    
    print("\nRecent metrics (last 1h):")
    metrics = aggregator.get_system_metrics()
    print(f"Total metric entries: {len(metrics)}")