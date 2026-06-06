# This assumes the Province class is in models/province.py
# Update the owner attribute type annotation:

class Province:
    def __init__(self, province_id: int, color: tuple):
        self.id = province_id
        self.color = color
        self.is_sea: bool = False
        self.is_lake: bool = False
        self.owner: str | None = None
        self.population = 0
        
        # Seeded random terrain to keep it consistent
        import random
        rng = random.Random(province_id)
        roll = rng.random()
        if roll < 0.2:
            self.terrain = "mountains"
        elif roll < 0.3:
            self.terrain = "desert"
        elif roll < 0.4:
            self.terrain = "hills"
        else:
            self.terrain = "plains"
            
        self.neighbors = []