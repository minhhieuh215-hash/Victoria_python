# engine/event_loader.py
import os
import re
import json

def load_all_events(event_folder="data/events"):
    """Đọc tất cả event từ các file .txt trong thư mục và subfolder"""
    all_events = {}
    localization = {}
    
    # Load localization files nếu có
    loc_folder = os.path.join(os.path.dirname(event_folder), "localization")
    if os.path.exists(loc_folder):
        localization = load_localization(loc_folder)
    
    for root, dirs, files in os.walk(event_folder):
        for filename in files:
            if not filename.endswith(".txt"):
                continue
            
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()
            
            # Lấy namespace từ file
            namespace_match = re.search(r'^namespace\s*=\s*(\w+)', content, re.MULTILINE)
            if not namespace_match:
                # Thử tìm kiểu khác: namespace = { ... }
                namespace_match = re.search(r'namespace\s*=\s*{?\s*(\w+)\s*}?', content)
                if not namespace_match:
                    continue
            
            namespace = namespace_match.group(1)
            
            # Tìm tất cả event trong file - dùng regex đệ quy để bắt block lồng nhau
            event_pattern = rf'{namespace}\.(\d+)\s*=\s*{{'
            start_pos = 0
            
            while True:
                match = re.search(event_pattern, content[start_pos:])
                if not match:
                    break
                
                event_id = match.group(1)
                event_start = start_pos + match.start()
                # Tìm dấu } đóng tương ứng (xử lý nested braces)
                brace_count = 0
                event_end = event_start + match.end() - start_pos
                for i in range(event_end, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        if brace_count == 0:
                            event_end = i + 1
                            break
                        brace_count -= 1
                
                event_body = content[event_start + match.end() - start_pos:event_end - 1]
                event_key = f"{namespace}.{event_id}"
                
                parsed = parse_event_body(event_body, namespace, localization)
                if parsed:
                    all_events[event_key] = parsed
                
                start_pos = event_end
        
    print(f"Loaded {len(all_events)} events")
    return all_events, localization


def load_localization(loc_folder):
    """Load các file localization (thường là .yml hoặc .csv)"""
    localization = {}
    
    for filename in os.listdir(loc_folder):
        if filename.endswith(".yml"):
            filepath = os.path.join(loc_folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                
                # Parse YAML đơn giản: key: "value"
                for line in content.split('\n'):
                    line = line.strip()
                    if ':' in line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        localization[key] = value
            except:
                pass
    
    return localization


def get_localized_text(key, localization, default=None):
    """Lấy text đã được localization"""
    if not key:
        return default or ""
    
    # Nếu key có dạng namespace.id (ví dụ: alaska.1.t)
    if key in localization:
        return localization[key]
    
    # Thử tìm trong localization
    for k, v in localization.items():
        if k == key or k.endswith(f".{key}"):
            return v
    
    return default or key


def parse_event_body(body, namespace, localization):
    """Parse nội dung event thành dict"""
    event_data = {
        "id": f"{namespace}.{body[:20]}",
        "namespace": namespace,
        "type": "country_event",
        "title": "",
        "desc": "",
        "icon": "",
        "duration": 0,
        "options": [],
        "trigger": {},
        "immediate": {},
        "weight": 10
    }
    
    # Lấy type
    type_match = re.search(r'type\s*=\s*(\w+)', body)
    if type_match:
        event_data["type"] = type_match.group(1)
    
    # Lấy title
    title_match = re.search(r'title\s*=\s*(\w+)', body)
    if title_match:
        event_data["title_key"] = title_match.group(1)
        event_data["title"] = get_localized_text(title_match.group(1), localization, title_match.group(1))
    
    # Lấy desc
    desc_match = re.search(r'desc\s*=\s*(\w+)', body)
    if desc_match:
        event_data["desc_key"] = desc_match.group(1)
        event_data["desc"] = get_localized_text(desc_match.group(1), localization, desc_match.group(1))
    
    # Lấy icon
    icon_match = re.search(r'icon\s*=\s*"?([^"\n]+)"?', body)
    if icon_match:
        event_data["icon"] = icon_match.group(1).strip()
    
    # Lấy duration (thời gian event tồn tại)
    duration_match = re.search(r'duration\s*=\s*(\d+)', body)
    if duration_match:
        event_data["duration"] = int(duration_match.group(1))
    
    # Parse trigger block (xử lý nested braces)
    trigger_content = extract_block(body, 'trigger')
    if trigger_content:
        event_data["trigger"] = parse_trigger(trigger_content)
    
    # Parse immediate block
    immediate_content = extract_block(body, 'immediate')
    if immediate_content:
        event_data["immediate"] = parse_effect_block(immediate_content)
    
    # Parse các option
    option_matches = re.finditer(r'option\s*=\s*{', body)
    for opt_match in option_matches:
        opt_start = opt_match.end()
        opt_body = extract_block_at_position(body, opt_start - 1)
        if opt_body:
            opt_data = parse_option(opt_body, localization)
            event_data["options"].append(opt_data)
    
    return event_data


def extract_block(content, block_name):
    """Extract nội dung của một block (ví dụ: trigger = { ... })"""
    pattern = rf'{block_name}\s*=\s*{{'
    match = re.search(pattern, content)
    if not match:
        return None
    
    start = match.end()
    brace_count = 1
    for i in range(start, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[start:i]
    return None


def extract_block_at_position(content, pos):
    """Extract block tại vị trí pos (đã biết là bắt đầu bằng {)"""
    brace_count = 1
    for i in range(pos + 1, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[pos + 1:i]
    return None


def parse_option(option_str, localization):
    """Parse nội dung option"""
    option_data = {
        "name": "",
        "name_key": "",
        "default_option": False,
        "ai_chance": 100,
        "effect": {},
        "trigger_event": None
    }
    
    # Lấy name
    name_match = re.search(r'name\s*=\s*(\w+)', option_str)
    if name_match:
        option_data["name_key"] = name_match.group(1)
        option_data["name"] = get_localized_text(name_match.group(1), localization, name_match.group(1))
    
    # Kiểm tra default_option
    if re.search(r'default_option\s*=\s*yes', option_str):
        option_data["default_option"] = True
    
    # Parse ai_chance
    ai_chance_match = re.search(r'ai_chance\s*=\s*{\s*base\s*=\s*(\d+)', option_str)
    if ai_chance_match:
        option_data["ai_chance"] = int(ai_chance_match.group(1))
    
    # Parse effect block
    effect_content = extract_block(option_str, 'effect')
    if effect_content:
        option_data["effect"] = parse_effect_block(effect_content)
    
    # Parse trigger_event
    trigger_event_match = re.search(r'trigger_event\s*=\s*{\s*id\s*=\s*(\w+\.\d+)', option_str)
    if trigger_event_match:
        option_data["trigger_event"] = trigger_event_match.group(1)
    
    return option_data


def parse_effect_block(effect_str):
    """Parse effect block (có thể chứa nested blocks)"""
    effect = {}
    
    # Các effect đơn giản
    patterns = {
        'prestige': r'add_prestige\s*=\s*([+-]?\d+)',
        'treasury': r'treasury\s*=\s*([+-]?\d+)',
        'population': r'population\s*=\s*([+-]?\d+)',
        'tax_rate': r'tax_rate\s*=\s*([+-]?[\d.]+)',
        'government': r'government\s*=\s*(\w+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, effect_str)
        if match:
            val = match.group(1)
            if '.' in val:
                effect[key] = float(val)
            else:
                effect[key] = int(val)
    
    # add_modifier
    modifier_match = re.search(r'add_modifier\s*=\s*{\s*name\s*=\s*(\w+)\s*months\s*=\s*(\d+)', effect_str)
    if modifier_match:
        effect["add_modifier"] = {
            "name": modifier_match.group(1),
            "months": int(modifier_match.group(2))
        }
    
    # set_variable
    var_match = re.search(r'set_variable\s*=\s*{\s*name\s*=\s*(\w+)\s*value\s*=\s*(\d+)', effect_str)
    if var_match:
        effect["set_variable"] = {
            "name": var_match.group(1),
            "value": int(var_match.group(2))
        }
    
    # change_relations
    rel_match = re.search(r'change_relations\s*=\s*{\s*country\s*=\s*(\w+)\s*value\s*=\s*([+-]?\d+)', effect_str)
    if rel_match:
        effect["change_relations"] = {
            "country": rel_match.group(1),
            "value": int(rel_match.group(2))
        }
    
    # annex_state / set_state_owner
    annex_match = re.search(r'(annex_state|set_state_owner)\s*=\s*(\w+)', effect_str)
    if annex_match:
        effect[annex_match.group(1)] = annex_match.group(2)
    
    # random_state block
    random_state_content = extract_block(effect_str, 'random_state')
    if random_state_content:
        effect["random_state"] = parse_effect_block(random_state_content)
    
    return effect


def parse_trigger(trigger_str):
    """Parse điều kiện trigger"""
    trigger = {}
    
    # AND block (mặc định)
    and_content = extract_block(trigger_str, 'AND')
    if not and_content:
        # Nếu không có AND, treat entire string as conditions
        conditions_str = trigger_str
    else:
        conditions_str = and_content
    
    # Parse từng condition
    # year check
    year_match = re.search(r'year\s*=\s*(\d+)', conditions_str)
    if year_match:
        trigger["year"] = int(year_match.group(1))
    
    # year range
    year_range = re.search(r'year\s*=\s*{\s*min\s*=\s*(\d+)\s*max\s*=\s*(\d+)}', conditions_str)
    if year_range:
        trigger["year_min"] = int(year_range.group(1))
        trigger["year_max"] = int(year_range.group(2))
    
    # technology
    tech_match = re.search(r'has_technology\s*=\s*"?(\w+)"?', conditions_str)
    if tech_match:
        trigger["technology"] = tech_match.group(1)
    
    # country
    country_match = re.search(r'c:([A-Z]{3})\s*=', conditions_str)
    if country_match:
        trigger["country"] = country_match.group(1)
    
    # has_state
    state_match = re.search(r'has_state\s*=\s*(\w+)', conditions_str)
    if state_match:
        trigger["has_state"] = state_match.group(1)
    
    # relations
    rel_match = re.search(r'relations\s*=\s*{\s*country\s*=\s*(\w+)\s*value\s*>\s*(\d+)', conditions_str)
    if rel_match:
        trigger["relations_with"] = rel_match.group(1)
        trigger["relations_min"] = int(rel_match.group(2))
    
    return trigger


# Hàm kiểm tra event có trigger không
def check_event_trigger(event, country, game_state):
    """Kiểm tra event có được trigger cho country hiện tại không"""
    trigger = event.get("trigger", {})
    
    # Kiểm tra year
    if "year" in trigger and game_state.current_date.year != trigger["year"]:
        return False
    
    if "year_min" in trigger:
        if game_state.current_date.year < trigger["year_min"]:
            return False
        if "year_max" in trigger and game_state.current_date.year > trigger["year_max"]:
            return False
    
    # Kiểm tra country
    if "country" in trigger and trigger["country"] != country.tag:
        return False
    
    # Kiểm tra technology
    if "technology" in trigger:
        if trigger["technology"] not in getattr(country, "technologies", []):
            return False
    
    # Kiểm tra state
    if "has_state" in trigger:
        if trigger["has_state"] not in game_state.states:
            return False
        if game_state.states[trigger["has_state"]].owner != country.tag:
            return False
    
    # Kiểm tra relations
    if "relations_with" in trigger:
        rel_value = country.relations.get(trigger["relations_with"], 0)
        if rel_value < trigger.get("relations_min", 0):
            return False
    
    return True


def apply_event_effect(effect, country, game_state):
    """Áp dụng effect của event"""
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
        country.tax_rate = max(0.05, min(0.4, country.tax_rate + effect["tax_rate"]))
        results.append(f"Thuế suất {effect['tax_rate']:+.0%}")
    
    if "government" in effect:
        country.government = effect["government"]
        results.append(f"Chính phủ -> {effect['government']}")
    
    if "add_modifier" in effect:
        mod = effect["add_modifier"]
        if not hasattr(country, "active_modifiers"):
            country.active_modifiers = {}
        country.active_modifiers[mod["name"]] = mod
        results.append(f"Thêm modifier: {mod['name']}")
    
    if "change_relations" in effect:
        target = effect["change_relations"]["country"]
        value = effect["change_relations"]["value"]
        if target in game_state.countries:
            country.relations[target] = country.relations.get(target, 0) + value
            country.relations[target] = max(-100, min(100, country.relations[target]))
            results.append(f"Quan hệ với {target} {value:+d}")
    
    return ", ".join(results) if results else "Không có thay đổi"