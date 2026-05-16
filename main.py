from engine.country_loader import load_countries
from engine.history_loader import load_state_history
from engine.map_loader import load_provinces
from engine.map_loader import *

provinces = load_provinces()
load_adjacencies(provinces)
states = load_states(provinces)

color_to_province = {prov.color: prov for prov in provinces.values()}

countries_data = load_countries() # Lấy danh sách màu các nước
load_state_history(color_to_province) # Gán TAG quốc gia vào Province

test_color = list(color_to_province.keys())[1000]
test_prov = color_to_province[test_color]

print(f"Province {test_prov.id} màu {test_color} đang bị chiếm bởi: {test_prov.owner}")
if test_prov.owner in countries_data:
    print(f"Màu hiển thị trên bản đồ chính trị của nước này sẽ là: {countries_data[test_prov.owner]}")