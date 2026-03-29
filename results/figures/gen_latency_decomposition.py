#!/usr/bin/env python3
"""
Generate stacked bar chart for Assignment 2 from measured Scenario A + CloudWatch REPORT lines.

Values (ms) derived from:
- Client: results/scenario-a-zip.txt, scenario-a-container.txt (slowest ≈ cold; p50 ≈ warm cluster)
- Server: results/cloudwatch-zip-reports.txt, cloudwatch-container-reports.txt (Init Duration, Duration)
- Network RTT: total_ms - Init - Duration (cold), total_ms - Duration (warm)
"""
from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "latency-decomposition.png"

# --- Inputs (ms) ---
# Zip cold: slowest client 1655.3; first REPORT Init 615.32, Duration 77.11
zip_cold_total, zip_cold_init, zip_cold_handler = 1655.3, 615.32, 77.11
zip_cold_net = zip_cold_total - zip_cold_init - zip_cold_handler

# Zip warm: p50 229.0 ms; representative handler ~75 ms (median warm REPORT lines)
zip_warm_p50, zip_warm_handler = 229.0, 75.0
zip_warm_net = zip_warm_p50 - zip_warm_handler

# Container cold: slowest 1673.8; Init 685.43, Duration 82.00
ctr_cold_total, ctr_cold_init, ctr_cold_handler = 1673.8, 685.43, 82.00
ctr_cold_net = ctr_cold_total - ctr_cold_init - ctr_cold_handler

# Container warm: p50 223.9 ms; handler ~75 ms
ctr_warm_p50, ctr_warm_handler = 223.9, 75.0
ctr_warm_net = ctr_warm_p50 - ctr_warm_handler

labels = [
    "Lambda zip\n(cold)",
    "Lambda zip\n(warm, p50)",
    "Lambda container\n(cold)",
    "Lambda container\n(warm, p50)",
]
network = [zip_cold_net, zip_warm_net, ctr_cold_net, ctr_warm_net]
init = [zip_cold_init, 0.0, ctr_cold_init, 0.0]
handler = [zip_cold_handler, zip_warm_handler, ctr_cold_handler, ctr_warm_handler]

x = np.arange(len(labels))
width = 0.62

fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
c_net = "#4c72b0"
c_init = "#dd8452"
c_hdl = "#55a868"

b1 = ax.bar(x, network, width, label="Network RTT (est.)", color=c_net)
b2 = ax.bar(x, init, width, bottom=network, label="Init duration", color=c_init)
bottom2 = np.array(network) + np.array(init)
b3 = ax.bar(x, handler, width, bottom=bottom2, label="Handler duration", color=c_hdl)

ax.set_ylabel("Latency (ms)")
ax.set_title("Scenario A: client latency decomposition (Lambda zip vs container)")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.legend(loc="upper right")
ax.grid(axis="y", linestyle="--", alpha=0.35)

plt.tight_layout()
plt.savefig(OUT, bbox_inches="tight")
print(f"Wrote {OUT}")
