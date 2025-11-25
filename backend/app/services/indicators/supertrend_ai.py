"""Pure-Python implementation of the SuperTrend AI (clustering) indicator.

This is a best-effort translation of the Pine Script logic into Python using
only the standard library so it can run inside the backend without extra
dependencies.

API:
  compute_supertrend(candles, length=10, min_mult=1.0, max_mult=5.0, step=0.5,
                     perf_alpha=10.0, max_iter=1000, max_data=10000, from_cluster='Best')

candles: sequence of dicts with keys: t (iso string or int), o, h, l, c, v
Returns: dict with summary fields and per-bar outputs (list)
"""

from typing import List, Dict, Any, Optional, Tuple
import math
from statistics import mean
from datetime import datetime


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def _percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    d0 = s[int(f)] * (c - k)
    d1 = s[int(c)] * (k - f)
    return d0 + d1


def _ema(values: List[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if period <= 0 or not values:
        return out
    # seed with simple average
    if len(values) >= period:
        seed = mean(values[:period])
        out[period - 1] = seed
        mult = 2.0 / (period + 1)
        for i in range(period, len(values)):
            out[i] = (values[i] - out[i - 1]) * mult + out[i - 1]
    else:
        # not enough values: simple cumulative average
        s = 0.0
        for i, v in enumerate(values):
            s += v
            out[i] = s / (i + 1)
    return out


def compute_supertrend(
    candles: List[Dict[str, Any]],
    length: int = 10,
    min_mult: float = 1.0,
    max_mult: float = 5.0,
    step: float = 0.5,
    perf_alpha: float = 10.0,
    from_cluster: str = "Best",
    max_iter: int = 1000,
    max_data: int = 10000,
) -> Dict[str, Any]:
    """Compute SuperTrend AI clustering over the supplied candles.

    Returns a dictionary with keys:
      - signals: list of per-bar dictionaries (timestamp, symbol optional, ts, perf_idx, target_factor, os, perf_ama, etc.)
      - summary: last signal dictionary
    """

    # transform candles to arrays (we expect dicts with keys 'o','h','l','c')
    highs = [float(c["h"]) for c in candles]
    lows = [float(c["l"]) for c in candles]
    closes = [float(c["c"]) for c in candles]
    hl2 = [(h + l) / 2.0 for h, l in zip(highs, lows)]

    n = len(candles)
    if n == 0:
        return {"signals": [], "summary": None}

    # ATR (Wilder style)
    trs: List[float] = []
    for i in range(n):
        if i == 0:
            trs.append(highs[i] - lows[i])
        else:
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
            trs.append(tr)

    atr = [None] * n
    if n >= length:
        # seed ATR as SMA of first length
        seed = mean(trs[:length])
        atr[length - 1] = seed
        for i in range(length, n):
            atr[i] = (atr[i - 1] * (length - 1) + trs[i]) / length
    else:
        # fallback: simple running average
        s = 0.0
        for i in range(n):
            s += trs[i]
            atr[i] = s / (i + 1)

    # prepare factors
    factors: List[float] = []
    i = 0
    while True:
        f = min_mult + i * step
        if f > max_mult + 1e-9:
            break
        factors.append(round(f, 6))
        i += 1

    m = len(factors)
    # structures to hold per-factor state
    outputs = [[None] * n for _ in range(m)]
    trends = [[0] * n for _ in range(m)]
    uppers = [[None] * n for _ in range(m)]
    lowers = [[None] * n for _ in range(m)]
    perfs = [[0.0] * n for _ in range(m)]

    # compute per-factor supertrend and perf
    for fi, factor in enumerate(factors):
        prev_output = None
        prev_upper = None
        prev_lower = None
        prev_trend = 0
        prev_perf = 0.0
        for idx in range(n):
            a = atr[idx] if atr[idx] is not None else 0.0
            up = hl2[idx] + a * factor
            dn = hl2[idx] - a * factor

            if idx == 0:
                cur_trend = 0
                cur_upper = up
                cur_lower = dn
                output = hl2[idx]
            else:
                # trend logic similar to pine: change when price crosses
                cur_trend = 1 if closes[idx] > (prev_upper if prev_upper is not None else up) else 0 if closes[idx] < (prev_lower if prev_lower is not None else dn) else prev_trend
                cur_upper = min(up, prev_upper) if closes[idx - 1] < (prev_upper if prev_upper is not None else up) else up
                cur_lower = max(dn, prev_lower) if closes[idx - 1] > (prev_lower if prev_lower is not None else dn) else dn
                output = cur_lower if cur_trend == 1 else cur_upper

            # perf update
            if idx == 0:
                perf = prev_perf
            else:
                # diff uses previous close vs previous output (approximation)
                diff = _sign(closes[idx - 1] - (prev_output if prev_output is not None else closes[idx - 1]))
                change = (closes[idx] - closes[idx - 1]) * diff
                k = 2.0 / (perf_alpha + 1.0)
                perf = prev_perf + k * (change - prev_perf)

            outputs[fi][idx] = output
            trends[fi][idx] = cur_trend
            uppers[fi][idx] = cur_upper
            lowers[fi][idx] = cur_lower
            perfs[fi][idx] = perf

            prev_output = output
            prev_upper = cur_upper
            prev_lower = cur_lower
            prev_trend = cur_trend
            prev_perf = perf

    # Prepare clustering over the most recent available perfs
    recent_perfs = [perfs[fi][-1] for fi in range(m)]

    # initialize centroids using quartiles
    centroids = [
        _percentile(recent_perfs, 25),
        _percentile(recent_perfs, 50),
        _percentile(recent_perfs, 75),
    ]

    # k-means k=3
    clusters: List[List[int]] = []
    for _ in range(max_iter):
        clusters = [[] for _ in range(3)]
        for fi, val in enumerate(recent_perfs):
            dists = [abs(val - c) for c in centroids]
            idx = dists.index(min(dists))
            clusters[idx].append(fi)

        new_centroids = []
        for cluster in clusters:
            if cluster:
                vals = [recent_perfs[i] for i in cluster]
                new_centroids.append(mean(vals))
            else:
                new_centroids.append(0.0)

        if all(abs(a - b) < 1e-12 for a, b in zip(new_centroids, centroids)):
            break
        centroids = new_centroids

    # identify 'Best' cluster by highest centroid
    order = sorted(range(3), key=lambda i: centroids[i])
    best_idx = order[2]
    avg_idx = order[1]
    worst_idx = order[0]

    mapping = {"Best": best_idx, "Average": avg_idx, "Worst": worst_idx}
    chosen_cluster = mapping.get(from_cluster, best_idx)

    # compute target_factor as average of factors in chosen cluster
    chosen_factors = [factors[i] for i in clusters[chosen_cluster]] if clusters[chosen_cluster] else [factors[best_idx]]
    target_factor = mean(chosen_factors) if chosen_factors else factors[0]

    # compute perf_idx as positive average perf over denominator (ema of abs delta)
    # den: EMA of abs(close - prev_close)
    diffs = [abs(closes[i] - closes[i - 1]) if i > 0 else 0.0 for i in range(n)]
    den_series = _ema(diffs, int(perf_alpha) if perf_alpha >= 1 else 1)
    den = den_series[-1] or 1.0
    avg_perf_cluster = mean([recent_perfs[i] for i in clusters[chosen_cluster]]) if clusters[chosen_cluster] else recent_perfs[best_idx]
    perf_idx = max(avg_perf_cluster, 0.0) / (den if den != 0 else 1.0)

    # compute trailing stop and perf_ama for last bar
    # find index of factor closest to target_factor
    closest_fi = min(range(m), key=lambda i: abs(factors[i] - target_factor))
    ts_series = outputs[closest_fi]
    ts_last = ts_series[-1]

    # perf_ama: we compute a simple adaptive MA on ts_series
    perf_amas = [None] * n
    for i in range(n):
        if i == 0:
            perf_amas[i] = ts_series[i]
        else:
            prev = perf_amas[i - 1] if perf_amas[i - 1] is not None else ts_series[i - 1]
            perf_amas[i] = prev + perf_idx * (ts_series[i] - prev)
    perf_ama_last = perf_amas[-1]

    # prepare per-bar outputs (we return only a compact set)
    signals: List[Dict[str, Any]] = []
    for i in range(n):
        signals.append(
            {
                "timestamp": candles[i].get("t") if isinstance(candles[i].get("t"), (str, int)) else None,
                "price": closes[i],
                "target_factor": target_factor,
                "perf_idx": perf_idx,
                "os": trends[closest_fi][i],
                "ts": outputs[closest_fi][i],
                "perf_ama": perf_amas[i],
            }
        )

    summary = signals[-1] if signals else None
    if summary is not None:
        summary.update({"factors": factors, "centroids": centroids, "clusters": clusters})

    return {"signals": signals, "summary": summary}
