class Pop:
    """
    Đại diện cho một nhóm dân số trong 1 tỉnh.
    Victoria 3 có: aristocrats, burghers, clergymen, farmers,
                   laborers, machinists, officers, slaves, ...
    Simplified: chỉ dùng 3 loại chính.
    """
    TYPES = ("farmers", "laborers", "burghers")

    def __init__(self, pop_type: str, size: int, province_id: int):
        self.type        = pop_type     # farmers / laborers / burghers
        self.size        = size         # số người
        self.province_id = province_id
        self.literacy    = 0.1          # 0.0 – 1.0
        self.militancy   = 0.0          # 0.0 – 10.0  (cao → nổi loạn)
        self.consciousness = 0.0        # 0.0 – 10.0

    def monthly_tick(self, prosperity: float = 1.0):
        """Tăng trưởng dân số mỗi tháng."""
        growth = self.size * 0.001 * prosperity
        self.size = int(self.size + growth)
        # Nếu kinh tế kém → militancy tăng
        if prosperity < 0.8:
            self.militancy = min(10.0, self.militancy + 0.05)
        else:
            self.militancy = max(0.0, self.militancy - 0.02)

    def __repr__(self):
        return f"<Pop {self.type} size={self.size:,} mil={self.militancy:.1f}>"