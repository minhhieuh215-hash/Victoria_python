"""
engine/politics.py
Gộp từ: politics.py + law.py + interest_groups.py
"""
import random


# ── GOVERNMENT TYPES ────────────────────────────────────────────
GOVERNMENT_TYPES = {
    "default":           {"tax_bonus": 0.00, "pop_happiness": 0.0,  "prestige_gain": 0.1},
    "absolute_monarchy": {"tax_bonus": 0.05, "pop_happiness":-0.1,  "prestige_gain": 0.2},
    "republic":          {"tax_bonus":-0.02, "pop_happiness": 0.2,  "prestige_gain": 0.1},
    "dictatorship":      {"tax_bonus": 0.08, "pop_happiness":-0.2,  "prestige_gain": 0.0},
    "theocracy":         {"tax_bonus": 0.03, "pop_happiness": 0.1,  "prestige_gain": 0.3},
    "communist":         {"tax_bonus": 0.10, "pop_happiness":-0.3,  "prestige_gain":-0.1},
    "fascist":           {"tax_bonus": 0.07, "pop_happiness":-0.25, "prestige_gain": 0.0},
}


# ── INTEREST GROUPS ─────────────────────────────────────────────
class InterestGroup:
    def __init__(self, name, ideology, pops_supported):
        self.name          = name
        self.ideology      = ideology
        self.pops_supported = pops_supported
        self.clout         = 0.0   # 0–100
        self.leader        = None
        self.opinion       = 0     # -100–100
        self.in_government = False

    def calculate_clout(self, country):
        total = 0
        for pop in country.pops:
            if pop.type in self.pops_supported:
                total += pop.size * getattr(pop, "political_power", 1)
        self.clout = min(100, total / max(country.population, 1) * 100)
        return self.clout


INTEREST_GROUPS = {
    "landowners":     InterestGroup("Địa chủ",   "conservative", ["aristocrats"]),
    "industrialists": InterestGroup("Tư bản",    "liberal",      ["capitalists"]),
    "military":       InterestGroup("Quân đội",  "jingoist",     ["officers"]),
    "clergy":         InterestGroup("Giáo hội",  "moralist",     ["clergymen"]),
    "intelligentsia": InterestGroup("Trí thức",  "progressive",  ["bureaucrats", "clerks"]),
    "peasants":       InterestGroup("Nông dân",  "agrarian",     ["farmers"]),
    "workers":        InterestGroup("Công nhân", "socialist",    ["laborers", "machinists"]),
}


# ── LAWS ─────────────────────────────────────────────────────────
class Law:
    def __init__(self, name, category, enactment_chance):
        self.name             = name
        self.category         = category   # "governance" | "economy" | "human_rights"
        self.enactment_chance = enactment_chance
        self.supporters       = []         # Interest group names
        self.opposers         = []


LAWS = {
    "free_press":        Law("Tự do báo chí",    "human_rights", 0.4),
    "land_reform":       Law("Cải cách ruộng đất","economy",      0.3),
    "universal_suffrage":Law("Phổ thông đầu phiếu","governance",  0.25),
    "conscription":      Law("Nghĩa vụ quân sự", "governance",   0.5),
    "free_trade":        Law("Thương mại tự do",  "economy",      0.45),
}


# ── LOGIC FUNCTIONS ──────────────────────────────────────────────
def apply_government_bonus(country, player_tag=None, game_state=None):
    gov = GOVERNMENT_TYPES.get(country.government, GOVERNMENT_TYPES["default"])
    country.tax_rate = max(0.05, min(0.40, 0.15 + gov["tax_bonus"]))
    
    prestige_gain = gov["prestige_gain"]
    difficulty = getattr(game_state, 'difficulty', 'normal')
    if player_tag and country.tag == player_tag:
        if difficulty == 'easy':
            prestige_gain *= 1.2
        elif difficulty == 'hard':
            prestige_gain *= 0.8
    else:
        if difficulty == 'hard':
            prestige_gain *= 1.2
            
    country.prestige += prestige_gain


def monthly_politics_tick(countries: dict, player_tag: str, game_state=None):
    for tag, country in countries.items():
        if country.is_colonizable:
            continue
        apply_government_bonus(country, player_tag, game_state)
        # AI tự tăng quân nếu đủ giàu
        if tag != player_tag and country.treasury > 200 and random.random() < 0.05:
            country.army_size += 5
            country.treasury  -= 50


def get_relations_color(value: int) -> tuple:
    if value >= 50:  return (80, 200, 120)
    if value >= 0:   return (180, 180, 100)
    if value >= -50: return (200, 120, 60)
    return (200, 60, 60)