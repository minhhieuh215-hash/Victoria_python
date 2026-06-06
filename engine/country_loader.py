import glob
import json
import os
import re
import colorsys

def load_countries():
    countries = {}
    folder_path = "data/common/country_definitions"

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
            
        with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
            current_tag = None
            
            for line in file:
                # Bỏ qua các dòng comment (bắt đầu bằng #)
                line = line.split('#')[0].strip() 
                if not line:
                    continue
                    
                # Bắt đầu một quốc gia mới (VD: GBR = { )
                tag_match = re.match(r"^([A-Z0-9]{3})\s*=\s*\{", line)
                if tag_match:
                    current_tag = tag_match.group(1)
                    continue
                    
                # Nếu đang ở trong block của 1 quốc gia và tìm thấy chữ "color"
                if current_tag and "color" in line:
                    # Regex này lấy ra hệ màu và 3 con số
                    color_match = re.search(r"color\s*=\s*(hsv360|hsv)?\s*\{\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", line)
                    
                    if color_match:
                        color_type = color_match.group(1)
                        v1 = float(color_match.group(2))
                        v2 = float(color_match.group(3))
                        v3 = float(color_match.group(4))
                        
                        # Chuyển đổi các hệ màu hsv/hsv360 về RGB chuẩn (0-255)
                        if color_type == "hsv360":
                            r, g, b = colorsys.hsv_to_rgb(v1/360.0, v2/100.0, v3/100.0)
                            rgb = (int(r*255), int(g*255), int(b*255))
                        elif color_type == "hsv":
                            r, g, b = colorsys.hsv_to_rgb(v1, v2, v3)
                            rgb = (int(r*255), int(g*255), int(b*255))
                        else:
                            # Nếu không có chữ hsv, nó là RGB thường
                            rgb = (int(v1), int(v2), int(v3))
                            
                        # Lưu vào từ điển { "GBR": (252, 178, 229), "GER": (147, 130, 110) }
                        countries[current_tag] = rgb
                        current_tag = None # Reset để chờ lấy TAG nước tiếp theo
                        
    return countries


def parse_country_types(base_dir=None):
    """Đọc country_type từ country_definitions (decentralized, colonial, ...)."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(base_dir, "data", "common", "country_definitions")
    result = {}
    if not os.path.isdir(folder):
        return result

    for path in glob.glob(os.path.join(folder, "*.txt")):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except OSError:
            continue

        for match in re.finditer(r"([A-Z0-9]{2,4})\s*=\s*\{", content):
            tag = match.group(1)
            start_pos = match.end()
            brace_count = 1
            end_pos = start_pos
            for i in range(start_pos, len(content)):
                if content[i] == "{":
                    brace_count += 1
                elif content[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            if end_pos <= start_pos:
                continue
            body = content[start_pos:end_pos]
            if "dynamic_country_definition" in body:
                continue
            type_match = re.search(r"country_type\s*=\s*(\w+)", body)
            country_type = type_match.group(1) if type_match else "recognized"
            result[tag] = {"type": country_type}
    return result


def load_countries_full(base_dir=None, save=True):
    """Load country types; luôn merge từ definitions để có đủ decentralized/colonial."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parsed = parse_country_types(base_dir)
    full_path = os.path.join(base_dir, "data", "countries_full.json")
    merged = dict(parsed)

    if os.path.isfile(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if raw:
                    saved = json.loads(raw)
                    for tag, info in saved.items():
                        if tag not in merged:
                            merged[tag] = info
        except (json.JSONDecodeError, OSError):
            pass

    if save and len(merged) > 50:
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
        except OSError:
            pass
    return merged


# Code test thử xem có chạy mượt không
if __name__ == "__main__":
    my_countries = load_countries()
    print(f"Đã load thành công {len(my_countries)} quốc gia!")
    print(f"Màu của Anh (GBR) là: {my_countries.get('GBR')}")
    print(f"Màu của Đại Nam (DAI) là: {my_countries.get('DAI')}")