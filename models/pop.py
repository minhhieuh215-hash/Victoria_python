# models/pop.py
class Pop:
    TYPES = {
        "aristocrats": {"political_power": 0.4, "base_literacy": 0.8, "icon": "👑"},
        "clergymen": {"political_power": 0.2, "base_literacy": 0.7, "icon": "⛪"},
        "bureaucrats": {"political_power": 0.3, "base_literacy": 0.9, "icon": "📋"},
        "officers": {"political_power": 0.25, "base_literacy": 0.7, "icon": "🎖️"},
        "farmers": {"political_power": 0.05, "base_literacy": 0.2, "icon": "🌾"},
        "laborers": {"political_power": 0.05, "base_literacy": 0.3, "icon": "🔨"},
        "machinists": {"political_power": 0.08, "base_literacy": 0.5, "icon": "⚙️"},
        "clerks": {"political_power": 0.1, "base_literacy": 0.7, "icon": "✍️"},
        "slaves": {"political_power": 0.0, "base_literacy": 0.1, "icon": "⛓️"}
    }
    
    def __init__(self, pop_type: str, size: int, culture: str, religion: str, province_id: int):
        self.type = pop_type
        self.size = size
        self.culture = culture
        self.religion = religion
        self.province_id = province_id
        
        # Stats
        self.literacy = self.TYPES[pop_type]["base_literacy"]
        self.militancy = 0.0  # 0-10
        self.consciousness = 0.0  # 0-10
        self.political_power = self.TYPES[pop_type]["political_power"]
        
        # Needs
        self.needs = {
            "basic_food": 1.0,
            "heating": 0.5,
            "clothing": 0.3,
            "luxury": 0.1
        }
    
    @property
    def icon(self):
        return self.TYPES[self.type]["icon"]
    
    def monthly_update(self, prosperity, literacy_bonus=0):
        # Tăng trưởng dân số
        growth_rate = 0.001 * prosperity
        self.size = int(self.size * (1 + growth_rate))
        
        # Cập nhật literacy (trường học, công nghệ)
        self.literacy = min(0.95, self.literacy + literacy_bonus)
        
        # Militancy dựa trên prosperity
        if prosperity < 0.5:
            self.militancy = min(10, self.militancy + 0.1)
        elif prosperity > 1.2:
            self.militancy = max(0, self.militancy - 0.05)
        
        # Consciousness dựa trên literacy
        self.consciousness = min(10, self.consciousness + self.literacy * 0.02)
    
    def __repr__(self):
        return f"<Pop {self.icon} {self.type}: {self.size:,} ({self.culture}) mil={self.militancy:.1f}>"