from __future__ import annotations

import json
import statistics
from pathlib import Path


def main(path: str):
    scores = []
    for line in Path(path).open():
        rec = json.loads(line)
        if rec.get("type") == "anomaly_impact":
            scores.append(rec["anomaly_score"])
    if not scores:
        print("no anomaly records")
        return
    print(f"anomaly_score count={len(scores)} mean={statistics.mean(scores):.4f} min={min(scores):.4f} max={max(scores):.4f}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m qmpt_lab.analyze_anomalies <jsonl_path>")
        raise SystemExit(1)
    main(sys.argv[1])

