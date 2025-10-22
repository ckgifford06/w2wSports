import requests
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
data = requests.get(url).json()

season_length = 17
playoffs = False

team_marketability = {
    "ARI_NFL": 6, "ATL_NFL": 6.5, "BAL_NFL": 8, "BUF_NFL": 8, "CAR_NFL": 5,
    "CHI_NFL": 9, "CIN_NFL": 8, "CLE_NFL": 7, "DAL_NFL": 10, "DEN_NFL": 8,
    "DET_NFL": 7.5, "GB_NFL": 9, "HOU_NFL": 6.5, "IND_NFL": 6, "JAX_NFL": 6,
    "KC_NFL": 10, "LV_NFL": 9, "LAC_NFL": 6.5, "LAR_NFL": 8, "MIA_NFL": 8,
    "MIN_NFL": 7.5, "NE_NFL": 10, "NO_NFL": 8, "NYG_NFL": 9, "NYJ_NFL": 8.5,
    "PHI_NFL": 9.5, "PIT_NFL": 9, "SF_NFL": 10, "SEA_NFL": 8, "TB_NFL": 8,
    "TEN_NFL": 6.5, "WAS_NFL": 7
}
rivalries = {
    
}
team_division = {
    "BUF_NFL": "AFC East", "MIA_NFL": "AFC East", "NE_NFL": "AFC East", "NYJ_NFL": "AFC East",
    "BAL_NFL": "AFC North", "CIN_NFL": "AFC North", "CLE_NFL": "AFC North", "PIT_NFL": "AFC North",
    "HOU_NFL": "AFC South", "IND_NFL": "AFC South", "JAX_NFL": "AFC South", "TEN_NFL": "AFC South",
    "DEN_NFL": "AFC West", "KC_NFL": "AFC West", "LV_NFL": "AFC West", "LAC_NFL": "AFC West",
    "DAL_NFL": "NFC East", "NYG_NFL": "NFC East", "PHI_NFL": "NFC East", "WAS_NFL": "NFC East",
    "CHI_NFL": "NFC North", "DET_NFL": "NFC North", "GB_NFL": "NFC North", "MIN_NFL": "NFC North",
    "ATL_NFL": "NFC South", "CAR_NFL": "NFC South", "NO_NFL": "NFC South", "TB_NFL": "NFC South",
    "ARI_NFL": "NFC West", "LAR_NFL": "NFC West", "SF_NFL": "NFC West", "SEA_NFL": "NFC West"
}
def buildRecords():
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NFL"
            record = competitor["records"][0]["summary"]  # e.g. "5-2"
            records[team_abbr] = record
    return records

def buildSeeds():
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NFL"
            seed = competitor.get("seed", {}).get("rank", None)
            seeds[team_abbr] = int(seed) if seed else None
    return seeds

def calculateScore(home, away):
    return rivalry(home,away) + marketability(home,away) + competitiveness(home,away) + gameImportance(home,away)

def rivalry(home, away):
    rating = 0
    if team_division.get(home) == team_division.get(away):
        rating += 5
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            rating += r
    return rating

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)
    
def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    winDiff = abs(int(homeRecord[0]) - int(awayRecord.[0]))
    compRank = (10 - winDiff)
    return compRank
    
def gameImportance(home, away):
    records = buildRecords()
    seeds = buildSeeds()
    importance = 0
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    homeGamesPlayed = int(homeRecord[0]) + int(homeRecord[1])
    awayGamesPlayed = int(awayRecord[0]) + int(awayRecord[1])
    home_seed = seeds.get(home)
    away_seed = seeds.get(away)
    gamesLeft = 17 - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        # not yet
        pass
    else:
        if gamesLeft > 12:
            return importance
        if gamesLeft <= 12:
            importance += 1
        if gamesLeft <= 7:
            importance += 1
        if gamesLeft <= 4:
            importance += 1
        if home_seed < 9 and home_seed > 5:
            importance += 3
        if away_seed < 9 and home_seed > 5:
            importance += 3
    return importance
