# QMPT Lab IDE – Changelog

## v0.2.0 (current)
- Run history + log viewer in IDE.
- Auto metadata insertion (timestamp, config, log path) into note template on runs.
- Note template now includes timestamp and log path placeholders.
- Configurable max run history.
- Version bumped to 0.2.0.

## v0.1.2
- Markdown/math preview for notes (headings + inline `$...$` highlighting).
- Simulation launcher stub:
  - scans `config/*.yaml|*.json`,
  - seed/device selectors,
  - runs placeholder simulation and writes logs to `lab/logs/`.
- Experiment template insertion in notes with auto-filled config/seed/device.

## v0.1.1 (planned)
- Add simulation launch panel:
  - select scenario/config from `config/`,
  - run long simulations on local GPU/cluster,
  - stream logs into a dedicated pane.
- Markdown/LaTeX preview for formulas in viewer/notes.
- Run queue with status badges (queued/running/done/failed).
- Persist recent simulations to `lab/logs/`.

## v0.1.0 (current)
- Dark-theme Tkinter IDE with:
  - document browser for `.md` theory files,
  - read-only viewer,
  - note editor saving to `lab/notes/`,
  - status bar with version info.
- Configurable via `config/ide_default.json`.
