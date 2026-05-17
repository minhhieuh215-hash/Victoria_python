import csv
import os
import re

from PIL import Image
from models.province import Province
from models.state import State

def load_sea_colors():
    sea_colors = set()
    # Đường dẫn tới file default.map trong thư mục dự án của bạn
    file_path = "data/map_data/default.map" 
    
    if not os.path.exists(file_path):
        print(f"⚠️ Không tìm thấy file {file_path}! Tạm thời hệ thống chưa phân biệt được Biển.")
        return sea_colors

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        
        # Loại bỏ các đoạn ghi chú (comment bắt đầu bằng #) để tránh nhận diện nhầm ký tự rác
        content_clean = re.sub(r'#.*', '', content)
        
        # Tìm khối sea_starts = { ... }
        match = re.search(r"sea_starts\s*=\s*\{([^}]+)\}", content_clean)
        if match:
            hex_pids = match.group(1).split()
            for hex_pid in hex_pids:
                # Làm sạch chuỗi Hex (bỏ ngoặc kép, khoảng trắng và chữ x/X ở đầu)
                hex_str = hex_pid.replace('"', '').strip().lstrip('x').lstrip('X')
                if len(hex_str) != 6:
                    continue
                try:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    sea_colors.add((r, g, b))
                except ValueError:
                    continue
                    
    print(f"-> Đã trích xuất thành công {len(sea_colors)} mã màu của vùng Đại dương.")
    return sea_colors

def load_provinces():
    # Bước 1: Nạp danh sách các màu thuộc về Biển trước khi quét ảnh
    sea_colors = load_sea_colors()

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
                
                # Tạo đối tượng Province
                prov = Province(province_id, color)
                
                # Bước 2: Tự động đối chiếu màu để phân loại Đất liền vs Biển
                if color in sea_colors:
                    prov.is_sea = True
                    prov.owner = "SEA"  # Đặt nhãn chủ sở hữu mặc định cho đại dương
                else:
                    prov.is_sea = False
                    prov.owner = "Không có / Đất trống"  # Sẽ được ghi đè ở hàm history_loader sau này
                
                provinces[province_id] = prov
                province_id += 1
                
    img.close()  # Đảm bảo giải phóng file ảnh để Pygame không bị lỗi tranh chấp (lock file)
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

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            name_match = re.search(r"(\w+)\s*=", content)
            provinces_match = re.search(r"provinces\s*=\s*{([^}]*)}", content)

            if name_match and provinces_match:
                state_name = name_match.group(1)
                province_ids = provinces_match.group(1).split()
                state = State(state_name)

                for hex_pid in province_ids:
                    hex_str = hex_pid.replace('"', '').lstrip('x')
                    
                    if len(hex_str) != 6:
                        continue 

                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    target_color = (r, g, b)

                    if target_color in color_to_province:
                        state.provinces.append(color_to_province[target_color])

                states.append(state)

    return states