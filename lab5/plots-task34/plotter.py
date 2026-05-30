#!/usr/bin/env python3
import os
import re
import csv
from statistics import median
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# File lists
# -----------------------------
THROUGHPUT_FILES = {
    "UDP DL": {
        "UE1": "throughput_udp_dl_ue1_100.csv",
        "UE2": "throughput_udp_dl_ue2_100.csv",
    },
    "UDP UL": {
        "UE1": "throughput_udp_ul_ue1_100.csv",
        "UE2": "throughput_udp_ul_ue2_100.csv",
    },
    "TCP DL": {
        "UE1": "throughput_tcp_dl_ue1_100.csv",
        "UE2": "throughput_tcp_dl_ue2_100.csv",
    },
    "TCP UL": {
        "UE1": "throughput_tcp_ul_ue1_100.csv",
        "UE2": "throughput_tcp_ul_ue2_100.csv",
    },
}

RTT_FILES = {
    "DL": {
        "UE1": "rtt_dl_ue1_100.txt",
        "UE2": "rtt_dl_ue2_100.txt",
    },
    "UL": {
        "UE1": "rtt_ul_ue1_100.txt",
        "UE2": "rtt_ul_ue2_100.txt",
    },
}


# -----------------------------
# Helpers
# -----------------------------
INTERVAL_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$")
RTT_RE = re.compile(r"time[=<]\s*([0-9]*\.?[0-9]+)\s*ms", re.IGNORECASE)


