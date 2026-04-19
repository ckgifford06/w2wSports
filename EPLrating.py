RIVALRIES = {
    # Manchester derby
    frozenset(["MNC_EPL", "MUN_EPL"]): 12,
    # North London derby
    frozenset(["ARS_EPL", "TOT_EPL"]): 12,
    # Merseyside derby
    frozenset(["LIV_EPL", "EVE_EPL"]): 12,
    # Tyne-Wear derby
    frozenset(["NEW_EPL", "SUN_EPL"]): 12,
    # Northwest derby
    frozenset(["LIV_EPL", "MUN_EPL"]): 12,
    # Roses rivalry
    frozenset(["LEE_EPL", "MUN_EPL"]): 11,
    # Modern title rivalries
    frozenset(["MNC_EPL", "LIV_EPL"]): 11,
    frozenset(["MNC_EPL", "ARS_EPL"]): 10,
    frozenset(["ARS_EPL", "MUN_EPL"]): 10,
    frozenset(["LIV_EPL", "ARS_EPL"]): 9,
    # Chelsea rivalries
    frozenset(["CHE_EPL", "ARS_EPL"]): 9,
    frozenset(["CHE_EPL", "TOT_EPL"]): 10,
    frozenset(["CHE_EPL", "LIV_EPL"]): 9,
    frozenset(["CHE_EPL", "MUN_EPL"]): 8,
    # Tottenham extras
    frozenset(["TOT_EPL", "MUN_EPL"]): 6,
    frozenset(["TOT_EPL", "WHU_EPL"]): 7,
    # Other derbies and rivalries
    frozenset(["AVL_EPL", "WOL_EPL"]): 8,
    frozenset(["AVL_EPL", "BIR_EPL"]): 9,   # Second City derby (Birmingham rarely in PL)
    frozenset(["BHA_EPL", "CRY_EPL"]): 9,   # M23 derby
    frozenset(["WHU_EPL", "MIL_EPL"]): 8,   # Millwall rarely in PL
    frozenset(["LEI_EPL", "NFO_EPL"]): 8,   # East Midlands derby
    frozenset(["NFO_EPL", "DER_EPL"]): 9,   # Derby rarely in PL
    frozenset(["SOU_EPL", "BOU_EPL"]): 6,   # South Coast
    frozenset(["SOU_EPL", "POR_EPL"]): 10,  # Portsmouth rarely in PL
    frozenset(["FUL_EPL", "CHE_EPL"]): 6,   # West London derby
    frozenset(["FUL_EPL", "BRE_EPL"]): 5,
    frozenset(["BUR_EPL", "BB_EPL"]):  9,   # East Lancashire (Blackburn rarely in PL)
    frozenset(["BUR_EPL", "LEE_EPL"]): 6,
}

def rivalry(home, away):
    return RIVALRIES.get(frozenset([home, away]), 0)


# Tiered by global audience, historical stature, and current profile
TEAM_MARKETABILITY = {
    # Tier 1: Global giants
    "MUN_EPL": 8,
    "LIV_EPL": 8,
    "MNC_EPL": 8,
    "ARS_EPL": 8,
    "CHE_EPL": 7,
    # Tier 2: Big Six edge
    "TOT_EPL": 6,
    "NEW_EPL": 6,
    # Tier 3: Established PL clubs
    "AVL_EPL": 5,
    "WHU_EPL": 5,
    "EVE_EPL": 5,
    "LEI_EPL": 5,
    "NFO_EPL": 5,
    "LEE_EPL": 5,
    # Tier 4: Mid/lower table
    "BHA_EPL": 4,
    "CRY_EPL": 4,
    "WOL_EPL": 4,
    "SUN_EPL": 4,
    # Tier 5: Smaller or recently promoted
    "FUL_EPL": 3,
    "BRE_EPL": 3,
    "BOU_EPL": 3,
    "SOU_EPL": 3,
    "BUR_EPL": 3,
    "IPS_EPL": 2,
    "LUT_EPL": 2,
    "SHU_EPL": 2,
}

def marketability(home, away):
    h = TEAM_MARKETABILITY.get(home, 3)
    a = TEAM_MARKETABILITY.get(away, 3)
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
title_race       = True
relegation_battle = True
european_spots   = True
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
