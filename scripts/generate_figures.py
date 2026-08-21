import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SUMMARY = Path("results/summary")
FIGURES = Path("results/figures")
FIGURES.mkdir(parents=True, exist_ok=True)

standard = pd.read_csv(
    SUMMARY / "standard_summary.csv"
)

concurrency = pd.read_csv(
    SUMMARY / "concurrency_summary.csv"
)

# 1. Standard p50 latency by workload
pivot = standard.pivot(
    index="workload",
    columns="platform",
    values="p50_ms",
)

pivot.plot(kind="bar", figsize=(12, 7))
plt.ylabel("p50 latency (ms)")
plt.xlabel("Workload")
plt.title("Standard workload p50 latency")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(
    FIGURES / "standard_p50_latency.png",
    dpi=200,
)
plt.close()

# 2. Standard p95 latency by workload
pivot = standard.pivot(
    index="workload",
    columns="platform",
    values="p95_ms",
)

pivot.plot(kind="bar", figsize=(12, 7))
plt.ylabel("p95 latency (ms)")
plt.xlabel("Workload")
plt.title("Standard workload p95 latency")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(
    FIGURES / "standard_p95_latency.png",
    dpi=200,
)
plt.close()

# 3. Standard QPS by workload
pivot = standard.pivot(
    index="workload",
    columns="platform",
    values="throughput_qps",
)

pivot.plot(kind="bar", figsize=(12, 7))
plt.ylabel("QPS")
plt.xlabel("Workload")
plt.title("Standard workload throughput")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(
    FIGURES / "standard_qps.png",
    dpi=200,
)
plt.close()

# 4. Concurrency QPS scaling
for platform, group in concurrency.groupby("platform"):
    group = group.sort_values("concurrency")

    plt.plot(
        group["concurrency"],
        group["overall_qps"],
        marker="o",
        label=platform,
    )

plt.xlabel("Concurrent clients")
plt.ylabel("Overall QPS")
plt.title("Concurrency scaling: overall QPS")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig(
    FIGURES / "concurrency_qps.png",
    dpi=200,
)
plt.close()

# 5. Concurrency p95 latency
for platform, group in concurrency.groupby("platform"):
    group = group.sort_values("concurrency")

    plt.plot(
        group["concurrency"],
        group["p95_ms"],
        marker="o",
        label=platform,
    )

plt.xlabel("Concurrent clients")
plt.ylabel("p95 latency (ms)")
plt.title("Concurrency scaling: p95 latency")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig(
    FIGURES / "concurrency_p95.png",
    dpi=200,
)
plt.close()

print("Figures generated:")
for path in sorted(FIGURES.glob("*.png")):
    print(path)
