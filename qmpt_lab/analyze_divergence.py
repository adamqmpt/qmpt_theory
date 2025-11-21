from __future__ import annotations

import json
import statistics
from pathlib import Path


def main(path: str):
    values_clone = []
    values_transfer = []
    for line in Path(path).open():
        rec = json.loads(line)
        if rec.get("type") == "clone_divergence":
            values_clone.append(rec["behavior_divergence_mid_copies"])
        elif rec.get("type") == "transfer_event":
            values_transfer.append(rec["behavior_divergence_transfer_vs_baseline"])
    if values_clone:
        print(f"clone divergence: count={len(values_clone)} mean={statistics.mean(values_clone):.4f} min={min(values_clone):.4f} max={max(values_clone):.4f}")
    else:
        print("no clone divergence records")
    if values_transfer:
        print(f"transfer divergence: count={len(values_transfer)} mean={statistics.mean(values_transfer):.4f} min={min(values_transfer):.4f} max={max(values_transfer):.4f}")
    else:
        print("no transfer divergence records")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m qmpt_lab.analyze_divergence <jsonl_path>")
        raise SystemExit(1)
    main(sys.argv[1])

