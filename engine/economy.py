"""
engine/economy.py
Hệ thống kinh tế cho Victoria 3 Simple Engine
"""
from config import BASE_TAX_RATE, BASE_GDP_GROWTH, BASE_POP_GROWTH

def calculate_country_gdp(country):
    """
    Tính GDP của một quốc gia dựa trên:
    - Dân số
    - Sản lượng công nghiệp
    - Trình độ công nghệ
    """
    # GDP cơ bản từ dân số (mỗi người đóng góp ~0.5£)
    base_gdp = country.population * 0.5
    
    # GDP từ sản xuất công nghiệp
    industrial_gdp = 0
    if hasattr(country, 'production'):
        industrial_gdp = sum(country.production.values()) * 2
        
    # Project: Industrial Subsidies (+10% industrial GDP)
    if hasattr(country, 'completed_projects') and "industrial_subsidies" in country.completed_projects:
        industrial_gdp *= 1.10
    
    # Bonus từ literacy (giáo dục)
    literacy_bonus = 1 + (country.literacy * 0.5)
    
    # Bonus từ công nghệ
    tech_bonus = 1 + (len(country.technologies) * 0.05)
    
    # Project multipliers
    project_mult = 1.0
    if hasattr(country, 'completed_projects'):
        if "transcontinental_railway" in country.completed_projects:
            project_mult += 0.15
        if "industrial_subsidies" in country.completed_projects:
            project_mult += 0.08
    
    return (base_gdp + industrial_gdp) * literacy_bonus * tech_bonus * project_mult


def calculate_tax_income(country):
    """Tính thu thuế hàng tháng"""
    # Thuế dựa trên GDP và thuế suất (Tăng hệ số từ 0.1 lên 1.5 để tăng nguồn thu thực tế)
    tax_from_gdp = country.gdp * country.tax_rate * 1.5
    
    # Thuế từ dân số giàu
    pop_tax = 0
    if hasattr(country, 'pops'):
        for pop in country.pops:
            if pop.type in ['aristocrats', 'capitalists']:
                pop_tax += pop.size * country.tax_rate * 0.5
    
    total_tax = tax_from_gdp + pop_tax
    
    # Project bonuses
    if hasattr(country, 'completed_projects'):
        if "agricultural_mechanization" in country.completed_projects:
            total_tax *= 1.05 # +5% tax efficiency
        if "suez_canal" in country.completed_projects:
            total_tax += 300.0 # Suez/Panama Canal toll (+300 gold monthly)
            
    return total_tax


def calculate_expenses(country, game_state=None):
    """Tính chi tiêu hàng tháng"""
    # Chi phí quân đội (Giảm hệ số từ 5 xuống 0.4 để giảm áp lực chi tiêu quân sự quá cao)
    army_cost = country.army_size * 0.4
    
    # Chi phí hành chính (Giảm hệ số từ 2 xuống 0.4)
    admin_cost = len(country.states) * 0.4 if hasattr(country, 'states') else 2.0
    
    # Chi phí duy trì công trình
    building_cost = 0
    if hasattr(country, 'states'):
        for state in country.states.values():
            building_cost += sum(b.upkeep for b in state.buildings)
    
    # Chi phí giáo dục (Giảm hệ số từ 20 xuống 5)
    education_cost = country.literacy * 5
    
    return army_cost + admin_cost + building_cost + education_cost


def update_population_growth(country, game_state=None):
    """Cập nhật tăng trưởng dân số"""
    # Tăng trưởng cơ bản tùy thuộc vào thời đại
    growth_rate = BASE_POP_GROWTH
    if game_state:
        age = getattr(game_state, "current_age", "Age of Industrialisation")
        if age == "Age of Revolution":
            growth_rate = 0.001     # +0.1% mỗi tháng
        elif age == "Age of Industrialisation":
            growth_rate = 0.0015    # +0.15% mỗi tháng
        elif age == "Age of Imperialism":
            growth_rate = 0.002     # +0.2% mỗi tháng

    # Bonus từ lương thực
    if hasattr(country, 'production') and country.production.get('grain', 0) > 0:
        growth_rate += 0.0005
    
    # Bonus từ y tế (nếu có công nghệ)
    if 'medicine' in country.technologies:
        growth_rate += 0.0005
        
    # Project: agricultural mechanization (+0.05% pop growth monthly)
    if hasattr(country, 'completed_projects') and "agricultural_mechanization" in country.completed_projects:
        growth_rate += 0.0005
    
    # Phạt từ chiến tranh
    if country.at_war_with:
        growth_rate -= 0.0002
    
    country.population *= (1 + growth_rate)
    
    # Giới hạn dân số tối thiểu
    country.population = max(0.1, country.population)