def check_file(path: str) -> None:
    """Raise a clear error if a file is missing or empty."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    if os.path.getsize(path) == 0:
        raise ValueError(f"Empty file: {path}")


def parse_iperf_csv(path: str) -> pd.DataFrame:
    """
    Parse an iPerf CSV file robustly.
    - Ignores text lines / prompts / malformed rows
    - Uses interval in column 6 (index 6)
    - Uses bandwidth in column 8 (index 8)
    - Skips summary rows (usually the wide interval spanning the whole test)
    """
    check_file(path)

    rows: List[Tuple[float, float, float]] = []  # start, end, bandwidth_bps

    with open(path, "r", newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            # Need at least 9 columns for TCP, 14 for UDP.
            if len(row) < 9:
                continue

            interval_text = row[6].strip() if len(row) > 6 else ""
            bw_text = row[8].strip() if len(row) > 8 else ""

            m = INTERVAL_RE.match(interval_text)
            if not m:
                continue

            try:
                start = float(m.group(1))
                end = float(m.group(2))
                bandwidth_bps = float(bw_text)
            except ValueError:
                continue

            rows.append((start, end, bandwidth_bps))

    if not rows:
        raise ValueError(f"No valid throughput data found in: {path}")

    df = pd.DataFrame(rows, columns=["start_s", "end_s", "bandwidth_bps"])

    # Remove likely summary rows:
    # The summary row typically spans the full test window (wider than normal intervals).
    widths = df["end_s"] - df["start_s"]
    typical_width = float(median(widths)) if len(widths) else 0.0

    if typical_width > 0:
        df = df[widths <= 1.5 * typical_width].copy()

    if df.empty:
        raise ValueError(f"Only summary or invalid rows remained after cleaning: {path}")

    df["throughput_mbps"] = df["bandwidth_bps"] / 1e6
    df = df.sort_values(["start_s", "end_s"]).reset_index(drop=True)
    return df[["start_s", "end_s", "throughput_mbps"]]


def parse_ping_txt(path: str) -> pd.DataFrame:
    """
    Parse standard ping output and extract RTT values from 'time=XX ms'.
    """
    check_file(path)

    rtts_ms: List[float] = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = RTT_RE.search(line)
            if m:
                try:
                    rtts_ms.append(float(m.group(1)))
                except ValueError:
                    pass

    if not rtts_ms:
        raise ValueError(f"No RTT values found in: {path}")

    return pd.DataFrame(
        {
            "sample": np.arange(1, len(rtts_ms) + 1),
            "rtt_ms": rtts_ms,
        }
    )


def plot_throughput(throughput_data: Dict[str, Dict[str, pd.DataFrame]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    axes = axes.flatten()

    plot_order = ["UDP DL", "UDP UL", "TCP DL", "TCP UL"]

    for ax, key in zip(axes, plot_order):
        for ue in ["UE1", "UE2"]:
            df = throughput_data[key][ue]
            x = df["end_s"]  # use interval end as the time axis
            y = df["throughput_mbps"]
            ax.plot(x, y, marker="o", linewidth=1.8, label=ue)

        ax.set_title(key)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Throughput (Mbps)")
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle("5G OAI Testbed Throughput", fontsize=16)
    plt.show()


def plot_rtt(rtt_data: Dict[str, Dict[str, pd.DataFrame]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    for ax, key in zip(axes, ["DL", "UL"]):
        for ue in ["UE1", "UE2"]:
            df = rtt_data[key][ue]
            ax.plot(df["sample"], df["rtt_ms"], marker="o", linewidth=1.8, label=ue)

        ax.set_title(f"{key} RTT")
        ax.set_xlabel("Ping sample")
        ax.set_ylabel("RTT (ms)")
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle("5G OAI Testbed RTT", fontsize=16)
    plt.show()


def summarize_throughput(throughput_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    records = []
    for link_type, ue_map in throughput_data.items():
        for ue, df in ue_map.items():
            records.append(
                {
                    "Type": link_type,
                    "UE": ue,
                    "Mean Mbps": df["throughput_mbps"].mean(),
                    "Min Mbps": df["throughput_mbps"].min(),
                    "Max Mbps": df["throughput_mbps"].max(),
                }
            )
    return pd.DataFrame(records)


def summarize_rtt(rtt_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    records = []
    for direction, ue_map in rtt_data.items():
        for ue, df in ue_map.items():
            records.append(
                {
                    "Direction": direction,
                    "UE": ue,
                    "Mean RTT (ms)": df["rtt_ms"].mean(),
                    "Min RTT (ms)": df["rtt_ms"].min(),
                    "Max RTT (ms)": df["rtt_ms"].max(),
                }
            )
    return pd.DataFrame(records)


def main() -> None:
    throughput_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    rtt_data: Dict[str, Dict[str, pd.DataFrame]] = {}

    # Load throughput files
    for link_type, ue_map in THROUGHPUT_FILES.items():
        throughput_data[link_type] = {}
        for ue, path in ue_map.items():
            try:
                throughput_data[link_type][ue] = parse_iperf_csv(path)
            except Exception as e:
                print(f"[Throughput] {path}: {e}")
                throughput_data[link_type][ue] = pd.DataFrame(
                    columns=["start_s", "end_s", "throughput_mbps"]
                )

    # Load RTT files
    for direction, ue_map in RTT_FILES.items():
        rtt_data[direction] = {}
        for ue, path in ue_map.items():
            try:
                rtt_data[direction][ue] = parse_ping_txt(path)
            except Exception as e:
                print(f"[RTT] {path}: {e}")
                rtt_data[direction][ue] = pd.DataFrame(columns=["sample", "rtt_ms"])

    # Remove any completely empty datasets before plotting
    if all(df.empty for group in throughput_data.values() for df in group.values()):
        print("No valid throughput data available to plot.")
    else:
        plot_throughput(throughput_data)

    if all(df.empty for group in rtt_data.values() for df in group.values()):
        print("No valid RTT data available to plot.")
    else:
        plot_rtt(rtt_data)

    # Print simple assessment tables
    thr_summary = summarize_throughput(throughput_data)
    rtt_summary = summarize_rtt(rtt_data)

    print("\n=== Throughput Summary (higher is better) ===")
    print(thr_summary.to_string(index=False))

    print("\n=== RTT Summary (lower is better) ===")
    print(rtt_summary.to_string(index=False))


if __name__ == "__main__":
    main()