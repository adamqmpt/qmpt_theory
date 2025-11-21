from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_records(path: str):
    with Path(path).open() as f:
        for line in f:
            yield json.loads(line)


def main(path: str):
    continuity = []
    divergence = []
    transfer_div = []
    for rec in load_records(path):
        if rec.get("type") == "pattern_continuity":
            continuity.append(rec["continuity_mid_to_final"])
        elif rec.get("type") == "clone_divergence":
            divergence.append(rec["behavior_divergence_mid_copies"])
        elif rec.get("type") == "transfer_event":
            transfer_div.append(rec["behavior_divergence_transfer_vs_baseline"])
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    if continuity:
        axes[0].hist(continuity, bins=20, color="skyblue")
        axes[0].set_title("Continuity")
    if divergence:
        axes[1].hist(divergence, bins=20, color="salmon")
        axes[1].set_title("Clone divergence")
    if transfer_div:
        axes[2].hist(transfer_div, bins=20, color="orange")
        axes[2].set_title("Transfer divergence")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m qmpt_lab.plot_qmpt_metrics <jsonl_path>")
        raise SystemExit(1)
    main(sys.argv[1])

