filepath = "game_ui.py"
with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add global variables at the top (only first occurrence)
code = code.replace(
    "diplomacy_selected_tag = None",
    "diplomacy_selected_tag = None\nshow_countries_list = False\nleaderboard_sort_by = 'prestige'\nleaderboard_sort_desc = True\n_countries_list_scroll = 0\n_leaderboard_cache = []",
    1
)

# 2. Modify draw_leaderboard function and cache system
old_draw_leaderboard = """def draw_leaderboard(screen, fonts, game_state, x=16, y=16, width=260, max_rows=6):
    sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.gdp, reverse=True)"""

new_draw_leaderboard = """_leaderboard_cache = []

def update_leaderboard_cache(game_state):
    global _leaderboard_cache
    _leaderboard_cache = sorted(game_state.countries.values(), key=lambda c: c.gdp, reverse=True)

def draw_leaderboard(screen, fonts, game_state, x=16, y=16, width=260, max_rows=6):
    global _leaderboard_cache
    if not _leaderboard_cache:
        update_leaderboard_cache(game_state)
    sorted_countries = _leaderboard_cache"""

code = code.replace(old_draw_leaderboard, new_draw_leaderboard)

# 2b. Implement build panel using selected_state and actual building levels
old_draw_build_panel = """def draw_build_panel(screen, fonts, game_state):
    \"\"\"Panel xây dựng công trình - gọi khi nhấn B\"\"\"
    global show_build_panel
    
    sw, sh = screen.get_size()
    panel_w, panel_h = 300, 280
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    panel(screen, panel_x, panel_y, panel_w, panel_h, 250)
    text(screen, fonts, "med", "XÂY DỰNG CÔNG TRÌNH", panel_x + 10, panel_y + 10, C_GOLD)
    
    country = game_state.player_country
    if not country:
        return
    
    buildings = [
        ("🌾 Nông trại", 50, "Tăng lương thực & dân số"),
        ("⛏️ Mỏ", 100, "Khai thác than/sắt"),
        ("🏭 Nhà máy", 200, "Sản xuất hàng hóa"),
        ("🎓 Đại học", 300, "Tăng học thức & nghiên cứu"),
        ("🏛️ Doanh trại", 150, "Tăng quân đội"),
    ]
    
    y = panel_y + 45
    for name, cost, desc in buildings:
        can_build = country.treasury >= cost
        btn = pygame.Rect(panel_x + 10, y, panel_w - 20, 38)
        hover = btn.collidepoint(pygame.mouse.get_pos())
        
        # Màu nút
        if hover and can_build:
            color = (50, 120, 70)
        elif can_build:
            color = (40, 90, 55)
        else:
            color = (50, 50, 50)
        
        pygame.draw.rect(screen, color, btn, border_radius=4)
        pygame.draw.rect(screen, C_GOLD if can_build else C_GREY, btn, 1, border_radius=4)
        
        text(screen, fonts, "sm", name, panel_x + 20, y + 11, C_WHITE)
        cost_text = f"£{cost}"
        text(screen, fonts, "sm", cost_text, panel_x + panel_w - 60, y + 11, 
             C_GREEN if can_build else C_RED)
        
        if hover and can_build and pygame.mouse.get_pressed()[0]:
            country.treasury -= cost
            # TODO: Thêm building vào state
            print(f"Built {name}")
            pygame.time.wait(200)
        
        y += 45
    
    # Nút đóng
    close_btn = pygame.Rect(panel_x + panel_w - 35, panel_y + 8, 28, 28)
    if close_btn.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
        show_build_panel = False
        pygame.time.wait(200)
    pygame.draw.rect(screen, (120, 40, 40), close_btn, border_radius=4)
    text(screen, fonts, "med", "X", close_btn.x + 8, close_btn.y + 5, C_WHITE)"""

