import subprocess
import time
import signal
import sys

def create_cpu_spike(duration=60):
    print(f"Creating CPU spike for {duration} seconds...")
    process = subprocess.Popen(['stress', '--cpu', '2', '--timeout', str(duration)])
    return process

def stop_stress(process):
    if process and process.poll() is None:
        process.terminate()
        print("Stress test stopped")

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    stress_process = create_cpu_spike(duration)
    
    try:
        stress_process.wait()
    except KeyboardInterrupt:
        stop_stress(stress_process)
        print("Stress test interrupted")
