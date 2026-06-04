playoffs = True #playoffs start April 12

from playoff_bonus import playoff_bonus

team_marketability = {
    "BOS_NBA": 9, "BKN_NBA": 7, "NY_NBA": 9, "PHI_NBA": 8, "TOR_NBA": 6,
    "CHI_NBA": 8, "CLE_NBA": 7, "DET_NBA": 5, "IND_NBA": 7, "MIL_NBA": 7,
    "ATL_NBA": 7, "CHA_NBA": 5, "MIA_NBA": 7, "ORL_NBA": 6, "WAS_NBA": 6.5,
    "DEN_NBA": 8, "MIN_NBA": 6, "OKC_NBA": 9, "POR_NBA": 5, "UTAH_NBA": 5,
    "GS_NBA": 9, "LAC_NBA": 7, "LAL_NBA": 9, "PHX_NBA": 7, "SAC_NBA": 5,
    "DAL_NBA": 8, "HOU_NBA": 8, "MEM_NBA": 5, "NO_NBA": 6, "SA_NBA": 8
}

rivalries = [
    ("OKC_NBA", "SA_NBA", 11),
    ("LAL_NBA", "BOS_NBA", 8),
    ("NY_NBA", "BOS_NBA", 8),
    ("NY_NBA", "IND_NBA", 5),
    ("CHI_NBA", "IND_NBA", 4),
    ("MIA_NBA", "BOS_NBA", 4),
    ("MIA_NBA", "NY_NBA", 4),
    ("DAL_NBA", "SAS_NBA", 3),
    ("GS_NBA", "LAL_NBA", 3),
    ("PHX_NBA", "SAS_NBA", 3),
    ("TOR_NBA", "BOS_NBA", 2),
    ("NY_NBA", "PHI_NBA", 6),
    ("DAL_NBA", "LAL_NBA", 6),
    ("OKC_NBA", "GS_NBA", 4),
    ("LAL_NBA", "SAS_NBA", 5),
    ("OKC_NBA", "IND_NBA", 5),
    ("NY_NBA", "CLE_NBA", 6)
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
    return ((20 - win_diff) / 3) + 3

def qualityOfPlay(home, away, home_record="0-0", away_record="0-0"):
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    combined_wins = float(hw + aw)
    games_played = float(hw + hl + aw + al)
    if games_played == 0:
        return 0
    return round((combined_wins / games_played) * 19, 3)

def gameImportance(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None, playoff_game_number=None, leader_wins=None):
    importance = 0
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    games_left = 82 - max(hw + hl, aw + al)

    if playoffs:
        importance += playoff_bonus(playoff_game_number, series_length=7, leader_wins=leader_wins, default=8)
        importance += 20 # its the knicks vs the spurs in the finals, cmonnnnn
    else:
        if games_left <= 50:
            importance += 2
        if games_left <= 30:
            importance += 2
        if games_left <= 20:
            importance += 2
        if home_seed is not None and 6 < home_seed < 11:
            importance += 4
        if away_seed is not None and 6 < away_seed < 11:
            importance += 4
        if home_seed == 1 and away_seed == 2:
            importance += 6
        if away_seed == 1 and home_seed == 2:
            importance += 6

    return importance

def calculate_score(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None, playoff_game_number=None, leader_wins=None):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away, home_record, away_record)
    q = qualityOfPlay(home, away, home_record, away_record)
    g = gameImportance(home, away, home_record, away_record, home_seed, away_seed, playoff_game_number, leader_wins)
    return round(r + m + c + q + g, 2)

def calculate_score_breakdown(home, away, home_record="0-0", away_record="0-0", home_seed=None, away_seed=None, playoff_game_number=None, leader_wins=None):
    return {
        "rivalry":         round(rivalry(home, away), 2),
        "marketability":   round(marketability(home, away), 2),
        "competitiveness": round(competitiveness(home, away, home_record, away_record), 2),
        "quality":         round(qualityOfPlay(home, away, home_record, away_record), 2),
        "importance":      round(gameImportance(home, away, home_record, away_record, home_seed, away_seed, playoff_game_number, leader_wins), 2),
    }
