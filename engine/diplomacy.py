"""
engine/diplomacy.py
Gộp từ: diplomacy.py + war.py
"""


# ── WAR ──────────────────────────────────────────────────────────
class War:
    def __init__(self, attackers, defenders, wargoal):
        self.attackers      = set(attackers) if not isinstance(attackers, set) else attackers
        self.defenders      = set(defenders) if not isinstance(defenders, set) else defenders
        self.wargoal        = wargoal
        self.war_exhaustion = {}   # { TAG: float }
        self.battles        = []
        self.war_score      = 0    # + = attacker winning, - = defender winning

    def add_exhaustion(self, tag, amount):
        self.war_exhaustion[tag] = self.war_exhaustion.get(tag, 0) + amount

    def is_over(self):
        return abs(self.war_score) >= 100


# ── ALLIANCES ────────────────────────────────────────────────────
class Alliance:
    def __init__(self, tag1, tag2):
        self.members      = {tag1, tag2}
        self.created_date = None

    def add_member(self, tag):
        self.members.add(tag)


# ── DIPLOMATIC ACTIONS ───────────────────────────────────────────
class DiplomaticAction:

    @staticmethod
    def improve_relations(country, target, amount=5):
        country.relations[target] = min(100, country.relations.get(target, 0) + amount)
        return f"Quan hệ với {target} +{amount}"

    @staticmethod
    def worsen_relations(country, target, amount=5):
        country.relations[target] = max(-100, country.relations.get(target, 0) - amount)
        return f"Quan hệ với {target} -{amount}"

    @staticmethod
    def declare_war(declarer, target):
        if target in declarer.at_war_with:
            return False, "Đã trong tình trạng chiến tranh"
        if declarer.relations.get(target, 0) > -10:
            return False, "Quan hệ còn quá cao (cần < -10)"

        declarer.at_war_with.add(target)
        declarer.relations[target] = max(-100, declarer.relations.get(target, 0) - 50)

        # Gọi đồng minh
        allies_joined = []
        for ally_tag in getattr(declarer, "allies", set()):
            if ally_tag == target or ally_tag in declarer.at_war_with:
                continue
            allies_joined.append(ally_tag)

        msg = f"Tuyên chiến với {target}"
        if allies_joined:
            msg += f" (Đồng minh tham chiến: {', '.join(allies_joined)})"
        return True, msg

    @staticmethod
    def form_alliance(country1, country2):
        if country1.relations.get(country2.tag, 0) < 50:
            return False, "Quan hệ quá thấp (cần 50+)"
        if country2.relations.get(country1.tag, 0) < 50:
            return False, "Quan hệ quá thấp (cần 50+)"
        country1.allies.add(country2.tag)
        country2.allies.add(country1.tag)
        return True, f"Liên minh thành lập: {country1.tag} — {country2.tag}"

    @staticmethod
    def break_alliance(country1, country2):
        country1.allies.discard(country2.tag)
        country2.allies.discard(country1.tag)
        return True, f"Liên minh tan vỡ: {country1.tag} — {country2.tag}"