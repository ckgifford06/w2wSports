RIVALRIES = {
    frozenset(["RMA_UCL", "BAR_UCL"]): 14,
    frozenset(["RMA_UCL", "BAY_UCL"]): 11,
    frozenset(["RMA_UCL", "LIV_UCL"]): 11,
    frozenset(["RMA_UCL", "MCI_UCL"]): 10,
    frozenset(["RMA_UCL", "PSG_UCL"]): 10,
    frozenset(["RMA_UCL", "ATL_UCL"]): 10,
    frozenset(["RMA_UCL", "JUV_UCL"]): 8,
    frozenset(["BAR_UCL", "PSG_UCL"]): 10,
    frozenset(["BAR_UCL", "BAY_UCL"]): 9,
    frozenset(["BAR_UCL", "CHE_UCL"]): 7,
    frozenset(["BAY_UCL", "DOR_UCL"]): 10,
    frozenset(["BAY_UCL", "LIV_UCL"]): 8,
    frozenset(["MCI_UCL", "LIV_UCL"]): 10,
    frozenset(["MCI_UCL", "MUN_UCL"]): 12,
    frozenset(["MCI_UCL", "RMA_UCL"]): 10,
    frozenset(["ARS_UCL", "TOT_UCL"]): 12,
    frozenset(["ARS_UCL", "BAY_UCL"]): 7,
    frozenset(["LIV_UCL", "MUN_UCL"]): 12,
    frozenset(["CHE_UCL", "ARS_UCL"]): 9,
    frozenset(["INT_UCL", "MIL_UCL"]): 12,
    frozenset(["INT_UCL", "JUV_UCL"]): 10,
    frozenset(["JUV_UCL", "MIL_UCL"]): 9,
    frozenset(["NAP_UCL", "JUV_UCL"]): 8,
    frozenset(["POR_UCL", "BEN_UCL"]): 10,
    frozenset(["BEN_UCL", "SPO_UCL"]): 10,
    frozenset(["PSV_UCL", "FEY_UCL"]): 8,
    frozenset(["AJA_UCL", "FEY_UCL"]): 10,
    frozenset(["DOR_UCL", "LEV_UCL"]): 6,
    frozenset(["CEL_UCL", "ARS_UCL"]): 4,
}

def rivalry(home, away):
    return RIVALRIES.get(frozenset([home, away]), 0)


CLUB_PRESTIGE = {
    "RMA_UCL": 10, "BAR_UCL": 9, "BAY_UCL": 9, "MCI_UCL": 9, "LIV_UCL": 9, "PSG_UCL": 9,
    "ARS_UCL": 7, "INT_UCL": 7, "JUV_UCL": 7, "ATL_UCL": 7, "CHE_UCL": 7, "MUN_UCL": 7,
    "DOR_UCL": 7, "MIL_UCL": 7, "NAP_UCL": 7, "ATA_UCL": 6, "LEV_UCL": 6, "TOT_UCL": 6,
    "RBL_UCL": 6, "BEN_UCL": 5, "POR_UCL": 5, "SPO_UCL": 5, "FEY_UCL": 5, "AJA_UCL": 5,
    "PSV_UCL": 5, "CEL_UCL": 5, "RSO_UCL": 4, "SHA_UCL": 4, "SLB_UCL": 4, "STU_UCL": 4,
    "BRU_UCL": 4, "BRE_UCL": 3, "LIL_UCL": 4, "MON_UCL": 4, "BOL_UCL": 4,
}

def marketability(home, away):
    h = CLUB_PRESTIGE.get(home, 3)
    a = CLUB_PRESTIGE.get(away, 3)
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
    score = max(0, 10 * (1 - diff * 1.3))
    return round(score, 2)


def quality_of_play(home, away, home_record, away_record):
    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)
    form_component = ((home_wpct + away_wpct) / 2) * 10
    prestige_component = (CLUB_PRESTIGE.get(home, 3) + CLUB_PRESTIGE.get(away, 3)) * 0.4
    score = round(form_component + prestige_component, 2)
    return min(score, 14)


#flip these manually as the competition progresses
#stage options: "league_phase", "knockout_playoff", "round_of_16", "quarterfinals", "semifinals", "final"
STAGE = "semifinals"
matchday_decider = False
is_matchday_final = False

STAGE_BONUS = {
    "league_phase":     0,
    "knockout_playoff": 4,
    "round_of_16":      7,
    "quarterfinals":    10,
    "semifinals":       13,
    "final":            16,
}


def importance(home, away, home_record, away_record):
    score = STAGE_BONUS.get(STAGE, 0)

    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)
    avg_wpct = (home_wpct + away_wpct) / 2
    score += round(avg_wpct * 4, 2)

    if STAGE == "league_phase":
        if matchday_decider and (home_wpct > 0.55 or away_wpct > 0.55):
            score += 3
        if is_matchday_final:
            score += 4

    if STAGE == "final":
        score = STAGE_BONUS["final"] + 4

    return round(min(score, 22), 2)


def calculate_score(home, away, home_record="0-0-0", away_record="0-0-0"):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home_record, away_record)
    q = quality_of_play(home, away, home_record, away_record)
    g = importance(home, away, home_record, away_record)
    return round(r + m + c + q + g, 2)


def calculate_score_breakdown(home, away, home_record="0-0-0", away_record="0-0-0"):
    return {
        "rivalry":         rivalry(home, away),
        "marketability":   marketability(home, away),
        "competitiveness": competitiveness(home_record, away_record),
        "quality":         quality_of_play(home, away, home_record, away_record),
        "importance":      importance(home, away, home_record, away_record),
    }
