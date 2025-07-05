import os
import logging
import logging.handlers
import json
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "devops-agent.log")
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

os.makedirs(LOG_DIR, exist_ok=True)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'metrics'):
            log_entry['metrics'] = record.metrics
        if hasattr(record, 'alert_type'):
            log_entry['alert_type'] = record.alert_type
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'confidence'):
            log_entry['confidence'] = record.confidence
            
        return json.dumps(log_entry)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console)
    
    return logger