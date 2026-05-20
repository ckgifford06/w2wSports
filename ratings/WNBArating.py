playoffs = False #Playoffs begin mid-September

team_marketability = {
    "ATL_WNBA": 5, "CHI_WNBA": 8, "CONN_WNBA": 6, "DAL_WNBA": 6.5, "GS_WNBA": 7,
    "IND_WNBA": 8, "LV_WNBA": 8, "LA_WNBA": 7, "MIN_WNBA": 7.5, "NY_WNBA": 7,
    "PHX_WNBA": 6, "POR_WNBA": 5, "SEA_WNBA": 7, "TOR_WNBA": 5, "WSH_WNBA": 6
}

rivalries = [
    ("IND_WNBA", "CHI_WNBA", 11),
    ("NY_WNBA", "LV_WNBA", 9),
    ("IND_WNBA", "NY_WNBA", 8),
    ("NY_WNBA", "CHI_WNBA", 7),
    ("LV_WNBA", "SEA_WNBA", 7),
    ("IND_WNBA", "LV_WNBA", 6),
    ("NY_WNBA", "CONN_WNBA", 6),
    ("LV_WNBA", "MIN_WNBA", 6),
    ("MIN_WNBA", "NY_WNBA", 5),
    ("LA_WNBA", "PHX_WNBA", 5),
    ("CHI_WNBA", "CONN_WNBA", 4),
    ("GS_WNBA", "LA_WNBA", 4),
    ("SEA_WNBA", "MIN_WNBA", 3),
]

def _parse_record(record_str):
    parts = record_str.replace("-", " ").split()
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return 0, 0

def rivalry(home, away):
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            return r
    return 0

def marketability(home, away):
    return team_marketability.get(home, 3) + team_marketability.get(away, 3)

def competitiveness(home, away, home_record="0-0", away_record="0-0"):
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    win_diff = abs(hw - aw)
    return ((20 - win_diff) / 4) + 3

def qualityOfPlay(home, away, home_record="0-0", away_record="0-0"):
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    combined_wins = float(hw + aw)
    games_played = float(hw + hl + aw + al)
    if games_played == 0:
        return 0
    return round((combined_wins / games_played) * 7, 3)

def gameImportance(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None):
    importance = 0
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    games_left = 44 - max(hw + hl, aw + al)

    if playoffs:
        importance += 8
    else:
        if games_left <= 25:
            importance += 1
        if games_left <= 15:
            importance += 1
        if games_left <= 8:
            importance += 1
        if home_seed is not None and 4 < home_seed < 9:
            importance += 2
        if away_seed is not None and 4 < away_seed < 9:
            importance += 2
        if home_seed == 1 and away_seed == 2:
            importance += 4
        if away_seed == 1 and home_seed == 2:
            importance += 4

    return importance

def calculate_score(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away, home_record, away_record)
    q = qualityOfPlay(home, away, home_record, away_record)
    g = gameImportance(home, away, home_record, away_record, home_seed, away_seed)
    return round(r + m + c + q + g, 2)

def calculate_score_breakdown(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None):
    return {
        "rivalry":         round(rivalry(home, away), 2),
        "marketability":   round(marketability(home, away), 2),
        "competitiveness": round(competitiveness(home, away, home_record, away_record), 2),
        "quality":         round(qualityOfPlay(home, away, home_record, away_record), 2),
        "importance":      round(gameImportance(home, away, home_record, away_record, home_seed, away_seed), 2),
    }
