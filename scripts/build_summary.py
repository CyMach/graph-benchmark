import csv
import json
from pathlib import Path

base = Path("results/raw/final")
out = Path("results/summary")
out.mkdir(parents=True, exist_ok=True)

platforms = [
    "neo4j_aura",
    "memgraph",
    "falkordb",
    "arangodb",
    "cognodb",
]

standard_rows = []

for platform in platforms:
    path = base / f"{platform}_standard_120runs.json"
    data = json.loads(path.read_text())

    for row in data:
        standard_rows.append({
            "platform": platform,
            "workload": row["workload"],
            "count": row["count"],
            "warmup_runs": row["warmup_runs"],
            "mean_ms": row["mean_ms"],
            "p50_ms": row["p50_ms"],
            "p95_ms": row["p95_ms"],
            "p99_ms": row["p99_ms"],
            "min_ms": row["min_ms"],
            "max_ms": row["max_ms"],
            "throughput_qps": row["throughput_qps"],
        })

with (out / "standard_summary.csv").open(
    "w",
    newline="",
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=standard_rows[0].keys(),
    )
    writer.writeheader()
    writer.writerows(standard_rows)


concurrency_rows = []

for platform in platforms:
    path = base / f"{platform}_concurrent_results.json"
    data = json.loads(path.read_text())

    for row in data:
        concurrency_rows.append({
            "platform": platform,
            "concurrency": row["concurrency"],
            "total_operations": row["total_operations"],
            "successful_operations": row["successful_operations"],
            "failed_operations": row["failed_operations"],
            "read_operations": row["read_operations"],
            "write_operations": row["write_operations"],
            "overall_qps": row["overall_qps"],
            "read_qps": row["read_qps"],
            "write_qps": row["write_qps"],
            "p50_ms": row["p50_ms"],
            "p95_ms": row["p95_ms"],
            "p99_ms": row["p99_ms"],
        })

with (out / "concurrency_summary.csv").open(
    "w",
    newline="",
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=concurrency_rows[0].keys(),
    )
    writer.writeheader()
    writer.writerows(concurrency_rows)

print("Created:")
print(out / "standard_summary.csv")
print(out / "concurrency_summary.csv")