new_draw_build_panel = """def draw_build_panel(screen, fonts, game_state, selected_state=None):
    \"\"\"Panel xây dựng công trình - gọi khi nhấn B. Trả về True nếu cần đóng panel.\"\"\"
    global show_build_panel
    sw, sh = screen.get_size()
    panel_w, panel_h = 350, 320
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    panel(screen, panel_x, panel_y, panel_w, panel_h, 250)
    text(screen, fonts, "med", "XÂY DỰNG CÔNG TRÌNH", panel_x + 10, panel_y + 10, C_GOLD)
    
    country = game_state.player_country
    if not country:
        return False
        
    # Nút đóng
    close_btn = pygame.Rect(panel_x + panel_w - 35, panel_y + 8, 28, 28)
    close_hov = close_btn.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(screen, (160, 45, 45) if close_hov else (120, 40, 40), close_btn, border_radius=4)
    text(screen, fonts, "med", "X", close_btn.x + 10, close_btn.y + 5, C_WHITE)
    if close_hov and pygame.mouse.get_pressed()[0]:
        show_build_panel = False
        pygame.time.wait(200)
        return True

    if not selected_state:
        text(screen, fonts, "sm", "Vui lòng chọn 1 bang trên bản đồ", panel_x + 20, panel_y + 120, C_GREY)
        text(screen, fonts, "sm", "trước khi xây dựng!", panel_x + 20, panel_y + 145, C_GREY)
        return False
        
    if selected_state.owner != game_state.player_tag:
        text(screen, fonts, "sm", "Bạn chỉ có thể xây dựng trên", panel_x + 20, panel_y + 120, C_RED)
        text(screen, fonts, "sm", "các bang thuộc chủ quyền của mình!", panel_x + 20, panel_y + 145, C_RED)
        state_owner = selected_state.owner or "Không rõ"
        text(screen, fonts, "sm", f"Bang này thuộc: {get_country_display_name(state_owner, state_owner)}", panel_x + 20, panel_y + 175, C_GREY)
        return False

    text(screen, fonts, "sm", f"Xây dựng tại: {selected_state.display_name}", panel_x + 10, panel_y + 35, C_GREY)

    # Khai báo các loại công trình (Tên hiển thị, Giá, type, Mô tả)
    buildings = [
        ("[FARM] Nong trai", 50, "farm", "Tang luong thuc & dan so"),
        ("[MINE] Mo", 100, "mine", "Khai thac than/sat"),
        ("[FACT] Nha may", 200, "factory", "San xuat hang hoa"),
        ("[UNIV] Dai hoc", 300, "university", "Tang hoc thuc & nghien cuu"),
        ("[BARR] Doanh trai", 150, "barracks", "Tang quan doi"),
    ]
    
    y = panel_y + 65
    for name, cost, btype, desc in buildings:
        can_build = country.treasury >= cost
        btn = pygame.Rect(panel_x + 10, y, panel_w - 20, 42)
        
        bg_col = (40, 90, 55) if can_build else (50, 50, 50)
        border_col = C_GOLD if can_build else C_GREY
        text_col = C_WHITE
        
        hover = btn.collidepoint(pygame.mouse.get_pos())
        if hover and can_build:
            bg_col = (50, 120, 70)
            
        pygame.draw.rect(screen, bg_col, btn, border_radius=4)
        pygame.draw.rect(screen, border_col, btn, 1, border_radius=4)
        
        # Vẽ chữ và giá trị lên nút
        text(screen, fonts, "sm", name, panel_x + 20, y + 13, C_WHITE)
        cost_text = f"£{cost}"
        text(screen, fonts, "sm", cost_text, panel_x + panel_w - 65, y + 13, 
             C_GOLD if can_build else C_RED)
        
        if hover and can_build and pygame.mouse.get_pressed()[0]:
            country.treasury -= cost
            selected_state.add_building(btype)
            print(f"Built {btype} in state {selected_state.name}, cost: £{cost}")
            game_state.last_event = {
                "title": "XÂY DỰNG XONG",
                "desc": f"Đã xây dựng {name} tại bang {selected_state.display_name}.",
                "effect_text": f"Ngân khố -£{cost}"
            }
            pygame.time.wait(200)
        
        y += 48
    return False"""

code = code.replace(old_draw_build_panel, new_draw_build_panel)

# 2c. Modify draw_sidebar function signature and usage
old_draw_sidebar = """def draw_sidebar(screen, fonts, tag, game_state, screen_h):"""

new_draw_sidebar = """def draw_sidebar(screen, fonts, tag, game_state, screen_h, selected_state=None):"""

