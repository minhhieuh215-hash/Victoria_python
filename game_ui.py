import pygame
import numpy as np
import sys
import os

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
SIDEBAR_W  = 280
HUD_H      = 48
COLOR_BG        = (15,  18,  28)
COLOR_PANEL     = (22,  28,  42)
COLOR_PANEL2    = (28,  36,  54)
COLOR_BORDER    = (58,  72, 100)
COLOR_GOLD      = (200, 165,  60)
COLOR_GOLD_DIM  = (120, 100,  40)
COLOR_SEA       = (19,  41,  63)
COLOR_WHITE     = (230, 235, 245)
COLOR_GREY      = (130, 140, 160)
COLOR_GREEN     = ( 80, 200, 120)
COLOR_RED       = (220,  80,  80)

MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

COUNTRY_NAMES = {
    "GBR":"Great Britain",    "FRA":"France",           "RUS":"Russia",
    "GER":"Germany",          "AUS":"Austria",          "PRU":"Prussia",
    "USA":"United States",    "JAP":"Japan",            "CHI":"China",
    "TUR":"Ottoman Empire",   "SPA":"Spain",            "POR":"Portugal",
    "ITA":"Italy",            "SCA":"Scandinavia",      "NET":"Netherlands",
    "BEL":"Belgium",          "SWI":"Switzerland",      "HBC":"Hudson Bay Co.",
    "BRZ":"Brazil",           "ARG":"Argentina",        "MEX":"Mexico",
    "PER":"Persia",           "EGY":"Egypt",            "ETH":"Ethiopia",
    "MAD":"Madagascar",       "MOR":"Morocco",          "TUN":"Tunisia",
    "TRI":"Tripoli",          "SOK":"Sokoto",           "ZUL":"Zulu Kingdom",
    "NEP":"Nepal",            "BUR":"Burma",            "SIA":"Siam",
    "DAI":"Dai Nam",          "KOR":"Korea",            "CAN":"Canada",
    "CHL":"Chile",            "CLM":"Colombia",         "GRE":"Greece",
    "SER":"Serbia",           "MON":"Montenegro",       "HAI":"Haiti",
    "HAN":"Hannover",         "SAX":"Saxony",           "BAV":"Bavaria",
    "NOR":"Norway",           "DEN":"Denmark",          "SWE":"Sweden",
    "DEI":"Dutch East Indies","PHI":"Philippines",      "PAN":"Punjab",
    "AFG":"Afghanistan",      "BOL":"Bolivia",          "VNZ":"Venezuela",
    "UPP":"Upper Peru",       "PAR":"Paraguay",         "URU":"Uruguay",
    "ICE":"Iceland",          "FIN":"Finland",          "POL":"Poland",
    "ROM":"Romania",          "BUL":"Bulgaria",         "ALB":"Albania",
}

COUNTRY_POP = {
    "GBR":25.0,"FRA":33.0,"RUS":60.0,"GER":30.0,"AUS":35.0,"PRU":14.0,
    "USA":15.0,"CHI":400.0,"JAP":30.0,"TUR":25.0,"SPA":12.0,"BRZ":7.0,
    "ITA":22.0,"SCA":4.0,"NET":3.0,"MEX":7.0,"PER":9.0,"EGY":4.0,
    "ETH":5.0,"MOR":4.0,"NEP":5.0,"BUR":8.0,"SIA":5.0,"KOR":8.0,
    "DAI":8.0,"HBC":0.1,"CAN":1.5,"ARG":0.8,"GRE":0.8,"SER":1.0,
    "DEI":30.0,"CHI":400.0,"POR":3.5,"BEL":4.0,"NET":3.0,
}


# ─────────────────────────────────────────────
#  FONT HELPER
# ─────────────────────────────────────────────
def load_fonts():
    candidates = ['Georgia', 'Times New Roman', 'Palatino', 'serif', 'arial']
    serif = None
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, 12)
            if f: serif = name; break
        except: pass
    serif = serif or 'arial'
    return {
        'title' : pygame.font.SysFont(serif, 22, bold=True),
        'med'   : pygame.font.SysFont(serif, 16, bold=True),
        'sm'    : pygame.font.SysFont(serif, 13),
        'hud'   : pygame.font.SysFont(serif, 17, bold=True),
        'date'  : pygame.font.SysFont(serif, 20, bold=True),
        'big'   : pygame.font.SysFont(serif, 26, bold=True),
    }


