#!/usr/bin/env python3
import sys
import csv
import re
import time
import subprocess
from pathlib import Path

def parse_distance_run(name):
    d = re.search(r"Distance=(\d+)m", name)
    r = re.search(r"Run=(\d+)", name)
    return (int(d.group(1)) if d else None, int(r.group(1)) if r else None)

def throughput_from_pcap(pcap_file):
    cmd = [
        "tshark",
        "-r", str(pcap_file),
        "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "tcp.len",
        "-Y", "tcp.len > 200"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    times=[]
    total_bytes=0

    for line in result.stdout.splitlines():
        parts = line.strip().split("\t")
        if len(parts) != 2:
            continue

        try:
            t = float(parts[0])
            tcp_len = int(parts[1])
        except ValueError:
            continue


        times.append(t)
        total_bytes += tcp_len

    if len(times) < 2:
        return None

    duration = max(times) - min(times)
    if duration <= 0:
        return None

    throughput_kbit_s = (total_bytes * 8) / duration / 1000.0
    return throughput_kbit_s

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 process-pcap.py <pcap_directory> <output_path>")
        sys.exit(1)

    pcap_dir = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])

    if not pcap_dir.is_dir():
        print(f"Error: {pcap_dir} is not a directory")
        sys.exit(1)

    pcap_files = sorted(pcap_dir.glob("*.pcap"))
    if not pcap_files:
        print(f"No .pcap files were found in {pcap_folder}")
        sys.exit(1)

    rows=[]

    for pcap_file in pcap_files:
        distance_m, run = parse_distance_run(pcap_file.name)

        print(f"Processing {pcap_file.name}...")
        time.sleep(0.2)
        try:
            throughput = throughput_from_pcap(pcap_file)
        except RuntimeError as e:
            print(f"skipping {pcap_file.name}: {e}")
            continue

        if throughput is None:
            print(f"Skipping {pcap_file.name}: no valid TCP payload packets found")
            continue

        rows.append({
            "file": pcap_file.name,
            "distance_m": distance_m,
            "run": run,
            "wireshark_kbit_s": throughput
        })

    rows.sort(key=lambda r: (r["distance_m"] if r["distance_m"] is not None else 10**9, r["run"] if r["run"] is not None else 10**9
    ))

    with output_csv.open("w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=["file", "distance_m", "run", "wireshark_kbit_s"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_csv}")

if __name__ == "__main__":
    main()






