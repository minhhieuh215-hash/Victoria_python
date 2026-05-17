# This assumes the Province class is in models/province.py
# Update the owner attribute type annotation:

class Province:
    def __init__(self, province_id: int, color: tuple):
        self.id = province_id
        self.color = color
        self.is_sea: bool = False
        self.owner: str | None = None  
        self.owner = None
        self.population = 0
        self.terrain = "plains"

        self.neighbors = []