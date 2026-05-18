"""
Đọc dữ liệu tài nguyên thực từ file state_regions của Victoria 3.
Tạo file MỚI - không đụng vào code cũ.

Dùng:
    from engine.state_resource_loader import load_state_resources, get_state_for_province
    
    resources = load_state_resources()   # { "STATE_ENGLAND": StateInfo }
    state = get_state_for_province(resources, (R,G,B))
"""
import re, os, glob
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List

# Map tên resource sang tên hiển thị + icon
RESOURCE_DISPLAY = {
    "bg_iron_mining":    ("Quặng sắt",   "⚙️"),
    "bg_coal_mining":    ("Than đá",      "🪨"),
    "bg_lead_mining":    ("Chì",          "🔩"),
    "bg_gold_mining":    ("Vàng",         "🥇"),
    "bg_copper_mining":  ("Đồng",         "🔶"),
    "bg_sulfur_mining":  ("Lưu huỳnh",   "🟡"),
    "bg_logging":        ("Gỗ",           "🌲"),
    "bg_fishing":        ("Thủy sản",     "🐟"),
    "bg_rye_farms":      ("Lúa mạch",     "🌾"),
    "bg_wheat_farms":    ("Lúa mì",       "🌾"),
    "bg_rice_farms":     ("Gạo",          "🍚"),
    "bg_livestock_ranches": ("Chăn nuôi", "🐄"),
    "bg_cotton_plantations": ("Bông",     "🌿"),
    "bg_silk_plantations": ("Tơ lụa",    "🧵"),
    "bg_coffee_plantations": ("Cà phê",  "☕"),
    "bg_tea_plantations": ("Trà",         "🍵"),
    "bg_tobacco_plantations": ("Thuốc lá","🍂"),
    "bg_opium_plantations": ("Thuốc phiện","💊"),
    "bg_sugar_plantations": ("Mía",       "🍬"),
    "bg_rubber_plantations": ("Cao su",   "🟤"),
    "bg_dye_plantations": ("Thuốc nhuộm", "🎨"),
    "bg_oil_extraction": ("Dầu mỏ",       "🛢️"),
}


@dataclass
class StateInfo:
    name: str                               # vd "STATE_ENGLAND"
    state_id: int = 0
    province_colors: Set[tuple] = field(default_factory=set)  # set of (R,G,B)
    capped_resources: Dict[str, int] = field(default_factory=dict)
    arable_resources: List[str] = field(default_factory=list)
    arable_land: int = 0
    traits: List[str] = field(default_factory=list)
    has_port: bool = False
    has_city: bool = False

    def top_resources(self, n=4):
        """Trả về n tài nguyên lớn nhất."""
        return sorted(self.capped_resources.items(), key=lambda x: x[1], reverse=True)[:n]

    def display_name(self):
        """Chuyển STATE_HOME_COUNTIES → Home Counties."""
        return self.name.replace("STATE_", "").replace("_", " ").title()


def _parse_hex_color(hex_str: str) -> Optional[tuple]:
    """Parse 'x0974E5' → (9, 116, 229)"""
    h = hex_str.strip().lstrip('"').rstrip('"').lstrip('x').lstrip('X')
    if len(h) == 6:
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            pass
    return None


def _extract_block(content: str, start: int) -> str:
    """Extract nội dung trong { } bắt đầu từ vị trí start."""
    depth, j = 0, start
    while j < len(content):
        if content[j] == '{':
            depth += 1
        elif content[j] == '}':
            depth -= 1
            if depth == 0:
                return content[start+1:j]
        j += 1
    return ""


