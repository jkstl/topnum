import time
import streamlit as st
from datetime import datetime
from typing import Tuple, Dict, Any, List

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


# mapping: display name -> expected field name in live `statistics` or traditional headers
STAT_FIELDS = {
    "Points": "points",
    "Rebounds": "reboundsTotal",
    "Assists": "assists",
    "FGM": "fieldGoalsMade",
    "FGA": "fieldGoalsAttempted",
    "3PM": "threePointersMade",
    "3PA": "threePointersAttempted",
    "Steals": "steals",
    "Blocks": "blocks",
}

# minimal team color map; unknown teams get a light gray
TEAM_COLORS = {
    # examples; add more if desired
    "BOS": "#007A33",
    "LAL": "#552583",
    "GSW": "#006BB6",
    "PHI": "#006BB6",
}


def parse_dataset(dataset) -> List[Dict[str, Any]]:
    if dataset is None:
        return []
    d = dataset.get_dict()
    headers = d.get("headers", []) or []
    rows = d.get("data", []) or []
    return [dict(zip(headers, row)) for row in rows]


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

        # colors (use TEAM_COLORS but default to muted colors)
        away_abbr = game.get("awayTeam", "")
        home_abbr = game.get("homeTeam", "")
        away_color = TEAM_COLORS.get(away_abbr.upper(), "#16a34a")
        home_color = TEAM_COLORS.get(home_abbr.upper(), "#2563eb")

        # Build HTML (flex layout). Left ~38%, right ~62%.
        boxscore_url = f"https://www.nba.com/game/{card.get('game', {}).get('gameId', card.get('game', {}).get('game_id',''))}/box-score"
        html = f"""
        <div style='font-family: Inter, Roboto, -apple-system, system-ui, sans-serif; background:#ffffff; padding:18px; border-radius:16px; box-shadow:0 6px 16px rgba(16,24,40,0.06); display:flex; gap:16px; align-items:stretch; max-width:900px;'>
            <div style='flex:0 0 38%; display:flex; flex-direction:column; justify-content:center; padding:8px 12px; align-items:center; text-align:center;'>
                <div style='font-size:14px; text-transform:uppercase; color:#6b7280; letter-spacing:1px; margin-bottom:8px; font-weight:700'>{statLabel}</div>
                <div style='font-size:56px; font-weight:800; color:#0f172a; line-height:1;'>{statValue}</div>
            </div>
            <div style='flex:1 1 62%; display:flex; flex-direction:column; justify-content:space-between; padding:8px 4px;'>
                <div style='display:flex; align-items:center; gap:12px;'>
                    <div style='width:56px; height:56px; border-radius:9999px; background:linear-gradient(135deg, rgba(0,0,0,0.04), rgba(0,0,0,0.02)); display:flex; align-items:center; justify-content:center; font-weight:600; color:#111;'>
                        {player.get('name','')[0:1]}
                    </div>
                    <div style='flex:1;'>
                        <div style='font-size:20px; font-weight:600; color:#0f172a;'>{player.get('name','—')}</div>
                        <div style='color:#6b7280; font-size:13px; margin-top:2px;'>{player.get('team','')}</div>
                    </div>
                </div>
                <div style='margin-top:8px; display:flex; flex-direction:column; align-items:flex-start;'>
                    <div style='margin-left:68px; display:flex; flex-direction:column; align-items:center;'>
                        <a href='{boxscore_url}' target='_blank' style='text-decoration:none;'>
                            <div style='display:inline-flex; align-items:center; gap:12px; padding:8px 14px; border-radius:18px; border:1px solid rgba(15,23,42,0.06); background:rgba(255,255,255,0);'>
                                <span style='color:{away_color}; font-weight:700'>{away_abbr}</span>
                                <span style='font-weight:600; color:#0f172a'>{game.get('awayScore', '')}</span>
                                <span style='color:#9ca3af; margin:0 8px;'>|</span>
                                <span style='color:{home_color}; font-weight:700'>{home_abbr}</span>
                                <span style='font-weight:600; color:#0f172a; margin-left:6px'>{game.get('homeScore', '')}</span>
                            </div>
                        </a>
                        <div style='margin-top:6px; text-align:center; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace; font-size:12px; color:#6b7280;'>
                            {game.get('clock','')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)



def fetch_top_stats() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    tops = {k: {"value": None, "player": None, "team": None, "game_id": None, "game_score": None} for k in STAT_FIELDS}
    debug = {"games_found": 0, "game_ids": [], "boxes_ok": 0, "boxes_failed": 0, "errors": []}

    sb = ScoreboardV2()
    games = parse_dataset(sb.game_header)
    debug["games_found"] = len(games)
    debug["game_ids"] = [g.get("GAME_ID") for g in games if g.get("GAME_ID")]

    def to_float(x):
        try:
            return float(x) if x not in (None, "") else 0.0
        except Exception:
            return 0.0

    def score_for_gid(gid, live_game=None):
        if live_game:
            try:
                ht = live_game.get("homeTeam", {})
                at = live_game.get("awayTeam", {})
                h_abbr = ht.get("teamTricode") or ht.get("teamName") or ""
                a_abbr = at.get("teamTricode") or at.get("teamName") or ""
                h_pts = ht.get("score")
                a_pts = at.get("score")
                if h_abbr and a_abbr and h_pts is not None and a_pts is not None:
                    return f"{h_abbr} {h_pts} {a_abbr} {a_pts}"
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
                    return f"{h_abbr} {h_pts} {a_abbr} {a_pts}"
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

            for disp, field in STAT_FIELDS.items():
                raw = None
                # support multiple naming conventions
                if field in flat:
                    raw = flat.get(field)
                elif isinstance(field, str) and field.upper() in flat:
                    raw = flat.get(field.upper())
                val = to_float(raw)
                cur = tops[disp]["value"]
                if cur is None or val > cur:
                    tops[disp] = {"value": val, "player": name or None, "team": team or None, "game_id": gid, "game_score": score_for_gid(gid, live_game)}

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
                    tops["Points"] = {"value": pts, "player": tl.get("PTS_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game_score": score_for_gid(gid)}
                if reb and (tops["Rebounds"]["value"] is None or reb > tops["Rebounds"]["value"]):
                    tops["Rebounds"] = {"value": reb, "player": tl.get("REB_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game_score": score_for_gid(gid)}
                if ast and (tops["Assists"]["value"] is None or ast > tops["Assists"]["value"]):
                    tops["Assists"] = {"value": ast, "player": tl.get("AST_PLAYER_NAME"), "team": tl.get("TEAM_ABBREVIATION") or tl.get("TEAM_NICKNAME"), "game_id": gid, "game_score": score_for_gid(gid)}
    except Exception:
        pass

    return tops, debug


def render(tops: Dict[str, Dict[str, Any]]):
    st.title("TopNum — Live leaders")
    st.caption("Minimal live leaderboard across tonight's games")
    items = list(tops.items())
    cols = st.columns(2)
    for i, (stat_name, info) in enumerate(items):
        col = cols[i % 2]
        with col:
            # Build card data
            val = info.get("value")
            display_val = int(val) if (isinstance(val, (int, float)) and float(val).is_integer()) else (round(float(val), 1) if val is not None else "—")
            card = {
                "statLabel": stat_name,
                "statValue": display_val,
                "player": {"name": info.get("player") or "—", "team": info.get("team") or ""},
                "game": {}
            }
            # Populate game details: try game_score 'PHI 62 WAS 56' or GAME_ID
            gs = info.get("game_score") or info.get("game_id")
            if isinstance(gs, str) and gs:
                parts = gs.split()
                if len(parts) >= 4:
                    card["game"] = {"awayTeam": parts[0], "awayScore": parts[1], "homeTeam": parts[2], "homeScore": parts[3], "clock": ""}
                else:
                    card["game"] = {"awayTeam": "", "awayScore": "", "homeTeam": "", "homeScore": "", "clock": "" , "game_id": gs}
            else:
                card["game"] = {"awayTeam": "", "awayScore": "", "homeTeam": "", "homeScore": "", "clock": "", "game_id": info.get("game_id")}

            render_stat_card(card)


def main():
    st_autorefresh(interval=30 * 1000, key="topnum_autorefresh")
    # Design preview for the modern stat card component
    with st.expander("Design preview — Stat Card (wireframe)", expanded=True):
        mock = {
            "statLabel": "Points",
            "statValue": 20,
            "player": {"name": "Tyrese Maxey", "team": "PHI"},
            "game": {"awayTeam": "BOS", "awayScore": 106, "homeTeam": "PHI", "homeScore": 99, "clock": "4TH 10:00"}
        }
        render_stat_card(mock)
    last_run = datetime.now()
    with st.spinner("Fetching live data..."):
        tops, debug = fetch_top_stats()
    render(tops)
    st.write(f"Last updated: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")

    with st.expander("Debug / fetch details"):
        st.write(f"Games found: {debug['games_found']}")
        st.write(f"Game IDs: {debug['game_ids']}")
        st.write(f"Boxscore fetches OK: {debug['boxes_ok']}")
        st.write(f"Boxscore fetches failed: {debug['boxes_failed']}")
        if debug['errors']:
            st.markdown("**Errors (first 5):**")
            for err in debug['errors'][:5]:
                st.write(err)


if __name__ == "__main__":
    main()
