# models/market.py
class Market:
    BASE_PRICES = {
        "grain": 2.0, "fish": 2.5, "meat": 4.0, "fruit": 3.0,
        "wood": 3.0, "coal": 4.0, "iron": 8.0, "steel": 15.0,
        "fabric": 5.0, "clothes": 12.0, "glass": 10.0,
        "tools": 12.0, "paper": 6.0, "furniture": 10.0,
        "opium": 20.0, "tea": 8.0, "coffee": 7.0, "sugar": 6.0,
        "oil": 15.0, "rubber": 18.0, "electricity": 25.0
    }
    
    def __init__(self):
        self.prices = dict(self.BASE_PRICES)
        self.supply = {g: 1000.0 for g in self.BASE_PRICES}
        self.demand = {g: 1000.0 for g in self.BASE_PRICES}
        self.convoys = {}  # {tag: available_convoys}
    
    def get_price(self, good: str) -> float:
        return self.prices.get(good, 1.0)
    
    def update_monthly(self, countries):
        """Cập nhật giá dựa trên cung cầu toàn cầu"""
        # Reset supply/demand
        for good in self.prices:
            self.supply[good] = max(100, self.supply[good] * 0.7)
            self.demand[good] = max(100, self.demand[good] * 0.7)
        
        # Tích lũy từ các quốc gia
        for country in countries.values():
            for good, amount in country.production.items():
                self.supply[good] += amount
            for good, amount in country.consumption.items():
                self.demand[good] += amount
        
        # Cập nhật giá
        for good in self.prices:
            ratio = self.demand[good] / max(self.supply[good], 1)
            target = self.BASE_PRICES[good] * (0.5 + ratio * 0.5)
            target = max(0.2, min(5.0, target))  # Giới hạn 0.2x - 5x
            self.prices[good] = round(self.prices[good] * 0.8 + target * 0.2, 2)
    
    def trade(self, tag, good, amount, is_export):
        """Thực hiện giao dịch"""
        if is_export:
            revenue = self.prices[good] * amount * 0.95  # 5% phí
            self.supply[good] += amount
            return revenue
        else:
            cost = self.prices[good] * amount
            self.demand[good] += amount
            return -cost