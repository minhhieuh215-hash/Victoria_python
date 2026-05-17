import pygame
import numpy as np
import sys
import os
from PIL import Image

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
    "TEX":"Texas",            "ECU":"Ecuador",
    "UCA":"Central America",  "COS":"Costa Rica",
    "HON":"Honduras",         "NIC":"Nicaragua",
    "GUA":"Guatemala",        "ELS":"El Salvador",
    "HAW":"Hawaii",           "TAH":"Tahiti",
    "CUB":"Cuba",             "DOM":"Dominican Republic",
    "HAI":"Haiti",            "PUR":"Puerto Rico",
    "JAM":"Jamaica",          "BAH":"Bahamas",
    "TRN":"Trinidad",         "GUY":"Guyana",
    "SUR":"Suriname",         "FGU":"French Guiana",
    "VIE":"Vietnam",          "LAO":"Laos",             "CAM":"Cambodia",
    "BRU":"Brunei",           "MAL":"Malaya",           "SIN":"Singapore",
    "INS":"Insulindia",       "TIM":"Timor",            "CEY":"Ceylon",
    "BHU":"Bhutan",           "MGL":"Mongolia",         "TIB":"Tibet",
    "XIN":"Xinjiang",         "MAN":"Manchuria",        "KOR":"Korea",
    "JAP":"Japan",            "RYU":"Ryukyu",
    "IRQ":"Iraq",             "SYR":"Syria",            "LEB":"Lebanon",
    "JOR":"Jordan",           "ISR":"Israel",           "PAL":"Palestine",
    "YEM":"Yemen",            "OMA":"Oman",             "TRU":"Trucial States",
    "KSA":"Saudi Arabia",     "KUW":"Kuwait",           "BAH":"Bahrain",
    "QAT":"Qatar",            "UAE":"United Arab Emirates",
    "ALG":"Algeria",          "TUN":"Tunisia",          "MOR":"Morocco",
    "LBY":"Libya",            "EGY":"Egypt",            "SUD":"Sudan",
    "ETH":"Ethiopia",         "ERI":"Eritrea",          "SOM":"Somalia",
    "KEN":"Kenya",            "UGA":"Uganda",           "TAN":"Tanganyika",
    "ZAN":"Zanzibar",         "MOZ":"Mozambique",       "MAD":"Madagascar",
    "ANG":"Angola",           "NAM":"Namibia",          "BOT":"Botswana",
    "ZIM":"Zimbabwe",         "ZAM":"Zambia",           "MLW":"Malawi",
    "RSA":"South Africa",     "SWA":"Swaziland",        "LES":"Lesotho",
    "QUE":"Quebec",           "ONT":"Ontario",          "MAN":"Manitoba",
    "SAS":"Saskatchewan",     "ALB":"Alberta",          "BC":"British Columbia",
    "NWT":"Northwest Territories", "YUK":"Yukon",       "NUN":"Nunavut",
    "CAL":"California",       "TEX":"Texas",            "FLO":"Florida",
    "ALA":"Alabama",          "MIS":"Mississippi",      "LOU":"Louisiana",
    "ARK":"Arkansas",         "TEN":"Tennessee",        "KEN":"Kentucky",
    "OHI":"Ohio",             "IND":"Indiana",          "ILL":"Illinois",
    "MIC":"Michigan",         "WIS":"Wisconsin",        "MIN":"Minnesota",
    "IOW":"Iowa",             "MIS":"Missouri",         "NOR":"North Carolina",
    "SOU":"South Carolina",   "GEO":"Georgia",          "VIR":"Virginia",
    "WVA":"West Virginia",    "PEN":"Pennsylvania",     "NY":"New York",
    "MAS":"Massachusetts",    "VER":"Vermont",          "NEW":"New Hampshire",
    "MAI":"Maine",            "CON":"Connecticut",      "RHO":"Rhode Island",
    "DEL":"Delaware",         "MAR":"Maryland",         "NJ":"New Jersey",
    "VEN":"Venezuela",        "COL":"Colombia",         "ECU":"Ecuador",
    "PER":"Peru",             "BOL":"Bolivia",          "PAR":"Paraguay",
    "CHL":"Chile",            "ARG":"Argentina",        "URU":"Uruguay",
    "BRZ":"Brazil",           "GUY":"Guyana",           "SUR":"Suriname",
    "FGU":"French Guiana",
    "AUS":"Australia",        "NZL":"New Zealand",      "PNG":"Papua New Guinea",
    "FIJ":"Fiji",             "SOL":"Solomon Islands",   "VAN":"Vanuatu",
    "NCL":"New Caledonia",    "SAM":"Samoa",            "TON":"Tonga",
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


