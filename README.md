TopNum
======

Minimal Streamlit app that shows live leaders (points, rebounds, assists, etc.) across tonight's NBA games using the `nba_api` package from PyPI.

Quick start
-----------

1. Install dependencies (prefer a venv).

```bash
pip install -r requirements.txt
```

2. Run the app. Two options:

```bash
streamlit run app.py
```

Notes
-----
- The app uses `ScoreboardV2` and `BoxScoreTraditionalV3` endpoints from the `nba_api` package.
- Auto-refresh requires `streamlit-autorefresh` (optional). If not installed, the app still works and you can manually refresh in the browser.

What this package contains
-------------------------

- `app.py` — the Streamlit application. It polls the scoreboard and per-game boxscore endpoints to show tonight's top personal totals for: Points, Rebounds, Assists, FGM, FGA, 3PM, 3PA, Steals, and Blocks. The app prefers the live boxscore feed and falls back to `BoxScoreTraditionalV3` and team-leaders data when needed.
- `requirements.txt` — minimal dependencies for running the app (`nba_api`, `streamlit`, `streamlit-autorefresh`).

Running the app
---------------

```bash
streamlit run app.py
```
