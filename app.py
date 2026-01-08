import re
import streamlit as st
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List, Optional

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


st.set_page_config(page_title="TopNum", layout="wide")


def apply_base_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: radial-gradient(circle at top, #f8fafc 0%, #f1f5f9 55%, #e2e8f0 100%);
            }
            .block-container {
                max-width: 1280px;
                padding-left: 2rem;
                padding-right: 2rem;
            }
            .topnum-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 1.5rem;
                padding: 0.5rem 0.2rem;
                flex-wrap: wrap;
                gap: 12px;
            }
            .topnum-title {
                font-size: 2rem;
                font-weight: 700;
                color: #0f172a;
                margin: 0;
            }
            .topnum-subtitle {
                color: #64748b;
                font-size: 0.95rem;
                margin-top: 0.2rem;
            }
            .topnum-meta {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            .meta-chip {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 999px;
                padding: 0.35rem 0.8rem;
                font-size: 0.78rem;
                color: #475569;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-weight: 600;
            }
            .stat-card {
                font-family: "Inter", "Roboto", -apple-system, system-ui, sans-serif;
                background: #ffffff;
                padding: 18px;
                border-radius: 18px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
                display: flex;
                flex-direction: column;
                gap: 10px;
                min-height: 220px;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                width: 100%;
            }
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 14px 26px rgba(15, 23, 42, 0.12);
            }
            .stat-label {
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1.3px;
                color: #94a3b8;
                font-weight: 700;
            }
            .stat-value {
                font-size: 48px;
                font-weight: 800;
                color: #0f172a;
                line-height: 1;
            }
            .player-row {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                justify-content: space-between;
                flex-wrap: nowrap;
            }
            .player-details {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .record-stack {
                text-align: right;
                font-size: 11px;
                color: #64748b;
                line-height: 1.2;
                display: flex;
                flex-direction: column;
                gap: 6px;
                margin-left: auto;
            }
            .record-label {
                font-weight: 700;
                color: #475569;
            }
            .record-item {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 2px;
                white-space: nowrap;
            }
            .record-value {
                color: #334155;
                font-weight: 700;
            }
            .player-avatar {
                width: 48px;
                height: 48px;
                border-radius: 999px;
                background: linear-gradient(135deg, #e2e8f0, #f8fafc);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #0f172a;
                font-weight: 700;
                font-size: 18px;
            }
            .player-name {
                font-size: 18px;
                font-weight: 600;
                color: #0f172a;
            }
            .player-team {
                color: #64748b;
                font-size: 13px;
                margin-top: 2px;
            }
            .game-pill {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                padding: 7px 12px;
                border-radius: 999px;
                border: 1px solid #e2e8f0;
                background: #f9fafb;
                font-size: 13px;
                color: #0f172a;
                font-weight: 600;
            }
            .game-clock {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace;
                font-size: 12px;
                color: #94a3b8;
                margin-top: 6px;
            }
            .section-title {
                font-size: 1.2rem;
                color: #0f172a;
                font-weight: 600;
                margin: 0.5rem 0 0.2rem;
            }
            .section-subtitle {
                color: #64748b;
                font-size: 0.9rem;
                margin-bottom: 0.8rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# mapping: display name -> expected field name in live `statistics` or traditional headers
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
    "Points",
    "Rebounds",
    "Assists",
    "FGM",
    "FGA",
    "Steals",
    "3PM",
    "3PA",
    "Blocks",
    "FTM",
    "FTA",
    "Turnovers",
]

STAT_ALL_TIME = {
    "Points": "ALL-TIME: 100 W. CHAMBERLAIN 1962",
    "Rebounds": "ALL-TIME: 55 W. CHAMBERLAIN 1960",
    "Assists": "ALL-TIME: 30 S. SKILES 1990",
    "FGM": "ALL-TIME: 36 W. CHAMBERLAIN 1967",
    "FGA": "ALL-TIME: 63 W. CHAMBERLAIN 1962",
    "Steals": "ALL-TIME: 11 L. ROBERTSON 1986",
    "3PM": "ALL-TIME: 14 K. THOMPSON 2018",
    "3PA": "ALL-TIME: 24 K. THOMPSON 2018",
    "Blocks": "ALL-TIME: 17 E. MANUTE 1985",
    "FTM": "ALL-TIME: 28 A. ROBERTSON 1959",
    "FTA": "ALL-TIME: 39 D. HOWARD 2013",
    "Turnovers": "ALL-TIME: 14 J. HARDEN 2017",
}

STAT_SEASON_HIGH = {
    "Points": "SEASON HIGH: 56 N. JOKIC",
    "Rebounds": "SEASON HIGH: 24 D. SABONIS",
    "Assists": "SEASON HIGH: 19 T. HALIBURTON",
    "FGM": "SEASON HIGH: 21 L. DONCIC",
    "FGA": "SEASON HIGH: 38 L. DONCIC",
    "Steals": "SEASON HIGH: 8 M. THYBULLE",
    "3PM": "SEASON HIGH: 12 S. CURRY",
    "3PA": "SEASON HIGH: 18 S. CURRY",
    "Blocks": "SEASON HIGH: 10 V. WEMBANYAMA",
    "FTM": "SEASON HIGH: 20 J. EMBIID",
    "FTA": "SEASON HIGH: 24 J. EMBIID",
    "Turnovers": "SEASON HIGH: 9 L. JAMES",
}

# minimal team color map; unknown teams get a light gray
TEAM_COLORS = {
    # examples; add more if desired
    "BOS": "#007A33",
    "LAL": "#552583",
    "GSW": "#006BB6",
    "PHI": "#006BB6",
    "CHI": "#CE1141",
}


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
    status_text = live_game.get("gameStatusText") or live_game.get("gameStatus") or ""
    if isinstance(status_text, str) and status_text:
        return status_text
    return ""


def render_stat_card(card: Dict[str, Any]):
    """Render a single modern stat card using inline CSS and minimal HTML.

    card JSON structure expected (see user mock):
    {
        "statLabel": "Points",
        "statValue": 20,
        "player": {"name":"Tyrese Maxey","team":"PHI"},
        "game": {"awayTeam":"BOS","awayScore":106,"homeTeam":"PHI","homeScore":99,"clock":"4TH 10:00"}
    }
    """
    statLabel = card.get("statLabel", "")
    statValue = card.get("statValue", "—")
    player = card.get("player", {})
    game = card.get("game", {})
    records = card.get("records", {})

    # colors (use TEAM_COLORS but default to muted colors)
    away_abbr = game.get("awayTeam", "")
    home_abbr = game.get("homeTeam", "")
    away_color = TEAM_COLORS.get(away_abbr.upper(), "#16a34a")
    home_color = TEAM_COLORS.get(home_abbr.upper(), "#2563eb")

    clock = game.get("clock", "")
    status = game.get("status", "")
    display_clock = clock or status
    boxscore_url = f"https://www.nba.com/game/{card.get('game', {}).get('gameId', card.get('game', {}).get('game_id',''))}/box-score"
    html = f"""
    <div class='stat-card'>
        <div class='stat-label'>{statLabel}</div>
        <div class='stat-value'>{statValue}</div>
        <div class='player-row'>
            <div class='player-details'>
                <div class='player-avatar'>
                        {player.get('name','')[0:1]}
                </div>
                <div>
                    <div class='player-name'>{player.get('name','—')}</div>
                    <div class='player-team'>{player.get('team','')}</div>
                </div>
            </div>
            <div class='record-stack'>
                <div class='record-item'>
                    <span class='record-label'>ALL-TIME</span>
                    <span class='record-value'>{records.get('all_time','—')}</span>
                </div>
                <div class='record-item'>
                    <span class='record-label'>SEASON HIGH</span>
                    <span class='record-value'>{records.get('season_high','—')}</span>
                </div>
            </div>
        </div>
        <div>
            <a href='{boxscore_url}' target='_blank' style='text-decoration:none;'>
                <div class='game-pill'>
                    <span style='color:{away_color}; font-weight:700'>{away_abbr}</span>
                    <span>{game.get('awayScore', '')}</span>
                    <span style='color:#cbd5f5;'>|</span>
                    <span style='color:{home_color}; font-weight:700'>{home_abbr}</span>
                    <span>{game.get('homeScore', '')}</span>
                </div>
            </a>
            <div class='game-clock'>{display_clock}</div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)



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

    sb = ScoreboardV2(game_date=game_date.strftime("%Y-%m-%d"))
    games = parse_dataset(sb.game_header)
    debug["games_found"] = len(games)
    debug["game_ids"] = [g.get("GAME_ID") for g in games if g.get("GAME_ID")]

    def to_float(x):
        try:
            return float(x) if x not in (None, "") else 0.0
        except Exception:
            return 0.0

    def game_for_gid(gid, live_game=None):
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
                clock = format_clock(clock_raw)
                if clock and period:
                    clock = f"Q{period} {clock}"
                elif period and not clock:
                    clock = f"Q{period}"
                if h_abbr and a_abbr and h_pts is not None and a_pts is not None:
                    return {
                        "awayTeam": a_abbr,
                        "awayScore": a_pts,
                        "homeTeam": h_abbr,
                        "homeScore": h_pts,
                        "clock": clock,
                        "status": status_text,
                    }
            except Exception:
                pass
        try:
            ls = parse_dataset(sb.line_score)
            rows = [r for r in ls if r.get("GAME_ID") == gid]
            if len(rows) >= 2:
                r1, r2 = rows[0], rows[1]
                h_abbr = r1.get("TEAM_ABBREVIATION") or r1.get("TEAM_NAME")
                a_abbr = r2.get("TEAM_ABBREVIATION") or r2.get("TEAM_NAME")
                h_pts = r1.get("PTS")
                a_pts = r2.get("PTS")
                if h_abbr and a_abbr and h_pts is not None and a_pts is not None:
                    return {
                        "awayTeam": a_abbr,
                        "awayScore": a_pts,
                        "homeTeam": h_abbr,
                        "homeScore": h_pts,
                        "clock": "",
                        "status": "",
                    }
        except Exception:
            pass
        return None

    for gid in debug["game_ids"]:
        players = []
        live_game = None
        # try live feed first
        if LiveBoxScore is not None:
            try:
                live = LiveBoxScore(gid)
                lg = live.game.get_dict() if getattr(live, "game", None) else None
                if lg:
                    live_game = lg
                    hp = lg.get("homeTeam", {}).get("players", []) or []
                    ap = lg.get("awayTeam", {}).get("players", []) or []
                    home_name = lg.get("homeTeam", {}).get("teamTricode") or lg.get("homeTeam", {}).get("teamName")
                    away_name = lg.get("awayTeam", {}).get("teamTricode") or lg.get("awayTeam", {}).get("teamName")
                    for p in hp:
                        if "teamName" not in p:
                            p["teamName"] = home_name
                    for p in ap:
                        if "teamName" not in p:
                            p["teamName"] = away_name
                    players = hp + ap
                    debug["boxes_ok"] += 1
            except Exception as e:
                debug["errors"].append({"game_id": gid, "error": f"live_box_error: {e}"})

        # fallback to traditional v3 boxscore
        if not players:
            try:
                box = BoxScoreTraditionalV3(gid)
                pdata = parse_dataset(box.player_stats)
                players = pdata
                debug["boxes_ok"] += 1
            except Exception as e:
                debug["boxes_failed"] += 1
                debug["errors"].append({"game_id": gid, "error": str(e)})
                continue

        for p in players:
            # normalize player name and team
            name = p.get("name") or f"{p.get('firstName','') or ''} {p.get('familyName','') or ''}".strip()
            team = p.get("teamTricode") or p.get("teamName") or p.get("TEAM_ABBREVIATION") or p.get("TEAM_NAME")

            # flatten live `statistics` dict if present
            stats_src = p.get("statistics") if isinstance(p.get("statistics"), dict) else p
            flat = dict(p)
            if isinstance(stats_src, dict):
                for k, v in stats_src.items():
                    if k not in flat:
                        flat[k] = v

            for disp, field in STAT_FIELDS:
                raw = None
                # support multiple naming conventions
                if field in flat:
                    raw = flat.get(field)
                elif isinstance(field, str) and field.upper() in flat:
                    raw = flat.get(field.upper())
                val = to_float(raw)
                cur = tops[disp]["value"]
                if cur is None or val > cur:
                    tops[disp] = {"value": val, "player": name or None, "team": team or None, "game_id": gid, "game": game_for_gid(gid, live_game)}

    # Team leaders fallback (when some categories missing)
    try:
        if any(tops[k]["value"] in (None, 0) for k in ("Points", "Rebounds", "Assists")):
            team_leaders = parse_dataset(sb.team_leaders)
            for tl in team_leaders:
                gid = tl.get("GAME_ID")
                try:
                    pts = to_float(tl.get("PTS"))
                except Exception:
                    pts = 0.0
                try:
                    reb = to_float(tl.get("REB"))
                except Exception:
                    reb = 0.0
                try:
                    ast = to_float(tl.get("AST"))
                except Exception:
                    ast = 0.0

                if pts and (tops["Points"]["value"] is None or pts > tops["Points"]["value"]):
                    tops["Points"] = {"value": pts, "player": tl.get("PTS_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game": game_for_gid(gid)}
                if reb and (tops["Rebounds"]["value"] is None or reb > tops["Rebounds"]["value"]):
                    tops["Rebounds"] = {"value": reb, "player": tl.get("REB_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game": game_for_gid(gid)}
                if ast and (tops["Assists"]["value"] is None or ast > tops["Assists"]["value"]):
                    tops["Assists"] = {"value": ast, "player": tl.get("AST_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game": game_for_gid(gid)}
    except Exception:
        pass

    return tops, debug, games


def extract_schedule_rows(games: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows = []
    for game in games:
        away = game.get("VISITOR_TEAM_ABBREVIATION") or game.get("VISITOR_TEAM_NAME") or ""
        home = game.get("HOME_TEAM_ABBREVIATION") or game.get("HOME_TEAM_NAME") or ""
        status = game.get("GAME_STATUS_TEXT") or ""
        rows.append(
            {
                "Matchup": f"{away} @ {home}".strip(),
                "Status": status,
            }
        )
    return rows


def render(tops: Dict[str, Dict[str, Any]], last_run: datetime, meta: Dict[str, Any]):
    st.markdown(
        f"""
        <div class='topnum-header'>
            <div>
                <div class='topnum-title'>TopNum</div>
                <div class='topnum-subtitle'>Live leaders across tonight's games</div>
            </div>
            <div class='topnum-meta'>
                <span class='meta-chip'>🕒 Updated {last_run.strftime('%H:%M:%S')} local</span>
                <span class='meta-chip'>📅 Data date {meta.get('data_date')}</span>
                <span class='meta-chip'>🏀 Games tracked {meta.get('game_count')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='section-title'>Stat leaders</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Highest single-game totals currently on the board.</div>", unsafe_allow_html=True)
    items = [(stat_name, tops.get(stat_name, {})) for stat_name in STAT_DISPLAY_ORDER]
    cols = st.columns(3)
    for i, (stat_name, info) in enumerate(items):
        col = cols[i % 3]
        with col:
            # Build card data
            val = info.get("value")
            display_val = int(val) if (isinstance(val, (int, float)) and float(val).is_integer()) else (round(float(val), 1) if val is not None else "—")
            card = {
                "statLabel": stat_name,
                "statValue": display_val,
                "player": {"name": info.get("player") or "—", "team": info.get("team") or ""},
                "game": info.get("game") or {},
                "records": {
                    "all_time": STAT_ALL_TIME.get(stat_name, "—").replace("ALL-TIME:", "").strip(),
                    "season_high": STAT_SEASON_HIGH.get(stat_name, "—").replace("SEASON HIGH:", "").strip(),
                },
            }
            if not card["game"]:
                card["game"] = {"awayTeam": "", "awayScore": "", "homeTeam": "", "homeScore": "", "clock": "", "game_id": info.get("game_id")}

            render_stat_card(card)


def main():
    st_autorefresh(interval=30 * 1000, key="topnum_autorefresh")
    apply_base_styles()
    last_run = datetime.now()
    with st.spinner("Fetching live data..."):
        today = datetime.now()
        tops, debug, games = fetch_top_stats_for_date(today)
        has_stats = any(info.get("value") not in (None, 0) for info in tops.values())
        if not has_stats:
            yesterday = today - timedelta(days=1)
            fallback_tops, fallback_debug, fallback_games = fetch_top_stats_for_date(yesterday)
            fallback_has_stats = any(info.get("value") not in (None, 0) for info in fallback_tops.values())
            if fallback_has_stats:
                tops, debug, games = fallback_tops, fallback_debug, fallback_games
                debug["fallback_used"] = True
                debug["fallback_date"] = fallback_debug.get("game_date")
            else:
                debug["fallback_used"] = False
    meta = {
        "data_date": debug.get("fallback_date") or debug.get("game_date"),
        "game_count": debug.get("games_found", 0),
    }
    render(tops, last_run, meta)

    has_stats = any(info.get("value") not in (None, 0) for info in tops.values())
    if not has_stats:
        st.info("No live stats yet. Games may be scheduled or not started. Check back at tipoff.")
        schedule = extract_schedule_rows(games)
        if schedule:
            st.markdown("**Tonight's schedule**")
            st.table(schedule)
    elif debug.get("fallback_used"):
        st.info(f"Showing previous day's top totals ({debug.get('fallback_date')}) while today's games are idle.")

    with st.expander("Debug / fetch details"):
        st.write(f"Games found: {debug['games_found']}")
        st.write(f"Game IDs: {debug['game_ids']}")
        st.write(f"Boxscore fetches OK: {debug['boxes_ok']}")
        st.write(f"Boxscore fetches failed: {debug['boxes_failed']}")
        if debug.get("fallback_used"):
            st.write(f"Fallback used: {debug.get('fallback_date')}")
        if debug['errors']:
            st.markdown("**Errors (first 5):**")
            for err in debug['errors'][:5]:
                st.write(err)


if __name__ == "__main__":
    main()
