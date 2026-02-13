import requests

url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

season_length = 30 
march_madness = False
conference_tournament = False

# Marketability scores for major college basketball programs (1-10 scale)
team_marketability = {
    "UK_CBB": 9, "UNC_CBB": 9, "DUKE_CBB": 10, "KU_CBB": 9, "UCLA_CBB": 8,
    "UL_CBB": 8, "IU_CBB": 8, "MICH_CBB": 8, "MSU_CBB": 8, "OSU_CBB": 7,
    "GONZ_CBB": 8, "VILL_CBB": 8, "CUSE_CBB": 7, "CONN_CBB": 8, "MD_CBB": 7,
    "WIS_CBB": 7, "ARIZ_CBB": 8, "PITT_CBB": 7, "MARQ_CBB": 7, "WAKE_CBB": 6,
    "GTWN_CBB": 7, "TEX_CBB": 7, "TENN_CBB": 7, "ARK_CBB": 7, "FLA_CBB": 7,
    "AUB_CBB": 7, "ALA_CBB": 7, "MISS_CBB": 6, "LSU_CBB": 7, "UGA_CBB": 6,
    "SCAR_CBB": 6, "VANDY_CBB": 6, "MIST_CBB": 6, "TAMU_CBB": 6, "OKST_CBB": 6,
    "ISU_CBB": 7, "TTU_CBB": 6, "TCU_CBB": 6, "BAY_CBB": 6, "WVU_CBB": 7,
    "CREI_CBB": 7, "PROV_CBB": 7, "MARQ_CBB": 7, "HALL_CBB": 6, "STJ_CBB": 7,
    "GTOWN_CBB": 7, "XAV_CBB": 7, "BUTL_CBB": 7, "ORE_CBB": 6, "USC_CBB": 7,
    "STAN_CBB": 7, "CAL_CBB": 6, "WASH_CBB": 6, "WSU_CBB": 5, 
    "ORST_CBB": 5, "COLO_CBB": 6, "UTAH_CBB": 6, "ASU_CBB": 6, "SDSU_CBB": 7,
    "NEV_CBB": 6, "UNLV_CBB": 7, "BSU_CBB": 6, "NMSU_CBB": 5, "WYO_CBB": 5,
    "SJSU_CBB": 5, "FRES_CBB": 5, "CSU_CBB": 5, "USU_CBB": 5, "AF_CBB": 5,
    "ND_CBB": 8, "MIA_CBB": 7, "VT_CBB": 6, "BC_CBB": 6,
    "NCST_CBB": 6, "CLEM_CBB": 7, "FSU_CBB": 7, "LOU_CBB": 7, "UVA_CBB": 7,
    "PURD_CBB": 8, "ILL_CBB": 7, "IOWA_CBB": 7, "NEB_CBB": 6, "MINN_CBB": 6,
    "NW_CBB": 6, "PSU_CBB": 6, "RUTG_CBB": 6, "HOU_CBB": 8, "CINC_CBB": 7,
    "UCF_CBB": 6, "MEM_CBB": 7, "SMU_CBB": 6, "TUL_CBB": 5, "TULN_CBB": 5,
    "ECU_CBB": 5, "USF_CBB": 5, "TEM_CBB": 6, "WICH_CBB": 7, "VCU_CBB": 7,
    "RICH_CBB": 6, "DAVN_CBB": 6, "SLU_CBB": 7, "SBU_CBB": 6, "URI_CBB": 6,
    "MASS_CBB": 6, "FORD_CBB": 6, "GMU_CBB": 6, "SJU_CBB": 6, "LAS_CBB": 6,
    "STBV_CBB": 6, "DUQE_CBB": 5, "LOY_CBB": 5, "SDAK_CBB": 6, "NDAK_CBB": 6,
    "DRAKE_CBB": 6, "UNI_CBB": 6, "BYU_CBB": 7, "UNM_CBB": 6, "PUR_CBB": 8,
    "VAN_CBB": 6, "MIZ_CBB": 6, "GW_CBB": 5, "M-OH_CBB": 5
}

# Major college basketball rivalries with intensity scores
rivalries = [
    ("DUKE_CBB", "UNC_CBB", 12),  
    ("UK_CBB", "UL_CBB", 10),  
    ("KU_CBB", "MU_CBB", 9),  
    ("UK_CBB", "IU_CBB", 8),
    ("NEB_CBB", "MICH_CBB", 8),
    ("DUKE_CBB", "NCST_CBB", 7), 
    ("UNC_CBB", "NCST_CBB", 7),  
    ("OSU_CBB", "MICH_CBB", 9),  
    ("UCLA_CBB", "USC_CBB", 9),  
    ("GONZ_CBB", "SMC_CBB", 7),  
    ("VILL_CBB", "GTOWN_CBB", 8),  
    ("CUSE_CBB", "GTOWN_CBB", 9),  
    ("IU_CBB", "PUR_CBB", 10), 
    ("ARIZ_CBB", "ASU_CBB", 8),  
    ("TEX_CBB", "OKLA_CBB", 7),  
    ("KU_CBB", "KSU_CBB", 8),   
    ("MICH_CBB", "MSU_CBB", 9),  
    ("MD_CBB", "DUKE_CBB", 6),  
    ("UVA_CBB", "VT_CBB", 7),  
    ("PITT_CBB", "WVU_CBB", 8),  
    ("XAV_CBB", "CINC_CBB", 9),  
    ("FLA_CBB", "UGA_CBB", 6),  
    ("ARK_CBB", "LSU_CBB", 6),  
    ("CONN_CBB", "CUSE_CBB", 7),  
    ("MARQ_CBB", "WIS_CBB", 7),  
    ("STAN_CBB", "CAL_CBB", 7),  
    ("WAKE_CBB", "DUKE_CBB", 6),  
    ("UNC_CBB", "UVA_CBB", 6),  
    ("ND_CBB", "MARQ_CBB", 6), 
]

