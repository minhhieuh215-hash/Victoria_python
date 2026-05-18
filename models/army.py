class Army:
    def __init__(self, owner_tag: str, size: int = 10):
        self.owner    = owner_tag
        self.size     = size        # nghìn quân
        self.morale   = 1.0         # 0.0 – 1.0
        self.location = None        # TAG tỉnh đang đứng
        self.in_combat = False

    @property
    def upkeep(self) -> float:
        """Chi phí duy trì mỗi tháng (£)."""
        from config import ARMY_UPKEEP_PER_1000
        return self.size * ARMY_UPKEEP_PER_1000

    @property
    def strength(self) -> float:
        """Sức mạnh chiến đấu thực tế."""
        return self.size * self.morale

    def monthly_tick(self, can_afford: bool):
        if not can_afford:
            self.morale = max(0.1, self.morale - 0.05)
        else:
            self.morale = min(1.0, self.morale + 0.02)

    def __repr__(self):
        return f"<Army {self.owner} {self.size}k morale={self.morale:.2f}>"