def find_province_by_color(rgb, color_to_province, tolerance=5):
    """Find province by RGB color with fuzzy matching (within tolerance)."""
    # Normalize RGB to tuple of ints
    if not isinstance(rgb, tuple) or len(rgb) < 3:
        return None
    
    try:
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    except (ValueError, TypeError):
        return None
    
    # Try exact match first
    exact_key = (r, g, b)
    if exact_key in color_to_province:
        return color_to_province[exact_key]
    
    # Fuzzy match: find closest color within tolerance
    best_match = None
    best_distance = float('inf')
    
    for color_key in color_to_province.keys():
        if not isinstance(color_key, tuple) or len(color_key) < 3:
            continue
        try:
            cr, cg, cb = int(color_key[0]), int(color_key[1]), int(color_key[2])
        except (ValueError, TypeError):
            continue
        
        # Euclidean distance
        distance = ((r - cr)**2 + (g - cg)**2 + (b - cb)**2) ** 0.5
        if distance < best_distance:
            best_distance = distance
            best_match = color_to_province[color_key]
    
    # Only return if within tolerance
    if best_distance <= tolerance:
        return best_match
    return None

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

#  LOBBY
def run_lobby(screen, fonts, original_map, political_map, color_to_province, zoom_level, pil_pixels=None):
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()

    zoom      = zoom_level
    cam_x     = 0
    cam_y     = 0
    is_pan    = False
    last_pos  = (0,0)

    selected_tag  = "DAI"  # Default to Dai Nam
    selected_mode = "default"
    mode_idx      = 0

    PANEL_H = 110
    panel_y = sh - PANEL_H

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
    
    print(f"[LOBBY] Default country: {selected_tag} (Dai Nam)")

    while True:
        scaled_w = int(map_w * zoom)
        scaled_h = int(map_h * zoom)
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); 
                    sys.exit()
                elif event.key == pygame.K_d:
                    print("\n=== DEBUG INFO ===")
                    print(f"Camera position: ({cam_x}, {cam_y})")
                    print(f"Zoom level: {zoom}")
                    print(f"Map size: {map_w}x{map_h}")
                    print(f"Scaled map size: {int(map_w*zoom)}x{int(map_h*zoom)}")
                    print(f"Screen size: {sw}x{sh}")
                    print(f"Selected country: {selected_tag}")
                    print(f"Color lookup size: {len(color_to_province)}")

                    center_x = sw // 2
                    center_y = sh // 2
                    print(f"\nChecking center of screen ({center_x}, {center_y}):")
                    
                    scaled_w = int(map_w * zoom)
                    map_x = center_x - cam_x
                    while map_x < 0:
                        map_x += scaled_w
                    while map_x >= scaled_w:
                        map_x -= scaled_w
                    map_y = center_y - cam_y

                    if 0 <= map_x < scaled_w and 0 <= map_y < scaled_h:
                        rx = int(map_x / zoom)
                        ry = int(map_y / zoom)
                        debug_color_at_position(pil_pixels, rx, ry, color_to_province)

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
                    # Ưu tiên kiểm tra nút UI trước
                    clicked_ui = False

                    # Nút Start
                    if btn_start.collidepoint(ex, ey) and selected_tag:
                        return selected_tag, selected_mode

                    # Nút chuyển chế độ
                    if selected_tag and btn_prev.collidepoint(ex, ey):
                        avail = _avail_modes(flags_cache_ref, selected_tag)
                        mode_idx = (mode_idx - 1) % len(avail)
                        selected_mode = avail[mode_idx]
                        clicked_ui = True

                    if selected_tag and btn_next.collidepoint(ex, ey):
                        avail = _avail_modes(flags_cache_ref, selected_tag)
                        mode_idx = (mode_idx + 1) % len(avail)
                        selected_mode = avail[mode_idx]
                        clicked_ui = True

                    if not clicked_ui and ey < panel_y:
                        scaled_w = int(map_w * zoom)
                        scaled_h = int(map_h * zoom)

                        map_x = ex - cam_x
                        map_y = ey - cam_y

                        while map_x < 0:
                            map_x += scaled_w
                        while map_x >= scaled_w:
                            map_x -= scaled_w

                        if 0 <= map_x < scaled_w and 0 <= map_y < scaled_h:
                            rx = int(map_x / zoom)
                            ry = int(map_y / zoom)

                            rx = max(0, min(rx, map_w - 1))
                            ry = max(0, min(ry, map_h - 1))

                            try:
                                if pil_pixels:
                                    rgb = pil_pixels[rx, ry]
                                else:
                                    rgb = original_map.get_at((rx, ry))[:3]
                                
                                print(f"Click at screen ({ex},{ey}) -> map ({rx},{ry}) -> RGB {rgb}")
                                
                                prov = find_province_by_color(rgb, color_to_province, tolerance=5)
                                if prov:
                                    owner = getattr(prov, "owner", None)
                                    if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                        selected_tag  = owner
                                        mode_idx      = 0
                                        selected_mode = _avail_modes(flags_cache_ref, owner)[0]
                                        print(f"✓ Selected country: {selected_tag} (RGB: {rgb})")
                                    else:
                                        print(f"✗ Click on water/empty land (owner: {owner})")
                                else:
                                    print(f"✗ Color not found: {rgb}")

                            except Exception as e:
                                print(f"✗ Error selecting country: {e}")

                    # Bắt đầu kéo map (chỉ khi click vào bản đồ, không trúng UI)
                    if not clicked_ui and ey < panel_y:
                        is_pan   = True
                        last_pos = event.pos

                elif event.button == 3:
                    if ey < panel_y:
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

        pygame.display.flip()
        clock.tick(60)