# ─────────────────────────────────────────────
#  MAP GENERATION
# ─────────────────────────────────────────────
def load_flags_cache(base_dir):
    """Parse flags: Flag_TAG.png hoặc Flag_TAG_chedo.png -> {TAG: {mode: Surface}}"""
    flags_cache = {}
    flags_dir = os.path.join(base_dir, "data", "flags")
    if not os.path.exists(flags_dir):
        os.makedirs(flags_dir)
        return flags_cache
    for filename in os.listdir(flags_dir):
        if not filename.endswith(".png"): continue
        parts = filename[:-4].split("_")
        if len(parts) < 2 or parts[0].lower() != "flag": continue
        tag  = parts[1].upper()
        mode = "_".join(parts[2:]) if len(parts) > 2 else "default"
        try:
            img = pygame.image.load(os.path.join(flags_dir, filename)).convert_alpha()
            if tag not in flags_cache: flags_cache[tag] = {}
            flags_cache[tag][mode] = img
        except: pass
    print(f"Nap flags: {len(flags_cache)} quoc gia")
    return flags_cache

def get_flag(flags_cache, tag, mode="default", size=(72,48)):
    entry = flags_cache.get(tag, {})
    img = entry.get(mode) or entry.get("default") or None
    if img: return pygame.transform.scale(img, size)
    return None

GOVTS = [
    ("default",           "Mac dinh"),
    ("absolute_monarchy", "Quan chu chuyen che"),
    ("republic",          "Cong hoa"),
    ("dictatorship",      "Doc tai"),
    ("theocracy",         "Than quyen"),
    ("communist",         "Cong san"),
]
# ─── FLAGS HELPERS ───
flags_cache_ref = {}   # global ref, set bởi start_engine

def _avail_modes(cache, tag):
    """Các chế độ có cờ cho TAG này, luôn có 'default' đầu tiên."""
    entry = cache.get(tag, {})
    modes = sorted(entry.keys())
    if "default" in modes:
        modes.remove("default")
        modes = ["default"] + modes
    return modes if modes else ["default"]

def _mode_label(mode):
    labels = {
        "default":           "Mac dinh",
        "absolute_monarchy": "Quan chu chuyen che",
        "republic":          "Cong hoa",
        "dictatorship":      "Doc tai",
        "theocracy":         "Than quyen",
        "communist":         "Cong san",
        "fascist":           "Phat xit",
        "subject":           "Phu thuoc",
    }
    return labels.get(mode, mode.replace("_"," ").title())




def generate_political_map(original_image, color_to_province, countries_data):
    print("Đang tô màu bản đồ...")
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    H, W, _ = arr.shape
    color_lookup = {}
    for rgb_tuple, prov in color_to_province.items():
        if getattr(prov, 'is_sea', False):
            color_lookup[rgb_tuple] = COLOR_SEA
        elif getattr(prov, 'is_lake', False):
            color_lookup[rgb_tuple] = (26, 128, 128)
        else:
            owner_tag = getattr(prov, 'owner', None)
            if owner_tag and owner_tag in countries_data:
                color_lookup[rgb_tuple] = tuple(int(v) for v in countries_data[owner_tag][:3])
            else:
                color_lookup[rgb_tuple] = (26, 128, 128)

    arr_u32 = (arr[:,:,0].astype(np.uint32)*65536 +
               arr[:,:,1].astype(np.uint32)*256 +
               arr[:,:,2].astype(np.uint32))
    lut_r = np.zeros(16777216, dtype=np.uint8)
    lut_g = np.zeros(16777216, dtype=np.uint8)
    lut_b = np.zeros(16777216, dtype=np.uint8)
    in_lookup = np.zeros(16777216, dtype=bool)
    for (r,g,b),(nr,ng,nb) in color_lookup.items():
        k = r*65536+g*256+b
        lut_r[k]=nr; lut_g[k]=ng; lut_b[k]=nb; in_lookup[k]=True
    mask = in_lookup[arr_u32]
    result = np.stack([
        np.where(mask, lut_r[arr_u32], arr[:,:,0]),
        np.where(mask, lut_g[arr_u32], arr[:,:,1]),
        np.where(mask, lut_b[arr_u32], arr[:,:,2]),
    ], axis=2)
    surf = pygame.surfarray.make_surface(result.transpose(1,0,2))
    print("-> Hoàn tất!")
    return surf


