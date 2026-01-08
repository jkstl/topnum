TopNum
======

Minimal Streamlit app that shows live leaders (points, rebounds, assists, etc.) across tonight's NBA games using the local `nba_api` package in this repository.

Quick start
-----------

1. Install dependencies (prefer a venv).

```bash
pip install -r tools/topnum/requirements.txt
```

2. Run the app. Two options:

- Preferred: vendor the in-repo package locally so `TopNum` is self-contained. From the repository root run in PowerShell:

```powershell
.\tools\topnum\copy_vendor.ps1
.\tools\topnum\run_local.ps1
```

- Quick (no vendor): set PYTHONPATH to the repository `src` and run Streamlit:

Windows (PowerShell):

```powershell
$env:PYTHONPATH = "src"
streamlit run tools/topnum/app.py
```

Windows (cmd.exe):

```cmd
set PYTHONPATH=src
streamlit run tools/topnum/app.py
```

Notes
-----
- The app uses `ScoreboardV2` and `BoxScoreTraditionalV3` endpoints from the repository's `nba_api` package.
- Auto-refresh requires `streamlit-autorefresh` (optional). If not installed, the app still works and you can manually refresh in the browser.

What this package contains
-------------------------

- `app.py` — the Streamlit application. It polls the scoreboard and per-game boxscore endpoints to show tonight's top personal totals for: Points, Rebounds, Assists, FGM, FGA, 3PM, 3PA, Steals, and Blocks. The app prefers the live boxscore feed and falls back to `BoxScoreTraditionalV3` and team-leaders data when needed.
- `requirements.txt` — minimal dependencies for running the app (`streamlit`, `streamlit-autorefresh`).
- `copy_vendor.ps1` — a helper PowerShell script to copy the repository's `src/nba_api` package into `tools/topnum/vendor/nba_api`. This makes `TopNum` self-contained so you can run it without adjusting `PYTHONPATH` or your environment. Use this when you want an isolated, portable copy of the dependency.
- `run_local.ps1` — convenience script to run Streamlit using the vendored package (or the project's `.venv` if present).

Why `copy_vendor.ps1` exists
----------------------------

The repository already contains a local development copy of `nba_api` under `src/`. `copy_vendor.ps1` simply copies those sources into `tools/topnum/vendor/nba_api` so `TopNum` can import the package directly (imports `vendor` first via a simple `sys.path` tweak). This is useful when:

- You want to run `TopNum` without setting `PYTHONPATH` or installing the whole repository in your environment.
- You want a lightweight, standalone snapshot of the dependency for deployment or quick testing.

Running the app
---------------

Recommended (self-contained):

```powershell
.\tools\topnum\copy_vendor.ps1
.\tools\topnum\run_local.ps1
```

Quick dev mode (use repo `src`):

```powershell
$env:PYTHONPATH = "src"
streamlit run tools/topnum/app.py
```

If you want me to vendor the package now, or to start the Streamlit server and preview it here, tell me and I'll run the corresponding script.
