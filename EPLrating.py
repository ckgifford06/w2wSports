RIVALRIES = {
    frozenset(["MCI_EPL", "MUN_EPL"]): 12,
    frozenset(["ARS_EPL", "TOT_EPL"]): 12,
    frozenset(["LIV_EPL", "MUN_EPL"]): 12,
    frozenset(["LIV_EPL", "EVE_EPL"]): 12,
    frozenset(["AVL_EPL", "WOL_EPL"]): 8,
    frozenset(["SOU_EPL", "BOU_EPL"]): 6,
    frozenset(["CHE_EPL", "ARS_EPL"]): 9,
    frozenset(["CHE_EPL", "TOT_EPL"]): 9,
    frozenset(["CHE_EPL", "LIV_EPL"]): 9,
    frozenset(["MCI_EPL", "LIV_EPL"]): 11,
    frozenset(["NEW_EPL", "SUN_EPL"]): 11,
    frozenset(["LEE_EPL", "MUN_EPL"]): 11,
    frozenset(["BHA_EPL", "CRY_EPL"]): 8,
    frozenset(["WHU_EPL", "MIL_EPL"]): 8,
    frozenset(["LEI_EPL", "NFO_EPL"]): 8,
}

def rivalry(home, away):
    return RIVALRIES.get(frozenset([home, away]), 0)


TEAM_MARKETABILITY = {
    "MUN_EPL": 8,  
    "LIV_EPL": 8,  
    "MCI_EPL": 7,   
    "ARS_EPL": 7,   
    "CHE_EPL": 7,   
    "TOT_EPL": 6,   
    "NEW_EPL": 6,   
    "AVL_EPL": 5,  
    "WHU_EPL": 5,   
    "EVE_EPL": 5,   
    "LEI_EPL": 5,   
    "NFO_EPL": 5,   
    "BHA_EPL": 3,   
    "CRY_EPL": 3,   
    "WOL_EPL": 3,   
    "FUL_EPL": 2,   
    "BOU_EPL": 2,   
    "BRE_EPL": 2,   
    "SOU_EPL": 2,   
    "IPS_EPL": 1,   
}

def marketability(home, away):
    h = TEAM_MARKETABILITY.get(home, 4)
    a = TEAM_MARKETABILITY.get(away, 4)
    return h + a


def parse_record(record_str):
    if not record_str or record_str == "N/A":
        return 0, 0, 0, 0
    try:
        parts = record_str.split("-")
        if len(parts) == 3:
            w, d, l = int(parts[0]), int(parts[1]), int(parts[2])
            return w, d, l, w + d + l
        elif len(parts) == 2:
            w, l = int(parts[0]), int(parts[1])
            return w, 0, l, w + l
    except (ValueError, IndexError):
        pass
    return 0, 0, 0, 0


def win_percentage(record_str):
    w, d, l, gp = parse_record(record_str)
    if gp == 0:
        return 0.5
    return (w + d * 0.5) / gp

def competitiveness(home_record, away_record):
    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)
    diff = abs(home_wpct - away_wpct)

    score = max(0, 6.67 * (1 - diff * 1.5))
    return round(score, 2)


def quality_of_play(home_record, away_record):
    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)
    combined = (home_wpct + away_wpct) / 2
    score = round(combined * 17, 3)
    return min(score, 8.5)

#flip these manually as the season progresses
title_race       = False   
relegation_battle = False 
european_spots   = False   
season_finale    = False   

def importance(home, away, home_record, away_record):
    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)

    score = 0

    avg_wpct = (home_wpct + away_wpct) / 2
    score += round(avg_wpct * 8, 2)

    if title_race:
        if home_wpct > 0.6 and away_wpct > 0.6:
            score += 4
        elif home_wpct > 0.55 or away_wpct > 0.55:
            score += 2

    if relegation_battle:
        if home_wpct < 0.35 and away_wpct < 0.35:
            score += 4
        elif home_wpct < 0.4 or away_wpct < 0.4:
            score += 2

    if european_spots:
        if home_wpct > 0.5 and away_wpct > 0.5:
            score += 2

    if season_finale:
        score += 2

    return round(min(score, 14), 2)


def calculate_score(home, away, home_record="0-0-0", away_record="0-0-0"):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home_record, away_record)
    q = quality_of_play(home_record, away_record)
    g = importance(home, away, home_record, away_record)
    return round(r + m + c + q + g, 2)


def calculate_score_breakdown(home, away, home_record="0-0-0", away_record="0-0-0"):
    return {
        "rivalry":        rivalry(home, away),
        "marketability":  marketability(home, away),
        "competitiveness": competitiveness(home_record, away_record),
        "quality":        quality_of_play(home_record, away_record),
        "importance":     importance(home, away, home_record, away_record),
    }