def run_game(screen, fonts, game_state, original_map, political_map,
             color_to_province, initial_zoom, flags_cache, pil_pixels=None):
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()

    zoom_level  = initial_zoom
    camera_x    = 0
    camera_y    = 0
    is_panning  = False
    last_mouse  = (0, 0)
    selected_tag = None
    show_political = True
    next_turn_pressed = False
    menu_open   = False

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
                    menu_open = not menu_open   # Toggle menu
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
                    # Check if Next Turn button was clicked (will check btn rect in render loop)
                elif event.button == 3:
                    mx, my = event.pos
                    # Right-click to select province - only outside sidebar and HUD
                    if mx < sw - SIDEBAR_W and my < sh - HUD_H:
                        try:
                            rx = int((mx - camera_x) / zoom_level)
                            ry = int((my - camera_y) / zoom_level)
                            if 0 <= rx < map_w and 0 <= ry < map_h:
                                # Use PIL for exact colors if available
                                if pil_pixels:
                                    rgb = pil_pixels[rx, ry]
                                else:
                                    rgb = original_map.get_at((rx, ry))[:3]
                                
                                prov = find_province_by_color(rgb, color_to_province, tolerance=3)
                                if prov:
                                    owner = getattr(prov, 'owner', None)
                                    if owner and owner not in ('SEA', 'LAKE', 'Không có / Đất trống'):
                                        selected_tag = owner
                                        print(f"✓ Selected province owner: {selected_tag} (RGB: {rgb})")
                                    else:
                                        print(f"✗ Click on {owner}")
                                else:
                                    print(f"✗ Province not found for color: {rgb}")
                        except Exception as e:
                            print(f"✗ Error selecting province: {e}")

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

        # Menu button or menu overlay
        if menu_open:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            # Menu panel
            menu_w, menu_h = 300, 200
            menu_x = sw // 2 - menu_w // 2
            menu_y = sh // 2 - menu_h // 2
            pygame.draw.rect(screen, COLOR_PANEL, (menu_x, menu_y, menu_w, menu_h), border_radius=8)
            pygame.draw.rect(screen, COLOR_GOLD, (menu_x, menu_y, menu_w, menu_h), 2, border_radius=8)
            
            # Menu title
            title = fonts["big"].render("MENU", True, COLOR_GOLD)
            screen.blit(title, (menu_x + (menu_w - title.get_width()) // 2, menu_y + 15))
            
            # Continue button
            continue_rect = pygame.Rect(menu_x + 30, menu_y + 60, menu_w - 60, 40)
            cmx, cmy = pygame.mouse.get_pos()
            ch = continue_rect.collidepoint(cmx, cmy)
            pygame.draw.rect(screen, (50, 100, 50) if ch else (30, 60, 30), continue_rect, border_radius=4)
            pygame.draw.rect(screen, COLOR_GOLD, continue_rect, 1, border_radius=4)
            ct = fonts["sm"].render("Continue", True, COLOR_WHITE)
            screen.blit(ct, ct.get_rect(center=continue_rect.center))
            if pygame.mouse.get_pressed()[0] and ch:
                menu_open = False
            
            # Exit button
            exit_rect = pygame.Rect(menu_x + 30, menu_y + 110, menu_w - 60, 40)
            eh = exit_rect.collidepoint(cmx, cmy)
            pygame.draw.rect(screen, (140, 40, 40) if eh else (80, 30, 30), exit_rect, border_radius=4)
            pygame.draw.rect(screen, (180, 60, 60), exit_rect, 1, border_radius=4)
            et = fonts["sm"].render("Exit to Lobby", True, COLOR_WHITE)
            screen.blit(et, et.get_rect(center=exit_rect.center))
            if pygame.mouse.get_pressed()[0] and eh:
                return
        else:
            # Show MENU button when menu is not open
            menu_rect = pygame.Rect(sw - SIDEBAR_W - 100, 8, 88, 30)
            mmx, mmy = pygame.mouse.get_pos()
            mh = menu_rect.collidepoint(mmx, mmy)
            pygame.draw.rect(screen, (140,40,40) if mh else (80,30,30), menu_rect, border_radius=6)
            pygame.draw.rect(screen, (180,60,60), menu_rect, 1, border_radius=6)
            ms = fonts["sm"].render("< MENU", True, COLOR_WHITE)
            screen.blit(ms, ms.get_rect(center=menu_rect.center))
            if pygame.mouse.get_pressed()[0] and mh:
                menu_open = True

        # Next Turn click - handle left mouse click with debounce
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed and btn.collidepoint(pygame.mouse.get_pos()):
            if not next_turn_pressed:
                game_state.next_turn()
                next_turn_pressed = True
        else:
            next_turn_pressed = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

# Thêm vào game_ui.py, ví dụ sau hàm find_province_by_color

def debug_color_at_position(pil_image, x, y, color_to_province):
    """Debug function to check color mapping at specific coordinates"""
    if not pil_image:
        print("PIL image not available")
        return None, None
    
    width, height = pil_image.size
    if 0 <= x < width and 0 <= y < height:
        rgb = pil_image.getpixel((x, y))
        prov = find_province_by_color(rgb, color_to_province, tolerance=5)
        
        print(f"\n--- DEBUG ---")
        print(f"Position: ({x}, {y})")
        print(f"RGB value: {rgb}")
        
        if prov:
            print(f"Province ID: {prov.id}")
            print(f"Province color: {prov.color}")
            print(f"Is sea: {prov.is_sea}")
            print(f"Is lake: {prov.is_lake}")
            print(f"Owner: {prov.owner}")
        else:
            print("No province found for this color")
            # Tìm màu gần nhất để debug
            closest = None
            min_dist = float('inf')
            for color_key, p in color_to_province.items():
                if len(color_key) == 3:
                    dist = ((rgb[0]-color_key[0])**2 + (rgb[1]-color_key[1])**2 + (rgb[2]-color_key[2])**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest = p
            if closest:
                print(f"Closest province: ID {closest.id}, color {closest.color}, distance: {min_dist:.2f}")
        print("---------------\n")
        return rgb, prov
    else:
        print(f"Coordinates ({x},{y}) out of bounds (0-{width}, 0-{height})")
        return None, None


#  ENTRY POINT
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
    # Load WITHOUT .convert() to preserve exact color values
    original_map = pygame.image.load(map_path)
    
    # Also load with PIL for guaranteed exact color lookups
    pil_map = Image.open(map_path).convert("RGB")
    pil_pixels = pil_map.load()
    
    color_to_province = {prov.color: prov for prov in game_state.provinces.values()}
    print(f"[DEBUG] Loaded {len(color_to_province)} provinces in color lookup")

    political_map = generate_political_map(
        original_map, color_to_province, game_state.countries_data)

    map_w, map_h = original_map.get_size()
    initial_zoom = max(sw / map_w, sh / map_h)

    # Lobby trả về (tag, mode)
    while True:
        result = run_lobby(screen, fonts, original_map, political_map,
                           color_to_province, initial_zoom, pil_pixels)
        chosen_tag, chosen_mode = result
        game_state.player_tag  = chosen_tag
        game_state.player_mode = chosen_mode   # lưu chế độ chính phủ

        print(f"Chon: {chosen_tag} / che do: {chosen_mode}")

        run_game(screen, fonts, game_state, original_map, political_map,
                 color_to_province, initial_zoom, flags_cache_ref, pil_pixels)
        # Nếu run_game return (nhấn ESC) thì quay về lobby
