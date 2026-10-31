#!/usr/bin/env python3
"""
Sentro Chaos & Stress Testing Simulator
Triggers artificial cloud resource anomalies (CPU, RAM, Network, Traffic)
to test and demonstrate the Isolation Forest Anomaly Detection ML model.
"""

import sys
import time
import math
import argparse
import random
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def _cpu_worker(stop_event):
    """Tight mathematical computation loop to maximize CPU core utilization."""
    while not stop_event.is_set():
        _ = [math.sqrt(x) * math.sin(x) for x in range(2000)]

def burn_cpu(duration_sec: int = 30, num_threads: int = None):
    """
    Maxes out CPU cores for the specified duration.
    """
    import os
    num_threads = num_threads or (os.cpu_count() or 4)
    print(f"[*] Starting CPU Burn with {num_threads} worker threads for {duration_sec}s...")

    stop_event = threading.Event()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=_cpu_worker, args=(stop_event,), daemon=True)
        t.start()
        threads.append(t)

    start_time = time.time()
    try:
        while time.time() - start_time < duration_sec:
            elapsed = int(time.time() - start_time)
            remaining = duration_sec - elapsed
            print(f"  🔥 CPU Spiking... [{elapsed}s elapsed, {remaining}s remaining]", end="\r")
            time.sleep(1)
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=1.0)
    print(f"\n[+] CPU Burn finished. CPU returning to baseline.")

