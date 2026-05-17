class War:
    def __init__(self, attackers, defenders, wargoal):
        self.attackers = attackers
        self.defenders = defenders
        self.wargoal = wargoal
        self.war_exhaustion = {}    # Mệt mỏi chiến tranh mỗi bên
        self.battles = []