code = code.replace(old_draw_sidebar, new_draw_sidebar)

# Draw selected state information in sidebar if present
old_sidebar_hints = """    # Hints gọn
    for i, txt in enumerate(["SPACE: Next Turn", "F2: Ngoại giao", "B: Xây dựng"]):
        hs = fonts["sm"].render(txt,True,(80,90,110))
        screen.blit(hs,(x+10, screen_h-40+i*16))"""

new_sidebar_hints = """    if selected_state:
        state_title = selected_state.display_name
        y = row(screen, fonts, x, y, "Bang dang chon", state_title, C_GOLD)
        
        from engine.state_resource_loader import format_resources
        if selected_state.provinces:
            first_prov_color = selected_state.provinces[0].color
            from engine.state_resource_loader import _color_to_state_cache
            state_info = _color_to_state_cache.get(first_prov_color)
            if state_info:
                res_lines = format_resources(state_info)
                for line in res_lines[:3]:
                    text(screen, fonts, "sm", f" {line}", x + 10, y, C_WHITE)
                    y += 18
                y += 4
        
        farms = len(selected_state.get_buildings_by_type("farm"))
        mines = len(selected_state.get_buildings_by_type("mine"))
        factories = len(selected_state.get_buildings_by_type("factory"))
        univ = len(selected_state.get_buildings_by_type("university"))
        barracks = len(selected_state.get_buildings_by_type("barracks"))
        
        b_summary = []
        if farms > 0: b_summary.append(f"Nông trại Lvl {farms}")
        if mines > 0: b_summary.append(f"Mỏ Lvl {mines}")
        if factories > 0: b_summary.append(f"Nhà máy Lvl {factories}")
        if univ > 0: b_summary.append(f"Đại học Lvl {univ}")
        if barracks > 0: b_summary.append(f"Doanh trại Lvl {barracks}")
        
        if b_summary:
            text(screen, fonts, "sm", " Công trình:", x + 10, y, C_GOLD_DIM)
            y += 18
            for b_line in b_summary[:3]:
                text(screen, fonts, "sm", f"  * {b_line}", x + 10, y, C_GREY)
                y += 18
        else:
            y = row(screen, fonts, x, y, " Công trình", "Chưa có", C_GREY)

    # Hints gọn
    for i, txt in enumerate(["SPACE: Next Turn", "F2: Ngoại giao", "F3: BXH quoc gia", "B: Xây dựng"]):
        hs = fonts["sm"].render(txt,True,(80,90,110))
        screen.blit(hs,(x+10, screen_h-70+i*16))"""

code = code.replace(old_sidebar_hints, new_sidebar_hints)


