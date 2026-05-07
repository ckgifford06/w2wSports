import time
import requests

STANDINGS_LEAGUES = {
    "NFL": "football/nfl",
    "MLB": "baseball/mlb",
    "NBA": "basketball/nba",
    "NHL": "hockey/nhl",
    "WNBA": "basketball/wnba",
    "EPL": "soccer/eng.1",
}

_cache = {}
_TTL = 3600


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _fetch_standings(league_path):
    now = time.time()
    cached = _cache.get(league_path)
    if cached and cached["expires"] > now:
        return cached["data"]

    try:
        url = f"https://site.api.espn.com/apis/v2/sports/{league_path}/standings"
        resp = requests.get(url, timeout=5)
        if not resp.ok:
            return None
        data = resp.json()
    except Exception:
        return None

    _cache[league_path] = {"data": data, "expires": now + _TTL}
    return data


def _find_team(standings_data, abbr):
    def walk(node):
        entries = node.get("standings", {}).get("entries", [])
        for entry in entries:
            team = entry.get("team", {})
            if team.get("abbreviation") == abbr:
                stats = {}
                for s in entry.get("stats", []):
                    name = s.get("name")
                    if name:
                        stats[name] = s.get("value")
                return {
                    "group_name": node.get("name", ""),
                    "group_abbr": node.get("abbreviation", "") or node.get("shortName", ""),
                    "stats": stats,
                }
        for child in node.get("children", []):
            r = walk(child)
            if r:
                return r
        return None

    for child in standings_data.get("children", []):
        r = walk(child)
        if r:
            return r
    return None


def _team_blurb(info):
    if not info:
        return None
    stats = info.get("stats", {})
    rank = (
        stats.get("playoffSeed")
        or stats.get("divisionRank")
        or stats.get("rank")
    )
    group = info.get("group_abbr") or info.get("group_name")
    if not rank or not group:
        return None
    try:
        return f"{_ordinal(int(rank))} {group}"
    except (ValueError, TypeError):
        return None


def get_standings_context(league, home_abbr, away_abbr):
    league_path = STANDINGS_LEAGUES.get(league)
    if not league_path:
        return None

    data = _fetch_standings(league_path)
    if not data:
        return None

    home_info = _find_team(data, home_abbr)
    away_info = _find_team(data, away_abbr)

    home_blurb = _team_blurb(home_info)
    away_blurb = _team_blurb(away_info)

    if not home_blurb and not away_blurb:
        return None

    parts = []
    if home_blurb:
        parts.append(f"{home_abbr} {home_blurb}")
    if away_blurb:
        parts.append(f"{away_abbr} {away_blurb}")

    return {"summary": " · ".join(parts)}
