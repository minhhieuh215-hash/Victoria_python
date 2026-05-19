# models/state.py - sửa lại
"""
models/state.py
Gộp từ: state.py + building.py
"""

# ── BUILDING ─────────────────────────────────────────────────────
class Building:
    STATS = {
        "farm":       {"production": 8,  "cost": 50,  "upkeep_ratio": 0.02},
        "mine":       {"production": 12, "cost": 100, "upkeep_ratio": 0.02},
        "factory":    {"production": 18, "cost": 200, "upkeep_ratio": 0.02},
        "university": {"production": 0,  "cost": 300, "upkeep_ratio": 0.02},
        "barracks":   {"production": 0,  "cost": 150, "upkeep_ratio": 0.02},
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
        if self.type == "farm":       return {"population_growth": 0.001 * self.level}
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
        """Thêm công trình vào bang"""
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