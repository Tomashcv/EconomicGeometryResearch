from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np


IMPLICATE_COUNT = 5
REPLICATE_COUNT = 999

IMPUTATION_VARIANCE_DIVISOR = IMPLICATE_COUNT - 1
SAMPLING_VARIANCE_DIVISOR = REPLICATE_COUNT - 1
MI_MULTIPLIER = (IMPLICATE_COUNT + 1.0) / IMPLICATE_COUNT


@dataclass(frozen=True)
class SCFInference:
    pooled_point: float
    implicate_statistics: np.ndarray
    imputation_variance: float
    replicate_statistics: np.ndarray
    replicate_mean: float
    sampling_variance: float
    combined_variance: float
    combined_se: float


@dataclass(frozen=True)
class SCFDifferenceInference:
    pooled_difference: float
    implicate_differences: np.ndarray
    imputation_variance: float
    replicate_differences: np.ndarray
    replicate_mean_difference: float
    sampling_variance: float
    combined_variance: float
    combined_se: float


def _as_float_array(name: str, x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)

    if np.isinf(arr).any():
        raise ValueError(f"{name} contains infinite values")

    return arr


def _as_finite_2d(name: str, x, shape: tuple[int, int]) -> np.ndarray:
    arr = _as_float_array(name, x)

    if arr.shape != shape:
        raise ValueError(
            f"{name} must have shape {shape}, observed={arr.shape}"
        )

    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains non-finite values")

    return arr


def _as_domain_matrix(name: str, x, n: int) -> np.ndarray:
    arr = np.asarray(x)

    if arr.shape != (n, IMPLICATE_COUNT):
        raise ValueError(
            f"{name} must have shape ({n}, {IMPLICATE_COUNT}), "
            f"observed={arr.shape}"
        )

    if arr.dtype != np.bool_:
        if not np.isin(arr, [0, 1, False, True]).all():
            raise ValueError(f"{name} must be boolean")
        arr = arr.astype(bool)

    return arr


def effective_replicate_weights(
    raw_weights,
    multiplicities,
) -> np.ndarray:
    """
    Exact SCF codebook semantics:
        MAX(0, WT1B_r) * MAX(0, MM_r)

    Missing (NaN) entries correspond to cases not selected in a replicate and
    therefore contribute zero. Infinite values are rejected.
    """
    rw = _as_float_array("raw_weights", raw_weights)
    mm = _as_float_array("multiplicities", multiplicities)

    if rw.shape != mm.shape:
        raise ValueError("raw weight / multiplicity shape mismatch")

    if rw.ndim != 2 or rw.shape[1] != REPLICATE_COUNT:
        raise ValueError(
            f"replicate matrices must have exactly {REPLICATE_COUNT} columns"
        )

    rw_pos = np.where(
        np.isfinite(rw) & (rw > 0.0),
        rw,
        0.0,
    )
    mm_pos = np.where(
        np.isfinite(mm) & (mm > 0.0),
        mm,
        0.0,
    )

    out = rw_pos * mm_pos

    if not np.isfinite(out).all():
        raise ValueError("effective replicate weight is non-finite")

    return out


def weighted_mean(values, weights) -> float:
    x = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)

    if x.ndim != 1 or w.ndim != 1 or len(x) != len(w):
        raise ValueError("weighted_mean expects equal-length 1D arrays")

    if not np.isfinite(x).all():
        raise ValueError("weighted_mean values must be finite")

    if not np.isfinite(w).all():
        raise ValueError("weighted_mean weights must be finite")

    if np.any(w < 0.0):
        raise ValueError("effective weights must be nonnegative")

    denominator = float(np.sum(w))

    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("weighted_mean denominator must be positive")

    result = float(np.dot(x, w) / denominator)

    if not math.isfinite(result):
        raise ValueError("weighted_mean result is non-finite")

    return result


