from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable


@dataclass
class LogConfig:
    log_dir: Path
    run_id: str


class JSONLLogger:
    def __init__(self, cfg: LogConfig):
        self.cfg = cfg
        self.cfg.log_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.cfg.log_dir / f"qmpt_runs_{self.cfg.run_id}.jsonl"
        self.summary_csv = self.cfg.log_dir / f"qmpt_summary_{self.cfg.run_id}.csv"
        self._csv_writer = None
        self._csv_file = None

    def write_jsonl(self, record: dict):
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def write_csv_rows(self, rows: Iterable[Dict]):
        rows = list(rows)
        if not rows:
            return
        # union of keys to avoid field mismatch
        headers = sorted({k for row in rows for k in row.keys()})
        if self._csv_file is None:
            self._csv_file = self.summary_csv.open("w", newline="", encoding="utf-8")
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=headers)
            self._csv_writer.writeheader()
        for row in rows:
            full_row = {h: row.get(h, "") for h in self._csv_writer.fieldnames}
            self._csv_writer.writerow(full_row)
        self._csv_file.flush()

    def close(self):
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
