fighter_marketability = {
    "JONES_MMA": 10, "MCGREGOR_MMA": 10, "PEREIRA_MMA": 9, "MAKHACHEV_MMA": 9,
    "OMALLEY_MMA": 9, "TOPURIA_MMA": 9, "ADESANYA_MMA": 9, "HOLLOWAY_MMA": 8,
    "OLIVEIRA_MMA": 8, "POIRIER_MMA": 8, "CHIMAEV_MMA": 8, "ASPINALL_MMA": 8,
    "DVALISHVILI_MMA": 7, "DUPLESSIS_MMA": 7, "EDWARDS_MMA": 7, "MUHAMMAD_MMA": 7,
    "WHITTAKER_MMA": 7, "USMAN_MMA": 7, "GAETHJE_MMA": 8, "TSARUKYAN_MMA": 7,
    "FERGUSON_MMA": 7, "VOLKANOVSKI_MMA": 8, "HILL_MMA": 6, "CANNONIER_MMA": 6,
    "ROUNTREE_MMA": 6, "PANTOJA_MMA": 6, "STERLING_MMA": 6, "SANDHAGEN_MMA": 6,
    "BURNS_MMA": 6, "COVINGTON_MMA": 7, "MASVIDAL_MMA": 7, "FIGUEIREDO_MMA": 6,
    "BLACHOWICZ_MMA": 6, "GANE_MMA": 7, "VOLKOV_MMA": 6, "PAVLOVICH_MMA": 6,
    "SHEVCHENKO_MMA": 7, "GRASSO_MMA": 6, "NUNES_MMA": 8, "ZHANG_MMA": 7,
    "NAMAJUNAS_MMA": 6, "JEDRZEJCZYK_MMA": 6,
}

rivalries = [
    ("MCGREGOR_MMA", "POIRIER_MMA", 12),
    ("JONES_MMA", "ASPINALL_MMA", 11),
    ("PEREIRA_MMA", "ADESANYA_MMA", 11),
    ("VOLKANOVSKI_MMA", "TOPURIA_MMA", 10),
    ("MAKHACHEV_MMA", "VOLKANOVSKI_MMA", 10),
    ("DUPLESSIS_MMA", "ADESANYA_MMA", 9),
    ("OMALLEY_MMA", "DVALISHVILI_MMA", 9),
    ("OMALLEY_MMA", "STERLING_MMA", 8),
    ("USMAN_MMA", "EDWARDS_MMA", 9),
    ("EDWARDS_MMA", "MUHAMMAD_MMA", 8),
    ("POIRIER_MMA", "GAETHJE_MMA", 8),
    ("OLIVEIRA_MMA", "POIRIER_MMA", 7),
    ("ADESANYA_MMA", "WHITTAKER_MMA", 8),
    ("SHEVCHENKO_MMA", "GRASSO_MMA", 8),
    ("FIGUEIREDO_MMA", "MORENO_MMA", 9),
    ("COVINGTON_MMA", "USMAN_MMA", 8),
    ("COVINGTON_MMA", "MASVIDAL_MMA", 7),
]

def rivalry(fighter_a, fighter_b):
    for f1, f2, r in rivalries:
        if (f1 == fighter_a and f2 == fighter_b) or (f2 == fighter_a and f1 == fighter_b):
            return r
    return 0

def marketability(fighter_a, fighter_b):
    a = fighter_marketability.get(fighter_a, 3)
    b = fighter_marketability.get(fighter_b, 3)
    return a + b

def competitiveness(rank_a=None, rank_b=None):
    if rank_a is None and rank_b is None:
        return 3
    a = rank_a if rank_a is not None else 16
    b = rank_b if rank_b is not None else 16
    rank_diff = abs(a - b)
    both_ranked = rank_a is not None and rank_b is not None
    base = 6 if both_ranked else 3
    return round(max(0, base - (rank_diff * 0.4)), 2)

def qualityOfPlay(rank_a=None, rank_b=None, is_title=False):
    if is_title:
        return 12
    a_score = 0 if rank_a is None else max(0, 10 - rank_a * 0.5)
    b_score = 0 if rank_b is None else max(0, 10 - rank_b * 0.5)
    return round(a_score + b_score, 2)

def eventImportance(is_title=False, is_ppv=False, is_main_card=True, num_ranked_fighters=0):
    importance = 0
    if is_title:
        importance += 12
    if is_ppv:
        importance += 6
    elif is_main_card:
        importance += 2
    if num_ranked_fighters >= 10:
        importance += 4
    elif num_ranked_fighters >= 6:
        importance += 2
    elif num_ranked_fighters >= 3:
        importance += 1
    return importance

def calculate_score(fighter_a, fighter_b, rank_a=None, rank_b=None,
                    is_title=False, is_ppv=False, is_main_card=True,
                    num_ranked_fighters=0):
    r = rivalry(fighter_a, fighter_b)
    m = marketability(fighter_a, fighter_b)
    c = competitiveness(rank_a, rank_b)
    q = qualityOfPlay(rank_a, rank_b, is_title)
    e = eventImportance(is_title, is_ppv, is_main_card, num_ranked_fighters)
    return round(r + m + c + q + e, 2)

def calculate_score_breakdown(fighter_a, fighter_b, rank_a=None, rank_b=None,
                              is_title=False, is_ppv=False, is_main_card=True,
                              num_ranked_fighters=0):
    return {
        "rivalry":         round(rivalry(fighter_a, fighter_b), 2),
        "marketability":   round(marketability(fighter_a, fighter_b), 2),
        "competitiveness": round(competitiveness(rank_a, rank_b), 2),
        "quality":         round(qualityOfPlay(rank_a, rank_b, is_title), 2),
        "importance":      round(eventImportance(is_title, is_ppv, is_main_card, num_ranked_fighters), 2),
    }
