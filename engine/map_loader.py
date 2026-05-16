import csv
import os
import re

from PIL import Image
from models.province import Province
from models.state import State

def load_provinces():
    img = Image.open("data/map_data/provinces.png").convert("RGB")
    pixels = img.load()

    provinces = {}
    color_to_id = {}
    province_id = 1
    width, height = img.size

    assert pixels is not None

    for y in range(height):
        for x in range(width):
            color = pixels[x, y]

            if color == (0,0,0):
                continue

            if color not in color_to_id:
                color_to_id[color] = province_id
                provinces[province_id] = Province(province_id,color)
                province_id += 1
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