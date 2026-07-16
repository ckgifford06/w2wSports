# 2026 FIFA World Cup - 48 qualified teams
# AFC (9): Australia, Iran, Iraq, Japan, Jordan, Qatar, Saudi Arabia, South Korea, Uzbekistan
# CAF (10): Algeria, Cape Verde, DR Congo, Egypt, Ghana, Ivory Coast, Morocco, Senegal, South Africa, Tunisia
# CONCACAF (6): Canada, Curaçao, Haiti, Mexico, Panama, USA
# CONMEBOL (6): Argentina, Brazil, Colombia, Ecuador, Paraguay, Uruguay
# OFC (1): New Zealand
# UEFA (16): Austria, Belgium, Bosnia & Herzegovina, Croatia, Czechia, England, France, Germany,
#            Netherlands, Norway, Portugal, Scotland, Spain, Sweden, Switzerland, Türkiye

RIVALRIES = {
    frozenset(["ARG_WC", "BRA_WC"]): 14,
    frozenset(["GER_WC", "ARG_WC"]): 13,
    frozenset(["ENG_WC", "GER_WC"]): 13,
    frozenset(["SCO_WC", "ENG_WC"]): 12,
    frozenset(["FRA_WC", "ARG_WC"]): 12,
    frozenset(["ENG_WC", "ARG_WC"]): 12,
    frozenset(["USA_WC", "MEX_WC"]): 12,
    frozenset(["BRA_WC", "GER_WC"]): 11,
    frozenset(["URU_WC", "ARG_WC"]): 11,
    frozenset(["URU_WC", "BRA_WC"]): 11,
    frozenset(["POR_WC", "ESP_WC"]): 11,
    frozenset(["NED_WC", "GER_WC"]): 11,
    frozenset(["BEL_WC", "NED_WC"]): 10,
    frozenset(["FRA_WC", "ENG_WC"]): 10,
    frozenset(["IRN_WC", "USA_WC"]): 10,
    frozenset(["KOR_WC", "JPN_WC"]): 10,
    frozenset(["MAR_WC", "ALG_WC"]): 10,
    frozenset(["TUR_WC", "GER_WC"]): 9,
    frozenset(["BOS_WC", "CRO_WC"]): 9,
    frozenset(["CAN_WC", "USA_WC"]): 9,
    frozenset(["ESP_WC", "ARG_WC"]): 9,
    frozenset(["MEX_WC", "ARG_WC"]): 9,
    frozenset(["SEN_WC", "EGY_WC"]): 8,
    frozenset(["BRA_WC", "COL_WC"]): 8,
    frozenset(["COL_WC", "ARG_WC"]): 8,
    frozenset(["IRQ_WC", "IRN_WC"]): 8,
    frozenset(["QAT_WC", "SAU_WC"]): 8,
    frozenset(["GHA_WC", "CIV_WC"]): 8,
    frozenset(["NOR_WC", "SWE_WC"]): 7,
    frozenset(["ECU_WC", "COL_WC"]): 7,
    frozenset(["PAR_WC", "ARG_WC"]): 7,
    frozenset(["PAR_WC", "URU_WC"]): 7,
    frozenset(["AUS_WC", "NZL_WC"]): 7,
    frozenset(["MEX_WC", "CAN_WC"]): 6,
    frozenset(["CZE_WC", "SCO_WC"]): 5,
    frozenset(["AUT_WC", "GER_WC"]): 6,
    frozenset(["SUI_WC", "GER_WC"]): 5,
}

def rivalry(home, away):
    return RIVALRIES.get(frozenset([home, away]), 0)


COUNTRY_PRESTIGE = {
    "ARG_WC": 10,
    "BRA_WC": 10,
    "FRA_WC": 9,
    "GER_WC": 9,
    "ESP_WC": 8,
    "ENG_WC": 8,
    "POR_WC": 8,
    "NED_WC": 7,
    "URU_WC": 7,
    "COL_WC": 7,
    "MEX_WC": 7,
    "USA_WC": 7,
    "BEL_WC": 7,
    "MAR_WC": 7,
    "NOR_WC": 6,
    "CRO_WC": 6,
    "JPN_WC": 6,
    "KOR_WC": 6,
    "SEN_WC": 6,
    "SWE_WC": 5,
    "SUI_WC": 5,
    "AUT_WC": 5,
    "TUR_WC": 5,
    "ECU_WC": 5,
    "PAR_WC": 5,
    "AUS_WC": 5,
    "SAU_WC": 5,
    "GHA_WC": 5,
    "CIV_WC": 5,
    "ALG_WC": 5,
    "EGY_WC": 5,
    "SCO_WC": 5,
    "CAN_WC": 5,
    "IRN_WC": 5,
    "IRQ_WC": 4,
    "QAT_WC": 4,
    "BOS_WC": 4,
    "CZE_WC": 4,
    "TUN_WC": 4,
    "PAN_WC": 4,
    "HAI_WC": 4,
    "ZAF_WC": 4,
    "CPV_WC": 4,
    "COD_WC": 4,
    "CUW_WC": 3,
    "UZB_WC": 3,
    "JOR_WC": 3,
    "NZL_WC": 3,
}

def marketability(home, away):
    h = COUNTRY_PRESTIGE.get(home, 3)
    a = COUNTRY_PRESTIGE.get(away, 3)
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
    prestige_component = (COUNTRY_PRESTIGE.get(home, 3) + COUNTRY_PRESTIGE.get(away, 3)) * 0.4
    score = round(form_component + prestige_component, 2)
    return min(score, 14)


# Flip manually as the tournament progresses
# stage options: "group", "round_of_32", "round_of_16", "quarterfinals", "semifinals", "final"
STAGE = "group"
is_must_win = True
is_final_matchday = True

STAGE_BONUS = {
    "group":         0,
    "round_of_32":   5,
    "round_of_16":   8,
    "quarterfinals": 11,
    "semifinals":    14,
    "final":         17,
}


def importance(home, away, home_record, away_record):
    score = STAGE_BONUS.get(STAGE, 0)

    home_wpct = win_percentage(home_record)
    away_wpct = win_percentage(away_record)
    avg_wpct = (home_wpct + away_wpct) / 2
    score += round(avg_wpct * 4, 2)

    if STAGE == "group":
        if is_must_win:
            score += 4
        if is_final_matchday:
            score += 3

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
