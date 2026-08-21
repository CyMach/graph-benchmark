# Graph Database Benchmark

## Summary

This project benchmarks five managed graph-database platforms using a common Mushroom graph dataset and a standardized workload suite:

- CognoDB Cloud
- Neo4j Aura
- Memgraph Cloud
- FalkorDB Cloud
- ArangoGraph Insights Platform

The benchmark graph contains **30,000 Mushroom nodes, 116 attribute nodes, and 359,084 relationships**. Each platform was loaded with the same logical graph and verified against those counts.

The standard benchmark used **10 warm-up runs and 120 measured runs per workload**, with deterministic parameter selection using random seed 42. Seven workloads were evaluated. A separate concurrency benchmark used **1, 2, 4, 8, 16, and 40 concurrent clients**, with 10 seconds of warm-up and 30 seconds of measurement at each level.

The results should be interpreted as **observed performance under the tested managed-service/free-tier configurations**, not as a hardware-normalized comparison of database engines. The deployments had materially different resource allocations.

## Dataset and Graph Model

The controlled benchmark dataset contains:

- Mushroom nodes: **30,000**
- Attribute-value nodes: **116**
- Relationships: **359,084**

The graph model represents mushroom records as `Mushroom` nodes connected to categorical attribute-value nodes through typed relationships such as `HAS_CAP_SHAPE`, `HAS_STEM_ROOT`, `IN_HABITAT`, and `IN_SEASON`.

For ArangoGraph, the same logical graph was represented using `mushrooms`, `attributes`, and `relationships` collections, with AQL equivalents for the logical workloads.

## Platforms and Tested Configurations

| Platform | Provider | Plan | CPU | Memory | Storage | Region | Version | HA | Replication |
|---|---|---|---|---:|---:|---|---|---|---|
| CognoDB | CognoDB Cloud | Free | burst to 0.5 vCPU | 512 MB | 1 GiB | not disclosed | not disclosed | not disclosed | not disclosed |
| Neo4j Aura | Google Cloud | AuraDB Free | vCPU (numeric allocation not disclosed) | 1 GB | 2 GB | not disclosed | not disclosed | not disclosed | not disclosed |
| Memgraph | Memgraph Cloud | Free | vCPU (numeric allocation not disclosed) | 2 GB | 14 GB | not disclosed | not disclosed | not disclosed | not disclosed |
| FalkorDB | AWS | FalkorDB Free | vCPU (numeric allocation not disclosed) | 100 MB | 100 MB | ap-south-1 | v4.20.1 | disabled | disabled |
| ArangoGraph | ArangoGraph Insights Platform | Free | VCPU (numeric allocation not disclosed) | 1.02 GB | 4 GiB | not disclosed | 3.12.10-1 | not disclosed | not disclosed |

Because the deployments are not resource-equivalent, performance comparisons should be described as configuration-specific observations.

## Data Loading

The same controlled dataset was loaded into all five platforms and the resulting graph was verified by node/relationship counts.

| Platform | Load time |
|---|---:|
| CognoDB | **303.048 s** |
| Neo4j Aura | **82.968 s** |
| Memgraph | **2750.520 s** |
| FalkorDB | **2430.751 s** |
| ArangoGraph | **229.455 s** |

Approximate rates calculated from the common graph size are:

| Platform | Mushroom nodes/s | Relationships/s |
|---|---:|---:|
| CognoDB | 98.99 | 1,184.9 |
| Neo4j Aura | 361.59 | 4,328.2 |
| Memgraph | 10.91 | 130.55 |
| FalkorDB | 12.34 | 147.73 |
| ArangoGraph | 130.74 | 1,564.9 |

These ingestion rates are also configuration-dependent and should not be treated as intrinsic engine limits.

## Standard Workloads

Seven logical workloads were used:

1. `1_hop_habitat`
2. `2_hop_shared_stem_root`
3. `3_hop_stem_root_season`
4. `point_lookup`
5. `indexed_habitat_lookup`
6. `aggregation`
7. `mixed_read_write`

The Cypher-compatible platforms use Cypher; ArangoGraph uses AQL implementations with equivalent logical semantics.

Semantic validation was performed before the final 120-run campaign. Representative reference values included:

- 1-hop habitat for the reference node: `d`
- 2-hop shared stem-root count: `1563`
- 3-hop stem-root/season count: `3`
- Indexed habitat lookup for `d`: `21715`
- Aggregation: `e=13245`, `p=16755`

## Standard Benchmark Method

- Warm-up runs: **10**
- Measured runs: **120**
- Random seed: **42**
- Deterministic start-node pool: 5 Mushroom IDs
- Habitat values cycled deterministically
- Metrics: mean, p50, p95, p99, min, max, QPS

All five final result files contained **7 workloads with 120 measured and 10 warm-up runs**.

## Standard Benchmark Results

### Mean latency / throughput by platform

Across the seven workloads, mean QPS was:

| Platform | Mean QPS across 7 workloads |
|---|---:|
| **FalkorDB** | **32.96** |
| **Neo4j Aura** | **9.13** |
| **Memgraph** | **5.70** |
| **ArangoGraph** | **3.12** |
| **CognoDB** | **1.49** |

