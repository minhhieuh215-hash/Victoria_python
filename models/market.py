class Market:
    """Thị trường toàn cầu đơn giản hóa."""

    BASE_PRICES = {
        "grain":    2.0,
        "fabric":   5.0,
        "iron":     8.0,
        "coal":     4.0,
        "lumber":   3.0,
        "opium":   20.0,
        "cotton":   6.0,
        "rubber":  15.0,
    }

    def __init__(self):
        self.prices  = dict(self.BASE_PRICES)
        self.supply  = {g: 1000.0 for g in self.BASE_PRICES}
        self.demand  = {g: 1000.0 for g in self.BASE_PRICES}

    def get_price(self, good: str) -> float:
        return self.prices.get(good, 1.0)

    def monthly_tick(self):
        """Điều chỉnh giá theo cung/cầu."""
        for good in self.prices:
            ratio = self.demand[good] / max(self.supply[good], 1)
            # Giá dao động ±10% quanh giá cơ bản
            target = self.BASE_PRICES[good] * ratio
            self.prices[good] = round(
                self.prices[good] * 0.9 + target * 0.1, 2)

    def buy(self, good: str, amount: float) -> float:
        """Mua hàng, trả về chi phí thực tế."""
        self.demand[good] = self.demand[good] * 0.99 + amount
        return self.get_price(good) * amount

    def sell(self, good: str, amount: float) -> float:
        """Bán hàng, trả về doanh thu."""
        self.supply[good] = self.supply[good] * 0.99 + amount
        return self.get_price(good) * amount * 0.9   # phí thị trường 10%

    def __repr__(self):
        return f"<Market grain={self.prices['grain']:.2f} iron={self.prices['iron']:.2f}>"