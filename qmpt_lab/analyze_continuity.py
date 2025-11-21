from __future__ import annotations

import json
from pathlib import Path
import statistics


def main(path: str):
    values = []
    for line in Path(path).open():
        rec = json.loads(line)
        if rec.get("type") == "pattern_continuity":
            values.append(rec["continuity_mid_to_final"])
    if not values:
        print("no continuity records")
        return
    print(f"count={len(values)} mean={statistics.mean(values):.4f} min={min(values):.4f} max={max(values):.4f}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m qmpt_lab.analyze_continuity <jsonl_path>")
        raise SystemExit(1)
    main(sys.argv[1])

