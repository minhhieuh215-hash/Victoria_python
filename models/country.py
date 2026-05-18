from config import START_YEAR, START_MONTH

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

        # Lịch sử
        self.year         = START_YEAR
        self.month        = START_MONTH

    @property
    def is_colonizable(self):
        return self.country_type in ('decentralized', 'unrecognized')

    @property
    def is_great_power(self):
        return self.gdp > 500 and self.population > 10

    def __repr__(self):
        return f"<Country {self.tag} pop={self.population:.1f}M gdp={self.gdp:.0f}>"