These are simple averages across the seven reported workload QPS values and are intended only as a compact summary; the per-workload data in `results/summary/standard_summary.csv` is the primary result.

### Representative standard results

| Platform | Workload | Mean ms | P50 ms | P95 ms | P99 ms | QPS |
|---|---|---:|---:|---:|---:|---:|
| Neo4j Aura | 1-hop habitat | 104.95 | 103.90 | 107.99 | 110.48 | 9.53 |
| Neo4j Aura | 2-hop shared stem root | 108.25 | 105.36 | 111.43 | 126.74 | 9.24 |
| Neo4j Aura | 3-hop stem-root season | 109.73 | 106.50 | 112.39 | 179.26 | 9.11 |
| Neo4j Aura | aggregation | 115.86 | 113.93 | 128.62 | 142.54 | 8.63 |
| Memgraph | 1-hop habitat | 172.96 | 172.10 | 176.66 | 179.57 | 5.78 |
| Memgraph | aggregation | 181.76 | 176.78 | 216.98 | 255.19 | 5.50 |
| FalkorDB | 1-hop habitat | 30.77 | 30.09 | 31.94 | 33.11 | 32.50 |
| FalkorDB | indexed habitat lookup | 27.45 | 27.19 | 29.76 | 29.93 | 36.43 |
| FalkorDB | aggregation | 32.71 | 32.44 | 34.27 | 41.26 | 30.57 |
| ArangoGraph | 1-hop habitat | 306.78 | 305.27 | 382.06 | 393.82 | 3.26 |
| ArangoGraph | 3-hop stem-root season | 379.52 | 307.18 | 860.50 | 921.73 | 2.63 |
| CognoDB | 1-hop habitat | 637.24 | 581.46 | 1023.28 | 1256.29 | 1.57 |
| CognoDB | aggregation | 661.27 | 612.78 | 1333.56 | 1534.18 | 1.51 |
| CognoDB | mixed read/write | 1501.36 | 1435.62 | 1922.95 | 2030.47 | 0.67 |

The complete per-workload table is stored in `results/summary/standard_summary.csv`.

## Concurrency Benchmark

The concurrency experiment used:

- 1, 2, 4, 8, 16, 40 concurrent clients
- 10-second warm-up
- 30-second measurement
- mixed read/write workload
- 80% reads / 20% writes by the benchmark worker selection logic
- random seed 42
- metrics: overall QPS, read QPS, write QPS, p50, p95, p99, error count

All five platforms completed all six concurrency levels with **zero reported benchmark errors**.

### Concurrency results

| Platform | Clients | Overall QPS | p50 ms | p95 ms | p99 ms |
|---|---:|---:|---:|---:|---:|
| Neo4j Aura | 1 | 7.10 | 114.64 | 134.03 | 374.19 |
| Neo4j Aura | 2 | 17.80 | 106.31 | 114.30 | 311.90 |
| Neo4j Aura | 4 | 35.40 | 110.14 | 119.17 | 132.37 |
| Neo4j Aura | 8 | 70.03 | 108.69 | 121.47 | 307.81 |
| Neo4j Aura | 16 | 140.80 | 107.18 | 119.19 | 311.55 |
| Neo4j Aura | 40 | **344.63** | 108.43 | 145.92 | 218.88 |
| Memgraph | 1 | 5.70 | 172.31 | 180.81 | 196.33 |
| Memgraph | 2 | 11.27 | 174.11 | 184.04 | 208.14 |
| Memgraph | 4 | 22.97 | 170.93 | 185.34 | 190.92 |
| Memgraph | 8 | 42.93 | 181.82 | 205.99 | 235.11 |
| Memgraph | 16 | 83.90 | 181.34 | 217.21 | 390.57 |
| Memgraph | 40 | 131.77 | 299.28 | 363.30 | 394.15 |
| FalkorDB | 1 | **33.90** | 29.38 | 31.01 | 32.95 |
| FalkorDB | 2 | 68.73 | 28.12 | 31.29 | 33.35 |
| FalkorDB | 4 | 137.17 | 27.83 | 32.35 | 35.65 |
| FalkorDB | 8 | 142.07 | 65.22 | 88.33 | 92.37 |
| FalkorDB | 16 | 141.77 | 101.78 | 176.18 | 182.67 |
| FalkorDB | 40 | 143.67 | 283.33 | 298.76 | 304.16 |
| ArangoGraph | 1 | 3.13 | 306.89 | 389.07 | 474.95 |
| ArangoGraph | 2 | 6.30 | 272.62 | 393.41 | 415.05 |
| ArangoGraph | 4 | 12.50 | 271.99 | 407.37 | 506.94 |
| ArangoGraph | 8 | 17.90 | 402.79 | 604.25 | 763.43 |
| ArangoGraph | 16 | 23.17 | 607.06 | 1096.10 | 1198.66 |
| ArangoGraph | 40 | 26.40 | 1402.19 | 2592.31 | 3042.87 |
| CognoDB | 1 | 1.37 | 610.86 | 1395.70 | 1434.77 |
| CognoDB | 2 | 2.23 | 661.47 | 1615.01 | 1851.87 |
| CognoDB | 4 | 4.13 | 811.71 | 1876.56 | 2331.12 |
| CognoDB | 8 | 7.00 | 1023.30 | 2048.54 | 2243.17 |
| CognoDB | 16 | 14.03 | 1071.49 | 1989.73 | 2202.79 |
| CognoDB | 40 | 28.73 | 1317.96 | 1592.72 | 2631.76 |

