import requests
url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
data = requests.get(url).json()

season_length = 82
playoffs = False

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
    # Use below website to continue
    # https://www.yardbarker.com/nhl/articles/the_all_time_best_nhl_rivalries/s1__40843961#slide_10
]

def buildRecords():
    records = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NHL"
            record = competitor["records"][0]["summary"]
            records[team_abbr] = record
    return records
def buildSeeds():
    seeds = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NHL"
            seed = competitor.get("seed", {}).get("rank", None)
            seeds[team_abbr] = int(seed) if seed else None
    return seeds


def calculate_score(home, away):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away)
    q = qualityOfPlay(home, away)
    g = gameImportance(home, away)

    print(f"DEBUG {home} vs {away} → R:{r} M:{m} C:{c} Q:{q} G:{g}")
    return round((r + m + c + q + g), 2)



def calculate_score_breakdown(home, away):
    return {
        "rivalry":        round(rivalry(home, away), 2),
        "marketability":  round(marketability(home, away), 2),
        "competitiveness":round(competitiveness(home, away), 2),
        "quality":        round(qualityOfPlay(home, away), 2),
        "importance":     round(gameImportance(home, away), 2),
    }

def rivalry(home, away):
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            return r
    else: return 0

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)
    
def competitiveness(home, away):
    records = buildRecords()
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    try:
        winDiff = abs(homeRecord[0] - awayRecord[0])
    except ValueError:
        winDiff = 0
    compRank = (20 - winDiff) / 5
    return compRank

def qualityOfPlay(home, away):
    records = buildRecords()
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    combinedWins = float(homeRecord[0] + awayRecord[0])
    gamesPlayed = float(homeRecord[0] + homeRecord[1] + awayRecord[0] + awayRecord[1])
    if gamesPlayed == 0:
        return 0
    quality = round(((combinedWins / gamesPlayed)*10), 3)
    return quality
    
def gameImportance(home, away):
    importance = 0
    seeds = buildSeeds()
    records = buildRecords()
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    homeGamesPlayed = int(homeRecord[0]) + int(homeRecord[1])
    awayGamesPlayed = int(awayRecord[0]) + int(awayRecord[1])
    home_seed = seeds.get(home)
    away_seed = seeds.get(away)
    gamesLeft = 82 - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        importance += 10
    else:
        if gamesLeft <= 50:
            importance += 1
        if gamesLeft <= 30:
            importance += 1
        if gamesLeft <= 20:
            importance += 1
        if home_seed is not None and 6 <  home_seed < 11:
            importance += 3
        if away_seed is not None and 6 < away_seed < 11:
            importance += 3
    return importance