# ─────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────
def draw_panel(screen, x, y, w, h, alpha=230, border=True):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*COLOR_PANEL, alpha))
    screen.blit(s, (x, y))
    if border:
        pygame.draw.rect(screen, COLOR_BORDER, (x, y, w, h), 1)

def draw_gold_rect(screen, x, y, w, h, radius=4):
    pygame.draw.rect(screen, COLOR_GOLD, (x, y, w, h), 1, border_radius=radius)

def draw_label_value(screen, fonts, x, y, label, value, val_color=COLOR_WHITE):
    lbl = fonts['sm'].render(label, True, COLOR_GREY)
    val = fonts['med'].render(str(value), True, val_color)
    screen.blit(lbl, (x, y))
    screen.blit(val, (x, y + 16))
    return y + 38

def draw_separator(screen, x, y, w):
    pygame.draw.line(screen, COLOR_BORDER, (x+8, y), (x+w-8, y))
    return y + 10


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
def draw_sidebar(screen, fonts, selected_tag, countries_data, screen_h, game_state):
    if not selected_tag or selected_tag in ("SEA","LAKE","Không có / Đất trống"):
        return

    x = screen.get_width() - SIDEBAR_W

    # Nền sidebar
    draw_panel(screen, x, 0, SIDEBAR_W, screen_h, alpha=245)

    # Header — màu quốc gia
    raw = countries_data.get(selected_tag, [100, 100, 100])
    c = tuple(int(v) for v in raw[:3])
    # Gradient giả: vẽ 2 lớp
    pygame.draw.rect(screen, c, (x, 0, SIDEBAR_W, 60))
    dark = tuple(max(0, v-40) for v in c)
    pygame.draw.rect(screen, dark, (x, 50, SIDEBAR_W, 10))
    pygame.draw.line(screen, COLOR_GOLD, (x, 60), (x+SIDEBAR_W, 60), 2)

    # Tên quốc gia
    name = COUNTRY_NAMES.get(selected_tag, selected_tag)
    surf = fonts['title'].render(name, True, COLOR_WHITE)
    if surf.get_width() > SIDEBAR_W - 20:
        surf = fonts['med'].render(name, True, COLOR_WHITE)
    screen.blit(surf, (x + 12, 10))

    # TAG nhỏ
    tag_s = fonts['sm'].render(f"[{selected_tag}]", True, (220,220,220,180))
    screen.blit(tag_s, (x + 12, 36))

    y_cur = 76

    # ── Thông tin quốc gia ──
    pop = COUNTRY_POP.get(selected_tag)
    pop_str = f"{pop:.1f}M" if pop else "Chưa có dữ liệu"

    # Dân số
    lbl = fonts['sm'].render("Dân số (1836)", True, COLOR_GREY)
    val = fonts['med'].render(pop_str, True, COLOR_GREEN)
    screen.blit(lbl, (x+12, y_cur)); screen.blit(val, (x+12, y_cur+16))
    y_cur += 42

    y_cur = draw_separator(screen, x, y_cur, SIDEBAR_W)

    # Màu hex
    hex_str = "#{:02X}{:02X}{:02X}".format(*c)
    lbl = fonts['sm'].render("Màu quốc gia", True, COLOR_GREY)
    val = fonts['sm'].render(hex_str, True, (200,200,200))
    swatch = pygame.Surface((14,14)); swatch.fill(c)
    screen.blit(lbl, (x+12, y_cur))
    screen.blit(swatch, (x+SIDEBAR_W-30, y_cur+2))
    screen.blit(val, (x+SIDEBAR_W-val.get_width()-32, y_cur+2))
    y_cur += 24
    y_cur = draw_separator(screen, x, y_cur, SIDEBAR_W)

    # Hint dưới cùng
    for txt in ["Chuột trái: kéo bản đồ", "Chuột phải: chọn tỉnh", "SPACE: Next Turn"]:
        s = fonts['sm'].render(txt, True, (70,85,110))
        screen.blit(s, (x+12, screen_h - 60 + (["Chuột trái: kéo bản đồ","Chuột phải: chọn tỉnh","SPACE: Next Turn"].index(txt))*18))

    # Viền trái
    pygame.draw.line(screen, COLOR_GOLD_DIM, (x, 0), (x, screen_h), 2)


