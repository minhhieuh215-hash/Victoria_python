# engine/events.py
"""
Hệ thống sự kiện hoàn chỉnh cho Victoria 3 Simple Engine.
Kết hợp giữa random events và historical events từ file.
"""
import random
import os
import re
from typing import Dict, List, Optional, Any

# ============ PART 1: RANDOM EVENTS ĐƠN GIẢN ============

SIMPLE_EVENTS = [
    {
        "id": "harvest_good",
        "title": "🌾 Mùa màng bội thu",
        "desc": "Nông dân cả nước được mùa lớn, kho lương đầy ắp.",
        "condition": lambda c: c.population > 1,
        "effect": lambda c: setattr(c, "gdp", c.gdp * 1.03),
        "effect_text": "GDP +3%",
        "weight": 10,
        "icon": "event_harvest"
    },
    {
        "id": "harvest_bad",
        "title": "🌧️ Mất mùa nghiêm trọng",
        "desc": "Hạn hán tàn phá mùa màng, dân chúng đói kém.",
        "condition": lambda c: c.population > 1,
        "effect": lambda c: setattr(c, "gdp", c.gdp * 0.97),
        "effect_text": "GDP -3%",
        "weight": 6,
        "icon": "event_famine"
    },
    {
        "id": "gold_rush",
        "title": "⛏️ Phát hiện vàng!",
        "desc": "Thợ đào vàng tìm thấy mỏ vàng lớn ở vùng đất phía Tây.",
        "condition": lambda c: True,
        "effect": lambda c: setattr(c, "treasury", c.treasury + c.gdp * 0.1),
        "effect_text": "Kho bạc +10% GDP",
        "weight": 4,
        "icon": "event_gold"
    },
    {
        "id": "revolt",
        "title": "⚔️ Nổi loạn trong nước",
        "desc": "Một nhóm nổi dậy chiếm giữ tỉnh biên giới phía Nam.",
        "condition": lambda c: c.army_size > 0,
        "effect": lambda c: setattr(c, "prestige", c.prestige - 5),
        "effect_text": "Uy tín -5",
        "weight": 5,
        "icon": "event_revolt"
    },
    {
        "id": "trade_boom",
        "title": "📈 Thương mại phát triển",
        "desc": "Các tuyến thương mại mở rộng, thương nhân ùn ùn kéo đến.",
        "condition": lambda c: c.gdp > 50,
        "effect": lambda c: setattr(c, "treasury", c.treasury + 20),
        "effect_text": "Kho bạc +20£",
        "weight": 8,
        "icon": "event_trade"
    },
    {
        "id": "plague",
        "title": "🦠 Dịch bệnh bùng phát",
        "desc": "Bệnh dịch lan rộng khắp các thành phố lớn.",
        "condition": lambda c: c.population > 5,
        "effect": lambda c: setattr(c, "population", c.population * 0.98),
        "effect_text": "Dân số -2%",
        "weight": 3,
        "icon": "event_plague"
    },
    {
        "id": "great_reform",
        "title": "📜 Cải cách lớn",
        "desc": "Quốc hội thông qua đạo luật cải cách quan trọng, lòng dân phấn khởi.",
        "condition": lambda c: c.treasury > 100,
        "effect": lambda c: (setattr(c, "prestige", c.prestige + 10), 
                            setattr(c, "treasury", c.treasury - 50)),
        "effect_text": "Uy tín +10, Kho bạc -50£",
        "weight": 4,
        "icon": "event_reform"
    },
    {
        "id": "military_parade",
        "title": "🎖️ Cuộc diễu binh hoành tráng",
        "desc": "Quân đội diễu binh qua thủ đô, khí thế hừng hực.",
        "condition": lambda c: c.army_size >= 10,
        "effect": lambda c: setattr(c, "prestige", c.prestige + 5),
        "effect_text": "Uy tín +5",
        "weight": 6,
        "icon": "event_military"
    },
    {
        "id": "industrial_innovation",
        "title": "🏭 Đổi mới công nghiệp",
        "desc": "Một phát minh mới giúp tăng năng suất nhà máy.",
        "condition": lambda c: c.gdp > 100,
        "effect": lambda c: setattr(c, "gdp", c.gdp * 1.05),
        "effect_text": "GDP +5%",
        "weight": 7,
        "icon": "event_industry"
    },
    {
        "id": "diplomatic_victory",
        "title": "🤝 Thắng lợi ngoại giao",
        "desc": "Các nhà ngoại giao của ta đạt được thỏa thuận có lợi.",
        "condition": lambda c: len(c.relations) > 0,
        "effect": lambda c: setattr(c, "prestige", c.prestige + 8),
        "effect_text": "Uy tín +8",
        "weight": 5,
        "icon": "event_diplomacy"
    }
]


