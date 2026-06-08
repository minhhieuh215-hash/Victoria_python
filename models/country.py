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
        self.allies       = set()
        self.trade_agreements      = set()
        self.non_aggression_pacts  = set()
        self.defense_pacts         = set()
        self.expelled_diplomats    = set()
        self.guarantees            = set()
        self.power_bloc            = set()
        self.subjects              = set()
        self.leads_bloc            = False

        # Lịch sử
        self.year         = START_YEAR
        self.month        = START_MONTH

        self.states       = {}   # { state_name: State }
        
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

        # National Projects
        self.active_project = None
        self.project_progress = 0
        self.project_time_needed = 0
        self.completed_projects = []

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
                    # Backward compatibility for old types
                    if building.type == "farm" or building.type == "rye_farm":
                        self.production["grain"] += building.production
                        self.production["fruit"] += building.production * 0.2
                    elif building.type == "livestock_ranches":
                        self.production["grain"] += building.production * 0.5
                        self.production["fruit"] += building.production * 0.5
                    elif building.type == "cotton_plantation":
                        self.production["fabric"] += building.production
                    elif building.type == "vineyard":
                        self.production["fruit"] += building.production * 1.5
                    elif building.type == "mine" or building.type == "coal_mine":
                        self.production["coal"] += building.production
                    elif building.type == "iron_mine":
                        self.production["iron"] += building.production
                    elif building.type == "logging_camp":
                        self.production["fabric"] += building.production * 0.5
                    elif building.type == "factory" or building.type == "food_industry":
                        self.production["grain"] += building.production * 0.5
                        self.production["fruit"] += building.production * 0.5
                    elif building.type == "textile_mill":
                        self.production["clothes"] += building.production * 0.8
                        self.production["fabric"] += building.production * 0.2
                    elif building.type == "steel_mill":
                        self.production["iron"] += building.production * 0.4
                        self.production["coal"] += building.production * 0.2
                    elif building.type == "arms_industry":
                        self.production["clothes"] += building.production * 0.3
    
    def update_pops_monthly(self):
        """Cập nhật POPs hàng tháng"""
        literacy_bonus = 0.01 if "education" in self.technologies else 0
        prosperity = self.treasury / max(self.gdp, 1)
        
        for pop in self.pops:
            pop.monthly_update(prosperity, literacy_bonus)