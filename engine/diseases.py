# engine/diseases.py
"""
Hệ thống dịch bệnh (Epidemics) mô phỏng AOH3 và Victoria 3.
Bùng phát ngẫu nhiên, lan rộng qua mạng lưới giáp ranh các tỉnh đất liền,
gây tử vong giảm dân số và tăng tàn phá (devastation).
"""
import random
from typing import Dict, List, Set, Any
from engine.country_names import get_country_display_name

DISEASE_TEMPLATES = [
    {
        "name": "Đậu mùa (Smallpox)",
        "beginning_year": 1800,
        "end_year": 2000,
        "duration_min": 5,
        "duration_extra": 12,
        "outbreak_chance": 0.02,
        "death_rate_min": 0.003,
        "death_rate_max": 0.012,
        "devastation_increase": 0.15,
        "color": (87, 219, 75),
        "desc": "Bệnh đậu mùa lây lan mạnh qua đường hô hấp, gây sốt cao và phát ban đỏ khắp cơ thể."
    },
    {
        "name": "Sởi (Measles)",
        "beginning_year": 1800,
        "end_year": 2000,
        "duration_min": 4,
        "duration_extra": 10,
        "outbreak_chance": 0.02,
        "death_rate_min": 0.001,
        "death_rate_max": 0.006,
        "devastation_increase": 0.08,
        "color": (255, 183, 25),
        "desc": "Bệnh sởi bùng phát ở các khu vực đông dân cư, ảnh hưởng lớn đến trẻ em và lực lượng lao động."
    },
    {
        "name": "Lao phổi (Tuberculosis)",
        "beginning_year": 1800,
        "end_year": 2000,
        "duration_min": 6,
        "duration_extra": 16,
        "outbreak_chance": 0.015,
        "death_rate_min": 0.002,
        "death_rate_max": 0.008,
        "devastation_increase": 0.12,
        "color": (8, 97, 56),
        "desc": "Bệnh lao tàn phá các khu vực đô thị chật hẹp, khiến thể trạng người bệnh suy yếu dần."
    },
    {
        "name": "Kiết lỵ (Dysentery)",
        "beginning_year": 1800,
        "end_year": 2000,
        "duration_min": 4,
        "duration_extra": 8,
        "outbreak_chance": 0.02,
        "death_rate_min": 0.0015,
        "death_rate_max": 0.005,
        "devastation_increase": 0.05,
        "color": (4, 78, 147),
        "desc": "Dịch tả lây lan qua nguồn nước ô nhiễm, hoành hành tại các khu trại lính và khu phố nghèo."
    },
    {
        "name": "Sốt vàng da (Yellow Fever)",
        "beginning_year": 1800,
        "end_year": 1910,
        "duration_min": 5,
        "duration_extra": 10,
        "outbreak_chance": 0.015,
        "death_rate_min": 0.004,
        "death_rate_max": 0.015,
        "devastation_increase": 0.18,
        "color": (232, 104, 39),
        "desc": "Căn bệnh nhiệt đới do muỗi truyền bệnh, gây tổn hại gan nặng nề tại các vùng đầm lầy ven biển."
    },
    {
        "name": "Cúm mùa (Influenza)",
        "beginning_year": 1800,
        "end_year": 2000,
        "duration_min": 3,
        "duration_extra": 8,
        "outbreak_chance": 0.03,
        "death_rate_min": 0.0005,
        "death_rate_max": 0.002,
        "devastation_increase": 0.03,
        "color": (202, 215, 199),
        "desc": "Dịch cúm lan truyền nhanh chóng theo mùa gió, gây ảnh hưởng diện rộng nhưng tỷ lệ tử vong thấp."
    },
    {
        "name": "Cái chết đen (Plague)",
        "beginning_year": 1800,
        "end_year": 1900,
        "duration_min": 8,
        "duration_extra": 20,
        "outbreak_chance": 0.005,
        "death_rate_min": 0.01,
        "death_rate_max": 0.04,
        "devastation_increase": 0.3,
        "color": (117, 30, 124),
        "desc": "Trận dịch hạch tàn khốc lây lan qua bọ chét và chuột, gieo rắc nỗi kinh hoàng và chết chóc khủng khiếp."
    }
]

