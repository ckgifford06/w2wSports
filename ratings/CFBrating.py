import requests
import team_resolver

URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"

_cached_data = None

def _get_data():
    global _cached_data
    if _cached_data is None:
        _cached_data = requests.get(URL).json()
    return _cached_data

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
    "CLEM_CFB": 9, "FSU_CFB": 9, "MIA_CFB": 8.5, "ND_CFB": 9.5,
    "UNC_CFB": 8, "VT_CFB": 8, "NCST_CFB": 7.5, "LOU_CFB": 7.5,
    "PITT_CFB": 7, "GT_CFB": 7, "WAKE_CFB": 6.5, "BC_CFB": 6.5,
    "DUKE_CFB": 7, "SYR_CFB": 7, "UVA_CFB": 7
}

rivalries = {
    "ALA_CFB": [("AUB_CFB", 10), ("TENN_CFB", 8), ("LSU_CFB", 9)],
    "AUB_CFB": [("UGA_CFB", 8)],
    "LSU_CFB": [("ARK_CFB", 7)],
    "UGA_CFB": [("FLA_CFB", 9), ("GT_CFB", 8)],
    "FLA_CFB": [("FSU_CFB", 9)],
    "MISS_CFB": [("MSST_CFB", 9)],
    "TEX_CFB": [("OK_CFB", 10), ("TEXAM_CFB", 8)],
    "SCAR_CFB": [("CLEM_CFB", 9)],
    "MIZZ_CFB": [("ARK_CFB", 6)],
    "TENN_CFB": [("VANDY_CFB", 5)],
    "ARK_CFB": [("TEXAM_CFB", 7)],
    "MICH_CFB": [("OSU_CFB", 10), ("MSU_CFB", 8)],
    "OSU_CFB": [("PSU_CFB", 7)],
    "MINN_CFB": [("WISC_CFB", 8), ("IOWA_CFB", 7)],
    "IOWA_CFB": [("NEB_CFB", 7)],
    "IND_CFB": [("PUR_CFB", 7)],
    "ILL_CFB": [("NW_CFB", 6)],
    "MD_CFB": [("RUTG_CFB", 5)],
    "KU_CFB": [("KSU_CFB", 7)],
    "BAY_CFB": [("TCU_CFB", 6)],
    "TTU_CFB": [("TCU_CFB", 6)],
    "CLEM_CFB": [("FSU_CFB", 7)],
    "FSU_CFB": [("MIA_CFB", 9)],
    "MIA_CFB": [("VT_CFB", 6)],
    "VT_CFB": [("UVA_CFB", 8)],
    "PITT_CFB": [("WVU_CFB", 8)],
    "UNC_CFB": [("NCST_CFB", 7), ("DUKE_CFB", 6)],
    "ND_CFB": [("USC_CFB", 8)],
    "BC_CFB": [("SYR_CFB", 5)],
    "LOU_CFB": [("UK_CFB", 8)]
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

try:
    team_marketability, _unresolved_m = team_resolver.remap(team_marketability)
    rivalries, _unresolved_r = team_resolver.remap(rivalries)
    team_conference, _unresolved_c = team_resolver.remap(team_conference)
    for _key in sorted(set(_unresolved_m + _unresolved_r + _unresolved_c)):
        _hint = ", ".join(team_resolver.suggest(_key))
        print("UNRESOLVED " + _key + (" -> " + _hint if _hint else ""))
except Exception as _err:
    print("team_resolver unavailable, using raw keys: " + str(_err))

def _canon(team):
    try:
        return team_resolver.resolve(team) or team
    except Exception:
        return team

def buildRecords():
    records = {}
    for event in _get_data().get("events", []):
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
    for event in _get_data().get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CFB"
            seed = competitor.get("seed", {}).get("rank")
            if not seed and "curatedRank" in competitor:
                seed = competitor["curatedRank"].get("current")
            seeds[team_abbr] = int(seed) if seed else None
    return seeds

def calculate_score(home, away):
    home = _canon(home)
    away = _canon(away)
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away)
    q = qualityOfPlay(home, away)
    g = gameImportance(home, away)
    print(f"DEBUG {home} vs {away} → R:{r} M:{m} C:{c} Q:{q} G:{g}")
    return max(0, round((r + m + c + q + g), 2))

def calculate_score_breakdown(home, away):
    home = _canon(home)
    away = _canon(away)
    return {
        "rivalry":        round(rivalry(home, away), 2),
        "marketability":  round(marketability(home, away), 2),
        "competitiveness":round(competitiveness(home, away), 2),
        "quality":        round(qualityOfPlay(home, away), 2),
        "importance":     round(gameImportance(home, away), 2),
    }

def rivalry(home, away):
    rating = 0
    home_conf = team_conference.get(home)
    away_conf = team_conference.get(away)
    if home_conf is not None and home_conf == away_conf:
        rating += 5
    for team, rivals in rivalries.items():
        for rival, r in rivals:
            if (team == home and rival == away) or (team == away and rival == home):
                rating += r
    return rating

def marketability(home, away):
    return team_marketability.get(home, 2) + team_marketability.get(away, 2)

def qualityOfPlay(home, away):
    seeds = buildSeeds()
    records = buildRecords()
    homeRank = seeds.get(home, 0)
    awayRank = seeds.get(away, 0)
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    combinedWins = float(homeRecord[0] + awayRecord[0])
    gamesPlayed = float(homeRecord[0] + homeRecord[1] + awayRecord[0] + awayRecord[1])
    quality = 0.0
    if gamesPlayed > 0:
        quality = round(((combinedWins / gamesPlayed) * 9), 3)
    if homeRank and homeRank <= 25:
        quality += (25 - homeRank) // 2
    if awayRank and awayRank <= 25:
        quality += (25 - awayRank) // 2
    return quality

def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home, "0-0").split("-")
    awayRecord = records.get(away, "0-0").split("-")
    winDiff = abs(int(homeRecord[0]) - int(awayRecord[0]))
    comp = max(1, 10 - winDiff)
    return round(comp * 0.7, 2)

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
    if playoffs:
        importance += 5
    return importance