# 3. Add draw_countries_list_panel function right before "# ── GAME ─────────────────────────────────────────────"
countries_list_panel_code = """def draw_countries_list_panel(screen, fonts, game_state, mouse_pos):
    global show_countries_list, leaderboard_sort_by, leaderboard_sort_desc, _countries_list_scroll
    
    sw, sh = screen.get_size()
    PW, PH = 640, 500
    px = (sw - PW) // 2
    py = (sh - PH) // 2

    # Draw panel background
    panel(screen, px, py, PW, PH, 250)
    
    # Close button
    close_btn = pygame.Rect(px + PW - 36, py + 8, 28, 28)
    close_hov = close_btn.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (160, 45, 45) if close_hov else (90, 30, 30), close_btn, border_radius=5)
    pygame.draw.rect(screen, C_GOLD_DIM, close_btn, 1, border_radius=5)
    xs = fonts["med"].render("X", True, C_WHITE)
    screen.blit(xs, xs.get_rect(center=close_btn.center))
    if close_hov and pygame.mouse.get_pressed()[0]:
        show_countries_list = False
        pygame.time.wait(200)
        return close_btn

    # Title
    title_text = fonts["title"].render("DANH SÁCH QUỐC GIA (COUNTRIES MAP LIST)", True, C_GOLD)
    screen.blit(title_text, (px + 16, py + 10))
    
    pygame.draw.line(screen, C_GOLD_DIM, (px + 8, py + 42), (px + PW - 8, py + 42))

    # Column Headers (Rank, Country, Prestige, GDP, SoL, Population)
    headers = [
        ("Rank", 50, None),
        ("Country", 180, None),
        ("Prestige", 85, "prestige"),
        ("GDP", 95, "gdp"),
        ("SoL", 70, "sol"),
        ("Population", 110, "population")
    ]
    
    hx = px + 12
    hy = py + 48
    
    for label, width, sort_key in headers:
        rect = pygame.Rect(hx, hy, width, 24)
        if sort_key:
            bg_col = (40, 55, 75) if leaderboard_sort_by == sort_key else (25, 35, 45)
            hover = rect.collidepoint(mouse_pos)
            if hover:
                bg_col = (60, 80, 105)
            pygame.draw.rect(screen, bg_col, rect, border_radius=3)
            pygame.draw.rect(screen, C_BORDER, rect, 1, border_radius=3)
            
            # Click to sort
            if hover and pygame.mouse.get_pressed()[0]:
                if leaderboard_sort_by == sort_key:
                    leaderboard_sort_desc = not leaderboard_sort_desc
                else:
                    leaderboard_sort_by = sort_key
                    leaderboard_sort_desc = True
                pygame.time.wait(200)
        else:
            pygame.draw.rect(screen, (20, 28, 38), rect, border_radius=3)
            pygame.draw.rect(screen, C_BORDER, rect, 1, border_radius=3)
            
        lbl_surf = fonts["sm"].render(label, True, C_GOLD if leaderboard_sort_by == sort_key else C_WHITE)
        screen.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))
        hx += width + 4
        
    pygame.draw.line(screen, C_GOLD_DIM, (px + 8, py + 76), (px + PW - 8, py + 76))
    
    # Sort and prepare country list
    countries = list(game_state.countries.values())
    for c in countries:
        c.derived_sol = 10.0 + c.literacy * 15.0 + (c.gdp / max(0.1, c.population)) * 2.0
        
    if leaderboard_sort_by == "prestige":
        countries.sort(key=lambda c: c.prestige, reverse=leaderboard_sort_desc)
    elif leaderboard_sort_by == "gdp":
        countries.sort(key=lambda c: c.gdp, reverse=leaderboard_sort_desc)
    elif leaderboard_sort_by == "sol":
        countries.sort(key=lambda c: c.derived_sol, reverse=leaderboard_sort_desc)
    elif leaderboard_sort_by == "population":
        countries.sort(key=lambda c: c.population, reverse=leaderboard_sort_desc)

    # Render List
    list_y = py + 82
    row_h = 28
    visible_rows = 14
    
    list_clip_rect = pygame.Rect(px + 8, list_y, PW - 16, row_h * visible_rows)
    old_clip = screen.get_clip()
    screen.set_clip(list_clip_rect)
    
    max_scroll = max(0, (len(countries) - visible_rows) * row_h)
    _countries_list_scroll = max(0, min(_countries_list_scroll, max_scroll))
    
    start_idx = _countries_list_scroll // row_h
    offset_y = _countries_list_scroll % row_h
    
    for idx in range(start_idx, min(len(countries), start_idx + visible_rows + 1)):
        c = countries[idx]
        rank = idx + 1 if leaderboard_sort_desc else len(countries) - idx
        
        ry = list_y + (idx - start_idx) * row_h - offset_y
        row_rect = pygame.Rect(px + 12, ry, PW - 24, row_h - 2)
        
        if c.tag == game_state.player_tag:
            bg_col = (45, 75, 45)
        elif row_rect.collidepoint(mouse_pos):
            bg_col = (30, 40, 55)
        else:
            bg_col = (18, 25, 34) if idx % 2 == 0 else (14, 20, 28)
            
        pygame.draw.rect(screen, bg_col, row_rect, border_radius=4)
        pygame.draw.rect(screen, C_BORDER, row_rect, 1, border_radius=4)
        
        # Column values
        rank_text = fonts["sm"].render(f"#{rank}", True, C_GOLD if rank <= 3 else C_GREY)
        screen.blit(rank_text, rank_text.get_rect(center=(px + 12 + 25, ry + row_h//2)))
        
        name_x = px + 12 + 50 + 6
        flag_rect = pygame.Rect(name_x, ry + 4, 24, 18)
        tc = (100, 100, 100)
        raw = game_state.countries_data.get(c.tag)
        if raw:
            try:
                tc = tuple(int(v) for v in raw[:3])
            except:
                pass
        pygame.draw.rect(screen, tc, flag_rect, border_radius=2)
        pygame.draw.rect(screen, C_GOLD_DIM, flag_rect, 1, border_radius=2)
        
        c_name = get_country_display_name(c.tag, c.tag)
        if len(c_name) > 16:
            c_name = c_name[:14] + ".."
        name_text = fonts["sm"].render(c_name, True, C_WHITE)
        screen.blit(name_text, (name_x + 30, ry + 5))
        
        pres_text = fonts["sm"].render(f"{c.prestige:.0f}", True, C_WHITE)
        screen.blit(pres_text, pres_text.get_rect(center=(px + 12 + 230 + 42, ry + row_h//2)))
        
        gdp_val = f"{c.gdp:.1f}M" if c.gdp < 1000 else f"{c.gdp/1000:.2f}B"
        gdp_text = fonts["sm"].render(gdp_val, True, (180, 220, 255))
        screen.blit(gdp_text, gdp_text.get_rect(center=(px + 12 + 319 + 47, ry + row_h//2)))
        
        sol_text = fonts["sm"].render(f"{c.derived_sol:.1f}", True, (220, 200, 140))
        screen.blit(sol_text, sol_text.get_rect(center=(px + 12 + 418 + 35, ry + row_h//2)))
        
        pop_val = f"{c.population:.1f}M"
        pop_text = fonts["sm"].render(pop_val, True, C_GREEN)
        screen.blit(pop_text, pop_text.get_rect(center=(px + 12 + 492 + 55, ry + row_h//2)))
        
    screen.set_clip(old_clip)
    return close_btn


"""