def weighted_median(values, weights) -> float:
    x = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)

    if x.ndim != 1 or w.ndim != 1 or len(x) != len(w):
        raise ValueError("weighted_median expects equal-length 1D arrays")

    if not np.isfinite(x).all():
        raise ValueError("weighted_median values must be finite")

    if not np.isfinite(w).all():
        raise ValueError("weighted_median weights must be finite")

    if np.any(w < 0.0):
        raise ValueError("effective weights must be nonnegative")

    denominator = float(np.sum(w))

    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("weighted_median denominator must be positive")

    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    ws = w[order]

    cumulative = np.cumsum(ws) / denominator
    idx = int(np.searchsorted(cumulative, 0.5, side="left"))

    if idx >= len(xs):
        raise ValueError("weighted_median threshold not reached")

    result = float(xs[idx])

    if not math.isfinite(result):
        raise ValueError("weighted_median result is non-finite")

    return result


def _statistic(
    values: np.ndarray,
    weights: np.ndarray,
    statistic: Literal["mean", "median"],
) -> float:
    if statistic == "mean":
        return weighted_mean(values, weights)

    if statistic == "median":
        return weighted_median(values, weights)

    raise ValueError(f"unsupported statistic={statistic}")


def _sample_variance(values: np.ndarray, expected_n: int) -> float:
    arr = np.asarray(values, dtype=np.float64)

    if arr.ndim != 1 or len(arr) != expected_n:
        raise ValueError(f"expected exactly {expected_n} statistics")

    if not np.isfinite(arr).all():
        raise ValueError("variance input contains non-finite values")

    center = float(np.mean(arr))
    variance = float(
        np.sum((arr - center) ** 2) / (expected_n - 1)
    )

    if not math.isfinite(variance) or variance < 0.0:
        raise ValueError("sample variance invalid")

    return variance


def scf_statistic_inference(
    values_by_implicate,
    full_weights_by_implicate,
    effective_sampling_weights,
    domains_by_implicate,
    *,
    statistic: Literal["mean", "median"] = "mean",
) -> SCFInference:
    values = np.asarray(values_by_implicate, dtype=np.float64)

    if values.ndim != 2 or values.shape[1] != IMPLICATE_COUNT:
        raise ValueError(
            f"values must have exactly {IMPLICATE_COUNT} implicates"
        )

    n = values.shape[0]

    if not np.isfinite(values).all():
        raise ValueError("values contain non-finite entries")

    w0 = _as_finite_2d(
        "full_weights_by_implicate",
        full_weights_by_implicate,
        (n, IMPLICATE_COUNT),
    )

    if np.any(w0 < 0.0):
        raise ValueError("full-sample weights must be nonnegative")

    wr = _as_finite_2d(
        "effective_sampling_weights",
        effective_sampling_weights,
        (n, REPLICATE_COUNT),
    )

    if np.any(wr < 0.0):
        raise ValueError("effective sampling weights must be nonnegative")

    domain = _as_domain_matrix(
        "domains_by_implicate",
        domains_by_implicate,
        n,
    )

    implicate_stats = np.empty(IMPLICATE_COUNT, dtype=np.float64)

    for m in range(IMPLICATE_COUNT):
        mask = domain[:, m]

        if not mask.any():
            raise ValueError(f"implicate {m+1} domain is empty")

        implicate_stats[m] = _statistic(
            values[mask, m],
            w0[mask, m],
            statistic,
        )

    pooled = float(np.mean(implicate_stats))
    imp_var = _sample_variance(
        implicate_stats,
        IMPLICATE_COUNT,
    )

    first_mask = domain[:, 0]

    if not first_mask.any():
        raise ValueError("first implicate sampling domain is empty")

    first_values = values[first_mask, 0]
    first_wr = wr[first_mask, :]

    rep_denominators = np.sum(first_wr, axis=0)

    if not np.isfinite(rep_denominators).all():
        raise ValueError("replicate denominator non-finite")

    if np.any(rep_denominators <= 0.0):
        raise ValueError(
            "every SCF replicate domain denominator must be positive"
        )

    rep_stats = np.empty(REPLICATE_COUNT, dtype=np.float64)

    for r in range(REPLICATE_COUNT):
        rep_stats[r] = _statistic(
            first_values,
            first_wr[:, r],
            statistic,
        )

    rep_mean = float(np.mean(rep_stats))
    sampling_var = _sample_variance(
        rep_stats,
        REPLICATE_COUNT,
    )

    combined_var = (
        MI_MULTIPLIER * imp_var
        + sampling_var
    )

    if not math.isfinite(combined_var) or combined_var < 0.0:
        raise ValueError("combined variance invalid")

    return SCFInference(
        pooled_point=pooled,
        implicate_statistics=implicate_stats,
        imputation_variance=imp_var,
        replicate_statistics=rep_stats,
        replicate_mean=rep_mean,
        sampling_variance=sampling_var,
        combined_variance=combined_var,
        combined_se=math.sqrt(combined_var),
    )


