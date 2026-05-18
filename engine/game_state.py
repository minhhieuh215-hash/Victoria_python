"""Trạng thái trung tâm của toàn bộ game."""
from config import START_YEAR, START_MONTH

class GameDate:
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    MONTH_FULL  = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    def __init__(self, year=START_YEAR, month=START_MONTH):
        self.year  = year
        self.month = month

    def advance(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    @property
    def short(self):
        return f"{self.MONTH_NAMES[self.month-1]} {self.year}"

    @property
    def full(self):
        return f"{self.MONTH_FULL[self.month-1]} {self.year}"

    def __repr__(self):
        return self.short


class GameState:
    def __init__(self, provinces, states, countries_data,
                 countries_obj=None, market=None):
        self.provinces      = provinces       # { id: Province }
        self.states         = states          # { name: State }
        self.countries_data = countries_data  # { TAG: [R,G,B] }
        self.countries      = countries_obj or {}  # { TAG: Country }
        self.market         = market

        self.current_date   = GameDate()
        self.player_tag     = "GBR"
        self.player_mode    = "default"

        # Log sự kiện gần nhất (hiện trong sidebar)
        self.last_event     = None   # dict hoặc None
        self.economy_report = {}     # { TAG: {income,expense,...} }
        
        # Events system
        self.historical_events = {}
        self.simple_events = []

    @property
    def player_country(self):
        return self.countries.get(self.player_tag)

    def next_turn(self):
        """Tiến 1 tháng: kinh tế → chính trị → sự kiện."""
        from engine.economy  import monthly_economy_tick
        from engine.politics import monthly_politics_tick
        from engine.events   import check_events, apply_event

        self.economy_report = monthly_economy_tick(
            self.countries, self.market, self.player_tag)

        monthly_politics_tick(self.countries, self.player_tag)

        # Kiểm tra sự kiện cho người chơi
        pc = self.player_country
        if pc:
            # ✅ SỬA: Truyền self (game_state) vào, không phải self.current_date
            ev = check_events(pc, self)
            if ev:
                apply_event(ev, pc)
                self.last_event = ev
            else:
                self.last_event = None

        self.current_date.advance()

    def __repr__(self):
        return f"<GameState {self.current_date} player={self.player_tag}>"