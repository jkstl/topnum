TopNum
=====

TopNum is a Streamlit dashboard that highlights live single-game statistical leaders across tonight's NBA games, along with season-high and all-time reference marks for each stat.

## Current state

- **Live leaderboard:** Points, rebounds, assists, shooting totals, steals, blocks, and turnovers are pulled from `nba_api` live/boxscore endpoints.
- **Contextual records:** Each stat card displays the season-high and all-time high for quick comparison.
- **Auto-refresh:** The dashboard refreshes on a short interval (when `streamlit-autorefresh` is installed).
- **Planned feature:** A future probability/odds indicator for players challenging records (placeholder in UI only).

## Quick start

1. Install dependencies (prefer a venv).

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
streamlit run app.py
```

## Notes

- The app uses `ScoreboardV2` and `BoxScoreTraditionalV3` endpoints from the `nba_api` package.
- Auto-refresh requires `streamlit-autorefresh` (optional). If not installed, the app still works and you can manually refresh in the browser.

## Project structure

- `app.py` — the Streamlit application. It polls the scoreboard and per-game boxscore endpoints to show tonight's top personal totals for: Points, Rebounds, Assists, FGM, FGA, 3PM, 3PA, Steals, and Blocks. The app prefers the live boxscore feed and falls back to `BoxScoreTraditionalV3` and team-leaders data when needed.
- `requirements.txt` — minimal dependencies for running the app (`nba_api`, `streamlit`, `streamlit-autorefresh`).

## Running the app

```bash
streamlit run app.py
```
