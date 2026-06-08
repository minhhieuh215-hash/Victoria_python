import glob
import json
import os
import re
import colorsys

def load_countries():
    countries = {}
    folder_path = os.path.join("data", "common", "country_definitions")

    if not os.path.isdir(folder_path):
        return countries

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(folder_path, filename)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except OSError:
            continue

        # Find all country blocks like TAG = { ... }
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

            # Try to find a color definition inside the block
            # Support formats: color = { R G B }, color = hsv{ ... }, color = hsv360{ ... }
            cm = re.search(r"color\s*=\s*(hsv360|hsv)?\s*\{\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", body)
            if not cm:
                # maybe color on a single line with commas or without braces
                cm = re.search(r"color\s*=\s*\{?\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*\}?", body)
                if cm:
                    ctype = None
                    v1, v2, v3 = float(cm.group(1)), float(cm.group(2)), float(cm.group(3))
                else:
                    continue
            else:
                ctype = cm.group(1)
                v1, v2, v3 = float(cm.group(2)), float(cm.group(3)), float(cm.group(4))

            # Convert to RGB 0-255
            try:
                if ctype == "hsv360":
                    r, g, b = colorsys.hsv_to_rgb(v1 / 360.0, v2 / 100.0, v3 / 100.0)
                    rgb = (int(r * 255), int(g * 255), int(b * 255))
                elif ctype == "hsv":
                    r, g, b = colorsys.hsv_to_rgb(v1, v2, v3)
                    rgb = (int(r * 255), int(g * 255), int(b * 255))
                else:
                    rgb = (int(v1), int(v2), int(v3))
            except Exception:
                continue

            countries[tag] = rgb

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