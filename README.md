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