code = code.replace("# ── GAME ─────────────────────────────────────────────", countries_list_panel_code + "# ── GAME ─────────────────────────────────────────────")

# 4. In run_game, declare globals and initialize selected_state
code = code.replace(
    "    global show_diplomacy, diplomacy_selected_tag, current_map_mode",
    "    global show_diplomacy, diplomacy_selected_tag, current_map_mode, show_countries_list, _countries_list_scroll, leaderboard_sort_by, leaderboard_sort_desc"
)
code = code.replace(
    "    current_map_mode = MAP_MODE_POLITICAL\n    show_build_panel = False",
    "    current_map_mode = MAP_MODE_POLITICAL\n    show_build_panel = False\n    selected_state = None"
)

# 5. F2 and F3 Key handlers
old_key_f2 = """                elif event.key == pygame.K_F2:
                    show_diplomacy = not show_diplomacy"""

new_key_f2_f3 = """                elif event.key == pygame.K_F2:
                    show_diplomacy = not show_diplomacy
                elif event.key == pygame.K_F3:
                    show_countries_list = not show_countries_list"""

code = code.replace(old_key_f2, new_key_f2_f3)

# 5b. Update next_turn to update cache
code = code.replace(
    "                    game_state.next_turn()\n                    next_turn_cooldown = 10",
    "                    game_state.next_turn()\n                    update_leaderboard_cache(game_state)\n                    next_turn_cooldown = 10"
)
code = code.replace(
    "                game_state.next_turn()\n                next_turn_cooldown = 10",
    "                game_state.next_turn()\n                update_leaderboard_cache(game_state)\n                next_turn_cooldown = 10"
)

# 6. Mouse wheel scrolling
old_mouse_wheel = """            elif event.type == pygame.MOUSEWHEEL:
                oz = zoom
                zoom = max(init_zoom, min(zoom * (1.2 if event.y > 0 else 1 / 1.2), ZOOM_MAX))
                if oz != zoom:
                    mx, my = pygame.mouse.get_pos()
                    cam_x = mx - (mx - cam_x) * (zoom / oz)
                    cam_y = my - (my - cam_y) * (zoom / oz)
                    cam_x, cam_y = clamp(cam_x, cam_y)
                    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))"""

