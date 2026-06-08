"""Trạng thái trung tâm của toàn bộ game."""
from config import START_YEAR, START_MONTH

class GameDate:
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    MONTH_FULL  = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    def __init__(self, year=START_YEAR, month=START_MONTH):
        self.year  = year
        self.month = month

    def advance(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    @property
    def short(self):
        return f"{self.MONTH_NAMES[self.month-1]} {self.year}"

    @property
    def full(self):
        return f"{self.MONTH_FULL[self.month-1]} {self.year}"

    def __repr__(self):
        return self.short


class GameState:
    def __init__(self, provinces, states, countries_data,
                 countries_obj=None, market=None):
        self.provinces      = provinces       # { id: Province }
        self.states         = states          # { name: State }
        self.countries_data = countries_data  # { TAG: [R,G,B] }
        self.countries      = countries_obj or {}  # { TAG: Country }
        self.market         = market

        self.current_date   = GameDate()
        self.player_tag     = "GBR"
        self.player_mode    = "default"

        # Log sự kiện gần nhất (hiện trong sidebar)
        self.last_event     = None   # dict hoặc None
        self.economy_report = {}     # { TAG: {income,expense,...} }
        
        # Events system
        self.historical_events = {}
        self.simple_events = []
        
        # War and Battle system
        self.active_wars = {}  # { (tag_a, tag_b): {score, battles_count} }
        self.event_queue = []  # Queue of popups to show sequentially

        # Epidemic/Disease System
        self.active_epidemics = {}
        # Historical Age System
        self.current_age = "Age of Industrialisation"

    @property
    def player_country(self):
        return self.countries.get(self.player_tag)

    def update_historical_age(self):
        # Cập nhật Thời kỳ Lịch sử (Age)
        year = self.current_date.year
        old_age = getattr(self, "current_age", None)
        if year < 1826:
            self.current_age = "Age of Revolution"
        elif 1826 <= year <= 1860:
            self.current_age = "Age of Industrialisation"
        else:
            self.current_age = "Age of Imperialism"

        # Nếu đổi thời kỳ thì tạo popup thông báo
        if old_age and old_age != self.current_age:
            age_names = {
                "Age of Revolution": "Kỷ nguyên Cách mạng",
                "Age of Industrialisation": "Kỷ nguyên Công nghiệp hóa",
                "Age of Imperialism": "Kỷ nguyên Đế quốc chủ nghĩa"
            }
            age_descs = {
                "Age of Revolution": "Thời kỳ của những thay đổi chính trị to lớn, các tư tưởng tự do và những cuộc nổi dậy lật đổ chế độ cũ.",
                "Age of Industrialisation": "Thời kỳ của hơi nước và than đá, các nhà máy mọc lên như nấm và đô thị hóa diễn ra mạnh mẽ.",
                "Age of Imperialism": "Thời kỳ các cường quốc mở rộng tầm ảnh hưởng toàn cầu, tranh giành thuộc địa và tài nguyên thế giới."
            }
            self.event_queue.append({
                "title": f"BƯỚC SANG {age_names[self.current_age].upper()}!",
                "desc": f"Thế giới đã chính thức bước sang một thời đại mới: {age_names[self.current_age]}.\n\n{age_descs[self.current_age]}",
                "type": "simple",
                "effect_text": "Tiến lên phía trước"
            })

    def update_research_monthly(self):
        import random
        for tag, country in self.countries.items():
            if not hasattr(country, "research_points"):
                country.research_points = 0.0
            if not hasattr(country, "technologies"):
                country.technologies = []
                
            uni_count = 0
            if hasattr(country, "states"):
                for state in country.states.values():
                    if state.owner == tag:
                        for b in state.buildings:
                            if b.type == "university":
                                uni_count += b.level
                                
            points_earned = (country.literacy * 5.0) + (uni_count * 2.0)
            
            # Project: Education Reform (+10% research speed)
            if hasattr(country, 'completed_projects') and "education_reform" in country.completed_projects:
                points_earned *= 1.10
                
            country.research_points += points_earned
            
            base_cost = 100.0
            age = getattr(self, "current_age", "Age of Industrialisation")
            if age == "Age of Revolution":
                cost_mult = 0.8
            elif age == "Age of Imperialism":
                cost_mult = 1.2
            else:
                cost_mult = 1.0
                
            tech_cost = base_cost * cost_mult
            
            ALL_TECHS = ["medicine", "education", "steam_engine", "railway", "bureaucracy", "nationalism"]
            available_techs = [t for t in ALL_TECHS if t not in country.technologies]
            
            if available_techs and country.research_points >= tech_cost:
                country.research_points -= tech_cost
                new_tech = random.choice(available_techs)
                country.technologies.append(new_tech)
                
                # Apply bonuses immediately
                if new_tech == "steam_engine":
                    country.gdp *= 1.05
                elif new_tech == "nationalism":
                    country.prestige += 10
                    country.army_size = int(country.army_size * 1.05)
                
                if tag == self.player_tag:
                    tech_names = {
                        "medicine": "Y học hiện đại (Medicine)",
                        "education": "Hệ thống Giáo dục quốc dân (Education)",
                        "steam_engine": "Động cơ hơi nước (Steam Engine)",
                        "railway": "Mạng lưới Đường sắt (Railway)",
                        "bureaucracy": "Hệ thống Hành chính quan liêu (Bureaucracy)",
                        "nationalism": "Chủ nghĩa Dân tộc (Nationalism)"
                    }
                    self.event_queue.append({
                        "title": "NGHIÊN CỨU THÀNH CÔNG!",
                        "desc": f"Đất nước chúng ta đã phát minh và ứng dụng thành công công nghệ: {tech_names[new_tech]}!\n\nHiệu ứng: Mở khóa các bonus tương ứng cho nền kinh tế và xã hội.",
                        "type": "simple",
                        "effect_text": "Tuyệt vời!"
                    })

    def complete_project(self, tag, project_key):
        """Hoàn thành dự án quốc gia và áp dụng hiệu ứng."""
        country = self.countries.get(tag)
        if not country:
            return
            
        from engine.projects import ensure_project_attrs, PROJECTS
        ensure_project_attrs(country)
        
        if project_key not in country.completed_projects:
            country.completed_projects.append(project_key)
            
        country.active_project = None
        country.project_progress = 0
        country.project_time_needed = 0
        
        proj_data = PROJECTS.get(project_key)
        if proj_data:
            effects = proj_data.get("effects", {})
            if "prestige" in effects:
                country.prestige += effects["prestige"]
            if "infrastructure" in effects:
                country.infrastructure += effects["infrastructure"]
            if "manpower" in effects:
                country.army_size += int(effects["manpower"] / 1000) # Thêm quân số (k)
                
        if tag == self.player_tag:
            proj_name = PROJECTS[project_key]["name"]
            effects_desc = PROJECTS[project_key]["effects_desc"]
            self.event_queue.append({
                "title": "DỰ ÁN QUỐC GIA HOÀN THÀNH!",
                "desc": f"Đất nước chúng ta đã hoàn thành xuất sắc dự án trọng điểm:\n\n★ {proj_name.upper()} ★\n\nHiệu ứng: {effects_desc}",
                "type": "simple",
                "effect_text": "Tuyệt vời!"
            })

    def next_turn(self):
        """Tiến 1 tháng: kinh tế → chính trị → sự kiện."""
        from engine.economy  import monthly_economy_tick
        from engine.politics import monthly_politics_tick
        from engine.events   import check_events, apply_event
        from engine.diseases import monthly_disease_tick

        # Cập nhật Thời kỳ Lịch sử (Age)
        self.update_historical_age()

        self.economy_report = monthly_economy_tick(
            self.countries, self.market, self.player_tag, game_state=self)

        # Trình tự chiến đấu quân sự hàng tháng
        self.monthly_war_tick()

        monthly_politics_tick(self.countries, self.player_tag, game_state=self)

        # Cập nhật tiến trình nghiên cứu công nghệ
        self.update_research_monthly()

        # Cập nhật dịch bệnh hàng tháng
        monthly_disease_tick(self)

        # Kiểm tra sự kiện cho người chơi
        pc = self.player_country
        if pc:
            # ✅ SỬA: Truyền self (game_state) vào, không phải self.current_date
            ev = check_events(pc, self)
            if ev:
                apply_event(ev, pc)
                self.last_event = ev
            else:
                self.last_event = None

        # Reset once-per-turn relation actions
        for country in self.countries.values():
            if hasattr(country, 'relations_modified_this_turn'):
                country.relations_modified_this_turn.clear()
            if hasattr(country, 'trade_action_done_this_turn'):
                country.trade_action_done_this_turn.clear()
            if hasattr(country, 'total_trade_actions_this_turn'):
                country.total_trade_actions_this_turn = 0

        # Ticking law enactment for all countries
        import sys
        ui = sys.modules.get('game_ui')
        for tag, country in self.countries.items():
            enacting = getattr(country, 'enacting_law', None)
            if enacting:
                enacting["turns_left"] -= 1
                if enacting["turns_left"] <= 0:
                    cat = enacting["category"]
                    law = enacting["law_name"]
                    country.active_laws[cat] = law
                    if ui and hasattr(ui, 'PARSED_LAWS'):
                        for l in ui.PARSED_LAWS.keys():
                            country.laws[l] = (l == law)
                        if hasattr(ui, 'update_regime_from_laws'):
                            ui.update_regime_from_laws(country)
                    
                    if tag == self.player_tag:
                        self.player_mode = country.government
                        from engine.politics import apply_government_bonus
                        apply_government_bonus(country, self.player_tag, self)
                        
                        ui_lbl = ui.GOVT_LABELS.get(country.government, country.government) if ui else country.government
                        self.last_event = {
                            "title": "LUAT MOI DA THONG QUA",
                            "desc": f"Bo luat '{law}' da duoc thong qua chinh thuc!",
                            "effect_text": f"The the moi: {ui_lbl}"
                        }
                    country.enacting_law = None

        # Ticking national projects and AI selection
        import random
        from engine.projects import ensure_project_attrs, PROJECTS
        
        for tag, country in self.countries.items():
            ensure_project_attrs(country)
            
            # Progress active project
            if country.active_project:
                country.project_progress += 1
                if country.project_progress >= country.project_time_needed:
                    self.complete_project(tag, country.active_project)
            
            # AI starting projects
            elif tag != self.player_tag and country.country_type not in ('decentralized', 'unrecognized', 'colonial'):
                # Check if this AI country has a flag
                import sys
                ui = sys.modules.get('game_ui')
                if ui and hasattr(ui, '_flags'):
                    if tag not in ui._flags:
                        continue
                
                # 2% chance per month to start a project
                if random.random() < 0.02:
                    avail = []
                    for pk, p_data in PROJECTS.items():
                        if pk in country.completed_projects:
                            continue
                        if country.treasury < p_data["cost"] + 100:  # Keep 100 reserve
                            continue
                        req = p_data.get("requirements", {})
                        req_tech = req.get("tech")
                        if req_tech and req_tech not in getattr(country, "technologies", []):
                            continue
                        req_gdp = req.get("gdp")
                        if req_gdp and country.gdp < req_gdp:
                            continue
                        avail.append(pk)
                    
                    if avail:
                        chosen = random.choice(avail)
                        from engine.projects import start_project
                        start_project(country, chosen)

        self.current_date.advance()

    def monthly_war_tick(self):
        import random
        from engine.country_names import get_country_display_name

        processed_pairs = set()
        all_pairs = []

        # Đồng bộ hóa at_war_with và thu thập các cặp chiến tranh
        for tag_a, c_a in list(self.countries.items()):
            for tag_b in list(c_a.at_war_with):
                if tag_b not in self.countries:
                    c_a.at_war_with.discard(tag_b)
                    continue
                c_b = self.countries[tag_b]
                if tag_a not in c_b.at_war_with:
                    c_b.at_war_with.add(tag_a)

                pair = tuple(sorted([tag_a, tag_b]))
                if pair not in processed_pairs:
                    processed_pairs.add(pair)
                    all_pairs.append((tag_a, tag_b))

        for tag_a, tag_b in all_pairs:
            if tag_a not in self.countries or tag_b not in self.countries:
                continue
            c_a = self.countries[tag_a]
            c_b = self.countries[tag_b]

            pair = tuple(sorted([tag_a, tag_b]))
            if pair not in self.active_wars:
                self.active_wars[pair] = {
                    "score": 0.0,
                    "battles_count": 0,
                    "allies_a": set(),
                    "allies_b": set(),
                    "dead_a": 0,
                    "dead_b": 0
                }
                # Enqueue a breakout popup if player is involved
                if tag_a == self.player_tag or tag_b == self.player_tag:
                    other_tag = tag_b if tag_a == self.player_tag else tag_a
                    self.event_queue.append({
                        "title": "CHIẾN TRANH BÙNG NỔ!",
                        "desc": f"Quốc gia {get_country_display_name(other_tag, other_tag)} đã tuyên chiến với chúng ta!\nChuẩn bị quân đội ngay!",
                        "type": "simple",
                        "effect_text": "Quyết chiến!"
                    })

            war_info = self.active_wars[pair]
            if "allies_a" not in war_info: war_info["allies_a"] = set()
            if "allies_b" not in war_info: war_info["allies_b"] = set()
            if "dead_a" not in war_info: war_info["dead_a"] = 0
            if "dead_b" not in war_info: war_info["dead_b"] = 0

            # AI swaying allies logic
            for leader_tag, side_key, other_side_key in [(tag_a, "allies_a", "allies_b"), (tag_b, "allies_b", "allies_a")]:
                if leader_tag != self.player_tag:
                    leader_country = self.countries[leader_tag]
                    if leader_country.treasury >= 150 and random.random() < 0.05:
                        neutrals = []
                        for n_tag, n_c in self.countries.items():
                            if n_tag in (self.player_tag, tag_a, tag_b) or n_c.is_colonizable:
                                continue
                            if n_c.at_war_with:
                                continue
                            if n_tag in war_info["allies_a"] or n_tag in war_info["allies_b"]:
                                continue
                            if leader_country.relations.get(n_tag, 0) >= 0:
                                neutrals.append(n_tag)
                        if neutrals:
                            target_sway = random.choice(neutrals)
                            rel_val = leader_country.relations.get(target_sway, 0)
                            chance_val = max(0, min(100, int(50 + rel_val * 0.5)))
                            leader_country.treasury -= 150
                            if random.randint(1, 100) <= chance_val:
                                war_info[side_key].add(target_sway)
                                leader_country.relations[target_sway] = min(100, rel_val + 15)
                                self.needs_map_update = True
                                if tag_a == self.player_tag or tag_b == self.player_tag:
                                    self.event_queue.append({
                                        "title": "KE THU LOI KEO DONG MINH!",
                                        "desc": f"Quoc gia {get_country_display_name(leader_tag, leader_tag)} da loi keo thanh cong {get_country_display_name(target_sway, target_sway)} tham chien chong lai ta!",
                                        "type": "simple",
                                        "effect_text": "Xac nhan"
                                    })
                            else:
                                leader_country.relations[target_sway] = max(-100, rel_val - 10)

            # Đấu trận: tính theo tương quan quân lực (bao gồm đồng minh và bổ trợ dự án quốc gia)
            def get_modified_power(tag, countries):
                c = countries.get(tag)
                if not c:
                    return 0
                base = c.army_size
                if hasattr(c, 'completed_projects') and "military_mobilization" in c.completed_projects:
                    base *= 1.20 # +20% combat bonus
                return base

            power_a = get_modified_power(tag_a, self.countries) + sum(get_modified_power(t, self.countries) for t in war_info["allies_a"])
            power_b = get_modified_power(tag_b, self.countries) + sum(get_modified_power(t, self.countries) for t in war_info["allies_b"])
            power_a = max(power_a, 1)
            power_b = max(power_b, 1)

            chance_a = power_a / (power_a + power_b)
            winner_tag = tag_a if random.random() < chance_a else tag_b
            loser_tag = tag_b if winner_tag == tag_a else tag_a

            winner = self.countries[winner_tag]
            loser = self.countries[loser_tag]

            # Thiệt hại quân số
            winner_c = int(winner.army_size * random.uniform(0.03, 0.10))
            loser_c = int(loser.army_size * random.uniform(0.10, 0.25))

            winner.army_size = max(1, winner.army_size - winner_c)
            loser.army_size = max(0, loser.army_size - loser_c)

            # Ghi nhận thương vong vào war_info
            if winner_tag == tag_a:
                war_info["dead_a"] += winner_c
                war_info["dead_b"] += loser_c
            else:
                war_info["dead_b"] += winner_c
                war_info["dead_a"] += loser_c

            # Cập nhật điểm chiến tranh (War Score)
            score_change = random.randint(15, 25)
            if winner_tag == tag_a:
                war_info["score"] = min(100.0, war_info["score"] + score_change)
            else:
                war_info["score"] = max(-100.0, war_info["score"] - score_change)

            war_info["battles_count"] += 1

            # Kiểm tra xem có bên nào đầu hàng/hòa bình hoàn toàn không
            b_surrenders = (war_info["score"] >= 100.0 or c_b.army_size <= 0)
            a_surrenders = (war_info["score"] <= -100.0 or c_a.army_size <= 0)
            war_is_over = b_surrenders or a_surrenders

            # Gửi thông báo cho người chơi nếu liên quan và CHIẾN TRANH CHƯA KẾT THÚC
            is_player_involved = (tag_a == self.player_tag or tag_b == self.player_tag)
            if is_player_involved and not war_is_over:
                player_won = (winner_tag == self.player_tag)
                title = "CHIẾN THẮNG TRẬN ĐẤU!" if player_won else "BẠI TRẬN TRÊN BÁN ĐẢO!"
                desc = (
                    f"Quân đội ta đã đụng độ với quân {get_country_display_name(loser_tag if player_won else winner_tag)}.\n\n"
                    f"Kết quả: {'QUÂN TA CHIẾN THẮNG!' if player_won else 'QUÂN TA THẤT BẠI!'}\n"
                    f"Thương vong của ta: {winner_c if player_won else loser_c}k quân.\n"
                    f"Thương vong đối phương: {loser_c if player_won else winner_c}k quân.\n\n"
                    f"Điểm chiến tranh (War Score): {abs(war_info['score']):.1f}% nghiêng về {'ta' if (war_info['score'] > 0 if self.player_tag == tag_a else war_info['score'] < 0) else 'đối phương'}."
                )
                self.event_queue.append({
                    "title": title,
                    "desc": desc,
                    "type": "simple",
                    "effect_text": "Xác nhận"
                })

            if war_is_over:
                victor_tag = tag_a if b_surrenders else tag_b
                defeated_tag = tag_b if b_surrenders else tag_a
                self.resolve_war_peace(victor_tag, defeated_tag, pair)

    def resolve_war_peace(self, victor_tag, defeated_tag, pair):
        import random
        from engine.country_names import get_country_display_name

        c_vic = self.countries[victor_tag]
        c_def = self.countries[defeated_tag]

        # Tắt tình trạng chiến tranh
        c_vic.at_war_with.discard(defeated_tag)
        c_def.at_war_with.discard(victor_tag)
        if pair in self.active_wars:
            del self.active_wars[pair]
        self.needs_map_update = True

        if victor_tag == self.player_tag:
            # Người chơi thắng -> Cho phép chọn hình thức xử lý
            event = {
                "title": "CHIẾN THẮNG TOÀN DIỆN!",
                "desc": f"Quốc gia {get_country_display_name(defeated_tag)} đã hoàn toàn đầu hàng trước sức ép quân sự của ta. Hãy đưa ra quyết sách xử lý đối với họ!",
                "type": "historical",
                "options": [
                    {
                        "name": "Sáp nhập lãnh thổ (Annexation)",
                        "effect_desc": "Họ sẽ bị xóa tên trên bản đồ, toàn bộ đất đai thuộc về ta",
                        "action_type": "annex",
                        "target_tag": defeated_tag,
                        "victor_tag": victor_tag
                    },
                    {
                        "name": "Biến thành chư hầu (Vassalization)",
                        "effect_desc": "Họ trở thành chư hầu, cống nạp và đổi cờ subject",
                        "action_type": "vassal",
                        "target_tag": defeated_tag,
                        "victor_tag": victor_tag
                    },
                    {
                        "name": "Yêu cầu bồi thường chiến phí",
                        "effect_desc": "Nhận 50% ngân khố của họ làm chiến phí (+20 Uy tín)",
                        "action_type": "reparations",
                        "target_tag": defeated_tag,
                        "victor_tag": victor_tag
                    }
                ]
            }
            self.event_queue.append(event)
        elif defeated_tag == self.player_tag:
            # Người chơi bại trận -> AI áp đặt điều khoản
            roll = random.random()
            if roll < 0.25:
                action_type = "annex"
                term_desc = "Sáp nhập toàn bộ lãnh thổ của ta. Trò chơi kết thúc!"
            elif roll < 0.65:
                action_type = "vassal"
                term_desc = f"Ép buộc ta trở thành chư hầu của họ."
            else:
                action_type = "reparations"
                term_desc = f"Buộc ta bồi thường chiến phí lớn (50% ngân khố)."

            opt = {
                "action_type": action_type,
                "victor_tag": victor_tag,
                "target_tag": defeated_tag
            }
            execute_custom_peace_action(self, opt)

            desc = f"Quân đội ta đã hoàn toàn bại trận trước {get_country_display_name(victor_tag)}.\n\nHọ đã áp đặt các điều khoản hòa bình bắt buộc:\n- {term_desc}"
            if action_type == "annex":
                desc += "\n\nBạn đã bị mất hết đất đai! Hãy nhấn Xác nhận để thoát ra sảnh chính."

            self.event_queue.append({
                "title": "THẤT BẠI HOÀN TOÀN!",
                "desc": desc,
                "type": "simple",
                "effect_text": "Xác nhận",
                "is_game_over": (action_type == "annex")
            })
        else:
            # AI đấu với AI -> Tự động giải quyết ngẫu nhiên
            roll = random.random()
            if roll < 0.35:
                action_type = "vassal"
            elif roll < 0.65:
                action_type = "reparations"
            else:
                action_type = "annex"

            opt = {
                "action_type": action_type,
                "victor_tag": victor_tag,
                "target_tag": defeated_tag
            }
            execute_custom_peace_action(self, opt)
            print(f"AI resolved war: {victor_tag} defeated {defeated_tag} via {action_type}")

    def __repr__(self):
        return f"<GameState {self.current_date} player={self.player_tag}>"


def execute_custom_peace_action(game_state, opt):
    action_type = opt.get("action_type")
    victor_tag = opt.get("victor_tag")
    defeated_tag = opt.get("target_tag")

    c_vic = game_state.countries.get(victor_tag)
    c_def = game_state.countries.get(defeated_tag)
    if not c_vic or not c_def:
        return

    if action_type == "annex":
        all_states = [s for s in game_state.states.values() if s.owner == defeated_tag]
        if not all_states:
            return

        if len(all_states) <= 3:
            states_to_annex = all_states
        else:
            bordering_states = []
            for state in all_states:
                is_bordering = False
                for prov in state.provinces:
                    for neighbor_id in getattr(prov, "neighbors", []):
                        neighbor_prov = game_state.provinces.get(neighbor_id)
                        if neighbor_prov and neighbor_prov.owner == victor_tag:
                            is_bordering = True
                            break
                    if is_bordering:
                        break
                if is_bordering:
                    bordering_states.append(state)

            annex_limit = max(3, len(all_states) // 2)
            
            # Milestone: if they are left with <= 3 states, we annex them completely!
            if len(all_states) - annex_limit <= 3:
                states_to_annex = all_states
            else:
                if bordering_states:
                    bordering_scores = []
                    for state in bordering_states:
                        border_count = 0
                        for prov in state.provinces:
                            for neighbor_id in getattr(prov, "neighbors", []):
                                neighbor_prov = game_state.provinces.get(neighbor_id)
                                if neighbor_prov and neighbor_prov.owner == victor_tag:
                                    border_count += 1
                        bordering_scores.append((border_count, state))
                    bordering_scores.sort(key=lambda x: x[0], reverse=True)
                    states_to_annex = [item[1] for item in bordering_scores[:annex_limit]]
                    if len(states_to_annex) < annex_limit:
                        needed = annex_limit - len(states_to_annex)
                        extra_states = [s for s in all_states if s not in states_to_annex]
                        states_to_annex.extend(extra_states[:needed])
                else:
                    states_to_annex = all_states[:annex_limit]

        # 1. Chuyển ownership các bang được chọn
        for state in states_to_annex:
            state.owner = victor_tag
            for b in state.buildings:
                b.owner_tag = victor_tag

        # 2. Chuyển ownership các province của các bang đó
        for state in states_to_annex:
            for prov in state.provinces:
                prov.owner = victor_tag

        # 3. Cập nhật danh sách states trong các Country objects
        for state in states_to_annex:
            c_vic.states[state.name] = state
            c_def.states.pop(state.name, None)

        # 4. Kiểm tra xem có bị sát nhập hoàn toàn hay không
        fully_annexed = (len(c_def.states) == 0)
        
        if fully_annexed:
            c_vic.treasury += max(0, c_def.treasury)
            c_vic.prestige += 50
            
            if defeated_tag in game_state.countries:
                del game_state.countries[defeated_tag]
            if defeated_tag in game_state.countries_data:
                del game_state.countries_data[defeated_tag]

            # Dọn dẹp quan hệ
            for c in game_state.countries.values():
                c.at_war_with.discard(defeated_tag)
                c.relations.pop(defeated_tag, None)
                c.allies.discard(defeated_tag)
                c.subjects.discard(defeated_tag)
                
            print(f"Executed Full Annexation: {defeated_tag} is completely annexed by {victor_tag}")
        else:
            # Cắt đất (sát nhập một phần)
            stolen_treasury = int(max(0, c_def.treasury) * (len(states_to_annex) / (len(states_to_annex) + len(c_def.states))))
            c_def.treasury -= stolen_treasury
            c_vic.treasury += stolen_treasury
            c_vic.prestige += 20
            
            # Cập nhật dân số và gdp của các country
            c_vic.population = sum(s.population for s in c_vic.states.values())
            c_vic.gdp = sum(s.gdp for s in c_vic.states.values())
            c_def.population = sum(s.population for s in c_def.states.values())
            c_def.gdp = sum(s.gdp for s in c_def.states.values())
            
            # Hòa giải
            c_vic.at_war_with.discard(defeated_tag)
            c_def.at_war_with.discard(victor_tag)
            c_vic.relations[defeated_tag] = -50
            c_def.relations[victor_tag] = -50
            
            print(f"Executed Partial Annexation: {victor_tag} annexed {len(states_to_annex)} states from {defeated_tag}")

        game_state.needs_map_update = True

    elif action_type == "vassal":
        c_vic.subjects.add(defeated_tag)
        c_vic.prestige += 30
        c_vic.relations[defeated_tag] = 20
        c_def.relations[victor_tag] = 20
        print(f"Executed Vassalization: {defeated_tag} became subject of {victor_tag}")

    elif action_type == "reparations":
        amount = int(max(0, c_def.treasury) * 0.5)
        c_def.treasury -= amount
        c_vic.treasury += amount
        c_vic.prestige += 20
        c_vic.relations[defeated_tag] = -10
        c_def.relations[victor_tag] = -10
        print(f"Executed Reparations: {victor_tag} took {amount}L from {defeated_tag}")