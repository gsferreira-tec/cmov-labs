#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import time

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ./study-plot.py <study_nr> </path/to/file1.csv> [path/to/file2.csv]")
        sys.exit(1)

    study_nr = int(sys.argv[1])
    csv1 = Path(sys.argv[2])
    csv2 = Path(sys.argv[3]) if len(sys.argv) == 4 else None

    if csv2:
        out_path = Path(f"{csv1.stem}-vs-{csv2.stem}.png")
        df1 = pd.read_csv(csv1)
        df2 = pd.read_csv(csv2)
    else:
        out_path = csv1.with_suffix(".png")
        df1 = pd.read_csv(csv1)


    time.sleep(1)
    print(f"\nGenerating, saving and plotting the graph for study number {study_nr}...\n")

    if study_nr == 1:
        if "distance_m" not in df1.columns or "rx_kbit_s" not in df1.columns:
            print("CSV1 must contain data for 'distance_m' and 'rx_kbit_s'")
            sys.exit(1)

        if csv2:
            if "distance_m" not in df2.columns or "wireshark_kbit_s" not in df2.columns:
                print("CSV2 must contain data for 'distance_m' and 'wireshark_kbit_s'")
                sys.exit(1)


        df1["distance_m"] = pd.to_numeric(df1["distance_m"], errors="coerce")
        df1["rx_kbit_s"] = pd.to_numeric(df1["rx_kbit_s"], errors="coerce")

        if csv2:
            df2["distance_m"] = pd.to_numeric(df2["distance_m"], errors="coerce")
            df2["wireshark_kbit_s"] = pd.to_numeric(df2["wireshark_kbit_s"], errors="coerce")


        df1 = df1.sort_values("distance_m")

        if csv2:
            df2 = df2.sort_values("distance_m")

        plt.plot(df1["distance_m"], df1["rx_kbit_s"], marker="o", linewidth=3, color="steelblue", label="flowmon")
        if csv2:
            plt.plot(df2["distance_m"], df2["wireshark_kbit_s"], marker="*", linewidth=3, color="red", label="Wireshark")
        plt.xlabel("Distance (m)")
        plt.ylabel("Throughput (Kbps)")

        plt.savefig(out_path, dpi=200) # saving the figure

        pl.tight_layout()
        plt.legend()
        plt.show()

    elif study_nr == 2:
        if "file" not in df1.columns or "rx_kbit_s" not in df1.columns:
            print("CSV1 must contain data for 'file' and 'rx_kbit_s'")
            sys.exit(1)


        df1["sender_nr"] = pd.to_numeric(df1["file"].str.extract(r"NrOfSenders=(\d+)", expand=False).astype(int), errors="coerce")
        df1["rx_kbit_s"] = pd.to_numeric(df1["rx_kbit_s"], errors="coerce")

        df1 = df1.dropna(subset=["sender_nr", "rx_kbit_s"]).sort_values("sender_nr")

        df1["total_throughput"] = df1["rx_kbit_s"] * df1["sender_nr"]

        _ ,ax1 = plt.subplots(figsize=(10, 6))

        # plotting total throughput per increase in number of STA
        color_total = 'steelblue'
        ax1.set_xlabel('Number of STAs')
        ax1.set_ylabel('Total Throughput (Kbps)', color=color_total, fontsize=12, fontweight='bold')
        ax1.plot(df1["sender_nr"], df1["total_throughput"], color=color_total, marker='o', linewidth=3, label="Total Throughput")
        ax1.tick_params(axis='y', labelcolor=color_total)
        ax1.set_ylim(0, 30000)

        # plotting avg throughput per number of STAs
        ax2 = ax1.twinx()
        color_avg = 'tab:red'
        ax2.set_ylabel('Avg Throughput per Sender (Kbps)', color=color_avg, fontsize=12, fontweight='bold')
        ax2.plot(df1["sender_nr"], df1["rx_kbit_s"], color=color_avg, marker='o', linewidth=3, label="Avg Throughput")
        ax2.tick_params(axis='y', labelcolor=color_avg)
        ax2.set_ylim(0, 12000)

        # apply a grid
        ax1.grid(True, linestyle=':', alpha=0.6)

        # apply legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        plt.savefig(out_path, dpi=200) # saving the figure

        pl.tight_layout()
        plt.legend()
        plt.show()

    elif study_nr == 3:
        if "file" not in df1.columns or "rx_kbit_s" not in df1.columns:
            print("CSV1 must contain data for 'file' and 'rx_kbit_s'")
            sys.exit(1)

        out_path_2 = Path("./3rd-study-mean.png")
        out_path_3 = Path("./3rd-study-pktloss.png")


        df1["udp_birate"] = pd.to_numeric(df1["file"].str.extract(r"UDP_DataRate=(\d+)", expand=False), errors="coerce")
        df1["rx_kbit_s"] = pd.to_numeric(df1["rx_kbit_s"], errors="coerce")
        df1["delay_ms"] = pd.to_numeric(df1["delay_ms"], errors="coerce")
        df1["loss_pct"] = pd.to_numeric(df1["loss_pct"], errors="coerce")
        df1 = df1.dropna(subset=["udp_birate","rx_kbit_s"]).sort_values("udp_birate")

        df_tcp = df1[df1["protocol"]=="TCP"]
        df_udp = df1[df1["protocol"]=="UDP"]

        # plotting mean delay and saving
        plt.figure(figsize=(10,6))
        plt.plot(df_tcp["udp_birate"], df_tcp["delay_ms"], marker="s", linewidth=3, color="red", label="TCP Mean Delay (ms)")
        plt.plot(df_udp["udp_birate"], df_udp["delay_ms"], marker="o", linewidth=3, color="steelblue", label="UDP Mean Delay (ms)")

        plt.xlabel("Transmitted UDP Bitrate (Mbps)", fontweight="bold")
        plt.ylabel("Mean Delay (ms)", fontweight="bold")
        plt.grid(True, linestyle=":", alpha=0.6)

        plt.savefig(out_path_2, dpi=200) # saving the figure

        plt.tight_layout()
        plt.legend()
        # plt.show()

        # plotting the packet loss
        plt.figure(figsize=(10,6))
        plt.plot(df_udp["udp_birate"], df_udp["loss_pct"], marker="o", linewidth=3, color="steelblue", label="UDP Packet Loss")

        plt.xlabel("Transmitted UDP Bitrate (Mbps)", fontweight="bold")
        plt.ylabel("Packet Loss Ratio (%)", fontweight="bold")
        plt.grid(True, linestyle=":", alpha=0.6)

        plt.savefig(out_path_3, dpi=200) # saving the figure

        plt.tight_layout()
        plt.legend()
        # plt.show()

        # plotting the UDP vs TCP throughput with varying bitrates
        plt.figure(figsize=(10,6))
        plt.plot(df_udp["udp_birate"], df_udp["rx_kbit_s"], marker="o", linewidth=3, color="steelblue", label="UDP")
        plt.plot(df_tcp["udp_birate"], df_tcp["rx_kbit_s"], marker="o", linewidth=3, color="red", label="TCP")

        plt.xlabel("Transmitted UDP Bitrate (Mbps)", fontweight="bold")
        plt.ylabel("Throughput (Kbps)", fontweight="bold")
        plt.grid(True, linestyle=":", alpha=0.6)

        plt.savefig(out_path, dpi=200) # saving the figure

        plt.tight_layout()
        plt.legend()
        plt.show()

    elif study_nr == 4:
        if "distance_m" not in df1.columns or "rx_kbit_s" not in df1.columns:
            print("CSV1 must contain data for 'distance_m' and 'rx_kbit_s'")
            sys.exit(1)

        if csv2:
            if "distance_m" not in df2.columns or "rx_kbit_s" not in df2.columns:
                print("CSV2 must contain data for 'distance_m' and 'rx_kbit_s'")
                sys.exit(1)


        df1["distance_m"] = pd.to_numeric(df1["distance_m"], errors="coerce")
        df1["rx_kbit_s"] = pd.to_numeric(df1["rx_kbit_s"], errors="coerce")

        if csv2:
            df2["distance_m"] = pd.to_numeric(df2["distance_m"], errors="coerce")
            df2["rx_kbit_s"] = pd.to_numeric(df2["rx_kbit_s"], errors="coerce")


        df1 = df1.sort_values("distance_m")

        if csv2:
            df2 = df2.sort_values("distance_m")

        plt.plot(df1["distance_m"], df1["rx_kbit_s"], marker="o", linewidth=3, color="steelblue", label="with RELAY")
        if csv2:
            plt.plot(df2["distance_m"], df2["rx_kbit_s"], marker="*", linewidth=3, color="red", label="without RELAY")

        plt.xlabel("Distance (m)")
        plt.ylabel("Throughput (Kbps)")


        plt.savefig(out_path, dpi=200) # saving the figure

        pl.tight_layout()
        plt.legend()
        plt.show()


    else:
        print(f"The study number provided {study_nr} is not supported. Aborting...")
        time.sleep(1)
        sys.exit(1)

#     if study_nr != 2:
#         plt.grid(True)
#         plt.legend()
#
    # plt.tight_layout()
    # plt.savefig(out_path, dpi=200)

    if csv2:
        print(f"The plot for {csv1}_vs_{csv2} was saved in {out_path}")
    else:
        print(f"The plot for {csv1} was saved in {out_path}")

    time.sleep(1)

    # if study_nr != 2:
    #     plt.show()


if __name__ == "__main__":
    main()
