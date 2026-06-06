# models/state.py - sửa lại
"""
models/state.py
Gộp từ: state.py + building.py
"""

# ── BUILDING ─────────────────────────────────────────────────────
class Building:
    STATS = {
        # Old structures (for compatibility)
        "farm":              {"production": 8,  "cost": 50,  "upkeep_ratio": 0.02},
        "mine":              {"production": 12, "cost": 100, "upkeep_ratio": 0.02},
        "factory":           {"production": 18, "cost": 200, "upkeep_ratio": 0.02},

        # New structures
        "rye_farm":          {"production": 8,  "cost": 50,  "upkeep_ratio": 0.02},
        "livestock_ranches": {"production": 8,  "cost": 50,  "upkeep_ratio": 0.02},
        "cotton_plantation": {"production": 8,  "cost": 50,  "upkeep_ratio": 0.02},
        "vineyard":          {"production": 10, "cost": 60,  "upkeep_ratio": 0.02},
        "coal_mine":         {"production": 12, "cost": 100, "upkeep_ratio": 0.02},
        "iron_mine":         {"production": 12, "cost": 100, "upkeep_ratio": 0.02},
        "logging_camp":      {"production": 10, "cost": 80,  "upkeep_ratio": 0.02},
        
        "food_industry":     {"production": 18, "cost": 200, "upkeep_ratio": 0.02},
        "textile_mill":      {"production": 18, "cost": 200, "upkeep_ratio": 0.02},
        "steel_mill":        {"production": 24, "cost": 250, "upkeep_ratio": 0.02},
        "arms_industry":     {"production": 20, "cost": 250, "upkeep_ratio": 0.02},
        
        "barracks":          {"production": 0,  "cost": 150, "upkeep_ratio": 0.02},
        "university":        {"production": 0,  "cost": 300, "upkeep_ratio": 0.02},
        "port":              {"production": 0,  "cost": 150, "upkeep_ratio": 0.02},
        "railway":           {"production": 0,  "cost": 200, "upkeep_ratio": 0.02},
        "skyscraper":        {"production": 0,  "cost": 500, "upkeep_ratio": 0.02},
    }

    def __init__(self, name, btype, level=1, state_name=""):
        self.name       = name
        self.type       = btype
        self.level      = level
        self.state_name = state_name
        self.owner_tag  = None

    @property
    def production(self):
        return self.STATS.get(self.type, {}).get("production", 0) * self.level

    @property
    def cost(self):
        return self.STATS.get(self.type, {}).get("cost", 50) * self.level

    @property
    def upkeep(self):
        return self.cost * self.STATS.get(self.type, {}).get("upkeep_ratio", 0.02)

    @property
    def effect(self):
        if self.type == "university": return {"literacy":          0.005 * self.level}
        if self.type == "barracks":   return {"army":              2     * self.level}
        if self.type in ("farm", "rye_farm", "livestock_ranches", "cotton_plantation", "vineyard"):
            return {"population_growth": 0.001 * self.level}
        if self.type == "port":       return {"prestige":          5     * self.level}
        if self.type == "railway":    return {"prestige":          10    * self.level}
        if self.type == "skyscraper": return {"prestige":          20    * self.level}
        return {}


# ── STATE ─────────────────────────────────────────────────────────
class State:
    def __init__(self, name):
        self.name       = name
        self.provinces  = []       # list of Province objects
        self.owner      = None     # TAG của quốc gia sở hữu
        self.buildings  = []       # list of Building objects
        self.population = 0
        self.gdp        = 0

    def add_building(self, btype, level=1) -> Building:
        """Thêm công trình vào bang hoặc tăng cấp độ nếu đã tồn tại"""
        existing = self.get_buildings_by_type(btype)
        if existing:
            existing[0].level += level
            return existing[0]
        else:
            b = Building(f"{btype}_{self.name}", btype, level, self.name)
            b.owner_tag = self.owner
            self.buildings.append(b)
            return b

    def remove_building(self, index):
        """Xóa công trình"""
        if 0 <= index < len(self.buildings):
            return self.buildings.pop(index)
        return None

    def total_production(self) -> float:
        return sum(b.production for b in self.buildings)

    def total_upkeep(self) -> float:
        return sum(b.upkeep for b in self.buildings)
    
    def get_buildings_by_type(self, btype):
        """Lọc công trình theo loại"""
        return [b for b in self.buildings if b.type == btype]
    
    @property
    def display_name(self):
        """Tên hiển thị đẹp"""
        return self.name.replace("STATE_", "").replace("_", " ").title()