The complete machine-readable table is stored in `results/summary/concurrency_summary.csv`.

## Main Findings

### 1. FalkorDB showed the strongest standard single-request performance

FalkorDB had the lowest standard-workload latencies across the measured seven-workload set. Its reported QPS values were substantially higher than the other platforms in this experiment.

### 2. Neo4j Aura showed the strongest concurrency scaling

At one concurrent client, Neo4j Aura achieved 7.10 QPS. At 40 clients it reached 344.63 QPS while retaining a p50 latency of about 108 ms. This was the highest overall QPS observed in the concurrency experiment.

### 3. FalkorDB saturated earlier under concurrency

FalkorDB began at 33.90 QPS with one client and reached 137.17 QPS at four clients, but throughput then flattened near 142-144 QPS as concurrency increased. At the same time, p50 latency rose substantially, reaching 283.33 ms at 40 clients.

### 4. Memgraph scaled steadily but degraded at higher concurrency

Memgraph rose from 5.70 QPS at one client to 131.77 QPS at 40 clients. However, p50 latency increased from 172 ms to about 299 ms and p95 increased to about 363 ms.

### 5. ArangoGraph and CognoDB exhibited high concurrency latency in the tested configurations

At 40 clients, ArangoGraph reached 26.40 QPS with p50 around 1.40 s and p95 around 2.59 s. CognoDB reached 28.73 QPS with p50 around 1.32 s and p95 around 1.59 s.

## Interpreting the Results Carefully

The data supports several observations about the tested deployments, but it does not support a claim that one database engine is universally superior.

The service configurations were materially different. For example, the recorded memory allocations ranged from 100 MB for the FalkorDB free-tier deployment to 2 GB for Memgraph, with different CPU/resource models across providers. Therefore, differences in latency, throughput, and ingestion rate may reflect both database implementation and managed-service resource constraints.

The benchmark also used provider-managed cloud deployments with different architectures, network paths, service layers, and free-tier limits. These factors are part of the real-world evaluation, but they limit strict apples-to-apples hardware conclusions.

## Reproducibility

The repository contains:

- platform adapters under `src/benchmark/platforms/`
- dataset/loading code under `src/benchmark/`
- benchmark runners under `scripts/`
- final raw measurements under `results/raw/final/`
- consolidated tables under `results/summary/`
- generated figures under `results/figures/`
- environment template in `.env.example`
- dependencies in `requirements.txt`

The `.env` file is intentionally excluded from version control.

### Standard benchmark

```bash
PYTHONPATH=src python scripts/run_five_platform_benchmark.py \
  --platform <platform> \
  --warmup 10 \
  --runs 120
```

Supported platforms:

```text
cognodb
neo4j_aura
memgraph
falkordb
arangodb
```

### Concurrency benchmark

```bash
PYTHONPATH=src python scripts/run_concurrent_benchmark.py \
  --platform <platform> \
  --concurrency 1 2 4 8 16 40 \
  --warmup 10 \
  --seconds 30
```

## Repository Outputs

The primary final outputs are:

- `results/raw/final/*_standard_120runs.json`
- `results/raw/final/*_concurrent_results.json`
- `results/summary/standard_summary.csv`
- `results/summary/concurrency_summary.csv`
- `results/summary/deployment_config.csv`
- `results/figures/standard_p50_latency.png`
- `results/figures/standard_p95_latency.png`
- `results/figures/standard_qps.png`
- `results/figures/concurrency_qps.png`
- `results/figures/concurrency_p95.png`

## Limitations

1. The platforms were tested using managed/free-tier configurations with different resource allocations.
2. Some deployment metadata such as numeric CPU allocation, exact region, version, or HA/replication settings was not publicly disclosed in the available deployment UI and is marked as `not disclosed` rather than inferred.
3. Network and service-layer latency are included in the measured end-to-end timings.
4. The concurrency workload is a benchmark-level mixed read/write workload and is not intended to represent a universal production traffic mix.
5. ArangoGraph uses a native AQL representation of the same logical graph rather than the same storage/query syntax used by the Cypher platforms.

## Conclusion

Under the specific managed-service configurations tested, FalkorDB provided the strongest standard-workload latency/throughput performance, while Neo4j Aura demonstrated the strongest scaling in the 1-to-40-client concurrency sweep. Memgraph showed intermediate behavior, while ArangoGraph and CognoDB showed substantially higher latency at high concurrency in the tested configurations.

These conclusions are specific to the benchmark dataset, workload definitions, network path, and service tiers used in this experiment. They should be reproduced with matched resource allocations and production-like workloads before being generalized to broader platform-selection decisions.
