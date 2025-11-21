from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

import numpy as np
import re

# Make sure repo root is importable even if launched from elsewhere.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Keep type checkers happy while allowing script-mode import.
if TYPE_CHECKING:  # pragma: no cover
    from qmpt_lab.run_sim import run_experiment  # type: ignore
else:  # pragma: no cover
    try:
        from qmpt_lab.run_sim import run_experiment
    except ImportError:
        from .run_sim import run_experiment


def parse_list(arg: str, cast) -> list:
    return [cast(x) for x in arg.split(",") if x]


def choose(items: Iterable):
    items = list(items)
    return random.choice(items)


def parse_duration_seconds(duration: str | None, hours: float, minutes: float) -> float:
    """
    Convert duration string with unit suffix to total seconds.
    Examples: '30s', '15m', '8h'. If missing or invalid, fallback to hours+minutes.
    """
    if duration:
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)([smhSMH])\s*", duration)
        if m:
            value = float(m.group(1))
            unit = m.group(2).lower()
            if unit == "s":
                return value
            if unit == "m":
                return value * 60.0
            if unit == "h":
                return value * 3600.0
    return hours * 3600.0 + minutes * 60.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run QMPT Lab simulations back-to-back for a fixed duration (e.g., 8 hours)."
    )
    parser.add_argument(
        "--duration",
        type=str,
        default=None,
        help="Total duration with unit suffix (e.g., 30s, 15m, 8h). Overrides --duration-hours/minutes if set.",
    )
    parser.add_argument(
        "--duration-hours",
        type=float,
        default=8.0,
        help="Total wall-clock hours to keep launching new runs.",
    )
    parser.add_argument(
        "--duration-minutes",
        type=float,
        default=0.0,
        help="Additional minutes to run (added to hours).",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Optional hard cap on number of runs (overrides duration if reached first).",
    )
    parser.add_argument(
        "--log-root",
        type=Path,
        default=Path(__file__).resolve().parent / "logs",
        help="Root directory to store batch logs.",
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default="8,10,12,16",
        help="Comma-separated grid sizes to sample from.",
    )
    parser.add_argument(
        "--internal-dims",
        type=str,
        default="8,16,32",
        help="Comma-separated internal state sizes to sample from.",
    )
    parser.add_argument(
        "--temperatures",
        type=str,
        default="0.8,1.0,1.2",
        help="Comma-separated policy temperatures to sample from.",
    )
    parser.add_argument(
        "--state-momenta",
        type=str,
        default="0.88,0.92,0.96",
        help="Comma-separated state momentum values to sample from.",
    )
    parser.add_argument(
        "--weight-scales",
        type=str,
        default="0.05,0.1,0.2",
        help="Comma-separated weight scales to sample from.",
    )
    parser.add_argument(
        "--sleep-sec",
        type=float,
        default=0.0,
        help="Optional pause between runs to reduce thermal throttling.",
    )
    parser.add_argument(
        "--print-every",
        type=int,
        default=1,
        help="How often to print status (every N runs).",
    )
    parser.add_argument(
        "--root-seed",
        type=int,
        default=None,
        help="Optional seed to make parameter sampling reproducible across batches.",
    )
    parser.add_argument(
        "--transfer-noise-grid",
        type=str,
        default="0.0,0.01,0.05",
        help="Noise std candidates for transfer distortion tests.",
    )
    parser.add_argument(
        "--continuity-threshold",
        type=float,
        default=0.95,
        help="Threshold for continuity vs mid under transfer noise.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.root_seed)

    sizes = parse_list(args.sizes, int)
    internal_dims = parse_list(args.internal_dims, int)
    temperatures = parse_list(args.temperatures, float)
    state_momenta = parse_list(args.state_momenta, float)
    weight_scales = parse_list(args.weight_scales, float)
    noise_grid = parse_list(args.transfer_noise_grid, float)

    batch_id = datetime.now(timezone.utc).strftime("batch_%Y%m%dT%H%M%SZ")
    batch_dir = args.log_root / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    summary_path = batch_dir / "summary.jsonl"

    start_monotonic = time.monotonic()
    total_seconds = parse_duration_seconds(args.duration, args.duration_hours, args.duration_minutes)
    deadline = time.monotonic() + total_seconds
    target_hours = total_seconds / 3600.0
    run_idx = 0

    print(f"[auto_sweep] Starting batch {batch_id}")
    print(f"[auto_sweep] Target duration: {target_hours:.2f} hours")
    if args.max_runs:
        print(f"[auto_sweep] Max runs: {args.max_runs}")
    print(f"[auto_sweep] Logs: {batch_dir}")

    rows: list[dict] = []

    with summary_path.open("a", encoding="utf-8") as summary_file:
        while time.monotonic() < deadline:
            if args.max_runs is not None and run_idx >= args.max_runs:
                break

            size = rng.choice(sizes)
            internal_dim = rng.choice(internal_dims)
            temperature = rng.choice(temperatures)
            state_momentum = rng.choice(state_momenta)
            weight_scale = rng.choice(weight_scales)
            max_steps = rng.choice([50, 75, 100, 150])
            mid_step = rng.choice([int(max_steps * frac) for frac in (0.25, 0.5, 0.75)])
            copy_eval_window = min(40, max_steps)
            seed_env = rng.randint(1, 10_000_000)
            seed_agent = rng.randint(1, 10_000_000)
            continuity_threshold = args.continuity_threshold

            run_start = time.monotonic()
            run_id, log_path, payload = run_experiment(
                size=size,
                max_steps=max_steps,
                mid_step=mid_step,
                internal_dim=internal_dim,
                temperature=temperature,
                state_momentum=state_momentum,
                weight_scale=weight_scale,
                seed_env=seed_env,
                seed_agent=seed_agent,
                copy_eval_window=copy_eval_window,
                log_dir=batch_dir,
                transfer_noise_grid=noise_grid,
                seed_transfer_noise=rng.randint(1, 10_000_000),
                continuity_threshold=continuity_threshold,
            )
            run_elapsed = time.monotonic() - run_start

            summary_row = {
                "run_id": run_id,
                "log_path": str(log_path),
                "size": size,
                "max_steps": max_steps,
                "mid_step": mid_step,
                "internal_dim": internal_dim,
                "temperature": temperature,
                "state_momentum": state_momentum,
                "weight_scale": weight_scale,
                "seed_env": seed_env,
                "seed_agent": seed_agent,
                "transfer_noise_grid": noise_grid,
                "continuity_threshold": continuity_threshold,
                "elapsed_sec": run_elapsed,
                "metrics": payload.get("metrics", {}),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            rows.append(summary_row)
            summary_file.write(json.dumps(summary_row) + "\n")
            summary_file.flush()

            run_idx += 1
            if run_idx % max(1, args.print_every) == 0:
                print(
                    f"[auto_sweep] run {run_idx} | "
                    f"R={payload['metrics']['continuity_mid_to_final']:.4f} | "
                    f"div={payload['metrics']['behavior_divergence_mid_copies']:.4f} | "
                    f"{run_elapsed:.2f}s | log={log_path.name}"
                )

            if args.sleep_sec > 0:
                time.sleep(args.sleep_sec)

            if time.monotonic() >= deadline:
                break

    meta_path = batch_dir / "batch_meta.json"
    if rows:
        avg_continuity = float(
            np.mean([r["metrics"].get("continuity_mid_to_final", 0.0) for r in rows])
        )
        avg_divergence = float(
            np.mean([r["metrics"].get("behavior_divergence_mid_copies", 0.0) for r in rows])
        )
        best = max(rows, key=lambda r: r["metrics"].get("continuity_mid_to_final", -1.0))
        worst = min(rows, key=lambda r: r["metrics"].get("continuity_mid_to_final", 1.0))
        meta_payload = {
            "batch_id": batch_id,
            "runs": run_idx,
            "duration_hours_target": args.duration_hours,
            "duration_hours_actual": float((time.monotonic() - start_monotonic) / 3600),
            "avg_continuity": avg_continuity,
            "avg_divergence": avg_divergence,
            "best_run": {"run_id": best["run_id"], "continuity": best["metrics"].get("continuity_mid_to_final"), "log_path": best["log_path"]},
            "worst_run": {"run_id": worst["run_id"], "continuity": worst["metrics"].get("continuity_mid_to_final"), "log_path": worst["log_path"]},
            "root_seed": args.root_seed,
            "grids": {
                "sizes": sizes,
                "internal_dims": internal_dims,
                "temperatures": temperatures,
                "state_momenta": state_momenta,
                "weight_scales": weight_scales,
                "transfer_noise_grid": noise_grid,
            },
        }
        meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    print(f"[auto_sweep] Finished. Runs executed: {run_idx}. Summary: {summary_path}")
    if meta_path.exists():
        print(f"[auto_sweep] Batch meta: {meta_path}")


if __name__ == "__main__":
    main()