def scf_owner_renter_difference_inference(
    values_by_implicate,
    full_weights_by_implicate,
    effective_sampling_weights,
    owner_domains_by_implicate,
    renter_domains_by_implicate,
    *,
    statistic: Literal["mean", "median"] = "mean",
) -> SCFDifferenceInference:
    values = np.asarray(values_by_implicate, dtype=np.float64)

    if values.ndim != 2 or values.shape[1] != IMPLICATE_COUNT:
        raise ValueError(
            f"values must have exactly {IMPLICATE_COUNT} implicates"
        )

    n = values.shape[0]

    if not np.isfinite(values).all():
        raise ValueError("values contain non-finite entries")

    w0 = _as_finite_2d(
        "full_weights_by_implicate",
        full_weights_by_implicate,
        (n, IMPLICATE_COUNT),
    )

    if np.any(w0 < 0.0):
        raise ValueError("full-sample weights must be nonnegative")

    wr = _as_finite_2d(
        "effective_sampling_weights",
        effective_sampling_weights,
        (n, REPLICATE_COUNT),
    )

    if np.any(wr < 0.0):
        raise ValueError("effective sampling weights must be nonnegative")

    owner = _as_domain_matrix(
        "owner_domains_by_implicate",
        owner_domains_by_implicate,
        n,
    )

    renter = _as_domain_matrix(
        "renter_domains_by_implicate",
        renter_domains_by_implicate,
        n,
    )

    if np.any(owner & renter):
        raise ValueError("owner and renter domains must be disjoint")

    deltas = np.empty(IMPLICATE_COUNT, dtype=np.float64)

    for m in range(IMPLICATE_COUNT):
        om = owner[:, m]
        rm = renter[:, m]

        if not om.any() or not rm.any():
            raise ValueError(
                f"owner/renter domain empty in implicate {m+1}"
            )

        owner_stat = _statistic(
            values[om, m],
            w0[om, m],
            statistic,
        )
        renter_stat = _statistic(
            values[rm, m],
            w0[rm, m],
            statistic,
        )

        deltas[m] = renter_stat - owner_stat

    pooled_delta = float(np.mean(deltas))
    imp_var = _sample_variance(
        deltas,
        IMPLICATE_COUNT,
    )

    owner_first = owner[:, 0]
    renter_first = renter[:, 0]

    owner_wr = wr[owner_first, :]
    renter_wr = wr[renter_first, :]

    owner_den = np.sum(owner_wr, axis=0)
    renter_den = np.sum(renter_wr, axis=0)

    if (
        not np.isfinite(owner_den).all()
        or not np.isfinite(renter_den).all()
        or np.any(owner_den <= 0.0)
        or np.any(renter_den <= 0.0)
    ):
        raise ValueError(
            "every owner/renter replicate denominator must be positive"
        )

    delta_reps = np.empty(REPLICATE_COUNT, dtype=np.float64)

    owner_values = values[owner_first, 0]
    renter_values = values[renter_first, 0]

    for r in range(REPLICATE_COUNT):
        owner_stat = _statistic(
            owner_values,
            owner_wr[:, r],
            statistic,
        )
        renter_stat = _statistic(
            renter_values,
            renter_wr[:, r],
            statistic,
        )

        delta_reps[r] = renter_stat - owner_stat

    rep_mean_delta = float(np.mean(delta_reps))
    sampling_var = _sample_variance(
        delta_reps,
        REPLICATE_COUNT,
    )

    combined_var = (
        MI_MULTIPLIER * imp_var
        + sampling_var
    )

    if not math.isfinite(combined_var) or combined_var < 0.0:
        raise ValueError("combined difference variance invalid")

    return SCFDifferenceInference(
        pooled_difference=pooled_delta,
        implicate_differences=deltas,
        imputation_variance=imp_var,
        replicate_differences=delta_reps,
        replicate_mean_difference=rep_mean_delta,
        sampling_variance=sampling_var,
        combined_variance=combined_var,
        combined_se=math.sqrt(combined_var),
    )
