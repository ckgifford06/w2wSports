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

def calculateScore(home, away):
    return 0
