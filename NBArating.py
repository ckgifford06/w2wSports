import requests
url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
data = requests.get(url).json()

season_length = 82
playoffs = False


team_marketability = {
    "BOS_NBA": 9, "BKN_NBA": 7, "NY_NBA": 9, "PHI_NBA": 8, "TOR_NBA": 6,
    "CHI_NBA": 8, "CLE_NBA": 7, "DET_NBA": 5, "IND_NBA": 7, "MIL_NBA": 7,
    "ATL_NBA": 7, "CHA_NBA": 5, "MIA_NBA": 7, "ORL_NBA": 6, "WAS_NBA": 6.5,
    "DEN_NBA": 7, "MIN_NBA": 6, "OKC_NBA": 9, "POR_NBA": 5, "UTAH_NBA": 5,
    "GS_NBA": 9, "LAC_NBA": 7, "LAL_NBA": 9, "PHX_NBA":7, "SAC_NBA": 5,
    "DAL_NBA": 8, "HOU_NBA": 8, "MEM_NBA": 5, "NO_NBA": 6, "SAS_NBA": 8
}
rivalries = [
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
    ("OKC_NBA", "IND_NBA", 5)
]
def buildRecords():
    records = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NBA"
            record = competitor["records"][0]["summary"]
            records[team_abbr] = record
    return records
def buildSeeds():
    seeds = {}
    for event in data["events"]:
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_NBA"
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
    compRank = (20 - winDiff) / 3
    return compRank

def qualityOfPlay(home, away):
    records = buildRecords()
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    combinedWins = float(homeRecord[0] + awayRecord[0])
    gamesPlayed = float(homeRecord[0] + homeRecord[1] + awayRecord[0] + awayRecord[1])
    if gamesPlayed == 0:
        return 0
    quality = round(((combinedWins / gamesPlayed)*17), 3)
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
        pass
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
        if home_seed == 1 and away_seed == 2:
            importance += 5
        if away_seed == 1 and home_seed == 2:
            importance += 5
    return importance

