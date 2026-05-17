# engine/game_state.py
from datetime import date

class GameDate:
    def __init__(self, year=1836, month=1, day=1):
        self.year = year
        self.month = month
        self.day = day

    def advance_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    def __str__(self):
        return f"{self.year}-{self.month:02d}"


class GameState:
    def __init__(self, provinces, states, countries_data, player_tag="DAI"):
        self.current_date = GameDate(1836, 1)
        self.turn = 0
        self.player_tag = player_tag
        
        self.provinces = provinces          # dict: province_id -> Province
        self.states = states                # list hoặc dict State
        self.countries_data = countries_data
        
        self.countries = {}                 # tag -> Country object (sau này)
        
        print(f"🎮 GameState khởi tạo thành công!")
        print(f"   Người chơi: {player_tag} | Bắt đầu: {self.current_date}")

    def next_turn(self):
        self.turn += 1
        self.current_date.advance_month()
        
        print(f"\n=== TURN {self.turn} | {self.current_date} ===")
        
        # TODO: Các update sau
        self.update_economy()
        self.update_pops()
        self.update_buildings()
        
        print(f"Turn hoàn thành → {self.current_date}")

    def update_economy(self):
        pass  # TODO

    def update_pops(self):
        pass

    def update_buildings(self):
        pass

    def get_player_provinces(self):
        """Lấy tất cả province thuộc người chơi"""
        return [p for p in self.provinces.values() if getattr(p, 'owner', None) == self.player_tag]