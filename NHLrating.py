playoffs = False #Starts on Sat Apr 14

team_marketability = {
    "ANA_NHL": 4, "UTA_NHL": 3.5, "BOS_NHL": 8, "BUF_NHL": 5, "CAR_NHL": 4,
    "CBJ_NHL": 4.5, "CGY_NHL": 5, "CHI_NHL": 6, "COL_NHL": 4, "DAL_NHL": 5.5,
    "DET_NHL": 6, "EDM_NHL": 4, "FLA_NHL": 4.5, "LA_NHL": 6.5, "MIN_NHL": 5,
    "MTL_NHL": 6.5, "NJD_NHL": 5, "NSH_NHL": 5.5, "NYI_NHL": 6, "NYR_NHL": 7,
    "OTT_NHL": 4, "PHI_NHL": 6, "PIT_NHL": 7, "SJS_NHL": 5, "SEA_NHL": 5,
    "STL_NHL": 5, "TBL_NHL": 6, "TOR_NHL": 7, "VAN_NHL": 4.5, "VGK_NHL": 5.5,
    "WPG_NHL": 5, "WSH_NHL": 6
}

rivalries = [
    ("TOR_NHL", "MTL_NHL", 7),
    ("DET_NHL", "CHI_NHL", 7),
    ("NYR_NHL", "NYI_NHL", 7),
    ("NYR_NHL", "NJD_NHL", 7),
    ("PHI_NHL", "PIT_NHL", 7),
    ("CAR_NHL", "TBL_NHL", 7),
    ("LA_NHL", "ANA_NHL", 7),
    ("DET_NHL", "COL_NHL", 7),
    ("TOR_NHL", "BUF_NHL", 7),
    # need to fill in more here
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
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)

def competitiveness(home, away, home_record="0-0", away_record="0-0"):
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    win_diff = abs(hw - aw)
    return (20 - win_diff) / 5

def qualityOfPlay(home, away, home_record="0-0", away_record="0-0"):
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    combined_wins = float(hw + aw)
    games_played = float(hw + hl + aw + al)
    if games_played == 0:
        return 0
    return round((combined_wins / games_played) * 10, 3)

def gameImportance(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None):
    importance = 0
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    games_left = 82 - max(hw + hl, aw + al)

    if playoffs:
        importance += 10
    else:
        if games_left <= 50:
            importance += 1
        if games_left <= 30:
            importance += 1
        if games_left <= 20:
            importance += 1
        if home_seed is not None and 6 < home_seed < 11:
            importance += 3
        if away_seed is not None and 6 < away_seed < 11:
            importance += 3

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
