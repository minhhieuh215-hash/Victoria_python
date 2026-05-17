class GameState:
    def __init__(self):
        self.current_date = Date(1836, 1, 1)   # class Date riêng hoặc dùng datetime
        self.player_country = None
        self.countries = {}          # tag -> Country
        self.states = {}             # state_id -> State
        self.provinces = {}          # province_id -> Province
        
        self.market = Market()
        self.game_speed = 1          # không dùng nữa, thay bằng turn
        self.is_paused = False
        self.current_turn = 0