# ============ PART 2: HISTORICAL EVENTS (từ file) ============

class HistoricalEvent:
    """Lớp đại diện cho một event lịch sử từ file Victoria 3"""
    
    def __init__(self, event_id: str, event_data: dict):
        self.id = event_id
        self.namespace = event_data.get("namespace", "")
        self.event_type = event_data.get("type", "country_event")
        self.title = event_data.get("title", event_id)
        self.desc = event_data.get("desc", "")
        self.icon = event_data.get("icon", "event_default")
        self.duration = event_data.get("duration", 0)
        self.options = event_data.get("options", [])
        self.trigger = event_data.get("trigger", {})
        self.immediate = event_data.get("immediate", {})
    
    def is_triggered(self, country, game_state) -> bool:
        """Kiểm tra event có được trigger không"""
        trigger = self.trigger
        
        # Kiểm tra năm
        if "year" in trigger:
            if game_state.current_date.year != trigger["year"]:
                return False
        
        if "year_min" in trigger:
            if game_state.current_date.year < trigger["year_min"]:
                return False
        if "year_max" in trigger:
            if game_state.current_date.year > trigger["year_max"]:
                return False
        
        # Kiểm tra quốc gia
        if "country" in trigger:
            if trigger["country"] != country.tag:
                return False
        
        # Kiểm tra technology
        if "technology" in trigger:
            techs = getattr(country, "technologies", [])
            if trigger["technology"] not in techs:
                return False
        
        # Kiểm tra state
        if "has_state" in trigger:
            state_name = trigger["has_state"]
            if state_name not in game_state.states:
                return False
            if game_state.states[state_name].owner != country.tag:
                return False
        
        # Kiểm tra relations
        if "relations_with" in trigger:
            rel_value = country.relations.get(trigger["relations_with"], 0)
            min_rel = trigger.get("relations_min", 0)
            if rel_value < min_rel:
                return False
        
        return True
    
    def execute_option(self, country, game_state, option_index: int = 0):
        """Thực hiện một option của event"""
        if option_index >= len(self.options):
            return "Không có option nào được chọn"
        
        option = self.options[option_index]
        effect = option.get("effect", {})
        
        return apply_event_effect(effect, country, game_state)
    
    def to_dict(self):
        """Chuyển event thành dict để hiển thị trong UI"""
        effect_text = "Tiếp tục"
        if self.options and len(self.options) > 0:
            effect_text = self.options[0].get("name", "Tiếp tục")

        return {
            "id": self.id,
            "title": self.title,
            "desc": self.desc,
            "effect_text": effect_text,
            "icon": self.icon,
            "options": self.options
        }


# ============ PART 3: EVENT LOADER TỪ FILE ============

def load_historical_events(event_folder: str = "data/events") -> Dict[str, HistoricalEvent]:
    """Đọc tất cả event từ các file .txt trong thư mục"""
    all_events = {}
    
    if not os.path.exists(event_folder):
        print(f"⚠️ Không tìm thấy thư mục events: {event_folder}")
        return all_events
    
    for root, dirs, files in os.walk(event_folder):
        for filename in files:
            if not filename.endswith(".txt"):
                continue
            
            filepath = os.path.join(root, filename)
            events_in_file = parse_event_file(filepath)
            
            for event_id, event_data in events_in_file.items():
                all_events[event_id] = HistoricalEvent(event_id, event_data)
    
    print(f"✅ Đã load {len(all_events)} historical events")
    return all_events


