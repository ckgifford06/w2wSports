import requests
url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
data = requests.get(url).json()

season_length = 13
playoffs = True

team_marketability = {
    # SEC
    "ALA_CFB": 10, "TEX_CFB": 10, "UGA_CFB": 9.5, "LSU_CFB": 9, "FLA_CFB": 9,
    "TENN_CFB": 8.5, "AUB_CFB": 8.5, "TEXAM_CFB": 8, "ARK_CFB": 7,
    "MSST_CFB": 6.5, "MISS_CFB": 7, "MIZZ_CFB": 6.5, "UK_CFB": 6.5,
    "SCAR_CFB": 7, "VANDY_CFB": 5.5,

    # Big Ten
    "MICH_CFB": 10, "OSU_CFB": 10, "PSU_CFB": 9, "WISC_CFB": 8,
    "IOWA_CFB": 7.5, "MSU_CFB": 7.5, "NEB_CFB": 8, "MINN_CFB": 7,
    "ILL_CFB": 6, "IND_CFB": 6, "NW_CFB": 6.5, "RUTG_CFB": 6,
    "MD_CFB": 6.5, "PUR_CFB": 6.5,

    # Big 12
    "OK_CFB": 9.5, "KSU_CFB": 7.5, "TCU_CFB": 7.5,
    "BAY_CFB": 7, "TTU_CFB": 7, "WVU_CFB": 7, "BYU_CFB": 8,
    "CIN_CFB": 7, "UCF_CFB": 7, "HOU_CFB": 6.5, "ISU_CFB": 6.5,
    "KU_CFB": 6.5, "UTSA_CFB": 6,

    # ACC
    "CLEM_CFB": 9, "FSU_CFB": 9, "MIA_CFB": 8.5, "ND_CFB": 9.5,   # Notre Dame partial ACC member
    "UNC_CFB": 8, "VT_CFB": 8, "NCST_CFB": 7.5, "LOU_CFB": 7.5,
    "PITT_CFB": 7, "GT_CFB": 7, "WAKE_CFB": 6.5, "BC_CFB": 6.5,
    "DUKE_CFB": 7, "SYR_CFB": 7, "UVA_CFB": 7
}
rivalries = {
    "ALA_CFB": [("AUB_CFB", 10), ("LSU_CFB", 9), ("TENN_CFB", 8)],
    "AUB_CFB": [("ALA_CFB", 10), ("GA_CFB", 8)],
    "LSU_CFB": [("ALA_CFB", 9), ("ARK_CFB", 7)],
    "GA_CFB": [("FLA_CFB", 9), ("AUB_CFB", 8)],
    
    "MICH_CFB": [("OSU_CFB", 10), ("MSU_CFB", 8)],
    "OSU_CFB": [("MICH_CFB", 10), ("UM_CFB", 7)],
    
    "TEX_CFB": [("OK_CFB", 9), ("UT_CFB", 8)],
    "OK_CFB": [("TEX_CFB", 9)],
    
    "USC_CFB": [("ND_CFB", 8), ("UCLA_CFB", 7)],
    "ND_CFB": [("USC_CFB", 8)],
    
    "FLA_CFB": [("GA_CFB", 9), ("FSU_CFB", 8)],
    "FSU_CFB": [("FLA_CFB", 8)]
}
team_conference = {
    # SEC
    "ALA_CFB": "SEC", "ARK_CFB": "SEC", "AUB_CFB": "SEC", "FLA_CFB": "SEC",
    "GA_CFB": "SEC", "KY_CFB": "SEC", "LSU_CFB": "SEC", "MSST_CFB": "SEC",
    "MO_CFB": "SEC", "MIA_CFB": "SEC", "TENN_CFB": "SEC", "VANDY_CFB": "SEC",
    "TEXASAM_CFB": "SEC", "UGA_CFB": "SEC", "USC_CFB": "SEC",

    # Big Ten
    "ILL_CFB": "Big Ten", "IND_CFB": "Big Ten", "IOWA_CFB": "Big Ten",
    "MARY_CFB": "Big Ten", "MICH_CFB": "Big Ten", "MINN_CFB": "Big Ten",
    "NEB_CFB": "Big Ten", "NW_CFB": "Big Ten", "OSU_CFB": "Big Ten",
    "PSU_CFB": "Big Ten", "RUTG_CFB": "Big Ten", "WISC_CFB": "Big Ten",

    # Big 12
    "BAY_CFB": "Big 12", "BYU_CFB": "Big 12", "CIN_CFB": "Big 12", 
    "KANS_CFB": "Big 12", "KSU_CFB": "Big 12", "OK_CFB": "Big 12",
    "OKST_CFB": "Big 12", "TCU_CFB": "Big 12", "UT_CFB": "Big 12",
    "UTSA_CFB": "Big 12", "WVU_CFB": "Big 12",

    # ACC
    "BC_CFB": "ACC", "CLEM_CFB": "ACC", "Duke_CFB": "ACC", "FLS_CFB": "ACC",
    "GT_CFB": "ACC", "MIA_CFB": "ACC", "NCST_CFB": "ACC", "ND_CFB": "ACC",
    "PITT_CFB": "ACC", "Syracuse_CFB": "ACC", "UVA_CFB": "ACC", "VT_CFB": "ACC",
    "WF_CFB": "ACC", "UNC_CFB": "ACC"
}

