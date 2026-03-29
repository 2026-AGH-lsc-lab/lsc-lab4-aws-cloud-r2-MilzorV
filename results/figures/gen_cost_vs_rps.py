#!/usr/bin/env python3
"""Cost vs average RPS (steady 24/7) for Assignment 6 — Lambda vs flat always-on."""
from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "cost-vs-rps.png"

# us-east-1 on-demand style assumptions (verify on pricing pages; screenshots in pricing-screenshots/)
LAMBDA_PER_MILLION_REQ = 0.20
LAMBDA_PER_GB_SECOND = 0.0000166667
DURATION_S = 0.075  # ~p50 handler from CloudWatch warm REPORT (Scenario B)
MEMORY_GB = 0.5  # 512 MB

SECONDS_PER_MONTH = 30 * 24 * 3600

# Fargate 0.5 vCPU, 1 GiB — approximate Linux x86 (verify current table)
FARGATE_VCPU_PER_HR = 0.04048
FARGATE_GB_PER_HR = 0.004445
FARGATE_HOURLY = 0.5 * FARGATE_VCPU_PER_HR + 1.0 * FARGATE_GB_PER_HR
FARGATE_MONTHLY_FLAT = FARGATE_HOURLY * 24 * 30

# EC2 t3.small on-demand us-east-1 (order of magnitude; verify)
EC2_T3_SMALL_HOURLY = 0.0208
EC2_MONTHLY_FLAT = EC2_T3_SMALL_HOURLY * 24 * 30


def lambda_monthly_usd(avg_rps: float) -> float:
    n = avg_rps * SECONDS_PER_MONTH
    req_cost = (n / 1_000_000) * LAMBDA_PER_MILLION_REQ
    gb_s = n * DURATION_S * MEMORY_GB
    comp_cost = gb_s * LAMBDA_PER_GB_SECOND
    return req_cost + comp_cost


def break_even_rps(flat_monthly: float) -> float:
    """Solve lambda_monthly(r) = flat_monthly for r (scalar cost per request)."""
    n_coeff = (1 / 1_000_000) * LAMBDA_PER_MILLION_REQ + DURATION_S * MEMORY_GB * LAMBDA_PER_GB_SECOND
    n_break = flat_monthly / n_coeff
    return n_break / SECONDS_PER_MONTH


r = np.linspace(0, 25, 200)
y_l = np.array([lambda_monthly_usd(x) for x in r])
r_be_f = break_even_rps(FARGATE_MONTHLY_FLAT)

fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
ax.plot(r, y_l, label="Lambda (variable)", color="#4c72b0", linewidth=2)
ax.axhline(FARGATE_MONTHLY_FLAT, color="#dd8452", linestyle="--", label=f"Fargate (flat, ~${FARGATE_MONTHLY_FLAT:.2f}/mo)")
ax.axhline(EC2_MONTHLY_FLAT, color="#55a868", linestyle=":", label=f"EC2 t3.small (flat, ~${EC2_MONTHLY_FLAT:.2f}/mo)")
ax.axvline(r_be_f, color="#8172b3", alpha=0.7, linestyle="-.", label=f"Break-even vs Fargate (~{r_be_f:.1f} avg RPS)")
ax.scatter([r_be_f], [FARGATE_MONTHLY_FLAT], color="#c44e52", s=40, zorder=5)
ax.set_xlabel("Average RPS (steady 24/7, uniform traffic)")
ax.set_ylabel("Estimated monthly cost (USD)")
ax.set_title("Lambda linear cost vs always-on flat cost (verify pricing)")
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, linestyle="--", alpha=0.35)
ax.set_xlim(0, 25)
plt.tight_layout()
plt.savefig(OUT, bbox_inches="tight")
print(f"Wrote {OUT}")
print(f"Break-even vs Fargate (approx): {r_be_f:.2f} RPS")
