def rivalry(home, away):
    if (home, away) in rivalries or (away, home) in rivalries
        return 5
    else return 0

def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)
    
def competitiveness(home, away):
    homeRecord = records.get(home).split("-")
    awayRecord = records.get(away).split("-")
    

def gameImportance(home, away):