new_mouse_wheel = """            elif event.type == pygame.MOUSEWHEEL:
                if show_countries_list:
                    import game_ui as _gui_ref
                    _gui_ref._countries_list_scroll = max(0, _gui_ref._countries_list_scroll - event.y * 30)
                else:
                    oz = zoom
                    zoom = max(init_zoom, min(zoom * (1.2 if event.y > 0 else 1 / 1.2), ZOOM_MAX))
                    if oz != zoom:
                        mx, my = pygame.mouse.get_pos()
                        cam_x = mx - (mx - cam_x) * (zoom / oz)
                        cam_y = my - (my - cam_y) * (zoom / oz)
                        cam_x, cam_y = clamp(cam_x, cam_y)
                        sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))"""

code = code.replace(old_mouse_wheel, new_mouse_wheel)

# 7. Mouse button down overlays collision check
old_mouse_down = """            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex, ey = event.pos
                if event.button == 1:  # Left click - chọn quốc gia
                    if ex < sw - SIDEBAR_W and ey < sh - HUD_H:"""

new_mouse_down = """            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex, ey = event.pos
                
                # Check UI collisions
                on_ui = False
                if show_build_panel:
                    build_panel_rect = pygame.Rect((sw - 350) // 2, (sh - 320) // 2, 350, 320)
                    if build_panel_rect.collidepoint(ex, ey):
                        on_ui = True
                if show_diplomacy:
                    diplo_panel_rect = pygame.Rect((sw - DIPLOMACY_PANEL_W) // 2, (sh - DIPLOMACY_PANEL_H) // 2, DIPLOMACY_PANEL_W, DIPLOMACY_PANEL_H)
                    if diplo_panel_rect.collidepoint(ex, ey):
                        on_ui = True
                if show_countries_list:
                    countries_panel_rect = pygame.Rect((sw - 640) // 2, (sh - 500) // 2, 640, 500)
                    if countries_panel_rect.collidepoint(ex, ey):
                        on_ui = True
                leaderboard_rect = pygame.Rect(16, 16, 260, 154)
                if leaderboard_rect.collidepoint(ex, ey):
                    on_ui = True
                    if not show_countries_list and not show_diplomacy and not show_build_panel:
                        show_countries_list = True
                        pygame.time.wait(200)
                menu_rect = pygame.Rect(sw - SIDEBAR_W - 110, 8, 100, 30)
                if menu_rect.collidepoint(ex, ey):
                    on_ui = True

                if event.button == 1:  # Left click - chọn quốc gia
                    if not on_ui and ex < sw - SIDEBAR_W and ey < sh - HUD_H:"""

code = code.replace(old_mouse_down, new_mouse_down)

# 8. Left click province selection state and fast lookup bug fix to use prov.color instead of rgb
old_left_click_lookup = """                            owner = getattr(prov, "owner", None) if prov else None
                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                print(f"Selected: {owner} (left click)")"""

new_left_click_lookup = """                            owner = getattr(prov, "owner", None) if prov else None
                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                # Fast O(1) lookup using pre-built index
                                selected_state = _province_to_state_fast.get(prov.color) if prov else None
                                print(f"Selected: {owner} (left click), State: {selected_state.name if selected_state else 'None'}")"""

code = code.replace(old_left_click_lookup, new_left_click_lookup)

# 9. Right click block if clicked on UI overlay, and state selection bug fix to use prov.color instead of rgb
old_right_click = """                elif event.button == 3:  # Right click - mở diplomacy
                    if ex < sw - SIDEBAR_W and ey < sh - HUD_H:"""

new_right_click = """                elif event.button == 3:  # Right click - mở diplomacy
                    if not on_ui and ex < sw - SIDEBAR_W and ey < sh - HUD_H:"""

code = code.replace(old_right_click, new_right_click)

old_right_click_lookup = """                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                show_diplomacy = True
                                print(f"Selected: {owner} (right click) - Diplomacy panel opened")"""

new_right_click_lookup = """                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                show_diplomacy = True
                                selected_state = _province_to_state_fast.get(prov.color) if prov else None
                                print(f"Selected: {owner} (right click) - Diplomacy opened")"""

code = code.replace(old_right_click_lookup, new_right_click_lookup)