def leak_memory(duration_sec: int = 30, target_mb: int = 300):
    """
    Simulates a memory leak by progressively allocating and holding RAM.
    """
    print(f"[*] Starting Memory Leak simulation: targeting ~{target_mb}MB for {duration_sec}s...")
    allocated_blocks = []
    chunk_size = 15 * 1024 * 1024  # 15 MB per chunk
    chunks_to_allocate = max(1, target_mb // 15)

    try:
        for i in range(chunks_to_allocate):
            # Allocate 15MB block of random bytes
            allocated_blocks.append(bytearray(chunk_size))
            mb_now = (i + 1) * 15
            print(f"  📈 RAM Leaking... Allocated {mb_now}MB / {target_mb}MB", end="\r")
            time.sleep(0.3)
        print(f"\n[*] Holding {len(allocated_blocks) * 15}MB in memory for {duration_sec}s...")
        time.sleep(duration_sec)
    finally:
        allocated_blocks.clear()
        import gc
        gc.collect()
        print("[+] Memory released. RAM returning to baseline.")

def flood_traffic(target_url: str = "http://localhost:5000", duration_sec: int = 30, concurrency: int = 20):
    """
    Floods the Flask app with concurrent HTTP requests to trigger latency and request surges.
    """
    print(f"[*] Starting Traffic Surge against {target_url} (Concurrency: {concurrency}) for {duration_sec}s...")
    stop_event = threading.Event()
    stats = {"success": 0, "errors": 0}

    def request_worker():
        while not stop_event.is_set():
            try:
                # Randomize endpoints between / and /health
                endpoint = target_url.rstrip("/") + random.choice(["/", "/health"])
                resp = requests.get(endpoint, timeout=2.0)
                if resp.status_code == 200:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1
            except Exception:
                stats["errors"] += 1
            time.sleep(0.01)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for _ in range(concurrency):
            executor.submit(request_worker)

        start = time.time()
        while time.time() - start < duration_sec:
            elapsed = int(time.time() - start)
            reqs = stats["success"] + stats["errors"]
            rate = reqs / max(1, elapsed)
            print(f"  🌊 Traffic Flooding: {reqs} requests ({rate:.1f} req/s, errors: {stats['errors']})", end="\r")
            time.sleep(1)

        stop_event.set()

    print(f"\n[+] Traffic Surge ended. Total requests sent: {stats['success'] + stats['errors']}.")

def stress_disk(duration_sec: int = 30):
    """
    Generates continuous heavy sequential disk write and read I/O operations.
    """
    import tempfile
    import os
    print(f"[*] Starting Disk I/O stress testing for {duration_sec}s...")
    start_time = time.time()
    chunk = b"X" * (1024 * 1024)  # 1 MB
    temp_files = []
    try:
        while time.time() - start_time < duration_sec:
            tf = tempfile.NamedTemporaryFile(delete=False)
            for _ in range(20):  # Write 20 MB per file
                tf.write(chunk)
            tf.flush()
            os.fsync(tf.fileno())
            tf.close()
            temp_files.append(tf.name)
            # Read back
            with open(tf.name, "rb") as f:
                _ = f.read()
            if len(temp_files) > 3:
                old = temp_files.pop(0)
                if os.path.exists(old):
                    os.remove(old)
            time.sleep(0.05)
    finally:
        for fpath in temp_files:
            if os.path.exists(fpath):
                os.remove(fpath)
        print("\n[+] Disk I/O stress finished and temporary scratch files cleaned.")

def normal_workload(target_url: str = "http://localhost:5000", duration_sec: int = 30):
    """
    Generates realistic, calm baseline user browsing traffic.
    """
    print(f"[*] Emulating Normal Baseline User Workload for {duration_sec}s...")
    start = time.time()
    req_count = 0
    while time.time() - start < duration_sec:
        try:
            endpoint = target_url.rstrip("/") + random.choice(["/", "/health"])
            requests.get(endpoint, timeout=2.0)
            req_count += 1
        except Exception:
            pass
        sleep_time = random.uniform(0.5, 2.0)
        time.sleep(sleep_time)
    print(f"[+] Normal traffic completed. Sent {req_count} baseline requests.")

def main():
    parser = argparse.ArgumentParser(
        description="Sentro Chaos & Stress Testing Simulator for ML Anomaly Detection"
    )
    parser.add_argument("--cpu-spike", action="store_true", help="Trigger a multi-threaded CPU spike")
    parser.add_argument("--memory-leak", action="store_true", help="Simulate progressive RAM leak")
    parser.add_argument("--disk-stress", action="store_true", help="Trigger heavy Disk I/O reads & writes")
    parser.add_argument("--traffic-burst", action="store_true", help="Flood the web app with concurrent traffic")
    parser.add_argument("--normal", action="store_true", help="Simulate normal, healthy background traffic")
    parser.add_argument("--all", action="store_true", help="Trigger combined CPU, Memory, Disk, and Traffic anomaly")
    parser.add_argument("--duration", type=int, default=30, help="Duration of stress test in seconds (default: 30)")
    parser.add_argument("--url", type=str, default="http://localhost:5000", help="Target Flask URL (default: http://localhost:5000)")
    parser.add_argument("--target-mb", type=int, default=300, help="Target MB to allocate for memory leak (default: 300)")

    args = parser.parse_args()

    # Default action if no flags provided: show help or run CPU spike
    if not any([args.cpu_spike, args.memory_leak, args.disk_stress, args.traffic_burst, args.normal, args.all]):
        print("[-] No stress scenario specified. Use --help to see all options.")
        print("[*] Defaulting to a short 15s CPU spike demonstration...")
        burn_cpu(duration_sec=15)
        return

    print("=" * 65)
    print("🚀 SENTRO CHAOS & ANOMALY INJECTION SIMULATOR")
    print("=" * 65)

    if args.normal:
        normal_workload(target_url=args.url, duration_sec=args.duration)

    if args.cpu_spike or args.all:
        burn_cpu(duration_sec=args.duration)

    if args.memory_leak or args.all:
        leak_memory(duration_sec=args.duration, target_mb=args.target_mb)

    if args.disk_stress or args.all:
        stress_disk(duration_sec=args.duration)

    if args.traffic_burst or args.all:
        flood_traffic(target_url=args.url, duration_sec=args.duration)

    print("=" * 65)
    print("✅ Stress testing scenario completed!")
    print("Check your Grafana dashboard (http://<IP>:3000) or ML Service status (http://<IP>:8000/status) to see anomaly detection in action.")
    print("=" * 65)

if __name__ == "__main__":
    main()