def getData():
    """Fetch fresh data from ESPN API"""
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error fetching CBB data: {e}")
        return {"events": []}

def buildRecords():
    """Build records dictionary from API data"""
    data = getData()
    records = {}
    
    if not data.get("events"):
        print("WARNING: No events found in CBB API data")
        return records
    
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CBB"
            # handle different record formats
            if competitor.get("records") and len(competitor["records"]) > 0:
                record = competitor["records"][0].get("summary", "0-0")
            else:
                record = "0-0"
            records[team_abbr] = record
    return records

def buildSeeds():
    """Build seeds/rankings dictionary from API data"""
    data = getData()
    seeds = {}
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CBB"
            rank = competitor.get("curatedRank", {}).get("current", None)
            seeds[team_abbr] = int(rank) if rank and rank != 99 else None
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
    """Returns 0-12 for rivalry intensity"""
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            return r
    return 0

def marketability(home, away):
    base = team_marketability.get(home, 5) + team_marketability.get(away, 5)
    return base

def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home, "0-0")
    awayRecord = records.get(away, "0-0")
    
    try:
        home_wins = int(homeRecord.split("-")[0])
        away_wins = int(awayRecord.split("-")[0])
        winDiff = abs(home_wins - away_wins)
    except (ValueError, IndexError) as e:
        print(f"Error parsing records for {home} ({homeRecord}) vs {away} ({awayRecord}): {e}")
        winDiff = 0
    
    compRank = (20 - winDiff) / 3
    return compRank

def qualityOfPlay(home, away):
    records = buildRecords()
    homeRecord = records.get(home, "0-0")
    awayRecord = records.get(away, "0-0")
    
    try:
        home_parts = homeRecord.split("-")
        away_parts = awayRecord.split("-")
        
        home_wins = int(home_parts[0])
        home_losses = int(home_parts[1])
        away_wins = int(away_parts[0])
        away_losses = int(away_parts[1])
        
        combinedWins = float(home_wins + away_wins)
        gamesPlayed = float(home_wins + home_losses + away_wins + away_losses)
        
        if gamesPlayed == 0:
            print(f"DEBUG qualityOfPlay: gamesPlayed = 0")
            return 0
        
        quality = round(((combinedWins / gamesPlayed) * 10), 3)
        print(f"DEBUG qualityOfPlay result: {quality}")
        return quality
    except (ValueError, IndexError) as e:
        print(f"Error calculating quality for {home} ({homeRecord}) vs {away} ({awayRecord}): {e}")
        return 0

def gameImportance(home, away):
    importance = 0
    seeds = buildSeeds()
    records = buildRecords()
    
    homeRecord = records.get(home, "0-0")
    awayRecord = records.get(away, "0-0")
    
    try:
        home_parts = homeRecord.split("-")
        away_parts = awayRecord.split("-")
        homeGamesPlayed = int(home_parts[0]) + int(home_parts[1])
        awayGamesPlayed = int(away_parts[0]) + int(away_parts[1])
    except (ValueError, IndexError):
        homeGamesPlayed = 0
        awayGamesPlayed = 0
    
    home_rank = seeds.get(home)
    away_rank = seeds.get(away)
    gamesLeft = season_length - max(homeGamesPlayed, awayGamesPlayed)
    
    if march_madness:
        importance += 15 
        if home_rank is not None and away_rank is not None:
            if home_rank <= 8 and away_rank <= 8: 
                importance += 7
            elif home_rank <= 16 and away_rank <= 16:  
                importance += 4
    elif conference_tournament:
        importance += 8
        if home_rank is not None and away_rank is not None:
            if home_rank <= 10 and away_rank <= 10:
                importance += 5
    else:
        if gamesLeft <= 20:
            importance += 1
        if gamesLeft <= 10:
            importance += 1
        if gamesLeft <= 5:
            importance += 2
        if home_rank is not None and home_rank <= 25:
            importance += 2
        if away_rank is not None and away_rank <= 25:
            importance += 2
        if home_rank is not None and away_rank is not None:
            if home_rank <= 10 and away_rank <= 10:
                importance += 4
            if home_rank <= 5 and away_rank <= 5:
                importance += 10
    
    return importance
