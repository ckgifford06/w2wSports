import requests
import logging

URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
_cached_data = None

ABBR_ALIASES = {"WSH": "WAS"}

def _get_data():
    global _cached_data
    if _cached_data is None:
        _cached_data = requests.get(URL).json()
    return _cached_data

def _team_key(competitor):
    abbr = competitor["team"]["abbreviation"]
    return ABBR_ALIASES.get(abbr, abbr) + "_NFL"

def _parse_record(record):
    parts = [int(p) for p in record.split("-")]
    wins = parts[0] if len(parts) > 0 else 0
    losses = parts[1] if len(parts) > 1 else 0
    ties = parts[2] if len(parts) > 2 else 0
    return wins, losses, ties

season_length = 17
playoffs = False

team_marketability = {
    "ARI_NFL": 6, "ATL_NFL": 6.5, "BAL_NFL": 8, "BUF_NFL": 8, "CAR_NFL": 5,
    "CHI_NFL": 9, "CIN_NFL": 8, "CLE_NFL": 7, "DAL_NFL": 10, "DEN_NFL": 8,
    "DET_NFL": 7.5, "GB_NFL": 9, "HOU_NFL": 6.5, "IND_NFL": 6, "JAX_NFL": 6,
    "KC_NFL": 10, "LV_NFL": 9, "LAC_NFL": 6.5, "LAR_NFL": 8, "MIA_NFL": 8,
    "MIN_NFL": 7.5, "NE_NFL": 10, "NO_NFL": 8, "NYG_NFL": 9, "NYJ_NFL": 8.5,
    "PHI_NFL": 9.5, "PIT_NFL": 9, "SF_NFL": 10, "SEA_NFL": 8, "TB_NFL": 8,
    "TEN_NFL": 6.5, "WSH_NFL": 7
}

rivalries = [
    ("BUF_NFL", "MIA_NFL"), ("BUF_NFL", "NE_NFL"), ("BUF_NFL", "NYJ_NFL"),
    ("MIA_NFL", "NE_NFL"), ("MIA_NFL", "NYJ_NFL"), ("NE_NFL", "NYJ_NFL"),

    ("BAL_NFL", "CIN_NFL"), ("BAL_NFL", "CLE_NFL"), ("BAL_NFL", "PIT_NFL"),
    ("CIN_NFL", "CLE_NFL"), ("CIN_NFL", "PIT_NFL"), ("CLE_NFL", "PIT_NFL"),

    ("HOU_NFL", "IND_NFL"), ("HOU_NFL", "JAX_NFL"), ("HOU_NFL", "TEN_NFL"),
    ("IND_NFL", "JAX_NFL"), ("IND_NFL", "TEN_NFL"), ("JAX_NFL", "TEN_NFL"),

    ("DEN_NFL", "KC_NFL"), ("DEN_NFL", "LV_NFL"), ("DEN_NFL", "LAC_NFL"),
    ("KC_NFL", "LV_NFL"), ("KC_NFL", "LAC_NFL"), ("LV_NFL", "LAC_NFL"),

    ("DAL_NFL", "NYG_NFL"), ("DAL_NFL", "PHI_NFL"), ("DAL_NFL", "WAS_NFL"),
    ("NYG_NFL", "PHI_NFL"), ("NYG_NFL", "WAS_NFL"), ("PHI_NFL", "WSH_NFL"),

    ("CHI_NFL", "DET_NFL"), ("CHI_NFL", "GB_NFL"), ("CHI_NFL", "MIN_NFL"),
    ("DET_NFL", "GB_NFL"), ("DET_NFL", "MIN_NFL"), ("GB_NFL", "MIN_NFL"),

    ("ATL_NFL", "CAR_NFL"), ("ATL_NFL", "NO_NFL"), ("ATL_NFL", "TB_NFL"),
    ("CAR_NFL", "NO_NFL"), ("CAR_NFL", "TB_NFL"), ("NO_NFL", "TB_NFL"),

    ("ARI_NFL", "LAR_NFL"), ("ARI_NFL", "SF_NFL"), ("ARI_NFL", "SEA_NFL"),
    ("LAR_NFL", "SF_NFL"), ("LAR_NFL", "SEA_NFL"), ("SF_NFL", "SEA_NFL"),
]

