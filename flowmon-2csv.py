#!/usr/bin/env python3
import sys
import csv
import re
from pathlib import Path

def parse_distance_run(name):
    d = re.search(r"Distance=(\d+)m", name)
    r = re.search(r"Run=(\d+)", name)
    return (int(d.group(1)) if d else None, int(r.group(1)) if r else None)

def parse_wrapper_output(text):
    rows=[]
    current_file=None
    current_flow=None

    for line in text.splitlines():
        line = line.strip()

        m_file = re.match(r"^\*+\s*(.+\.xml)\s*\*+$", line)
        if m_file:
            if current_file is not None and current_flow is not None:
                rows.append((current_file, current_flow))
            current_file = m_file.group(1)
            current_flow = None
            continue

        m_flow = re.match(r"^FlowID:\s*(\d+)\s*\((TCP|UDP)\s+(.+?)\s*-->\s*(.+?)\)$", line)
        if m_flow:
            if current_file is not None and current_flow is not None:
                rows.append((current_file, current_flow))

            current_flow = {
                    "flow_id": int(m_flow.group(1)),
                    "protocol": m_flow.group(2),
                    "flow_desc": line,
                    "rx_kbit_s": None,
                    "tx_kbit_s": None,
                    "delay_ms": None,
                    "loss_pct": None,
            }
            continue

        if current_flow is None:
            continue

        m_tx = re.match(r"^TX bitrate:\s*([-\d.]+)\s*kbit/s$", line)
        if m_tx:
            current_flow["tx_kbit_s"] = float(m_tx.group(1))
            continue

        m_rx = re.match(r"^RX bitrate:\s*([-\d.]+)\s*kbit/s$", line)
        if m_rx:
            current_flow["rx_kbit_s"] = float(m_rx.group(1))
            continue

        m_delay = re.match(r"^Mean Delay:\s*([-\d.]+)\s*ms$", line)
        if m_delay:
            current_flow["delay_ms"] = float(m_delay.group(1))
            continue

        m_loss = re.match(r"^Packet Loss Ratio:\s*([-\d.]+)\s*%$", line)
        if m_loss:
            current_flow["loss_pct"] = float(m_loss.group(1))
            continue

        if current_file and line.startswith("**********"):
            if current_flow:
                rows.append((current_file, current_flow))
                current_flow = None

    if current_file and current_flow:
        rows.append((current_file, current_flow))

    return rows

def choose_main_tcp_flow(flows):
    results=[]

    tcp = [f for f in flows if f["protocol"]=="TCP" and f["rx_kbit_s"] is not None]
    if tcp:
        results.append(max(tcp, key=lambda x: x["rx_kbit_s"]))

    udp = [f for f in flows if f["protocol"]=="UDP" and f["rx_kbit_s"] is not None]
    if udp:
        results.append(max(udp, key=lambda x: x["rx_kbit_s"]))

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 flowmon-2csv.py <parser-output.txt> [results.csv]")
        sys.exit(1)

    input_txt = Path(sys.argv[1])
    output_csv = Path(sys.argv[2]) if len(sys.argv) == 3 else Path(f"flowmon-output/{input_txt.stem}.csv")

    text = input_txt.read_text(errors="replace")
    parsed = parse_wrapper_output(text)

    grouped = {}
    for fname, flow in parsed:
        grouped.setdefault(fname, []).append(flow)

    rows = []
    for fname, flows in grouped.items():
        main_flows = choose_main_tcp_flow(flows)
        if main_flows is None:
            continue

        for flow in main_flows:
            distance_m, run = parse_distance_run(fname)
            rows.append({
                    "file": fname,
                    "distance_m": distance_m,
                    "run": run,
                    "flow_id": flow["flow_id"],
                    "protocol": flow["protocol"],
                    "rx_kbit_s": flow["rx_kbit_s"],
                    "tx_kbit_s": flow["tx_kbit_s"],
                    "delay_ms": flow["delay_ms"],
                    "loss_pct": flow["loss_pct"],
            })

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "distance_m", "run", "flow_id", "protocol", "rx_kbit_s", "tx_kbit_s",
        "delay_ms", "loss_pct"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_csv}")

if __name__ == "__main__":
    main()












