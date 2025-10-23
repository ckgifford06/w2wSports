import requests
url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
data = requests.get(url).json()

season_length = 82
playoffs = False

team_marketability = { 
    "ANA_NHL": 6, "UTA_NHL": 5.5, "BOS_NHL": 10, "BUF_NHL": 7, "CAR_NHL": 6,
    "CBJ_NHL": 6.5, "CGY_NHL": 7, "CHI_NHL": 8, "COL_NHL": 6.5, "DAL_NHL": 7.5,
    "DET_NHL": 8, "EDM_NHL": 6, "FLA_NHL": 6.5, "LA_NHL": 9, "MIN_NHL": 7,
    "MTL_NHL": 8.5, "NJD_NHL": 7, "NSH_NHL": 7.5, "NYI_NHL": 8, "NYR_NHL": 9,
    "OTT_NHL": 6, "PHI_NHL": 8, "PIT_NHL": 9, "SJS_NHL": 7, "SEA_NHL": 7,
    "STL_NHL": 7, "TBL_NHL": 8, "TOR_NHL": 9, "VAN_NHL": 6.5, "VGK_NHL": 7.5,
    "WPG_NHL": 7, "WSH_NHL": 8
}

rivalries = [
    
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
