# engine/military.py
class Army:
    def __init__(self, owner, location):
        self.owner = owner
        self.battalions = []        # Các đơn vị
        self.location = location    # Province hiện tại
        self.organization = 1.0     # Tổ chức (0-1)
        self.morale = 1.0           # Tinh thần
        
class Battalion:
    def __init__(self, type, technology):
        self.type = type            # infantry, cavalry, artillery
        self.strength = 1000        # Số quân
        self.technology = technology