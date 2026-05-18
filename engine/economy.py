from config import BASE_GDP_GROWTH, BASE_POP_GROWTH

# Dân số ước tính ban đầu (triệu) cho 1836
INITIAL_POP = {
    "GBR":25.0,"FRA":33.0,"RUS":60.0,"GER":30.0,"AUS":35.0,"PRU":14.0,
    "USA":15.0,"CHI":400.0,"JAP":30.0,"TUR":25.0,"SPA":12.0,"BRZ":7.0,
    "ITA":22.0,"NET":3.0,"MEX":7.0,"PER":9.0,"EGY":4.0,"ETH":5.0,
    "MOR":4.0,"NEP":5.0,"BUR":8.0,"SIA":5.0,"KOR":8.0,"DAI":8.0,
    "HBC":0.1,"CAN":1.5,"ARG":0.8,"GRE":0.8,"SER":1.0,"DEI":30.0,
    "POR":3.5,"BEL":4.0,"SWE":3.5,"NOR":1.5,"DEN":2.0,"POL":8.0,
}

# GDP ước tính ban đầu (triệu £)
INITIAL_GDP = {
    "GBR":800,"FRA":500,"RUS":350,"GER":400,"AUS":300,"PRU":250,
    "USA":300,"CHI":600,"JAP":150,"TUR":200,"SPA":150,"BRZ":80,
    "ITA":200,"NET":120,"MEX":70,"PER":80,"EGY":60,"DEI":100,
    "POR":80,"BEL":90,"SWE":80,"DEN":60,
}


def init_countries(countries_data: dict, countries_full: dict) -> dict:
    """
    Khởi tạo Country objects với dân số và GDP ban đầu.
    countries_data: { TAG: [R,G,B] }
    countries_full: { TAG: {color, type} }
    """
    from models.country import Country
    result = {}
    for tag, color in countries_data.items():
        ctype = countries_full.get(tag, {}).get("type", "recognized")
        c = Country(tag, tuple(int(v) for v in color[:3]), ctype)
        c.population = INITIAL_POP.get(tag, 0.5)
        c.gdp        = float(INITIAL_GDP.get(tag, 20))
        c.treasury   = c.gdp * 0.1
        c.army_size  = max(1, int(c.population * 0.5))
        result[tag]  = c
    return result


def monthly_economy_tick(countries: dict, market, player_tag: str) -> dict:
    """
    Tính toán kinh tế 1 tháng cho tất cả quốc gia.
    Trả về { TAG: { income, expense, delta } } để hiển thị.
    """
    report = {}
    for tag, country in countries.items():
        if country.is_colonizable:
            continue

        # Thu nhập thuế
        tax_income = country.gdp * country.tax_rate / 12

        # Thu nhập thương mại (đơn giản)
        trade_income = country.gdp * 0.02 / 12

        # Chi phí quân sự
        army_expense = country.army_size * 0.005  # £/tháng per 1k quân

        # Chi phí hành chính
        admin_expense = country.population * 0.1 / 12

        income  = tax_income + trade_income
        expense = army_expense + admin_expense
        delta   = income - expense

        country.treasury += delta

        # Tăng trưởng GDP & dân số
        prosperity = min(1.5, max(0.5, country.treasury / max(country.gdp, 1)))
        country.gdp        *= (1 + BASE_GDP_GROWTH * prosperity)
        country.population *= (1 + BASE_POP_GROWTH * prosperity)

        report[tag] = {
            "income":  round(income, 2),
            "expense": round(expense, 2),
            "delta":   round(delta, 2),
            "treasury": round(country.treasury, 1),
        }

    return report