# 9c. Render build panel with parameters
code = code.replace("draw_build_panel(screen, fonts, game_state)", "draw_build_panel(screen, fonts, game_state, selected_state)")
code = code.replace("draw_sidebar(screen, fonts, sel_tag, game_state, sh)", "draw_sidebar(screen, fonts, sel_tag, game_state, sh, selected_state)")

# 10. Render countries list panel if open
old_diplomacy_render = """        # Diplomacy Panel
        if show_diplomacy:
            close_btn = draw_diplomacy_panel(screen, fonts, game_state, (mx, my))
            if close_btn.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                show_diplomacy = False
                pygame.time.wait(200)"""

new_diplomacy_countries_render = """        # Diplomacy Panel
        if show_diplomacy:
            close_btn = draw_diplomacy_panel(screen, fonts, game_state, (mx, my))
            if close_btn.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                show_diplomacy = False
                pygame.time.wait(200)

        # Countries List Panel
        if show_countries_list:
            close_btn = draw_countries_list_panel(screen, fonts, game_state, (mx, my))
            if close_btn.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                show_countries_list = False
                pygame.time.wait(200)"""

code = code.replace(old_diplomacy_render, new_diplomacy_countries_render)

# 11. Add F3 helper in help bar
code = code.replace("F2: Diplomacy | L-Click: Select | R-Click: Select & Diplomacy", "SPACE: Turn | F2: Ngoai giao | F3: BXH quoc gia | 1: Ban do CT | 2: Ban do Bang | B: Xay dung | L/R-Click")

# 12. Fix draw_province_tooltip to use prov.color instead of rgb
old_tooltip_state = """    state = get_state_for_province(rgb)"""
new_tooltip_state = """    state = get_state_for_province(prov.color) if prov else None"""
code = code.replace(old_tooltip_state, new_tooltip_state)

# 13. Optimize startup routine in start_engine to avoid duplicate generation and unused textures
old_startup = """    print("Generating political map...")
    pol_map = generate_political_map(original_map, color_to_province,
                                     game_state.countries_data, countries_full)
    
    print("Generating combined political map with country names...")
    combined_political = generate_combined_political_map(original_map, color_to_province,
                                                          game_state.countries_data, 
                                                          countries_full, fonts)
    
    print("Generating province map...")
    province_map = generate_political_map(original_map, color_to_province,
                                           game_state.countries_data, countries_full,
                                           mode=MAP_MODE_PROVINCE_NAMES)
    province_name_surface = generate_province_name_map(original_map, color_to_province, fonts)
    combined_province = province_map.copy()
    combined_province.blit(province_name_surface, (0, 0))
    
    print("Generating country name map...")
    country_name_surface = generate_country_name_map(original_map, color_to_province,
                                                      game_state.countries_data, fonts)
    
    print("Generating province name map...")
    province_name_surface = generate_province_name_map(original_map, color_to_province, fonts)"""

new_startup = """    print("Generating country name map...")
    country_names = generate_country_name_map(original_map, color_to_province,
                                              game_state.countries_data, fonts)
    country_name_surface = country_names

    print("Generating political map...")
    pol_map = generate_political_map(original_map, color_to_province,
                                     game_state.countries_data, countries_full)
    
    print("Generating combined political map...")
    combined_political = pol_map.copy()
    combined_political.blit(country_names, (0, 0))

    # Generate state-level map (Victoria 3 style) - used for key 2
    print("Generating state-level map...")
    state_level_map = generate_state_level_map(original_map, color_to_province, game_state)
    # Add country names on top
    state_level_map.blit(country_names, (0, 0))

    # Build fast province-to-state lookup index
    print("Building province-state lookup...")
    build_province_state_lookup(game_state)
    
    # Initialize leaderboard cache
    print("Initializing leaderboard cache...")
    update_leaderboard_cache(game_state)"""

code = code.replace(old_startup, new_startup)

code = code.replace("run_game(screen, fonts, game_state, original_map, pol_map,\n                 color_to_province, init_zoom, country_name_surface, province_name_surface)",
                    "run_game(screen, fonts, game_state, original_map, pol_map,\n                 color_to_province, init_zoom, combined_political, state_level_map)")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully applied changes to game_ui.py!")