# ─────────────────────────────────────────────
#  HUD (thanh dưới)
# ─────────────────────────────────────────────
def draw_hud(screen, fonts, game_state, flags_cache, screen_w, screen_h):
    y0 = screen_h - HUD_H
    draw_panel(screen, 0, y0, screen_w, HUD_H, alpha=250)
    pygame.draw.line(screen, COLOR_GOLD, (0, y0), (screen_w, y0), 2)

    # Cờ + tên người chơi (trái)
    tag  = game_state.player_tag
    mode = getattr(game_state, "player_mode", "default")
    flag_rect = pygame.Rect(8, y0 + 4, 60, 40)
    flag_surf = get_flag(flags_cache, tag, mode, (60, 40))
    if flag_surf:
        screen.blit(flag_surf, flag_rect.topleft)
    else:
        pygame.draw.rect(screen, tuple(int(v) for v in game_state.countries_data.get(tag,[80,80,80])[:3]),
                         flag_rect, border_radius=4)
        ft = fonts["med"].render(tag, True, COLOR_WHITE)
        screen.blit(ft, ft.get_rect(center=flag_rect.center))
    pygame.draw.rect(screen, COLOR_GOLD, flag_rect, 1, border_radius=4)

    name = COUNTRY_NAMES.get(tag, tag)
    ns = fonts['hud'].render(name, True, (220, 200, 140))
    screen.blit(ns, (76, y0 + (HUD_H - ns.get_height())//2))

    # Ngày tháng (giữa)
    d = game_state.current_date
    date_str = f"{MONTH_NAMES[d.month-1]} {d.year}"
    ds = fonts['date'].render(date_str, True, COLOR_GOLD)
    screen.blit(ds, (screen_w//2 - ds.get_width()//2, y0 + (HUD_H - ds.get_height())//2))

    # Nút Next Turn (phải)
    btn_w, btn_h = 140, 32
    btn_x = screen_w - btn_w - 16
    btn_y = y0 + (HUD_H - btn_h)//2
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    mx, my = pygame.mouse.get_pos()
    hovered = btn_rect.collidepoint(mx, my)
    btn_color = (55, 130, 75) if hovered else (38, 95, 55)
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)
    draw_gold_rect(screen, btn_x, btn_y, btn_w, btn_h, radius=6)
    bt = fonts['hud'].render("Next Turn  ▶", True, (200, 255, 210))
    screen.blit(bt, bt.get_rect(center=btn_rect.center))
    return btn_rect


# ─────────────────────────────────────────────
#  LOBBY
# ─────────────────────────────────────────────
def run_lobby(screen, fonts, original_map, political_map, color_to_province, zoom_level):
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()

    zoom      = zoom_level
    cam_x     = 0
    cam_y     = 0
    is_pan    = False
    last_pos  = (0,0)

    selected_tag  = None
    selected_mode = "default"
    mode_idx      = 0

    PANEL_H = 110
    panel_y = sh - PANEL_H

    # Nút thoát (góc trên phải)
    EXIT_W, EXIT_H = 36, 36
    exit_rect = pygame.Rect(sw - EXIT_W - 8, 8, EXIT_W, EXIT_H)

    # Nút chuyển chế độ (< >) – hiện khi đã chọn quốc gia
    btn_prev = pygame.Rect(0, 0, 32, 32)
    btn_next = pygame.Rect(0, 0, 32, 32)

    # Nút VÀO GAME
    btn_start = pygame.Rect(sw - 196, panel_y + (PANEL_H-46)//2, 180, 46)

    def scaled():
        return pygame.transform.scale(political_map,
               (int(map_w*zoom), int(map_h*zoom)))

    def clamp(cx, cy):
        sw2 = int(map_w*zoom); sh2 = int(map_h*zoom)
        cy = max(panel_y - sh2, min(0, cy))
        cx = cx % sw2
        return cx, cy

    sc_map = scaled()
    clock  = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                old_z = zoom
                zoom *= 1.15 if event.y > 0 else (1/1.15)
                zoom = max(zoom_level, min(zoom, 8.0))
                if old_z != zoom:
                    cam_x = mx - (mx - cam_x)*(zoom/old_z)
                    cam_y = my - (my - cam_y)*(zoom/old_z)
                    cam_x, cam_y = clamp(cam_x, cam_y)
                    sc_map = scaled()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex, ey = event.pos   # dùng event.pos chính xác, không dùng mx,my

                if event.button == 1:
                    # Nút thoát
                    if exit_rect.collidepoint(ex, ey):
                        pygame.quit(); sys.exit()

                    # Nút Start
                    elif btn_start.collidepoint(ex, ey) and selected_tag:
                        return selected_tag, selected_mode

                    # Nút chuyển chế độ
                    elif selected_tag and btn_prev.collidepoint(ex, ey):
                        avail = _avail_modes(flags_cache_ref, selected_tag)
                        mode_idx = (mode_idx - 1) % len(avail)
                        selected_mode = avail[mode_idx]

                    elif selected_tag and btn_next.collidepoint(ex, ey):
                        avail = _avail_modes(flags_cache_ref, selected_tag)
                        mode_idx = (mode_idx + 1) % len(avail)
                        selected_mode = avail[mode_idx]

                    # Click bản đồ — chỉ khi không trúng nút nào ở trên
                    elif ey < panel_y:
                        rx = int((ex - cam_x) / zoom)
                        ry = int((ey - cam_y) / zoom)
                        if 0 <= rx < map_w and 0 <= ry < map_h:
                            rgb = original_map.get_at((rx, ry))[:3]
                            if rgb in color_to_province:
                                owner = getattr(color_to_province[rgb], "owner", None)
                                if owner and owner not in ("SEA","LAKE","Khong co / Dat trong"):
                                    selected_tag  = owner
                                    mode_idx      = 0
                                    selected_mode = _avail_modes(flags_cache_ref, owner)[0]

                    # Bắt đầu kéo map (chỉ khi click vào bản đồ, không trúng UI)
                    if ey < panel_y and not any([
                        exit_rect.collidepoint(ex, ey),
                        btn_start.collidepoint(ex, ey),
                        btn_prev.collidepoint(ex, ey),
                        btn_next.collidepoint(ex, ey),
                    ]):
                        is_pan   = True
                        last_pos = event.pos

                elif event.button == 3:
                    is_pan   = True
                    last_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3): is_pan = False

            elif event.type == pygame.MOUSEMOTION and is_pan:
                cam_x += mx - last_pos[0]
                cam_y += my - last_pos[1]
                last_pos = (mx, my)
                cam_x, cam_y = clamp(cam_x, cam_y)

        # ── Render ──
        screen.fill(COLOR_SEA)
        sw2 = int(map_w*zoom)
        screen.blit(sc_map, (cam_x, cam_y))
        screen.blit(sc_map, (cam_x - sw2, cam_y))
        screen.blit(sc_map, (cam_x + sw2, cam_y))

        # Panel dưới
        ov = pygame.Surface((sw, PANEL_H), pygame.SRCALPHA)
        ov.fill((*COLOR_BG, 238))
        screen.blit(ov, (0, panel_y))
        pygame.draw.line(screen, COLOR_GOLD, (0, panel_y), (sw, panel_y), 2)

        # Title
        t1 = fonts["big"].render("Victoria 3 — Simple Engine", True, COLOR_GOLD)
        screen.blit(t1, (20, panel_y + 10))
        t2 = fonts["sm"].render("Click chon quoc gia · Cuon chuot de zoom · Giu chuot de keo ban do", True, COLOR_GREY)
        screen.blit(t2, (20, panel_y + 42))

        if selected_tag:
            name = COUNTRY_NAMES.get(selected_tag, selected_tag)
            avail = _avail_modes(flags_cache_ref, selected_tag)
            mode_label = _mode_label(selected_mode)

            # Cờ lớn
            flag_surf = get_flag(flags_cache_ref, selected_tag, selected_mode, (90, 60))
            flag_r = pygame.Rect(sw//2 - 220, panel_y + 12, 90, 60)
            if flag_surf:
                screen.blit(flag_surf, flag_r.topleft)
            else:
                raw = flags_cache_ref  # fallback màu
                pygame.draw.rect(screen, (80,80,80), flag_r, border_radius=4)
            pygame.draw.rect(screen, COLOR_GOLD, flag_r, 1, border_radius=4)

            # Tên quốc gia
            ns = fonts["title"].render(name, True, COLOR_WHITE)
            screen.blit(ns, (flag_r.right + 12, panel_y + 12))

            # Chế độ + nút < >
            TAG_X = flag_r.right + 12
            mode_y = panel_y + 44
            btn_prev.topleft = (TAG_X, mode_y)
            btn_next.topleft = (TAG_X + 200, mode_y)

            # Nút <
            ph = btn_prev.collidepoint(mx, my)
            pygame.draw.rect(screen, (50,65,85) if ph else (35,45,60), btn_prev, border_radius=5)
            pygame.draw.rect(screen, COLOR_BORDER, btn_prev, 1, border_radius=5)
            ps = fonts["hud"].render("<", True, COLOR_WHITE)
            screen.blit(ps, ps.get_rect(center=btn_prev.center))

            # Label chế độ
            ml = fonts["med"].render(mode_label, True, (180,220,255))
            screen.blit(ml, (TAG_X + 38, mode_y + 8))

            # Nút >
            nh = btn_next.collidepoint(mx, my)
            pygame.draw.rect(screen, (50,65,85) if nh else (35,45,60), btn_next, border_radius=5)
            pygame.draw.rect(screen, COLOR_BORDER, btn_next, 1, border_radius=5)
            ns2 = fonts["hud"].render(">", True, COLOR_WHITE)
            screen.blit(ns2, ns2.get_rect(center=btn_next.center))

            # Chỉ số chế độ
            idx_s = fonts["sm"].render(f"{mode_idx+1}/{len(avail)}", True, COLOR_GREY)
            screen.blit(idx_s, (TAG_X + 38, mode_y + 14 + ml.get_height()))

        else:
            hint = fonts["hud"].render("Click vao mot quoc gia de chon...", True, COLOR_GREY)
            screen.blit(hint, (sw//2 - hint.get_width()//2, panel_y + 38))

        # Nút VÀO GAME
        active = bool(selected_tag)
        bc = (40,120,60) if active else (40,45,58)
        pygame.draw.rect(screen, bc, btn_start, border_radius=8)
        if active: draw_gold_rect(screen, btn_start.x, btn_start.y, btn_start.w, btn_start.h, 8)
        else: pygame.draw.rect(screen, COLOR_BORDER, btn_start, 1, border_radius=8)
        bt = fonts["hud"].render("VAO GAME  >", True, COLOR_WHITE if active else COLOR_GREY)
        screen.blit(bt, bt.get_rect(center=btn_start.center))

        # Nút X thoát
        xh = exit_rect.collidepoint(mx, my)
        pygame.draw.rect(screen, (140,40,40) if xh else (80,30,30), exit_rect, border_radius=6)
        pygame.draw.rect(screen, (180,60,60), exit_rect, 1, border_radius=6)
        xs = fonts["title"].render("X", True, COLOR_WHITE)
        screen.blit(xs, xs.get_rect(center=exit_rect.center))

        pygame.display.flip()
        clock.tick(60)


def run_game(screen, fonts, game_state, original_map, political_map,
             color_to_province, initial_zoom, flags_cache):
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()

    zoom_level  = initial_zoom
    camera_x    = 0
    camera_y    = 0
    is_panning  = False
    last_mouse  = (0, 0)
    selected_tag = None
    show_political = True

    current_map = political_map
    scaled_map  = pygame.transform.scale(current_map,
                  (int(map_w*zoom_level), int(map_h*zoom_level)))

    def clamp(cx, cy, z):
        sw2 = int(map_w*z)
        sh2 = int(map_h*z)
        cy = max(sh - HUD_H - sh2, min(0, cy))
        cx = cx % sw2
        return cx, cy

    def rescale(z):
        return pygame.transform.scale(current_map, (int(map_w*z), int(map_h*z)))

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return   # quay ve lobby
                elif event.key == pygame.K_SPACE:
                    game_state.next_turn()
                elif event.key == pygame.K_m:
                    show_political = not show_political
                    current_map = political_map if show_political else original_map
                    scaled_map = rescale(zoom_level)

            elif event.type == pygame.MOUSEWHEEL:
                old = zoom_level
                zoom_level *= 1.2 if event.y > 0 else (1/1.2)
                zoom_level = max(initial_zoom, min(zoom_level, 6.0))
                if old != zoom_level:
                    mx, my = pygame.mouse.get_pos()
                    camera_x = mx - (mx - camera_x) * (zoom_level/old)
                    camera_y = my - (my - camera_y) * (zoom_level/old)
                    camera_x, camera_y = clamp(camera_x, camera_y, zoom_level)
                    scaled_map = rescale(zoom_level)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_panning = True
                    last_mouse = event.pos
                elif event.button == 3:
                    mx, my = event.pos
                    # Không click vào sidebar hoặc HUD
                    if mx < sw - SIDEBAR_W and my < sh - HUD_H:
                        rx = int((mx - camera_x) / zoom_level)
                        ry = int((my - camera_y) / zoom_level)
                        if 0 <= rx < map_w and 0 <= ry < map_h:
                            rgb = original_map.get_at((rx, ry))[:3]
                            if rgb in color_to_province:
                                prov = color_to_province[rgb]
                                owner = getattr(prov, 'owner', None)
                                if owner and owner not in ('SEA','LAKE'):
                                    selected_tag = owner

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    mx, my = event.pos
                    camera_x += mx - last_mouse[0]
                    camera_y += my - last_mouse[1]
                    last_mouse = event.pos
                    camera_x, camera_y = clamp(camera_x, camera_y, zoom_level)

        # ── Render ──
        screen.fill(COLOR_SEA)
        scaled_w = int(map_w * zoom_level)
        screen.blit(scaled_map, (camera_x, camera_y))
        screen.blit(scaled_map, (camera_x - scaled_w, camera_y))
        screen.blit(scaled_map, (camera_x + scaled_w, camera_y))

        # Sidebar + HUD
        draw_sidebar(screen, fonts, selected_tag,
                     game_state.countries_data, sh, game_state)
        btn = draw_hud(screen, fonts, game_state, flags_cache, sw, sh)

        # Nút MENU góc trên phải (ngoài sidebar)
        menu_rect = pygame.Rect(sw - SIDEBAR_W - 100, 8, 88, 30)
        mmx, mmy = pygame.mouse.get_pos()
        mh = menu_rect.collidepoint(mmx, mmy)
        pygame.draw.rect(screen, (70,40,20) if mh else (45,28,12), menu_rect, border_radius=6)
        draw_gold_rect(screen, menu_rect.x, menu_rect.y, menu_rect.w, menu_rect.h, 6)
        ms = fonts["sm"].render("< MENU", True, COLOR_GOLD)
        screen.blit(ms, ms.get_rect(center=menu_rect.center))
        if pygame.mouse.get_pressed()[0] and mh:
            return

        # Next Turn click
        if pygame.mouse.get_pressed()[0] and btn.collidepoint(pygame.mouse.get_pos()):
            pass  # handled via SPACE; button click detected next frame via event

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def start_engine(game_state):
    global flags_cache_ref
    pygame.init()
    pygame.font.init()

    sw, sh = 1280, 720
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Victoria 3 — Simple Engine")

    fonts = load_fonts()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(base_dir, "data", "map_data", "provinces.png")

    flags_cache_ref = load_flags_cache(base_dir)
    original_map = pygame.image.load(map_path).convert()
    color_to_province = {prov.color: prov for prov in game_state.provinces.values()}

    political_map = generate_political_map(
        original_map, color_to_province, game_state.countries_data)

    map_w, map_h = original_map.get_size()
    initial_zoom = max(sw / map_w, sh / map_h)

    # Lobby trả về (tag, mode)
    while True:
        result = run_lobby(screen, fonts, original_map, political_map,
                           color_to_province, initial_zoom)
        chosen_tag, chosen_mode = result
        game_state.player_tag  = chosen_tag
        game_state.player_mode = chosen_mode   # lưu chế độ chính phủ

        print(f"Chon: {chosen_tag} / che do: {chosen_mode}")

        run_game(screen, fonts, game_state, original_map, political_map,
                 color_to_province, initial_zoom, flags_cache_ref)
        # Nếu run_game return (nhấn ESC) thì quay về lobby