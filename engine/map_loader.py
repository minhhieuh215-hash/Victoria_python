import csv
import os
import re
import sys

from PIL import Image
from models.province import Province
from models.state import State

def _parse_hex_colors(block_str):
    """Parse danh sách hex color từ một block string, trả về set các tuple (r,g,b)."""
    colors = set()
    for token in block_str.split():
        hex_str = token.replace('"', '').strip().lstrip('x').lstrip('X')
        if len(hex_str) != 6:
            continue
        try:
            colors.add((int(hex_str[0:2], 16),
                        int(hex_str[2:4], 16),
                        int(hex_str[4:6], 16)))
        except ValueError:
            continue
    return colors

def load_sea_colors():
    sea_colors = set()
    lake_colors = set()
    file_path = "data/map_data/default.map"

    if not os.path.exists(file_path):
        print(f"Không tìm thấy file {file_path}!")
        return sea_colors, lake_colors

    with open(file_path, "r", encoding="utf-8") as file:
        content = re.sub(r'#.*', '', file.read())

    # 1. Đại dương (sea_starts)
    match_sea = re.search(r"sea_starts\s*=\s*\{([^}]+)\}", content)
    if match_sea:
        sea_colors = _parse_hex_colors(match_sea.group(1))

    # 2. Hồ nội địa (lakes) - tách RIÊNG, không gộp vào sea
    match_lakes = re.search(r"lakes\s*=\s*\{([^}]+)\}", content)
    if match_lakes:
        lake_colors = _parse_hex_colors(match_lakes.group(1))

    msg = f"-> Biển: {len(sea_colors)} màu | Hồ nội địa: {len(lake_colors)} màu"
    try:
        # Prefer writing UTF-8 bytes to the stdout buffer so terminals that
        # don't use a Unicode-compatible encoding won't raise on print.
        sys.stdout.buffer.write((msg + "\n").encode("utf-8"))
    except Exception:
        # Fallback to an ASCII-safe message
        print("-> Seas:", len(sea_colors), "lakes:", len(lake_colors))
    return sea_colors, lake_colors

def load_provinces():
    # Bước 1: Nạp danh sách màu Biển và Hồ nội địa
    sea_colors, lake_colors = load_sea_colors()

    img = Image.open("data/map_data/provinces.png")
    img_rgb = img.convert("RGB")
    pixels = img_rgb.load()

    provinces = {}
    color_to_id = {}
    province_id = 1
    width, height = img.size

    assert pixels is not None

    for y in range(height):
        for x in range(width):
            color = pixels[x, y]

            if color == (0, 0, 0):
                continue

            if not isinstance(color, tuple):
                continue

            if color not in color_to_id:
                color_to_id[color] = province_id

                prov = Province(province_id, color)

                if color in sea_colors:
                    # Đại dương thật sự → tô xanh đậm
                    prov.is_sea = True
                    prov.is_lake = False
                    prov.owner = "SEA"
                elif color in lake_colors:
                    # Hồ nội địa (Great Lakes, hồ Canada...) → tô xanh nhạt hơn biển
                    prov.is_sea = False
                    prov.is_lake = True
                    prov.owner = "LAKE"
                else:
                    prov.is_sea = False
                    prov.is_lake = False
                    prov.owner = "Không có / Đất trống"

                provinces[province_id] = prov
                province_id += 1

    img.close()
    try:
        sys.stdout.buffer.write((f"-> Tổng số province: {len(provinces)}\n").encode("utf-8"))
    except Exception:
        print("-> Total provinces:", len(provinces))

    try:
        sys.stdout.buffer.write((f"-> Đất có chủ: {sum(1 for p in provinces.values() if p.owner not in ('SEA', 'LAKE', 'Không có / Đất trống'))}\n").encode("utf-8"))
    except Exception:
        print("-> Owned provinces:", sum(1 for p in provinces.values() if p.owner not in ('SEA', 'LAKE', 'Không có / Đất trống')))
    return provinces

def load_adjacencies(provinces):
    with open("data/map_data/adjacencies.csv", newline='') as file:
        reader = csv.reader(file)

        for row in reader:

            try:
                a = int(row[0])
                b = int(row[1])
                province_a = provinces[a]
                province_b = provinces[b]
                province_a.neighbors.append(b)
                province_b.neighbors.append(a)

            except:
                continue

def load_states(provinces):
    states = []
    folder = "data/map_data/state_regions"

    color_to_province = {prov.color: prov for prov in provinces.values()}
    
    # Debug: in ra 10 màu đầu tiên để kiểm tra
    print(f"Debug: First 5 province colors: {list(color_to_province.keys())[:5]}")

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        
        if not os.path.isfile(path):
            continue

        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as file:
                content = file.read()
            
        for match in re.finditer(r'^([A-Z_]+)\s*=\s*\{', content, re.MULTILINE):
            state_name = match.group(1)
            start_pos = match.end()

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

            if end_pos <= start_pos:
                continue

            state_body = content[start_pos:end_pos]
            prov_match = re.search(r'provinces\s*=\s*\{([^}]+(?:{[^}]*}[^}]*)*)\}', state_body, re.DOTALL)
            if not prov_match:
                continue

            # Parse province colors
            province_ids = prov_match.group(1).split()
            state = State(state_name)
            matched_count = 0

            for hex_pid in province_ids:
                hex_str = hex_pid.replace('"', '').strip().lstrip('x').lstrip('X')
                
                if len(hex_str) != 6:
                    continue

                try:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    target_color = (r, g, b)

                    if target_color in color_to_province:
                        state.provinces.append(color_to_province[target_color])
                        matched_count += 1

                except ValueError:
                    continue
                
            if state.provinces:
                states.append(state)
                # Chỉ in ra nếu có vấn đề hoặc giảm log
                if matched_count < len(province_ids) * 0.5:
                    print(f"State {state_name}: matched {matched_count}/{len(province_ids)} provinces")
    
    print(f"Total states loaded: {len(states)}")
    return states