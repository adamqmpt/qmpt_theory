"""
Toy implementations of QMPT metrics.
Shape follows QMPT specs: A(Ψ), R_norm(Ψ), O_self(Ψ).
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
import numpy as np

from .models import Pattern

METRICS_SCHEMA_VERSION = "0.2"


def estimate_anomaly(patterns: List[Pattern]) -> None:
    """
    Compute a toy anomaly score:
    A = w1 * rarity + w2 * distance + w3 * impact

    rarity   ~ inverse feature norm
    distance ~ distance from mean feature vector
    impact   ~ free scalar from metadata ("impact" fallback to 0.1)
    """
    if not patterns:
        return
    feats = [p.features for p in patterns if p.features is not None]
    if not feats:
        for p in patterns:
            p.anomaly_score = 0.1
        return
    stacked = np.stack(feats)
    mean_vec = np.mean(stacked, axis=0)
    for p in patterns:
        if p.features is None:
            p.anomaly_score = 0.1
            continue
        rarity = 1.0 / (np.linalg.norm(p.features) + 1e-6)
        distance = float(np.linalg.norm(p.features - mean_vec))
        impact = float(p.metadata.get("impact", 0.1))
        p.anomaly_score = float(0.5 * rarity + 0.3 * distance + 0.2 * impact)


def estimate_reflexivity(patterns: List[Pattern]) -> None:
    """
    Toy reflexivity R_norm in [0,1]:
    R_norm = sigmoid(var(features)) where variance approximates self-model richness.
    """
    for p in patterns:
        if p.features is None:
            p.reflexivity = 0.2
            continue
        var = float(np.var(p.features))
        p.reflexivity = float(1.0 / (1.0 + np.exp(-var)))


def estimate_self_operator(patterns: List[Pattern]) -> None:
    """
    O_self = alpha_pop * Q_pop + alpha_self * Q_self + alpha_meta * Q_meta + alpha_R * R_norm.
    Here we synthesize Q_pop/Q_self/Q_meta from simple heuristics.
    """
    alpha_pop = 0.25
    alpha_self = 0.25
    alpha_meta = 0.25
    alpha_R = 0.25
    for p in patterns:
        rarity_proxy = 1.0 / (np.linalg.norm(p.features) + 1e-6) if p.features is not None else 0.1
        q_pop = min(1.0, rarity_proxy)
        q_self = min(1.0, abs(p.anomaly_score or 0.0) / 5.0)
        q_meta = min(1.0, (p.metadata.get("meta_consistency", 0.2)))
        r_norm = p.reflexivity or 0.0
        p.self_operator = float(alpha_pop * q_pop + alpha_self * q_self + alpha_meta * q_meta + alpha_R * r_norm)


def compute_run_metrics(timeseries: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, float]:
    """
    Derive simple run-level metrics from timeseries.
    Works for classical (stress/protection/novelty/anomaly_proxy) and quantum
    (expectation_mean/entropy/anomaly_proxy) runs.
    """
    metrics: Dict[str, float] = {}
    sigma = _arr(timeseries, ["stress", "sigma_k"])
    anomaly_idx = _arr(timeseries, ["anomaly_proxy", "anomaly_index"])
    expectation = _arr(timeseries, ["expectation_mean"])
    entropy = _arr(timeseries, ["entropy"])

    sigma_crit = float(config.get("sigma_crit", 0.8))
    if sigma is not None and sigma.size > 0:
        metrics["max_sigma"] = float(np.max(sigma))
        metrics["sigma_time_above_crit"] = float(np.mean(sigma > sigma_crit))
        metrics["sigma_mean"] = float(np.mean(sigma))
        metrics["sigma_std"] = float(np.std(sigma))
    if anomaly_idx is not None and anomaly_idx.size > 0:
        metrics["anomaly_mean"] = float(np.mean(anomaly_idx))
        metrics["anomaly_std"] = float(np.std(anomaly_idx))
    if expectation is not None and expectation.size > 0:
        metrics["expectation_mean"] = float(np.mean(expectation))
        metrics["expectation_std"] = float(np.std(expectation))
        baseline = 0.0
        metrics["quantum_instability"] = float(np.mean(np.abs(expectation - baseline)))
    if entropy is not None and entropy.size > 0:
        metrics["entropy_mean"] = float(np.mean(entropy))
        metrics["entropy_std"] = float(np.std(entropy))
    # Ground truth comparisons (if provided)
    gt_anom = _arr(timeseries, ["anomaly_ground_truth", "anomaly_gt"])
    if gt_anom is not None and anomaly_idx is not None and gt_anom.size == anomaly_idx.size:
        metrics.update(_calibration_stats(anomaly_idx, gt_anom, threshold=config.get("anomaly_threshold", 0.5)))
    metrics["metrics_schema_version"] = METRICS_SCHEMA_VERSION
    return metrics


def compute_ensemble_summary(run_metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate metrics across multiple runs.
    Returns mean/std for sigma/anomaly/entropy when present, plus counts.
    """
    if not run_metrics_list:
        return {}
    keys = ["max_sigma", "sigma_mean", "anomaly_mean", "entropy_mean", "quantum_instability"]
    agg: Dict[str, float] = {"runs": len(run_metrics_list)}
    for key in keys:
        vals = [m[key] for m in run_metrics_list if key in m]
        if not vals:
            continue
        arr = np.array(vals, dtype=float)
        agg[f"{key}_mean"] = float(np.mean(arr))
        agg[f"{key}_std"] = float(np.std(arr))
        agg[f"{key}_min"] = float(np.min(arr))
        agg[f"{key}_max"] = float(np.max(arr))
    # Count near-breakdown runs (sigma > 0.9)
    high_sigma = [m["max_sigma"] for m in run_metrics_list if "max_sigma" in m]
    if high_sigma:
        agg["near_breakdown_runs"] = int(np.sum(np.array(high_sigma) > 0.9))
    # simple percentile bootstrap CI for anomaly_mean if available
    anoms = [m["anomaly_mean"] for m in run_metrics_list if "anomaly_mean" in m]
    if anoms:
        agg.update(_bootstrap_ci(np.array(anoms, dtype=float), "anomaly_mean"))
    return agg