def load_state_resources(state_regions_folder: Optional[str] = None) -> Dict[str, StateInfo]:
    """
    Parse tất cả file state_regions → dict { state_name: StateInfo }
    Tự động tìm đường dẫn nếu không truyền vào.
    """
    if state_regions_folder is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_regions_folder = os.path.join(base, "data", "map_data", "state_regions")

    if not os.path.exists(state_regions_folder):
        print(f"⚠️ Không tìm thấy thư mục state_regions: {state_regions_folder}")
        return {}

    all_states: Dict[str, StateInfo] = {}

    for filepath in glob.glob(os.path.join(state_regions_folder, "*.txt")):
        content = open(filepath, encoding="utf-8-sig", errors="replace").read()
        content = re.sub(r'#.*', '', content)  # bỏ comment

        for m in re.finditer(r'(STATE_\w+)\s*=\s*\{', content):
            state_name = m.group(1)
            body = _extract_block(content, m.end() - 1)
            info = StateInfo(name=state_name)

            # ID
            id_m = re.search(r'\bid\s*=\s*(\d+)', body)
            if id_m:
                info.state_id = int(id_m.group(1))

            # Provinces (hex colors)
            prov_m = re.search(r'provinces\s*=\s*\{([^}]+)\}', body)
            if prov_m:
                for token in prov_m.group(1).split():
                    c = _parse_hex_color(token)
                    if c:
                        info.province_colors.add(c)

            # Arable land
            al_m = re.search(r'arable_land\s*=\s*(\d+)', body)
            if al_m:
                info.arable_land = int(al_m.group(1))

            # Arable resources
            ar_m = re.search(r'arable_resources\s*=\s*\{([^}]+)\}', body)
            if ar_m:
                info.arable_resources = ar_m.group(1).split()

            # Capped resources
            cr_m = re.search(r'capped_resources\s*=\s*\{([^}]+)\}', body, re.DOTALL)
            if cr_m:
                for rm in re.finditer(r'(\w+)\s*=\s*(\d+)', cr_m.group(1)):
                    info.capped_resources[rm.group(1)] = int(rm.group(2))

            # Traits
            tr_m = re.search(r'traits\s*=\s*\{([^}]+)\}', body)
            if tr_m:
                info.traits = [t.strip('"') for t in tr_m.group(1).split()]

            # Port / city
            info.has_port = bool(re.search(r'\bport\s*=', body))
            info.has_city = bool(re.search(r'\bcity\s*=', body))

            all_states[state_name] = info

    print(f"-> State resources: {len(all_states)} bang")
    return all_states


# Cache toàn cục để không parse lại
_color_to_state_cache: Dict[tuple, StateInfo] = {}
_cache_built = False

def build_color_cache(state_resources: Dict[str, StateInfo]):
    """Xây dựng index màu → StateInfo để tra cứu O(1)."""
    global _color_to_state_cache, _cache_built
    _color_to_state_cache.clear()
    for state in state_resources.values():
        for color in state.province_colors:
            _color_to_state_cache[color] = state
    _cache_built = True
    print(f"-> Color cache: {len(_color_to_state_cache)} province colors đã index")


def get_state_for_province(color: tuple,
                            state_resources: Optional[Dict[str, StateInfo]] = None) -> Optional[StateInfo]:
    """
    Tra cứu StateInfo từ màu province (R,G,B).
    Gọi build_color_cache() trước lần đầu nếu muốn nhanh.
    """
    global _cache_built
    if _cache_built:
        return _color_to_state_cache.get(color)
    if state_resources:
        for state in state_resources.values():
            if color in state.province_colors:
                return state
    return None


def format_resources(state: StateInfo) -> list:
    """
    Trả về list string để hiển thị trong sidebar.
    Ví dụ: ["⚙️ Quặng sắt: 36", "🪨 Than đá: 20"]
    """
    lines = []
    for res_key, amount in state.top_resources(5):
        name, icon = RESOURCE_DISPLAY.get(res_key, (res_key, "▪"))
        lines.append(f"{icon} {name}: {amount}")
    if state.arable_land > 0:
        lines.append(f"🌾 Đất canh tác: {state.arable_land}")
    if state.has_port:
        lines.append("⚓ Có cảng biển")
    return lines