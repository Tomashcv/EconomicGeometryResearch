from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


REPLICATE_COUNT = 160
ASEC_VARIANCE_FACTOR = 4.0 / REPLICATE_COUNT


@dataclass(frozen=True)
class ShareInference:
    theta0: float
    replicate_estimates: np.ndarray
    variance: float
    standard_error: float


@dataclass(frozen=True)
class DifferenceInference:
    delta0: float
    replicate_differences: np.ndarray
    variance: float
    standard_error: float


def _as_1d_float(name: str, x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)

    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")

    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains non-finite values")

    return arr


def _as_binary_indicator(name: str, x) -> np.ndarray:
    arr = _as_1d_float(name, x)

    if not np.isin(arr, [0.0, 1.0]).all():
        raise ValueError(f"{name} must contain only 0/1")

    return arr


def _as_bool_mask(name: str, x, n: int) -> np.ndarray:
    arr = np.asarray(x)

    if arr.ndim != 1 or len(arr) != n:
        raise ValueError(f"{name} must be a one-dimensional mask of length {n}")

    if arr.dtype != np.bool_:
        if not np.isin(arr, [0, 1, False, True]).all():
            raise ValueError(f"{name} must be boolean")
        arr = arr.astype(bool)

    return arr


def _as_replicate_matrix(name: str, x, n: int) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)

    if arr.shape != (n, REPLICATE_COUNT):
        raise ValueError(
            f"{name} must have shape ({n}, {REPLICATE_COUNT}), "
            f"observed={arr.shape}"
        )

    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains non-finite values")

    # Negative replicate weights are explicitly permitted by the official
    # ASEC design. Do not clip or reject them here.
    return arr


def weighted_share(indicator, weights) -> float:
    z = _as_binary_indicator("indicator", indicator)
    w = _as_1d_float("weights", weights)

    if len(z) != len(w):
        raise ValueError("indicator and weights length mismatch")

    denominator = float(np.sum(w))

    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("weighted-share denominator must be finite and positive")

    numerator = float(np.dot(z, w))
    theta = numerator / denominator

    if not math.isfinite(theta):
        raise ValueError("weighted share is non-finite")

    return theta


def asec_variance(theta0: float, replicate_estimates) -> float:
    reps = _as_1d_float("replicate_estimates", replicate_estimates)

    if len(reps) != REPLICATE_COUNT:
        raise ValueError(
            f"exactly {REPLICATE_COUNT} replicate estimates are required"
        )

    theta0 = float(theta0)

    if not math.isfinite(theta0):
        raise ValueError("theta0 must be finite")

    variance = ASEC_VARIANCE_FACTOR * float(
        np.sum((reps - theta0) ** 2)
    )

    if not math.isfinite(variance) or variance < 0.0:
        raise ValueError("ASEC variance is invalid")

    return variance


def weighted_share_with_replicates(
    indicator,
    full_sample_weights,
    replicate_weights,
) -> ShareInference:
    z = _as_binary_indicator("indicator", indicator)
    w0 = _as_1d_float("full_sample_weights", full_sample_weights)

    if len(z) != len(w0):
        raise ValueError("indicator/full-sample weight length mismatch")

    wr = _as_replicate_matrix(
        "replicate_weights",
        replicate_weights,
        len(z),
    )

    theta0 = weighted_share(z, w0)

    denominators = np.sum(wr, axis=0)

    if not np.isfinite(denominators).all():
        raise ValueError("replicate denominator contains non-finite values")

    if np.any(denominators <= 0.0):
        raise ValueError(
            "every replicate domain denominator must be strictly positive"
        )

    numerators = z @ wr
    reps = numerators / denominators

    if not np.isfinite(reps).all():
        raise ValueError("replicate share contains non-finite values")

    variance = asec_variance(theta0, reps)

    return ShareInference(
        theta0=theta0,
        replicate_estimates=np.asarray(reps, dtype=np.float64),
        variance=variance,
        standard_error=math.sqrt(variance),
    )


def owner_renter_difference_with_replicates(
    indicator,
    owner_mask,
    renter_mask,
    full_sample_weights,
    replicate_weights,
) -> DifferenceInference:
    z = _as_binary_indicator("indicator", indicator)
    w0 = _as_1d_float("full_sample_weights", full_sample_weights)

    if len(z) != len(w0):
        raise ValueError("indicator/full-sample weight length mismatch")

    owner = _as_bool_mask("owner_mask", owner_mask, len(z))
    renter = _as_bool_mask("renter_mask", renter_mask, len(z))

    if np.any(owner & renter):
        raise ValueError("owner and renter masks must be disjoint")

    if not owner.any() or not renter.any():
        raise ValueError("owner and renter domains must both be nonempty")

    wr = _as_replicate_matrix(
        "replicate_weights",
        replicate_weights,
        len(z),
    )

    owner_inf = weighted_share_with_replicates(
        z[owner],
        w0[owner],
        wr[owner, :],
    )

    renter_inf = weighted_share_with_replicates(
        z[renter],
        w0[renter],
        wr[renter, :],
    )

    delta0 = renter_inf.theta0 - owner_inf.theta0
    delta_reps = (
        renter_inf.replicate_estimates
        - owner_inf.replicate_estimates
    )

    variance = asec_variance(delta0, delta_reps)

    return DifferenceInference(
        delta0=float(delta0),
        replicate_differences=np.asarray(
            delta_reps,
            dtype=np.float64,
        ),
        variance=variance,
        standard_error=math.sqrt(variance),
    )
