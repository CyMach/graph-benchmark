from statistics import mean


def percentile(values, percentile):
    if not values:
        return None

    values = sorted(values)

    index = (len(values) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    weight = index - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )


def summarize(latencies_ms, elapsed_seconds):
    if not latencies_ms:
        return {}

    return {
        "count": len(latencies_ms),
        "mean_ms": mean(latencies_ms),
        "p50_ms": percentile(latencies_ms, 0.50),
        "p95_ms": percentile(latencies_ms, 0.95),
        "min_ms": min(latencies_ms),
        "max_ms": max(latencies_ms),
        "throughput_qps": (
            len(latencies_ms) / elapsed_seconds
            if elapsed_seconds > 0
            else None
        ),
    }