def buildRecords():
    records = {}
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CFB"
            record_summary = None
            if "records" in competitor and len(competitor["records"]) > 0:
                record_summary = competitor["records"][0].get("summary", "0-0")
            records[team_abbr] = record_summary or "0-0"
    return records

def buildSeeds():
  # gets the seeding or playoff rank if present
    seeds = {}
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CFB"
            seed = competitor.get("seed", {}).get("rank")
            if not seed and "curatedRank" in competitor:
                seed = competitor["curatedRank"].get("current")
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
    rating = 0
    if team_conference.get(home) == team_conference.get(away):
        rating += 5
    for team, rivals in rivalries.items():
        for rival, r in rivals:
            if (team == home and rival == away) or (team == away and rival == home):
                rating += r
    return rating
  
def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)

def qualityOfPlay(home, away):
    seeds = buildSeeds()
    records = buildRecords()
    homeRank = seeds.get(home, 0)
    awayRank = seeds.get(home, 0)
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    combinedWins = float(homeRecord[0] + awayRecord[0])
    gamesPlayed = float(homeRecord[0] + homeRecord[1] + awayRecord[0] + awayRecord[1])
    if gamesPlayed == 0:
        return 0
    quality = round(((combinedWins / gamesPlayed)*10), 3)
    if homeRank != 0:
      quality += (25 - homeRank) // 2
    if awayRank != 0:
      quality += (25 - awayRank) // 2
    return quality

def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home, "0-0").split("-")
    awayRecord = records.get(away, "0-0").split("-")
    winDiff = abs(int(homeRecord[0]) - int(awayRecord[0]))
    return max(1, 10 - winDiff)

def gameImportance(home, away):
    records = buildRecords()
    seeds = buildSeeds()
    importance = 2
    homeRecord = records.get(home, "0-0").split("-")
    awayRecord = records.get(away, "0-0").split("-")
    homeGamesPlayed = sum(map(int, homeRecord))
    awayGamesPlayed = sum(map(int, awayRecord))
    home_seed = seeds.get(home)
    away_seed = seeds.get(away)
    gamesLeft = season_length - max(homeGamesPlayed, awayGamesPlayed)
    
    if gamesLeft <= 10:
        importance += 1
    if gamesLeft <= 6:
        importance += 1
    if gamesLeft <= 3:
        importance += 1
    if home_seed and home_seed <= 10:
        importance += 2
    if away_seed and away_seed <= 10:
        importance += 2
    return importance
