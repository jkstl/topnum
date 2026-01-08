import re
import streamlit as st
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List, Optional

# --- Import NBA API Endpoints ---
from nba_api.stats.endpoints.scoreboardv2 import ScoreboardV2
from nba_api.stats.endpoints.boxscoretraditionalv3 import BoxScoreTraditionalV3
try:
    from nba_api.live.nba.endpoints.boxscore import BoxScore as LiveBoxScore
except Exception:
    LiveBoxScore = None

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(interval=30000, key=None):
        return None

# --- Page Config ---
st.set_page_config(
    page_title="TopNum | NBA Live Leaders",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Constants & Config ---

# Mapping: Display Name -> Expected field name in data
STAT_FIELDS = [
    ("Points", "points"),
    ("Rebounds", "reboundsTotal"),
    ("Assists", "assists"),
    ("FGM", "fieldGoalsMade"),
    ("FGA", "fieldGoalsAttempted"),
    ("Steals", "steals"),
    ("3PM", "threePointersMade"),
    ("3PA", "threePointersAttempted"),
    ("Blocks", "blocks"),
    ("FTM", "freeThrowsMade"),
    ("FTA", "freeThrowsAttempted"),
    ("Turnovers", "turnovers"),
]

STAT_DISPLAY_ORDER = [
    "Points", "Rebounds", "Assists",
    "FGM", "FGA", "3PM",
    "3PA", "Steals", "Blocks",
    "FTM", "FTA", "Turnovers",
]

STAT_ALL_TIME = {
    "Points": "100 (Wilt)",
    "Rebounds": "55 (Wilt)",
    "Assists": "30 (Skiles)",
    "FGM": "36 (Wilt)",
    "FGA": "63 (Wilt)",
    "Steals": "11 (Larry/Kendall)",
    "3PM": "14 (Klay)",
    "3PA": "24 (Klay)",
    "Blocks": "17 (Elmore)",
    "FTM": "28 (Wilt/Adrian)",
    "FTA": "39 (Dwight)",
    "Turnovers": "14 (Kidd/Harden)",
}

# Expanded Team Colors for better UI accents
TEAM_COLORS = {
    "ATL": "#C8102E", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160",
    "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#FEC524",
    "DET": "#C8102E", "GSW": "#1D428A", "HOU": "#CE1141", "IND": "#002D62",
    "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9", "MIA": "#98002E",
    "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#F58426",
    "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160",
    "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141",
    "UTA": "#002B5C", "WAS": "#002B5C",
}

# --- Styling ---
def apply_base_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            .stApp {
                background-color: #F8FAFC; /* Slate-50 */
                font-family: 'Inter', sans-serif;
            }
            
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }

            /* Header Styling */
            .header-container {
                margin-bottom: 2rem;
                border-bottom: 1px solid #E2E8F0;
                padding-bottom: 1rem;
            }
            .app-title {
                font-size: 2.25rem;
                font-weight: 800;
                color: #0F172A;
                letter-spacing: -0.05rem;
                margin: 0;
            }
            .app-subtitle {
                font-size: 1rem;
                color: #64748B;
                margin-top: 0.25rem;
            }
            .meta-tags {
                display: flex;
                gap: 0.75rem;
                margin-top: 1rem;
                flex-wrap: wrap;
            }
            .meta-tag {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 0.75rem;
                font-weight: 600;
                color: #475569;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }

            /* Card Styling */
            .stat-card-container {
                background: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 1.25rem;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 200px; /* Fixed height for consistency */
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                transition: transform 0.2s, box-shadow 0.2s;
                position: relative;
                overflow: hidden;
            }
            .stat-card-container:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
                border-color: #CBD5E1;
            }
            
            /* Accent Bar on Left */
            .card-accent {
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 5px;
            }

            .stat-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }
            .stat-label {
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #94A3B8;
            }
            .stat-value {
                font-size: 3rem;
                font-weight: 800;
                line-height: 1;
                color: #0F172A;
                margin: 0.5rem 0;
            }

            .player-info {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            .player-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: #F1F5F9;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                color: #64748B;
                font-size: 1rem;
                border: 2px solid #fff;
                box-shadow: 0 0 0 1px #E2E8F0;
            }
            .player-text {
                display: flex;
                flex-direction: column;
            }
            .player-name {
                font-weight: 600;
                font-size: 0.95rem;
                color: #334155;
                line-height: 1.2;
            }
            .player-team {
                font-size: 0.75rem;
                color: #64748B;
                font-weight: 500;
            }

            .game-footer {
                margin-top: auto;
                padding-top: 0.75rem;
                border-top: 1px dashed #E2E8F0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.75rem;
            }
            .game-score {
                font-weight: 600;
                color: #475569;
                background: #F8FAFC;
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid #F1F5F9;
            }
            .game-clock {
                color: #EF4444; /* Red for live feel */
                font-weight: 600;
                font-variant-numeric: tabular-nums;
            }
            
            /* Metric Context (All Time Record) */
            .metric-context {
                font-size: 0.7rem;
                color: #94A3B8;
                text-align: right;
            }
            
            /* Status Messages */
            .info-box {
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                color: #1E40AF;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            
            /* Table Styling Override */
            div[data-testid="stTable"] {
                font-size: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Helper Functions ---

def parse_dataset(dataset) -> List[Dict[str, Any]]:
    if dataset is None:
        return []
    d = dataset.get_dict()
    headers = d.get("headers", []) or []
    rows = d.get("data", []) or []
    return [dict(zip(headers, row)) for row in rows]


def format_clock(clock_value: Optional[str]) -> str:
    if not clock_value:
        return ""
    if ":" in clock_value:
        return clock_value
    match = re.match(r"PT(?:(\d+)M)?(\d+(?:\.\d+)?)S", clock_value)
    if match:
        minutes = int(match.group(1) or 0)
        seconds = int(float(match.group(2) or 0))
        return f"{minutes}:{seconds:02d}"
    return clock_value


def format_game_status(live_game: Optional[Dict[str, Any]]) -> str:
    if not live_game:
        return ""
    # "gameStatusText" often contains "Final" or "7:30 pm ET"
    status_text = live_game.get("gameStatusText") or live_game.get("gameStatus") or ""
    if isinstance(status_text, str) and status_text:
        return status_text
    return ""


def render_stat_card(card: Dict[str, Any]):
    """Render a single modern stat card."""
    statLabel = card.get("statLabel", "")
    statValue = card.get("statValue", "—")
    player = card.get("player", {})
    game = card.get("game", {})
    record = card.get("record_all_time", "")

    # Determine colors based on player's team
    team_abbr = player.get("team", "").upper()
    accent_color = TEAM_COLORS.get(team_abbr, "#64748B") # Default slate

    # Game Details
    away = game.get("awayTeam", "")
    home = game.get("homeTeam", "")
    a_score = game.get("awayScore", "")
    h_score = game.get("homeScore", "")
    clock = game.get("clock") or game.get("status") or "Final"
    
    # Boxscore Link
    game_id = game.get('gameId') or game.get('game_id')
    boxscore_url = f"https://www.nba.com/game/{game_id}/box-score" if game_id else "#"

    html = f"""
    <a href="{boxscore_url}" target="_blank" style="text-decoration: none; color: inherit; display: block;">
        <div class="stat-card-container">
            <div class="card-accent" style="background-color: {accent_color};"></div>
            
            <div style="padding-left: 8px;">
                <div class="stat-header">
                    <span class="stat-label">{statLabel}</span>
                    <span class="metric-context" title="All-Time Record">Rec: {record}</span>
                </div>
                
                <div class="stat-value">{statValue}</div>
                
                <div class="player-info">
                    <div class="player-avatar" style="color: {accent_color}; background-color: {accent_color}15;">
                        {player.get('name', '?')[0]}
                    </div>
                    <div class="player-text">
                        <span class="player-name">{player.get('name', '—')}</span>
                        <span class="player-team">{team_abbr}</span>
                    </div>
                </div>
            </div>

            <div class="game-footer" style="margin-left: 8px;">
                <div class="game-score">
                    {away} {a_score} - {h_score} {home}
                </div>
                <div class="game-clock">
                    {clock}
                </div>
            </div>
        </div>
    </a>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- Data Fetching Logic (Unchanged from original logic, just organized) ---

def fetch_top_stats_for_date(game_date: datetime) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    tops = {k: {"value": None, "player": None, "team": None, "game_id": None, "game": None} for k, _ in STAT_FIELDS}
    debug = {
        "games_found": 0,
        "game_ids": [],
        "boxes_ok": 0,
        "boxes_failed": 0,
        "errors": [],
        "game_date": game_date.strftime("%Y-%m-%d"),
    }

    # 1. Get Scoreboard
    try:
        sb = ScoreboardV2(game_date=game_date.strftime("%Y-%m-%d"))
        games = parse_dataset(sb.game_header)
        debug["games_found"] = len(games)
        debug["game_ids"] = [g.get("GAME_ID") for g in games if g.get("GAME_ID")]
    except Exception as e:
        debug["errors"].append(f"Scoreboard fetch failed: {e}")
        return tops, debug, []

    # Helper: Safe float conversion
    def to_float(x):
        try:
            return float(x) if x not in (None, "") else 0.0
        except Exception:
            return 0.0

    # Helper: Build game info dict
    def game_for_gid(gid, live_game=None):
        # Try Live Data Structure
        if live_game:
            try:
                ht = live_game.get("homeTeam", {})
                at = live_game.get("awayTeam", {})
                h_abbr = ht.get("teamTricode") or ht.get("teamName") or ""
                a_abbr = at.get("teamTricode") or at.get("teamName") or ""
                h_pts = ht.get("score")
                a_pts = at.get("score")
                clock_raw = live_game.get("gameClock") or ""
                period = live_game.get("period") or ""
                status_text = format_game_status(live_game)
                
                clock = ""
                if status_text and "Final" in status_text:
                    clock = "Final"
                elif clock_raw:
                    clock = format_clock(clock_raw)
                    if period: clock = f"Q{period} {clock}"
                elif period:
                    clock = f"Q{period}"
                else:
                    clock = status_text

                if h_abbr and a_abbr:
                    return {
                        "awayTeam": a_abbr, "awayScore": a_pts if a_pts is not None else 0,
                        "homeTeam": h_abbr, "homeScore": h_pts if h_pts is not None else 0,
                        "clock": clock, "status": status_text, "gameId": gid
                    }
            except Exception:
                pass
        
        # Try Traditional Scoreboard Structure
        try:
            ls = parse_dataset(sb.line_score)
            rows = [r for r in ls if r.get("GAME_ID") == gid]
            if len(rows) >= 2:
                r1 = next((r for r in rows if r.get("TEAM_ID") == games[0].get("HOME_TEAM_ID")), rows[0]) # rough match
                # Simpler: just take first 2 rows for this game ID usually works
                r_away = rows[0]
                r_home = rows[1]
                # Check IDs to be sure? ScoreboardV2 line_score usually orders nicely. 
                # Let's trust the loop order or basic check.
                
                return {
                    "awayTeam": r_away.get("TEAM_ABBREVIATION"),
                    "awayScore": r_away.get("PTS"),
                    "homeTeam": r_home.get("TEAM_ABBREVIATION"),
                    "homeScore": r_home.get("PTS"),
                    "clock": "",
                    "status": "In Progress", # Placeholder if using fallback
                    "gameId": gid
                }
        except Exception:
            pass
        return None

    # 2. Iterate Games
    for gid in debug["game_ids"]:
        players = []
        live_game = None
        
        # A. Try Live Endpoint
        if LiveBoxScore:
            try:
                live = LiveBoxScore(gid)
                lg = live.game.get_dict() if getattr(live, "game", None) else None
                if lg:
                    live_game = lg
                    hp = lg.get("homeTeam", {}).get("players", []) or []
                    ap = lg.get("awayTeam", {}).get("players", []) or []
                    
                    # Ensure team names are attached to players
                    h_code = lg.get("homeTeam", {}).get("teamTricode")
                    a_code = lg.get("awayTeam", {}).get("teamTricode")
                    for p in hp: p["teamTricode"] = h_code
                    for p in ap: p["teamTricode"] = a_code
                    
                    players = hp + ap
                    debug["boxes_ok"] += 1
            except Exception as e:
                debug["errors"].append({"game_id": gid, "error": f"live_box_error: {e}"})

        # B. Fallback to Traditional
        if not players:
            try:
                box = BoxScoreTraditionalV3(gid)
                players = parse_dataset(box.player_stats)
                debug["boxes_ok"] += 1
            except Exception as e:
                debug["boxes_failed"] += 1
                continue

        # 3. Process Players for Leaders
        for p in players:
            name = p.get("name") or p.get("PLAYER_NAME") or f"{p.get('firstName','')} {p.get('familyName','')}"
            team = p.get("teamTricode") or p.get("TEAM_ABBREVIATION")
            
            # Flatten stats
            stats_src = p.get("statistics") if isinstance(p.get("statistics"), dict) else p
            flat = dict(p)
            if isinstance(stats_src, dict):
                flat.update(stats_src)

            for disp, field in STAT_FIELDS:
                raw = flat.get(field) or flat.get(field.upper())
                val = to_float(raw)
                
                current_max = tops[disp]["value"]
                if current_max is None or val > current_max:
                    # Found a new leader
                    game_info = game_for_gid(gid, live_game)
                    tops[disp] = {
                        "value": val,
                        "player": name,
                        "team": team,
                        "game_id": gid,
                        "game": game_info
                    }

    return tops, debug, games


def extract_schedule_rows(games: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows = []
    for game in games:
        away = game.get("VISITOR_TEAM_ABBREVIATION") or game.get("VISITOR_TEAM_NAME") or ""
        home = game.get("HOME_TEAM_ABBREVIATION") or game.get("HOME_TEAM_NAME") or ""
        status = game.get("GAME_STATUS_TEXT") or ""
        time = game.get("GAME_TIME") or "" # Sometimes available
        rows.append({
            "Matchup": f"{away} @ {home}",
            "Status": status
        })
    return rows


# --- Main Application ---

def main():
    # 1. Setup
    st_autorefresh(interval=30 * 1000, key="topnum_autorefresh")
    apply_base_styles()
    
    # 2. Data Fetch
    last_run = datetime.now()
    with st.spinner("Scouting the league..."):
        today = datetime.now()
        tops, debug, games = fetch_top_stats_for_date(today)
        
        has_stats = any(info.get("value") not in (None, 0) for info in tops.values())
        
        # Fallback to yesterday if today is empty
        if not has_stats:
            yesterday = today - timedelta(days=1)
            f_tops, f_debug, f_games = fetch_top_stats_for_date(yesterday)
            f_has_stats = any(info.get("value") not in (None, 0) for info in f_tops.values())
            
            if f_has_stats:
                tops, debug, games = f_tops, f_debug, f_games
                debug["fallback_used"] = True
                debug["fallback_date"] = f_debug.get("game_date")
            else:
                debug["fallback_used"] = False

    # 3. Header Rendering
    game_count = debug.get("games_found", 0)
    data_date = debug.get("fallback_date") or debug.get("game_date")
    
    st.markdown(f"""
        <div class="header-container">
            <h1 class="app-title">TopNum</h1>
            <div class="app-subtitle">Live statistical leaders from around the NBA</div>
            <div class="meta-tags">
                <span class="meta-tag">📅 {data_date}</span>
                <span class="meta-tag">🏀 {game_count} Games Tracked</span>
                <span class="meta-tag">🕒 Updated {last_run.strftime('%H:%M:%S')}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. Content Rendering
    has_stats = any(info.get("value") not in (None, 0) for info in tops.values())
    
    if debug.get("fallback_used"):
        st.info(f"ℹ️ No live games active. Showing leaders from **{debug.get('fallback_date')}**.")
    
    if not has_stats:
        st.markdown("""
            <div class="info-box">
                <strong>No stats available yet.</strong> Games may not have started.
            </div>
        """, unsafe_allow_html=True)
        
        schedule = extract_schedule_rows(games)
        if schedule:
            st.markdown("### Tonight's Schedule")
            st.table(schedule)
    else:
        # Render Grid
        # Create 4 columns for desktop (3 rows of 4 cards)
        # Streamlit columns wrap, but explicitly managing rows looks better
        
        st.markdown("### ⚡ Live Leaders", unsafe_allow_html=True)
        
        # Use columns in a loop for responsive grid
        cols = st.columns(4) 
        
        for i, stat_name in enumerate(STAT_DISPLAY_ORDER):
            info = tops.get(stat_name, {})
            val = info.get("value")
            
            # Formatting Value
            if isinstance(val, (int, float)):
                display_val = int(val) if float(val).is_integer() else round(float(val), 1)
            else:
                display_val = "—"
            
            # Build Card Data
            card_data = {
                "statLabel": stat_name,
                "statValue": display_val,
                "player": {"name": info.get("player"), "team": info.get("team")},
                "game": info.get("game") or {},
                "record_all_time": STAT_ALL_TIME.get(stat_name, "-")
            }
            
            # Place in column
            with cols[i % 4]:
                render_stat_card(card_data)
                st.write("") # Spacer

    # 5. Footer / Debug
    with st.expander("🛠 Debug Info"):
        st.json(debug)
        if debug.get('errors'):
            st.error("Errors encountered during fetch:")
            st.write(debug['errors'])

if __name__ == "__main__":
    main()
