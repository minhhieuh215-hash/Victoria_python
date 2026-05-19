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
    
    # Bonus từ literacy (giáo dục)
    literacy_bonus = 1 + (country.literacy * 0.5)
    
    # Bonus từ công nghệ
    tech_bonus = 1 + (len(country.technologies) * 0.05)
    
    return (base_gdp + industrial_gdp) * literacy_bonus * tech_bonus


def calculate_tax_income(country):
    """Tính thu thuế hàng tháng"""
    # Thuế dựa trên GDP và thuế suất
    tax_from_gdp = country.gdp * country.tax_rate * 0.1
    
    # Thuế từ dân số giàu
    pop_tax = 0
    if hasattr(country, 'pops'):
        for pop in country.pops:
            if pop.type in ['aristocrats', 'capitalists']:
                pop_tax += pop.size * country.tax_rate * 0.5
    
    return tax_from_gdp + pop_tax


def calculate_expenses(country, game_state=None):
    """Tính chi tiêu hàng tháng"""
    # Chi phí quân đội
    army_cost = country.army_size * 5
    
    # Chi phí hành chính (dựa trên số bang)
    admin_cost = len(country.states) * 2 if hasattr(country, 'states') else 10
    
    # Chi phí duy trì công trình
    building_cost = 0
    if hasattr(country, 'states'):
        for state in country.states.values():
            building_cost += sum(b.upkeep for b in state.buildings)
    
    # Chi phí giáo dục (dựa trên literacy)
    education_cost = country.literacy * 20
    
    return army_cost + admin_cost + building_cost + education_cost


def update_population_growth(country):
    """Cập nhật tăng trưởng dân số"""
    # Tăng trưởng cơ bản
    growth_rate = BASE_POP_GROWTH
    
    # Bonus từ lương thực
    if hasattr(country, 'production') and country.production.get('grain', 0) > 0:
        growth_rate += 0.0005
    
    # Bonus từ y tế (nếu có công nghệ)
    if 'medicine' in country.technologies:
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


def monthly_economy_tick(countries, market, player_tag=None):
    """
    Xử lý kinh tế hàng tháng cho tất cả các nước
    
    Returns:
        dict: Báo cáo kinh tế cho từng quốc gia
    """
    reports = {}
    
    for tag, country in countries.items():
        # 1. Cập nhật GDP
        old_gdp = country.gdp
        country.gdp = calculate_country_gdp(country)
        
        # 2. Tính thu nhập và chi phí
        income = calculate_tax_income(country)
        expense = calculate_expenses(country)
        net_change = income - expense
        
        # 3. Cập nhật ngân khố
        country.treasury += net_change
        
        # 4. Cập nhật tăng trưởng dân số
        update_population_growth(country)
        
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
                    if building.type == "farm":
                        country.production['grain'] = country.production.get('grain', 0) + building.production
                        country.production['fruit'] = country.production.get('fruit', 0) + building.production * 0.2
                    elif building.type == "mine":
                        country.production['coal'] = country.production.get('coal', 0) + building.production
                        country.production['iron'] = country.production.get('iron', 0) + building.production * 0.5
                    elif building.type == "factory":
                        country.production['fabric'] = country.production.get('fabric', 0) + building.production
                        country.production['clothes'] = country.production.get('clothes', 0) + building.production * 0.3
                    elif building.type == "university":
                        # Đại học tăng literacy
                        country.literacy = min(0.95, country.literacy + 0.001)
                    elif building.type == "barracks":
                        # Doanh trại tăng quân đội
                        country.army_size += 1
    
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
    
    countries = {}
    
    for tag, color in countries_data.items():
        # Lấy thông tin loại quốc gia
        info = countries_full.get(tag, {})
        country_type = info.get("type", "recognized")
        
        # Tạo country object
        country = Country(tag, color, country_type)
        
        # Set giá trị mặc định
        country.population = 1.0  # 1 triệu dân mặc định
        country.gdp = 50.0  # 50 triệu GDP mặc định
        country.treasury = 100.0
        country.army_size = 10  # 10k quân mặc định
        country.literacy = 0.3  # 30% mù chữ
        
        # Thêm vào dict
        countries[tag] = country
    
    return countries