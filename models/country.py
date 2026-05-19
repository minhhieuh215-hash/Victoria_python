from config import START_YEAR, START_MONTH
from models.market import Market


class Country:
    def __init__(self, tag: str, color: tuple, country_type: str = "recognized"):
        self.tag          = tag
        self.color        = color           # (R, G, B)
        self.country_type = country_type    # recognized / colonial / decentralized / unrecognized
        self.government   = "default"       # chế độ chính phủ

        # Kinh tế
        self.gdp          = 0.0    # triệu £
        self.treasury     = 100.0  # tiền mặt
        self.tax_rate     = 0.15

        # Dân số (triệu)
        self.population   = 0.0

        # Quân sự
        self.army_size    = 0      # nghìn quân
        self.prestige     = 0.0

        # Ngoại giao
        self.relations    = {}     # { TAG: int(-100..100) }
        self.at_war_with  = set()
        self.allies       = set()  # Thêm allies

        # Lịch sử
        self.year         = START_YEAR
        self.month        = START_MONTH

        # Buildings - LƯU Ý: sẽ được quản lý qua states, không phải ở đây
        # Nên để trống hoặc xóa
        
        # Military
        self.armies = []  # List of Army objects
        
        # Research
        self.technologies = []
        self.research_points = 0
        self.literacy = 0.2  # 0-1

        self.pops = []  # List of Pop objects
        self.cultures = {}  # {culture: percentage}

        # Economy
        self.production = {g: 0 for g in Market.BASE_PRICES}
        self.consumption = {g: 0 for g in Market.BASE_PRICES}
        self.infrastructure = 1.0
        
        # Politics
        self.interest_groups = []  # Active interest groups
        self.laws = {}  # {law_name: enacted}
        
        # Military
        self.conscription = 0.0
        self.war_exhaustion = 0.0

    @property
    def is_colonizable(self):
        return self.country_type in ('decentralized', 'unrecognized')

    @property
    def is_great_power(self):
        return self.gdp > 500 and self.population > 10

    def __repr__(self):
        return f"<Country {self.tag} pop={self.population:.1f}M gdp={self.gdp:.0f}>"
    
    # ✅ SỬA: Xóa hoặc comment phần này vì states được quản lý ở GameState
    # Không có self.states trong Country object
    """
    def get_all_buildings(self):
        all_buildings = []
        for state in self.states.values():
            all_buildings.extend(state.buildings)
        return all_buildings

    def get_total_buildings_count(self):
        return sum(len(s.buildings) for s in self.states.values())
    """
    
    # ✅ THAY THẾ BẰNG: Nếu cần, truyền states từ bên ngoài vào
    def get_buildings_from_states(self, states_dict):
        """Lấy tất cả công trình từ các bang của quốc gia"""
        all_buildings = []
        for state in states_dict.values():
            if state.owner == self.tag:
                all_buildings.extend(state.buildings)
        return all_buildings
    
    def get_total_upkeep_from_states(self, states_dict):
        """Tính tổng chi phí duy trì từ các bang"""
        total = 0
        for state in states_dict.values():
            if state.owner == self.tag:
                total += sum(b.upkeep for b in state.buildings)
        return total
    
    def monthly_production_from_states(self, states_dict):
        """Tính sản lượng từ các buildings trong bang"""
        self.production = {g: 0 for g in Market.BASE_PRICES}
        for state in states_dict.values():
            if state.owner == self.tag:
                for building in state.buildings:
                    if building.type == "farm":
                        self.production["grain"] += building.production
                        self.production["fruit"] += building.production * 0.2
                    elif building.type == "mine":
                        self.production["coal"] += building.production
                        self.production["iron"] += building.production * 0.5
                    elif building.type == "factory":
                        self.production["fabric"] += building.production
                        self.production["clothes"] += building.production * 0.3
    
    def update_pops_monthly(self):
        """Cập nhật POPs hàng tháng"""
        literacy_bonus = 0.01 if "education" in self.technologies else 0
        prosperity = self.treasury / max(self.gdp, 1)
        
        for pop in self.pops:
            pop.monthly_update(prosperity, literacy_bonus)