def parse_event_file(filepath: str) -> Dict[str, dict]:
    """Parse một file event .txt"""
    events = {}
    
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            content = f.read()
    
    # Tìm namespace
    namespace_match = re.search(r'namespace\s*=\s*(\w+)', content)
    if not namespace_match:
        return events
    
    namespace = namespace_match.group(1)
    
    # Tìm tất cả event trong file
    pattern = rf'{namespace}\.(\d+)\s*=\s*{{'
    matches = list(re.finditer(pattern, content))
    if not matches:
        return events
    
    for match in matches:
        event_id = f"{namespace}.{match.group(1)}"
        event_start = match.end()
        
        # Tìm dấu } đóng tương ứng
        brace_count = 0
        event_end = None
        for i in range(event_start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                if brace_count == 0:
                    event_end = i + 1
                    break
                brace_count -= 1
        
        if event_end is None:
            continue
        
        event_body = content[event_start:event_end - 1]
        
        # Parse event body
        event_data = parse_event_body(event_body, namespace)
        if event_data:
            events[event_id] = event_data
    
    return events


def ensure_historical_events_loaded(game_state):
    if getattr(game_state, '_historical_events_loaded', False):
        return
    print("  -> Loading historical events...")
    game_state.historical_events = load_historical_events("data/events")
    game_state._historical_events_loaded = True


def parse_event_body(body: str, namespace: str) -> Optional[dict]:
    """Parse nội dung event body"""
    event_data = {
        "namespace": namespace,
        "type": "country_event",
        "title": "",
        "desc": "",
        "icon": "",
        "options": [],
        "trigger": {},
        "immediate": {}
    }
    
    # Lấy type
    type_match = re.search(r'type\s*=\s*(\w+)', body)
    if type_match:
        event_data["type"] = type_match.group(1)
    
    # Lấy title và desc
    title_match = re.search(r'title\s*=\s*(\w+(?:\.\w+)?)', body)
    if title_match:
        event_data["title"] = title_match.group(1)
    
    desc_match = re.search(r'desc\s*=\s*(\w+(?:\.\w+)?)', body)
    if desc_match:
        event_data["desc"] = desc_match.group(1)
    
    # Lấy icon
    icon_match = re.search(r'icon\s*=\s*"?([^"\n]+)"?', body)
    if icon_match:
        event_data["icon"] = icon_match.group(1).strip()
    
    # Parse trigger
    trigger_match = re.search(r'trigger\s*=\s*{([^}]+)}', body, re.DOTALL)
    if trigger_match:
        event_data["trigger"] = parse_trigger_block(trigger_match.group(1))
    
    # Parse các option
    option_matches = re.finditer(r'option\s*=\s*{', body)
    for opt_match in option_matches:
        opt_start = opt_match.end()
        opt_body = extract_block_at_position(body, opt_start - 1)
        if opt_body:
            opt_data = parse_option_block(opt_body)
            event_data["options"].append(opt_data)
    
    return event_data


def parse_trigger_block(trigger_str: str) -> dict:
    """Parse trigger block"""
    trigger = {}
    
    # Year check
    year_match = re.search(r'year\s*=\s*(\d+)', trigger_str)
    if year_match:
        trigger["year"] = int(year_match.group(1))
    
    # Year range
    year_range = re.search(r'year\s*=\s*{\s*min\s*=\s*(\d+)\s*max\s*=\s*(\d+)}', trigger_str)
    if year_range:
        trigger["year_min"] = int(year_range.group(1))
        trigger["year_max"] = int(year_range.group(2))
    
    # Country
    country_match = re.search(r'c:([A-Z]{3})\s*=', trigger_str)
    if country_match:
        trigger["country"] = country_match.group(1)
    
    # Has state
    state_match = re.search(r'has_state\s*=\s*(\w+)', trigger_str)
    if state_match:
        trigger["has_state"] = state_match.group(1)
    
    # Relations
    rel_match = re.search(r'relations\s*=\s*{\s*country\s*=\s*(\w+)\s*value\s*>\s*(\d+)', trigger_str)
    if rel_match:
        trigger["relations_with"] = rel_match.group(1)
        trigger["relations_min"] = int(rel_match.group(2))
    
    return trigger


def parse_option_block(option_str: str) -> dict:
    """Parse option block"""
    option = {
        "name": "Tiếp tục",
        "default_option": False,
        "ai_chance": 100,
        "effect": {}
    }
    
    # Lấy name
    name_match = re.search(r'name\s*=\s*(\w+(?:\.\w+)?)', option_str)
    if name_match:
        option["name"] = name_match.group(1)
    
    # Check default_option
    if re.search(r'default_option\s*=\s*yes', option_str):
        option["default_option"] = True
    
    # Parse effect
    effect_match = re.search(r'effect\s*=\s*{([^}]+)}', option_str, re.DOTALL)
    if effect_match:
        option["effect"] = parse_effect_block(effect_match.group(1))
    
    # Parse ai_chance
    ai_match = re.search(r'ai_chance\s*=\s*{\s*base\s*=\s*(\d+)', option_str)
    if ai_match:
        option["ai_chance"] = int(ai_match.group(1))
    
    return option


def parse_effect_block(effect_str: str) -> dict:
    """Parse effect block"""
    effect = {}
    
    # add_prestige
    prestige_match = re.search(r'add_prestige\s*=\s*([+-]?\d+)', effect_str)
    if prestige_match:
        effect["prestige"] = int(prestige_match.group(1))
    
    # treasury
    treasury_match = re.search(r'treasury\s*=\s*([+-]?\d+)', effect_str)
    if treasury_match:
        effect["treasury"] = int(treasury_match.group(1))
    
    # population
    pop_match = re.search(r'population\s*=\s*([+-]?\d+)', effect_str)
    if pop_match:
        effect["population"] = int(pop_match.group(1))
    
    # tax_rate
    tax_match = re.search(r'tax_rate\s*=\s*([+-]?[\d.]+)', effect_str)
    if tax_match:
        effect["tax_rate"] = float(tax_match.group(1))
    
    # change_relations
    rel_match = re.search(r'change_relations\s*=\s*{\s*country\s*=\s*(\w+)\s*value\s*=\s*([+-]?\d+)', effect_str)
    if rel_match:
        effect["change_relations"] = {
            "country": rel_match.group(1),
            "value": int(rel_match.group(2))
        }
    
    return effect


def extract_block_at_position(content: str, pos: int) -> Optional[str]:
    """Extract block bắt đầu từ vị trí pos (đã biết là {)"""
    if pos >= len(content) or content[pos] != '{':
        return None
    
    brace_count = 1
    for i in range(pos + 1, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[pos + 1:i]
    return None


# ============ PART 4: HÀM ÁP DỤNG EFFECT ============

def apply_event_effect(effect: dict, country, game_state) -> str:
    """Áp dụng effect của event, trả về mô tả kết quả"""
    results = []
    
    if "prestige" in effect:
        country.prestige += effect["prestige"]
        results.append(f"Uy tín {effect['prestige']:+d}")
    
    if "treasury" in effect:
        country.treasury += effect["treasury"]
        results.append(f"Kho bạc {effect['treasury']:+d}£")
    
    if "population" in effect:
        country.population *= (1 + effect["population"] / 100)
        results.append(f"Dân số {effect['population']:+d}%")
    
    if "tax_rate" in effect:
        old_rate = country.tax_rate
        country.tax_rate = max(0.05, min(0.4, country.tax_rate + effect["tax_rate"]))
        results.append(f"Thuế suất {country.tax_rate - old_rate:+.0%}")
    
    if "government" in effect:
        country.government = effect["government"]
        results.append(f"Chính phủ -> {effect['government']}")
    
    if "change_relations" in effect:
        rel = effect["change_relations"]
        target = rel["country"]
        value = rel["value"]
        if target in game_state.countries:
            country.relations[target] = country.relations.get(target, 0) + value
            country.relations[target] = max(-100, min(100, country.relations[target]))
            results.append(f"Quan hệ với {target} {value:+d}")
    
    if "gdp_multiplier" in effect:
        country.gdp *= effect["gdp_multiplier"]
        results.append(f"GDP {(effect['gdp_multiplier']-1)*100:+.0f}%")
    
    return ", ".join(results) if results else "Không có thay đổi"


# ============ PART 5: HÀM KIỂM TRA VÀ TRIGGER EVENT ============

def check_events(country, game_state) -> Optional[dict]:
    """
    Kiểm tra và trả về event ngẫu nhiên hoặc lịch sử.
    Xác suất 20% mỗi tháng.
    """
    # 80% chance không có event
    if random.random() > 0.2:
        return None
    
    # 30% chance là historical event (nếu có), 70% là simple event
    use_historical = False
    if hasattr(game_state, 'historical_events') and game_state.historical_events:
        if random.random() < 0.3:
            use_historical = True
    
    if use_historical:
        # Load historical events on demand the first time they are needed.
        ensure_historical_events_loaded(game_state)
        for event in game_state.historical_events.values():
            if event.is_triggered(country, game_state):
                return event.to_dict()
    
    # Fallback to simple events
    eligible = [e for e in SIMPLE_EVENTS if e["condition"](country)]
    if not eligible:
        return None
    
    weights = [e["weight"] for e in eligible]
    event = random.choices(eligible, weights=weights, k=1)[0]
    
    return {
        "id": event["id"],
        "title": event["title"],
        "desc": event["desc"],
        "effect_text": event["effect_text"],
        "icon": event.get("icon", "event_default")
    }


def apply_event(event: dict, country) -> str:
    """Áp dụng sự kiện vào quốc gia, trả về mô tả effect"""
    # Tìm event trong SIMPLE_EVENTS
    for e in SIMPLE_EVENTS:
        if e["id"] == event["id"]:
            try:
                e["effect"](country)
            except Exception as ex:
                print(f"Error applying event effect: {ex}")
            return e["effect_text"]
    
    return event.get("effect_text", "Sự kiện đã được áp dụng")


# ============ PART 6: KHỞI TẠO HỆ THỐNG EVENTS ============

def init_events(game_state):
    """Khởi tạo hệ thống events cho game_state"""
    game_state.historical_events = {}
    game_state._historical_events_loaded = False
    game_state.simple_events = SIMPLE_EVENTS
    print(f"🎲 Hệ thống events sẵn sàng: {len(SIMPLE_EVENTS)} random events, historical events sẽ load khi cần")
    return game_state