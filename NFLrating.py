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
rivalries = [
    
]

def rivalry(home, away):
    #Could factor in divisions
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            return r
    else: return 0

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)
    
def competitiveness(home, away):
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    winDiff = abs(homeRecord[0] - awayRecord.[0])
    compRank = (10 - winDiff)
    return compRank
    
def gameImportance(home, away):
    importance = 0
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    homeGamesPlayed = homeRecord[0] + homeRecord[1]
    awayGamesPlayed = awayRecord[0] + awayRecord[1]
    home_seed = home["team"].get("seed", {}).get("rank")
    away_seed = away["team"].get("seed", {}).get("rank")
    gamesLeft = 17 - max(homeGamesPlayed, awayGamesPlayed)
    if playoffs:
        # not yet
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
