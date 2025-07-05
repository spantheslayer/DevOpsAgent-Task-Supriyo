import streamlit as st
import pandas as pd
from log_aggregator import LogAggregator
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="DevOps Agent Logs", layout="wide")

aggregator = LogAggregator()

st.title("DevOps Agent Log Viewer")

col1, col2, col3, col4 = st.columns(4)

with col1:
    hours = st.selectbox("Time Range", [1, 6, 24, 168], index=2, format_func=lambda x: f"Last {x} hours" if x < 168 else "Last week")

with col2:
    level = st.selectbox("Log Level", ["All", "ERROR", "WARNING", "INFO"])

with col3:
    alert_type = st.selectbox("Alert Type", ["All", "incident", "metrics", "remediation"])

with col4:
    limit = st.selectbox("Max Results", [50, 100, 500], index=1)

search_text = st.text_input("Search logs", placeholder="Enter search text...")

if st.button("Refresh"):
    st.rerun()

start_time = datetime.utcnow() - timedelta(hours=hours)

logs = aggregator.search_logs(
    start_time=start_time,
    level=None if level == "All" else level,
    alert_type=None if alert_type == "All" else alert_type,
    search_text=search_text if search_text else None,
    limit=limit
)

if logs:
    df = pd.DataFrame(logs)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Logs", len(logs))
    
    with col2:
        incidents = len([l for l in logs if l.get('alert_type') == 'incident'])
        st.metric("Incidents", incidents)
    
    with col3:
        errors = len([l for l in logs if l.get('level') == 'ERROR'])
        st.metric("Errors", errors)
    
    with col4:
        warnings = len([l for l in logs if l.get('level') == 'WARNING'])
        st.metric("Warnings", warnings)
    
    st.subheader("Log Entries")
    
    for log in logs:
        timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        
        if log['level'] == 'ERROR':
            st.error(f"**{timestamp}** | {log['message']}")
        elif log['level'] == 'WARNING':
            st.warning(f"**{timestamp}** | {log['message']}")
        else:
            st.info(f"**{timestamp}** | {log['message']}")
        
        with st.expander("Details"):
            details = {
                "Level": log.get('level'),
                "Module": log.get('module'),
                "Function": log.get('function'),
                "Line": log.get('line')
            }
            
            if log.get('alert_type'):
                details["Alert Type"] = log.get('alert_type')
            if log.get('confidence'):
                details["Confidence"] = log.get('confidence')
            if log.get('duration'):
                details["Duration"] = f"{log.get('duration')}s"
            if log.get('metrics'):
                details["Metrics"] = json.dumps(log.get('metrics'), indent=2)
            
            for key, value in details.items():
                if value:
                    st.text(f"{key}: {value}")

else:
    st.info("No logs found matching the criteria.")

st.sidebar.markdown("### Quick Stats")
recent_logs = aggregator.search_logs(start_time=datetime.utcnow() - timedelta(hours=1), limit=1000)

if recent_logs:
    level_counts = {}
    for log in recent_logs:
        level = log.get('level', 'UNKNOWN')
        level_counts[level] = level_counts.get(level, 0) + 1
    
    st.sidebar.json(level_counts)
else:
    st.sidebar.text("No recent activity")