# Quantum metrics

def quantum_entropy(statevector: np.ndarray) -> float:
    if statevector is None:
        return 0.0
    rho = _statevector_to_density(statevector)
    eigvals = np.real(np.linalg.eigvals(rho))
    eigvals = eigvals[eigvals > 1e-12]
    return float(-np.sum(eigvals * np.log2(eigvals)))


def entanglement_entropy(statevector: np.ndarray, subsystem: list[int]) -> float:
    if statevector is None:
        return 0.0
    rho = _statevector_to_density(statevector)
    reduced = _partial_trace(rho, subsystem)
    eigvals = np.real(np.linalg.eigvals(reduced))
    eigvals = eigvals[eigvals > 1e-12]
    return float(-np.sum(eigvals * np.log2(eigvals)))


def mutual_information(statevector: np.ndarray, A: list[int], B: list[int]) -> float:
    if statevector is None:
        return 0.0
    rho = _statevector_to_density(statevector)
    sA = entanglement_entropy(statevector, A)
    sB = entanglement_entropy(statevector, B)
    sAB = _entropy_from_density(_partial_trace(rho, A + B))
    return float(sA + sB - sAB)


def _statevector_to_density(statevector: np.ndarray) -> np.ndarray:
    sv = np.array(statevector, dtype=complex)
    return np.outer(sv, np.conjugate(sv))


def _partial_trace(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    # Basic partial trace for small systems; keep qubits listed in keep.
    dim = rho.shape[0]
    n = int(np.log2(dim))
    keep_set = set(keep)
    reshaped = rho.reshape([2] * (2 * n))
    axes_to_trace = []
    for qubit in range(n):
        if qubit not in keep_set:
            axes_to_trace.extend([qubit, qubit + n])
    reduced = np.trace(reshaped, axis1=axes_to_trace[0], axis2=axes_to_trace[1]) if axes_to_trace else rho
    # If more than one pair to trace, iteratively trace
    if len(axes_to_trace) > 2:
        for i in range(2, len(axes_to_trace), 2):
            reduced = np.trace(reduced, axis1=axes_to_trace[i] - i, axis2=axes_to_trace[i + 1] - i)
    return reduced


def _entropy_from_density(rho: np.ndarray) -> float:
    eigvals = np.real(np.linalg.eigvals(rho))
    eigvals = eigvals[eigvals > 1e-12]
    return float(-np.sum(eigvals * np.log2(eigvals)))


def _arr(timeseries: Dict[str, Any], keys: List[str]):
    for k in keys:
        if k in timeseries:
            return np.array(timeseries[k])
    return None


def _calibration_stats(pred: np.ndarray, truth: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    pred = np.array(pred, dtype=float)
    truth = np.array(truth, dtype=float)
    mse = float(np.mean((pred - truth) ** 2))
    bias = float(np.mean(pred - truth))
    # simple classification threshold
    pred_bin = pred >= threshold
    truth_bin = truth >= threshold
    tp = float(np.sum(pred_bin & truth_bin))
    fp = float(np.sum(pred_bin & ~truth_bin))
    fn = float(np.sum(~pred_bin & truth_bin))
    tn = float(np.sum(~pred_bin & ~truth_bin))
    total = tp + fp + fn + tn + 1e-9
    return {
        "calib_mse": mse,
        "calib_bias": bias,
        "calib_tp_rate": tp / (tp + fn + 1e-9),
        "calib_fp_rate": fp / (fp + tn + 1e-9),
        "calib_accuracy": (tp + tn) / total,
        "calibration_samples": float(len(pred)),
    }


def _bootstrap_ci(arr: np.ndarray, prefix: str, n_boot: int = 200, alpha: float = 0.05) -> Dict[str, float]:
    rng = np.random.default_rng(0)
    n = len(arr)
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))
    boot_means = np.sort(boot_means)
    lo = boot_means[int((alpha / 2) * n_boot)]
    hi = boot_means[int((1 - alpha / 2) * n_boot)]
    return {f"{prefix}_ci_low": float(lo), f"{prefix}_ci_high": float(hi)}