def update_market_prices(market, countries):
    """Cập nhật giá thị trường dựa trên cung cầu"""
    if not market:
        return
    
    # Reset supply/demand
    for good in market.prices:
        market.supply[good] = max(100, market.supply[good] * 0.8)
        market.demand[good] = max(100, market.demand[good] * 0.8)
    
    # Tích lũy từ các quốc gia
    for country in countries.values():
        if hasattr(country, 'production'):
            for good, amount in country.production.items():
                market.supply[good] = market.supply.get(good, 0) + amount
        
        if hasattr(country, 'consumption'):
            for good, amount in country.consumption.items():
                market.demand[good] = market.demand.get(good, 0) + amount
    
    # Cập nhật giá theo công thức: giá mới = giá cũ * (cầu/cung)
    for good in market.prices:
        supply = max(market.supply.get(good, 100), 1)
        demand = max(market.demand.get(good, 100), 1)
        ratio = demand / supply
        
        # Giá dao động từ 0.5x đến 2x base price
        base = market.BASE_PRICES.get(good, 10)
        target_price = base * (0.5 + ratio * 0.5)
        target_price = max(base * 0.3, min(base * 3, target_price))
        
        # Điều chỉnh dần (tránh biến động đột ngột)
        market.prices[good] = market.prices[good] * 0.7 + target_price * 0.3


def monthly_economy_tick(countries, market, player_tag=None, game_state=None):
    """
    Xử lý kinh tế hàng tháng cho tất cả các nước
    
    Returns:
        dict: Báo cáo kinh tế cho từng quốc gia
    """
    reports = {}
    
    for tag, country in countries.items():
        from engine.projects import ensure_project_attrs
        ensure_project_attrs(country)
        
        # Project: Education Reform (+0.05% monthly literacy growth)
        if hasattr(country, 'completed_projects') and "education_reform" in country.completed_projects:
            country.literacy = min(0.95, country.literacy + 0.0005)

        # 1. Cập nhật GDP
        old_gdp = country.gdp
        country.gdp = calculate_country_gdp(country)
        
        # 2. Tính thu nhập và chi phí
        income = calculate_tax_income(country)
        
        # Áp dụng bổ trợ độ khó cho thuế suất
        difficulty = getattr(game_state, 'difficulty', 'normal')
        if tag == player_tag:
            if difficulty == 'easy':
                income *= 1.2
            elif difficulty == 'hard':
                income *= 0.8
        else:
            if difficulty == 'hard':
                income *= 1.2
            elif difficulty == 'easy':
                income *= 0.9

        expense = calculate_expenses(country)
        net_change = income - expense
        
        # 3. Cập nhật ngân khố
        country.treasury += net_change
        
        # 4. Cập nhật tăng trưởng dân số
        update_population_growth(country, game_state)
        
        # 5. Tự động điều chỉnh thuế suất AI (nếu là AI và treasury thấp)
        if tag != player_tag and country.treasury < 50 and country.tax_rate < 0.25:
            country.tax_rate = min(0.3, country.tax_rate + 0.01)
        elif tag != player_tag and country.treasury > 500 and country.tax_rate > 0.1:
            country.tax_rate = max(0.05, country.tax_rate - 0.005)
        
        # 6. Lưu báo cáo
        reports[tag] = {
            "income": income,
            "expense": expense,
            "delta": net_change,
            "old_gdp": old_gdp,
            "new_gdp": country.gdp
        }
        
        # 7. Cập nhật production từ buildings nếu có
        if hasattr(country, 'states'):
            country.production = {}
            for state in country.states.values():
                for building in state.buildings:
                    if building.type == "farm" or building.type == "rye_farm":
                        country.production['grain'] = country.production.get('grain', 0) + building.production
                        country.production['fruit'] = country.production.get('fruit', 0) + building.production * 0.2
                    elif building.type == "livestock_ranches":
                        country.production['grain'] = country.production.get('grain', 0) + building.production * 0.5
                        country.production['fruit'] = country.production.get('fruit', 0) + building.production * 0.5
                    elif building.type == "cotton_plantation":
                        country.production['fabric'] = country.production.get('fabric', 0) + building.production
                    elif building.type == "vineyard":
                        country.production['fruit'] = country.production.get('fruit', 0) + building.production * 1.5
                    elif building.type == "mine" or building.type == "coal_mine":
                        country.production['coal'] = country.production.get('coal', 0) + building.production
                    elif building.type == "iron_mine":
                        country.production['iron'] = country.production.get('iron', 0) + building.production
                    elif building.type == "logging_camp":
                        country.production['fabric'] = country.production.get('fabric', 0) + building.production * 0.5
                    elif building.type == "factory" or building.type == "food_industry":
                        country.production['grain'] = country.production.get('grain', 0) + building.production * 0.5
                        country.production['fruit'] = country.production.get('fruit', 0) + building.production * 0.5
                    elif building.type == "textile_mill":
                        country.production['clothes'] = country.production.get('clothes', 0) + building.production * 0.8
                        country.production['fabric'] = country.production.get('fabric', 0) + building.production * 0.2
                    elif building.type == "steel_mill":
                        country.production['iron'] = country.production.get('iron', 0) + building.production * 0.4
                        country.production['coal'] = country.production.get('coal', 0) + building.production * 0.2
                    elif building.type == "arms_industry":
                        country.production['clothes'] = country.production.get('clothes', 0) + building.production * 0.3
                    elif building.type == "university":
                        country.literacy = min(0.95, country.literacy + 0.001 * building.level)
                    elif building.type == "barracks":
                        country.army_size += 1 * building.level
                    elif building.type == "port":
                        country.prestige += 0.05 * building.level
                    elif building.type == "railway":
                        country.prestige += 0.1 * building.level
                    elif building.type == "skyscraper":
                        country.prestige += 0.2 * building.level
    
    # Cập nhật thị trường toàn cầu
    update_market_prices(market, countries)
    
    return reports


