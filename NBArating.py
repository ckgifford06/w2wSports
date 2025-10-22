import requests
url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
data = requests.get(url).json()

season_length = 82
playoffs = False

team_marketability = {
    "BOS_NBA": 9, "BKN_NBA": 7, "NY_NBA": 10, "PHI_NBA": 8, "TOR_NBA": 6,
    "CHI_NBA": 8, "CLE_NBA": 7, "DET_NBA": 5, "IND_NBA": 6, "MIL_NBA": 7,
    "ATL_NBA": 7, "CHA_NBA": 5, "MIA_NBA": 7, "ORL_NBA": 6, "WAS_NBA": 6.5,
    "DEN_NBA": 7, "MIN_NBA": 6, "OKC_NBA": 6, "POR_NBA": 5:, "UTAH_NBA": 5,
    "GS_NBA": 9, "LAC_NBA": 7, "LAL_NBA": 10, "PHX_NBA":7, "SAC_NBA": 5,
    "DAL_NBA": 8, "HOU_NBA": 7.5, "MEM_NBA": 5, "NO_NBA": 6, "SAS_NBA": 7
}
rivalries = [
    ("LAL_NBA", "BOS_NBA", 10), ("NY_NBA", "BOS_NBA", 10),("NY_NBA", "IND_NBA", 7) 
    ("CHI_NBA", "IND_NBA", 6), ("MIA_NBA", "BOS_NBA", 6),("MIA_NBA", "NY_NBA", 6),
    ("DAL_NBA", "SAS_NBA", 5),("GS_NBA", "LAL_NBA", 5),("PHX_NBA", "SAS_NBA", 5), 
    ("TOR_NBA", "BOS_NBA", 4),("NY_NBA", "PHI_NBA", 8),("DAL_NBA", "LAL_NBA", 8)
    ("OKC_NBA", "GS_NBA", 6),("LAC_NBA", "GS_NBA", 7), ("LAL_NBA", "SAS_NBA", 7)
]
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


def calculate_score(home, away):
    return rivalry(home,away) + marketability(home,away) + competitiveness(home,away) + gameImportance(home,away)


def rivalry(home, away):
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            return r
    else: return 0

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)
    
def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    winDiff = abs(homeRecord[0] - awayRecord.[0])
    compRank = (20 - winDiff) / 5
    return compRank
    
def gameImportance(home, away):
    seeds = buildSeeds()
    records = buildRecords()
    importance = 0
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    homeGamesPlayed = homeRecord[0] + homeRecord[1]
    awayGamesPlayed = awayRecord[0] + awayRecord[1]
    home_seed = home["team"].get("seed", {}).get("rank")
    away_seed = away["team"].get("seed", {}).get("rank")
    gamesLeft = 82 - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        # not yet
    else:
        if gamesLeft > 50:
            return importance
        if gamesLeft <= 50:
            importance += 1
        if gamesLeft <= 30:
            importance += 1
        if gamesLeft <= 20:
            importance += 1
        if home_seed < 11 and home_seed > 6:
            importance += 3
        if away_seed < 11 and home_seed > 6:
            importance += 3
    return importance


