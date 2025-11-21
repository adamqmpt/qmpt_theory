# QMPT Lab

## English
- Purpose: a minimal 1D GridWorld to probe pattern continuity and behavioral stability during a run with precise, compact logging.
- What the test shows: continuity between mid-run and final pattern states, alignment/divergence of two mid-state copies, action entropy, reward/position stats.
- Outputs: concise JSON with config, metrics, episode summary (entropy, action distribution, positions), and full raw trajectory for deeper analysis (`schema_version=1.1`).
- Usage: `python -m qmpt_lab.run_sim --size 10 --max-steps 50 --mid-step 20 --transfer-noise-grid 0.0,0.01,0.05 --continuity-threshold 0.95` (or `python qmpt_lab/run_sim.py ...`). Flags cover seeds, temperature, log dir, transfer noise grid, and threshold. In a venv, launch from repo root or `pip install -e .`. If Python cannot find `qmpt_lab`, use `python run_qmpt_lab.py ...` which injects the repo root into `PYTHONPATH`.
- Logs: default path `qmpt_lab/logs/<run_id>.json`. Metrics include gaps (`continuity_gap_from_one`), alignment (`behavior_alignment_mid_copies`), and transfer noise sweep results (continuity drop vs noise, divergence growth).
- Batch sweeps: `python qmpt_lab/auto_sweep.py --duration 8h --root-seed 123 --transfer-noise-grid 0.0,0.02,0.05` runs randomized grids for a given duration (suffix s/m/h), writing per-run logs plus `summary.jsonl` and `batch_meta.json` with averages and best/worst runs; pacing via `--sleep-sec`.

## Русский
- Назначение: минимальный одномерный GridWorld с точным, компактным логом для оценки континуальности и стабильности поведения.
- Что показывает тест: континуальность между серединой и финалом эпизода, схождение/расхождение двух копий из середины, энтропия действий, статистика наград и позиций.
- Выводы: лаконичный JSON c конфигом, метриками, итоговым отчётом по эпизоду (энтропия, распределение действий, позиции) и исходной траекторией (`schema_version=1.1`).
- Как запускать: `python -m qmpt_lab.run_sim --size 10 --max-steps 50 --mid-step 20 --transfer-noise-grid 0.0,0.01,0.05 --continuity-threshold 0.95` (или `python qmpt_lab/run_sim.py ...`; параметры через CLI, включая шум переноса). В venv запускайте из корня репо или установите пакет в окружение: `pip install -e .`. Если Python не видит `qmpt_lab`, запустите `python run_qmpt_lab.py ...`, который добавляет корень репозитория в `PYTHONPATH`.
- Логи: путь по умолчанию `qmpt_lab/logs/<run_id>.json`. Метрики содержат разрыв до идеальной континуальности (`continuity_gap_from_one`), метрику схождения (`behavior_alignment_mid_copies`), а также результаты сканов по шуму переноса (где падает континуальность и как растёт дивергенция).
- Пакетные прогоны: `python qmpt_lab/auto_sweep.py --duration 8h --root-seed 123 --transfer-noise-grid 0.0,0.02,0.05` гоняет случайные сетки параметров по заданной длительности (s/m/h), складывая логи по эпизодам и `summary.jsonl`, плюс `batch_meta.json` со средними и лучшими/худшими прогонами; пауза между прогонами задаётся `--sleep-sec`.

## Advanced Simulation v2 (multi-layer, stress)
- Описание: многослойный 2D-мир (physical/cognitive), агенты с internal_state + self_model + MLP политикой, клоны и перенос с шумом.
- Быстрый запуск из корня (без установки пакета): `python run_qmpt_stress.py --world-size 32 32 --n-agents 12 --n-episodes 20 --calibrate-target-sec 10` или `python -m qmpt_lab.stress_run ...` (если пакет установлен/корень в PYTHONPATH).
- JSONL/CSV логи: `qmpt_lab/logs/qmpt_runs_<run_id>.jsonl`, `qmpt_lab/logs/qmpt_summary_<run_id>.csv`. Записываются meta, continuity, clone divergence, transfer events, anomaly impact, runtime stats.
- Постпроцессинг: `python -m qmpt_lab.analyze_continuity <jsonl>`, `python -m qmpt_lab.analyze_divergence <jsonl>`, `python -m qmpt_lab.analyze_anomalies <jsonl>`, `python -m qmpt_lab.plot_qmpt_metrics <jsonl>`.
- 10‑second high-load run: `python run_qmpt_high_load.py --target-runtime-sec 10` (или `python -m qmpt_lab.high_load --target-runtime-sec 10`) с автокалибровкой эпизодов под целевое время; логи в JSONL/CSV том же формате.