def monthly_disease_tick(game_state):
    """Mô phỏng bùng phát, lây lan và tác động của dịch bệnh hàng tháng"""
    
    # 1. Cập nhật các dịch bệnh đang hoạt động
    active_keys = list(game_state.active_epidemics.keys())
    for d_name in active_keys:
        epi = game_state.active_epidemics[d_name]
        epi["turns_left"] -= 1
        
        # Kết thúc dịch bệnh
        if epi["turns_left"] <= 0:
            del game_state.active_epidemics[d_name]
            game_state.event_queue.append({
                "title": "DỊCH BỆNH KẾT THÚC",
                "desc": f"Trận đại dịch '{d_name}' hoành hành bấy lâu nay cuối cùng đã bị đẩy lùi hoàn toàn.",
                "type": "simple",
                "effect_text": "Thở phào nhẹ nhõm"
            })
            game_state.needs_map_update = True
            continue
            
        # Lây lan dịch bệnh sang tỉnh giáp ranh
        current_provinces = list(epi["provinces"])
        new_infections = set()
        for prov_id in current_provinces:
            prov = game_state.provinces.get(prov_id)
            if not prov:
                continue
            for neighbor_id in getattr(prov, "neighbors", []):
                if neighbor_id in epi["provinces"] or neighbor_id in new_infections:
                    continue
                neighbor_prov = game_state.provinces.get(neighbor_id)
                if neighbor_prov and not neighbor_prov.is_sea and not neighbor_prov.is_lake:
                    # Tỷ lệ lây lan 12% mỗi tháng, có thể giảm nhờ cách ly
                    spread_chance = 0.12 * epi.get("spread_modifier", 1.0)
                    if random.random() < spread_chance:
                        new_infections.add(neighbor_id)
                        
        if new_infections:
            epi["provinces"].update(new_infections)
            game_state.needs_map_update = True

    # 2. Kiểm tra bùng phát dịch mới
    # Nếu chưa có dịch nào hoạt động, có 4% cơ hội bùng phát dịch mới mỗi tháng
    if not game_state.active_epidemics and random.random() < 0.04:
        # Chọn dịch phù hợp năm hiện tại
        current_year = game_state.current_date.year
        eligible_diseases = [
            d for d in DISEASE_TEMPLATES 
            if d["beginning_year"] <= current_year <= d["end_year"]
        ]
        
        if eligible_diseases:
            # Random chọn dịch theo outbreak chance
            weights = [d["outbreak_chance"] for d in eligible_diseases]
            disease = random.choices(eligible_diseases, weights=weights, k=1)[0]
            
            # Chọn 1-3 tỉnh đất liền ngẫu nhiên để làm trung tâm bùng phát
            all_land_provinces = [
                p for p in game_state.provinces.values()
                if not p.is_sea and not p.is_lake and p.owner not in ("SEA", "LAKE", "Không có / Đất trống", None)
            ]
            
            if all_land_provinces:
                outbreak_center = random.choice(all_land_provinces)
                infected_set = {outbreak_center.id}
                
                # Thêm 1-2 nước láng giềng gần
                for neighbor_id in getattr(outbreak_center, "neighbors", []):
                    n_prov = game_state.provinces.get(neighbor_id)
                    if n_prov and not n_prov.is_sea and not n_prov.is_lake and random.random() < 0.5:
                        infected_set.add(neighbor_id)
                        if len(infected_set) >= 3:
                            break
                            
                duration = disease["duration_min"] + random.randint(0, disease["duration_extra"])
                d_name = disease["name"]
                
                game_state.active_epidemics[d_name] = {
                    "provinces": infected_set,
                    "turns_left": duration,
                    "template": disease,
                    "spread_modifier": 1.0,
                    "death_rate_modifier": 1.0,
                    "player_notified": False
                }
                game_state.needs_map_update = True
                
                # Báo cáo sự kiện bùng phát
                owner_disp = get_country_display_name(outbreak_center.owner, outbreak_center.owner)
                game_state.event_queue.append({
                    "title": "ĐẠI DỊCH BÙNG PHÁT!",
                    "desc": f"Đại dịch '{d_name}' nguy hiểm đã bùng phát tại vùng lãnh thổ của {owner_disp}!\n\nChi tiết: {disease['desc']}\nDự báo dịch bệnh sẽ kéo dài khoảng {duration} tháng.",
                    "type": "simple",
                    "effect_text": "Phòng chống dịch"
                })

    # 3. Kích hoạt sự kiện lựa chọn cho người chơi khi dịch bệnh tấn công lãnh thổ
    player_tag = game_state.player_tag
    for d_name, epi in game_state.active_epidemics.items():
        template = epi.get("template", DISEASE_TEMPLATES[0])
        player_infected = False
        for p_id in epi["provinces"]:
            p_obj = game_state.provinces.get(p_id)
            if p_obj and p_obj.owner == player_tag:
                player_infected = True
                break
        
        if player_infected and not epi.get("player_notified", False):
            epi["player_notified"] = True
            
            # Queue sự kiện đa lựa chọn ứng phó dịch bệnh
            game_state.event_queue.append({
                "title": f"ĐẠI DỊCH LAN ĐẾN: {d_name.upper()}!",
                "desc": f"Đại dịch '{d_name}' đã chính thức lây lan vào lãnh thổ nước ta!\n\nChi tiết: {template['desc']}\nChúng ta cần đưa ra các quyết sách khẩn cấp để đối phó với cuộc khủng hoảng này.",
                "options": [
                    {
                        "name": "Áp dụng cách ly các vùng nhiễm bệnh",
                        "effect_desc": "Kho bạc -50£, giảm 50% tốc độ lây lan",
                        "effect": lambda c, gs, dn=d_name: (setattr(c, "treasury", max(0.0, c.treasury - 50)), gs.active_epidemics[dn].update({"spread_modifier": 0.5}) if dn in gs.active_epidemics else None)
                    },
                    {
                        "name": "Hỗ trợ y tế & phát cháo chấn chỉnh dân sinh",
                        "effect_desc": "Kho bạc -80£, giảm 50% tỷ lệ tử vong",
                        "effect": lambda c, gs, dn=d_name: (setattr(c, "treasury", max(0.0, c.treasury - 80)), gs.active_epidemics[dn].update({"death_rate_modifier": 0.5}) if dn in gs.active_epidemics else None)
                    },
                    {
                        "name": "Mặc kệ dịch bệnh tự sinh tự diệt",
                        "effect_desc": "Uy tín -15, Đại dịch tàn phá nặng nề",
                        "effect": lambda c, gs: setattr(c, "prestige", max(0.0, c.prestige - 15))
                    }
                ],
                "icon": "event_plague"
            })

    # 4. Áp dụng thiệt hại của dịch bệnh lên các tỉnh nhiễm bệnh
    for d_name, epi in game_state.active_epidemics.items():
        template = epi.get("template")
        if not template:
            # Tìm template dự phòng
            template = next((t for t in DISEASE_TEMPLATES if t["name"] == d_name), DISEASE_TEMPLATES[0])
            
        death_min = template["death_rate_min"]
        death_max = template["death_rate_max"]
        devastation_inc = template["devastation_increase"]
        
        # Áp dụng giảm dân số trong tỉnh nhiễm bệnh
        for prov_id in epi["provinces"]:
            prov = game_state.provinces.get(prov_id)
            if not prov:
                continue
                
            # Áp dụng giảm tỷ lệ tử vong nếu đã hỗ trợ y tế
            death_rate = random.uniform(death_min, death_max) * epi.get("death_rate_modifier", 1.0)
            
            # Giảm dân số province
            old_pop = prov.population
            prov.population = max(10, int(prov.population * (1.0 - death_rate)))
            
            # Áp dụng tàn phá, giảm nếu có cách ly
            dev_mult = 0.5 if epi.get("spread_modifier", 1.0) < 1.0 else 1.0
            if not hasattr(prov, 'devastation'):
                prov.devastation = 0.0
            prov.devastation = min(100.0, prov.devastation + devastation_inc * 100.0 * dev_mult)
            
            # Cập nhật state population
            import sys
            ui = sys.modules.get('game_ui')
            if ui and hasattr(ui, '_province_to_state_fast'):
                state = ui._province_to_state_fast.get(prov.color)
                if state:
                    state.population = sum(p.population for p in state.provinces)
                    owner_country = game_state.countries.get(state.owner)
                    if owner_country:
                        owner_country.population = sum(s.population for s in owner_country.states.values())