def init_countries(countries_data, countries_full):
    """
    Khởi tạo các đối tượng Country từ dữ liệu màu sắc và loại quốc gia
    
    Args:
        countries_data: dict {TAG: (R,G,B)}
        countries_full: dict {TAG: {"type": "recognized"}}
    
    Returns:
        dict: {TAG: Country}
    """
    from models.country import Country
    import json, os, random
    
    # Tải dữ liệu lịch sử 1836
    hist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "historical_gdp.json")
    historical = {}
    try:
        with open(hist_path, "r", encoding="utf-8") as f:
            historical = json.load(f)
    except:
        pass
    
    countries = {}
    
    for tag, color in countries_data.items():
        # Lấy thông tin loại quốc gia
        info = countries_full.get(tag, {})
        country_type = info.get("type", "recognized")
        
        # Tạo country object
        country = Country(tag, color, country_type)
        
        if tag in historical:
            h = historical[tag]
            country.gdp        = h.get("gdp", 50.0)
            country.population = h.get("population", 2.0)
            country.army_size  = h.get("army_size", 20)
            country.treasury   = h.get("treasury", 100.0)
            country.prestige   = h.get("prestige", 20.0)
            country.literacy   = h.get("literacy", 0.25)
        else:
            # Giá trị mặc định ngẫu nhiên theo loại quốc gia
            rng = random.Random(hash(tag) % (2**31))
            if country_type in ("decentralized", "unrecognized"):
                country.gdp        = rng.uniform(1, 15)
                country.population = rng.uniform(0.2, 5.0)
                country.army_size  = rng.randint(2, 20)
                country.treasury   = rng.uniform(5, 50)
                country.prestige   = rng.uniform(0, 10)
                country.literacy   = rng.uniform(0.03, 0.12)
            elif country_type == "colonial":
                country.gdp        = rng.uniform(5, 40)
                country.population = rng.uniform(0.5, 8.0)
                country.army_size  = rng.randint(5, 35)
                country.treasury   = rng.uniform(30, 120)
                country.prestige   = rng.uniform(5, 20)
                country.literacy   = rng.uniform(0.08, 0.25)
            else:  # recognized
                country.gdp        = rng.uniform(10, 80)
                country.population = rng.uniform(0.5, 15.0)
                country.army_size  = rng.randint(5, 60)
                country.treasury   = rng.uniform(50, 250)
                country.prestige   = rng.uniform(10, 40)
                country.literacy   = rng.uniform(0.15, 0.50)
        
        countries[tag] = country
    
    return countries