# engine/economy.py
class Market:
    def __init__(self):
        self.goods_prices = {}      # Giá từng loại hàng hóa
        self.buy_orders = {}        # Lệnh mua
        self.sell_orders = {}       # Lệnh bán
    
    def update_prices(self):
        # Công thức giá của Victoria 3
        for good in self.goods_prices:
            buy = self.buy_orders.get(good, 0)
            sell = self.sell_orders.get(good, 0)
            ratio = buy / max(sell, 1)
            # Giá thay đổi theo cung-cầu
            self.goods_prices[good] = self.base_price[good] * (0.25 + 0.75 * ratio)

class Building:
    def __init__(self, name, type, level, owner):
        self.name = name
        self.type = type            # "rice_farm", "coal_mine", "textile_mill"
        self.level = level          # Cấp độ (càng cao càng sản xuất nhiều)
        self.owner = owner
        self.employees = {}         # {pop_type: số_lượng}
        self.input_goods = {}       # {good: số_lượng}
        self.output_goods = {}      # {good: số_lượng}
        self.production_methods = [] # Phương thức sản xuất