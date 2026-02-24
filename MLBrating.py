import requests
url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
data = requests.get(url).json()

season_length = 162
playoffs = False


team_marketability = {
    "ARI_MLB": 6, "ATL_MLB": 8, "BAL_MLB": 7.5, "BOS_MLB": 10, "CHC_MLB": 9,
    "CHW_MLB": 7, "CIN_MLB": 6.5, "CLE_MLB": 7, "COL_MLB": 6, "DET_MLB": 7,
    "HOU_MLB": 9, "KC_MLB": 6, "LAA_MLB": 7.5, "LAD_MLB": 10, "MIA_MLB": 5.5,
    "MIL_MLB": 6.5, "MIN_MLB": 7, "NYM_MLB": 9, "NYY_MLB": 10, "OAK_MLB": 4.5,
    "PHI_MLB": 8.5, "PIT_MLB": 6.5, "SD_MLB": 8, "SF_MLB": 9, "SEA_MLB": 7.5,
    "STL_MLB": 9, "TB_MLB": 7, "TEX_MLB": 8, "TOR_MLB": 8, "WSH_MLB": 7
}
rivalries = [
    ("BOS_MLB", "NYY_MLB", 10)
]
def buildRecords():
    records = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_MLB"
            record = competitor["records"][0]["summary"]
            records[team_abbr] = record
    return records
def buildSeeds():
    seeds = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_MLB"
            seed = competitor.get("seed", {}).get("rank", None)
            seeds[team_abbr] = int(seed) if seed else None
    return seeds

def calculateScore(home, away):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away)
    q = qualityOfPlay(home, away)
    g = gameImportance(home, away)

    print(f"DEBUG {home} vs {away} → R:{r} M:{m} C:{c} Q:{q} G:{g}")
    return round((r + m + c + q + g), 2)


def rivalry(home,away):
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
    gamesLeft = season_length - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        importance += 30
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