rivalry_set = {frozenset(pair) for pair in rivalries}

team_division = {
    "BUF_NFL": "AFC East", "MIA_NFL": "AFC East", "NE_NFL": "AFC East", "NYJ_NFL": "AFC East",
    "BAL_NFL": "AFC North", "CIN_NFL": "AFC North", "CLE_NFL": "AFC North", "PIT_NFL": "AFC North",
    "HOU_NFL": "AFC South", "IND_NFL": "AFC South", "JAX_NFL": "AFC South", "TEN_NFL": "AFC South",
    "DEN_NFL": "AFC West", "KC_NFL": "AFC West", "LV_NFL": "AFC West", "LAC_NFL": "AFC West",
    "DAL_NFL": "NFC East", "NYG_NFL": "NFC East", "PHI_NFL": "NFC East", "WSH_NFL": "NFC East",
    "CHI_NFL": "NFC North", "DET_NFL": "NFC North", "GB_NFL": "NFC North", "MIN_NFL": "NFC North",
    "ATL_NFL": "NFC South", "CAR_NFL": "NFC South", "NO_NFL": "NFC South", "TB_NFL": "NFC South",
    "ARI_NFL": "NFC West", "LAR_NFL": "NFC West", "SF_NFL": "NFC West", "SEA_NFL": "NFC West"
}

def buildRecords():
    records = {}
    for event in _get_data()["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = _team_key(competitor)
            team_records = competitor.get("records") or []
            records[team_abbr] = team_records[0]["summary"] if team_records else "0-0"
    return records

def buildSeeds():
    seeds = {}
    for event in _get_data()["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = _team_key(competitor)
            seed = competitor.get("seed", {}).get("rank", None)
            seeds[team_abbr] = int(seed) if seed else None
    return seeds

def qualityOfPlay(home, away):
    records = buildRecords()
    homeWins, homeLosses, homeTies = _parse_record(records.get(home, "0-0"))
    awayWins, awayLosses, awayTies = _parse_record(records.get(away, "0-0"))
    combinedWins = float(homeWins + awayWins)
    gamesPlayed = float(homeWins + homeLosses + homeTies + awayWins + awayLosses + awayTies)
    if gamesPlayed == 0:
        return 0
    quality = round(((combinedWins / gamesPlayed) * 10), 3)
    return quality

def calculate_score(home, away):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away)
    q = qualityOfPlay(home, away)
    g = gameImportance(home, away)

    return round((r + m + c + q + g), 2) + 5

def calculate_score_breakdown(home, away):
    return {
        "rivalry":         round(rivalry(home, away), 2),
        "marketability":   round(marketability(home, away), 2),
        "competitiveness": round(competitiveness(home, away), 2),
        "quality":         round(qualityOfPlay(home, away), 2),
        "importance":      round(gameImportance(home, away), 2),
    }

def rivalry(home, away):
    if frozenset((home, away)) in rivalry_set:
        return 5
    return 0

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)

def competitiveness(home, away):
    records = buildRecords()
    homeWins, _, _ = _parse_record(records.get(home, "0-0"))
    awayWins, _, _ = _parse_record(records.get(away, "0-0"))
    winDiff = abs(homeWins - awayWins)
    compRank = (10 - winDiff)
    return compRank

def gameImportance(home, away):
    records = buildRecords()
    seeds = buildSeeds()
    importance = 2
    homeWins, homeLosses, homeTies = _parse_record(records.get(home, "0-0"))
    awayWins, awayLosses, awayTies = _parse_record(records.get(away, "0-0"))
    homeGamesPlayed = homeWins + homeLosses + homeTies
    awayGamesPlayed = awayWins + awayLosses + awayTies
    home_seed = seeds.get(home)
    away_seed = seeds.get(away)
    gamesLeft = season_length - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        importance += 15
    else:
        if gamesLeft > 12:
            return importance
        if gamesLeft <= 12:
            importance += 1
        if gamesLeft <= 7:
            importance += 1
        if gamesLeft <= 4:
            importance += 1
        if home_seed is not None and 5 < home_seed < 9:
            importance += 3
        if away_seed is not None and 5 < away_seed < 9:
            importance += 3
    return importance
