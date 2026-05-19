# models/army.py
class Army:
    def __init__(self, owner_tag: str, name: str = "Legion"):
        self.owner = owner_tag
        self.name = name
        self.size = 10  # nghìn quân
        self.morale = 1.0
        self.experience = 0.0
        self.location = None
        self.in_combat = False
        
    @property
    def upkeep(self) -> float:
        from config import ARMY_UPKEEP_PER_1000
        return self.size * ARMY_UPKEEP_PER_1000
    
    @property
    def strength(self) -> float:
        return self.size * self.morale * (1 + self.experience)
    
    def train(self):
        """Huấn luyện tăng kinh nghiệm"""
        self.experience = min(1.0, self.experience + 0.05)
        
    def monthly_tick(self, can_afford: bool):
        if not can_afford:
            self.morale = max(0.1, self.morale - 0.05)
            self.size = max(1, self.size - 0.5)
        else:
            self.morale = min(1.0, self.morale + 0.02)


class General:
    def __init__(self, name, tag, skill=0):
        self.name = name
        self.tag = tag
        self.skill = skill  # 0-10
        self.army = None