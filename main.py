import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.map_loader import load_provinces, load_states
from engine.country_loader import load_countries
from engine.history_loader import load_state_history
from engine.economy import init_countries   # Cách này đúng
from engine.game_state import GameState
from engine.events import init_events
from models.market import Market
from game_ui import start_engine

import json
import random

def main():
    print("="*45)
    print("  VICTORIA 3 — SIMPLE ENGINE")
    print("="*45)

    print("[1/6] Nap tinh (Provinces)...")
    provinces = load_provinces()
    print(f"  -> Loaded {len(provinces)} provinces")

    print("[2/6] Nap bang (States)...")
    states = load_states(provinces)
    print(f"  -> Loaded {len(states)} states")

    print("[3/6] Lap chi muc ban do...")
    color_to_province = {prov.color: prov for prov in provinces.values()}
    print(f"  -> Color map size: {len(color_to_province)}")

    print("[4/6] Nap quoc gia (Countries)...")
    countries_data = load_countries()   # { TAG: (R,G,B) }
    print(f"  -> Loaded {len(countries_data)} countries")

    print("[5/6] Phan chia lanh tho 1836...")
    load_state_history(color_to_province)
    print("  -> History loaded")

    print("[6/6] Khoi tao kinh te & thi truong...")
    print("  -> Initializing economy and market...")
    
    # Load country type
    full_path = os.path.join(os.path.dirname(__file__), "data", "countries_full.json")
    countries_full = {}
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                countries_full = json.loads(raw)
                print(f"  -> Loaded {len(countries_full)} country types from countries_full.json")
            else:
                raise ValueError("empty file")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"  -> Could not load countries_full.json: {e}")
        print("  -> Generating from country_definitions...")
        
        import re
        import glob
        
        def parse_country_types():
            result = {}
            folder = os.path.join(os.path.dirname(__file__), "data", "common", "country_definitions")
            
            if not os.path.exists(folder):
                print(f"     Warning: Folder not found: {folder}")
                return result
            
            for path in glob.glob(os.path.join(folder, "*.txt")):
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                except:
                    continue
                
                # Tìm tất cả các tag
                for match in re.finditer(r"([A-Z0-9]{2,4})\s*=\s*\{", content):
                    tag = match.group(1)
                    start_pos = match.end()
                    
                    # Đếm ngoặc để tìm block đóng
                    brace_count = 1
                    end_pos = start_pos
                    for i in range(start_pos, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i
                                break
                    
                    if end_pos > start_pos:
                        body = content[start_pos:end_pos]
                        
                        # Bỏ qua dynamic country definition
                        if "dynamic_country_definition" in body:
                            continue
                        
                        # Tìm country_type
                        type_match = re.search(r"country_type\s*=\s*(\w+)", body)
                        country_type = type_match.group(1) if type_match else "recognized"
                        
                        result[tag] = {"type": country_type}
            
            return result
        
        countries_full = parse_country_types()
        print(f"  -> Generated {len(countries_full)} country types")
        
        # Lưu lại để lần sau dùng
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(countries_full, f, indent=2)
            print(f"  -> Saved to {full_path}")
        except Exception as save_err:
            print(f"  -> Could not save: {save_err}")

    print(f"  -> Countries with types: {len(countries_full)}")
    
    # Khởi tạo market và countries
    market = Market()
    print("  -> Initializing country objects...")
    countries_obj = init_countries(countries_data, countries_full)
    print(f"  -> Created {len(countries_obj)} country objects")

    # Khởi tạo states dict
    states_dict = {s.name: s for s in states}
    print(f"  -> States dict: {len(states_dict)} states")

    # Khởi tạo GameState
    print("  -> Creating GameState...")
    game_state = GameState(provinces, states_dict, countries_data,
                           countries_obj, market)
    
    # Khởi tạo events
    print("  -> Initializing events system...")
    game_state = init_events(game_state)

    print("="*45)
    print(f"  San sang! {len(countries_obj)} quoc gia | {len(provinces)} tinh")
    print("="*45)

    print("  -> Starting game engine...")
    start_engine(game_state)
    print("Game engine finished (should not happen until exit)")

if __name__ == "__main__":
    main()