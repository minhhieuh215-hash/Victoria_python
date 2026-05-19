import pygame, numpy as np, sys, os, json

# ── Constants ──────────────────────────────────────
from config import (
    SCREEN_W, SCREEN_H, FPS, TITLE, ZOOM_MAX,
    C_BG, C_PANEL, C_BORDER, C_GOLD, C_GOLD_DIM,
    C_SEA, C_LAKE, C_WHITE, C_GREY, C_GREEN, C_RED,
    C_LAND_EMPTY, C_COLONIZABLE, COLONIZABLE_TYPES
)
from engine.state_resource_loader import RESOURCE_DISPLAY
from engine.state_resource_loader import get_state_for_province

SIDEBAR_W = 280
HUD_H     = 48
MONTH_FULL = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

COUNTRY_NAMES = {
    "GBR":"Great Britain",  "FRA":"France",       "RUS":"Russia",
    "GER":"Germany",        "AUS":"Austria",       "PRU":"Prussia",
    "USA":"United States",  "JAP":"Japan",         "CHI":"China",
    "TUR":"Ottoman Empire", "SPA":"Spain",         "POR":"Portugal",
    "ITA":"Italy",          "SCA":"Scandinavia",   "NET":"Netherlands",
    "BEL":"Belgium",        "HBC":"Hudson Bay Co.","BRZ":"Brazil",
    "ARG":"Argentina",      "MEX":"Mexico",        "PER":"Persia",
    "EGY":"Egypt",          "ETH":"Ethiopia",      "MOR":"Morocco",
    "NEP":"Nepal",          "BUR":"Burma",         "SIA":"Siam",
    "DAI":"Dai Nam",        "KOR":"Korea",         "CAN":"Canada",
    "CHL":"Chile",          "CLM":"Colombia",      "GRE":"Greece",
    "SER":"Serbia",         "HAN":"Hannover",      "SAX":"Saxony",
    "BAV":"Bavaria",        "NOR":"Norway",        "DEN":"Denmark",
    "SWE":"Sweden",         "DEI":"Dutch East Indies",
    "AFG":"Afghanistan",    "BOL":"Bolivia",       "VNZ":"Venezuela",
    "TEX":"Texas",          "ECU":"Ecuador",       "UCA":"Central America",
    "COS":"Costa Rica",     "HON":"Honduras",      "NIC":"Nicaragua",
    "GUA":"Guatemala",      "ELS":"El Salvador",   "CUB":"Cuba",
    "DOM":"Dominican Republic", "HAI":"Haiti",     "JAM":"Jamaica",
}

GOVT_LABELS = {
    "default":"Mac dinh",           "absolute_monarchy":"Quan chu chuyen che",
    "republic":"Cong hoa",          "dictatorship":"Doc tai",
    "theocracy":"Than quyen",       "communist":"Cong san",
    "fascist":"Phat xit",           "subject":"Phu thuoc",
}

DIPLOMACY_PANEL_W = 500
DIPLOMACY_PANEL_H = 450
MAP_MODE_POLITICAL = 0
MAP_MODE_COUNTRY_NAMES = 1
MAP_MODE_PROVINCE_NAMES = 2

current_map_mode = MAP_MODE_POLITICAL
country_name_surface = None
province_name_surface = None
game_state_ref = None
show_diplomacy = False
show_build_panel = False
diplomacy_selected_tag = None

# ── Global flags cache ──────────────────────────────
_flags = {}   # { TAG: { mode: Surface } }

# ── Fonts ───────────────────────────────────────────
def load_fonts():
    for name in ["segoeui","tahoma","calibri","verdana","arial","freesans"]:
        try:
            if pygame.font.SysFont(name,14).render("A",True,(0,0,0)).get_width():
                chosen = name; break
        except: pass
    else:
        chosen = "arial"
    return {
        "big"  : pygame.font.SysFont(chosen, 24, bold=True),
        "title": pygame.font.SysFont(chosen, 19, bold=True),
        "med"  : pygame.font.SysFont(chosen, 15, bold=True),
        "sm"   : pygame.font.SysFont(chosen, 13),
        "hud"  : pygame.font.SysFont(chosen, 16, bold=True),
        "date" : pygame.font.SysFont(chosen, 18, bold=True),
    }


# ── Flag helpers ────────────────────────────────────
def load_flags(base_dir):
    global _flags
    d = os.path.join(base_dir, "data", "flags")
    if not os.path.exists(d): return
    for fn in os.listdir(d):
        if not fn.endswith(".png"): continue
        parts = fn[:-4].split("_")
        if len(parts) < 2 or parts[0].lower() != "flag": continue
        tag  = parts[1].upper()
        mode = "_".join(parts[2:]) or "default"
        try:
            img = pygame.image.load(os.path.join(d,fn)).convert_alpha()
            _flags.setdefault(tag, {})[mode] = img
        except: pass
    print(f"Flags: {len(_flags)} quoc gia")

def get_flag(tag, mode="default", size=(72,48)):
    entry = _flags.get(tag, {})
    img = entry.get(mode) or entry.get("default")
    return pygame.transform.scale(img, size) if img else None

def avail_modes(tag):
    modes = sorted(_flags.get(tag, {}).keys())
    if "default" in modes: modes.remove("default"); modes = ["default"]+modes
    return modes or ["default"]


# ── Border masks ────────────────────────────────────
def generate_province_border_mask(original_image, color_to_province, countries_data):
    """
    Tạo mask cho viền tỉnh, CHỈ vẽ viền giữa các tỉnh khác quốc gia.
    """
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]
    
    owner_map = np.zeros((h, w), dtype=np.uint32)
    owner_by_color = {}
    
    for rgb, prov in color_to_province.items():
        owner = getattr(prov, 'owner', None)
        if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
            owner_by_color[rgb] = hash(owner) % (2**32)
        else:
            owner_by_color[rgb] = 0
    
    for y in range(h):
        for x in range(w):
            rgb = tuple(arr[y, x])
            owner_map[y, x] = owner_by_color.get(rgb, 0)
    
    mask = np.zeros((h, w), dtype=bool)
    mask[:, 1:] |= (owner_map[:, 1:] != owner_map[:, :-1]) & (owner_map[:, 1:] != 0) & (owner_map[:, :-1] != 0)
    mask[1:, :] |= (owner_map[1:, :] != owner_map[:-1, :]) & (owner_map[1:, :] != 0) & (owner_map[:-1, :] != 0)
    mask &= (owner_map != 0)
    
    return mask

def generate_province_border_mask_only(original_image, color_to_province):
    """Tạo mask viền cho TẤT CẢ các tỉnh (không phân biệt quốc gia)"""
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]
    
    province_map = np.zeros((h, w), dtype=np.uint32)
    province_by_color = {}
    
    for rgb, prov in color_to_province.items():
        province_by_color[rgb] = prov.id
    
    for y in range(h):
        for x in range(w):
            rgb = tuple(arr[y, x])
            province_map[y, x] = province_by_color.get(rgb, 0)
    
    mask = np.zeros((h, w), dtype=bool)
    mask[:, 1:] |= (province_map[:, 1:] != province_map[:, :-1]) & (province_map[:, 1:] != 0) & (province_map[:, :-1] != 0)
    mask[1:, :] |= (province_map[1:, :] != province_map[:-1, :]) & (province_map[1:, :] != 0) & (province_map[:-1, :] != 0)
    mask &= (province_map != 0)
    
    return mask


# ── Map generation ──────────────────────────────────
def generate_political_map(original_image, color_to_province, countries_data, countries_full, mode=MAP_MODE_POLITICAL):
    print("Dang to mau ban do...")
    arr = pygame.surfarray.array3d(original_image).transpose(1,0,2)
    lut_r = np.zeros(16777216, dtype=np.uint8)
    lut_g = np.zeros(16777216, dtype=np.uint8)
    lut_b = np.zeros(16777216, dtype=np.uint8)
    in_lut = np.zeros(16777216, dtype=bool)

    for rgb, prov in color_to_province.items():
        if getattr(prov,"is_sea",False):
            nr,ng,nb = C_SEA
        elif getattr(prov,"is_lake",False):
            nr,ng,nb = C_LAKE
        else:
            owner = getattr(prov,"owner",None)
            if owner and owner in countries_data:
                ctype = countries_full.get(owner,{}).get("type","recognized")
                if ctype in COLONIZABLE_TYPES:
                    nr,ng,nb = C_COLONIZABLE
                else:
                    v = countries_data[owner]
                    nr,ng,nb = int(v[0]),int(v[1]),int(v[2])
            else:
                nr,ng,nb = C_LAND_EMPTY

        k = rgb[0]*65536+rgb[1]*256+rgb[2]
        lut_r[k]=nr; lut_g[k]=ng; lut_b[k]=nb; in_lut[k]=True

    u32 = (arr[:,:,0].astype(np.uint32)*65536 +
           arr[:,:,1].astype(np.uint32)*256   +
           arr[:,:,2].astype(np.uint32))
    mask = in_lut[u32]
    result = np.stack([
        np.where(mask, lut_r[u32], arr[:,:,0]),
        np.where(mask, lut_g[u32], arr[:,:,1]),
        np.where(mask, lut_b[u32], arr[:,:,2]),
    ], axis=2)

    if mode == MAP_MODE_PROVINCE_NAMES:
        border_mask = generate_province_border_mask_only(original_image, color_to_province)
        result[border_mask] = np.array([80, 80, 80], dtype=np.uint8)
    else:
        border_mask = generate_province_border_mask(original_image, color_to_province, countries_data)
        result[border_mask] = np.array([60, 60, 60], dtype=np.uint8)

    result = (result * 0.9).astype(np.uint8)

    print("-> Hoan tat!")
    return pygame.surfarray.make_surface(result.transpose(1,0,2))

def generate_country_name_map(original_image, color_to_province, countries_data, fonts):
    """Tạo bản đồ hiển thị tên quốc gia ngay trên map"""
    print("Dang tao ban do ten quoc gia...")
    
    map_w, map_h = original_image.get_size()
    text_surface = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
    
    country_pixels = {}
    
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    
    for y in range(0, map_h, 5):
        for x in range(0, map_w, 5):
            rgb = tuple(arr[y, x])
            prov = color_to_province.get(rgb)
            if prov:
                owner = getattr(prov, 'owner', None)
                if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                    if owner not in country_pixels:
                        country_pixels[owner] = []
                    country_pixels[owner].append((x, y))

    country_data = []
    for owner, pixels in country_pixels.items():
        if len(pixels) > 50:  # Bỏ qua nước quá nhỏ
            center_x = sum(p[0] for p in pixels) // len(pixels)
            center_y = sum(p[1] for p in pixels) // len(pixels)
            area = len(pixels)
            country_data.append((owner, center_x, center_y, area))
    
    country_data.sort(key=lambda x: x[3], reverse=True)
    if not country_data:
        return text_surface
    
    areas = [c[3] for c in country_data]
    min_area, max_area = min(areas), max(areas)
    
    for owner, cx, cy, area in country_data:
        # Tính kích thước chữ: từ 10px đến 28px
        font_size = 10 + int(18 * (area - min_area) / (max_area - min_area + 1))
        font_size = max(10, min(28, font_size))
        
        # Tạo font tạm thời với kích thước phù hợp
        try:
            temp_font = pygame.font.SysFont("arial", font_size, bold=True)
        except:
            temp_font = fonts["sm"]
        
        name = COUNTRY_NAMES.get(owner, owner)
        if name is None:
            name = owner if owner else "Unknown"
        
        if not name or len(name) < 3:
            continue
        
        # Rút gọn tên nếu quá dài
        max_len = 14 if font_size > 20 else 18
        if len(name) > max_len:
            name = name[:max_len-2] + ".."
        
        # Vẽ bóng và text
        text = temp_font.render(name, True, C_WHITE)
        text_rect = text.get_rect(center=(cx, cy))
        
        # Nền mờ phía sau text
        padding = max(3, font_size // 8)
        bg_rect = pygame.Rect(text_rect.x - padding, text_rect.y - padding,
                              text_rect.width + padding * 2, text_rect.height + padding * 2)
        pygame.draw.rect(text_surface, (*C_PANEL, 200), bg_rect, border_radius=4)
        pygame.draw.rect(text_surface, C_GOLD, bg_rect, 1, border_radius=4)
        
        # Vẽ bóng đổ
        shadow = temp_font.render(name, True, (0, 0, 0, 150))
        text_surface.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        text_surface.blit(text, text_rect)
    
    print("-> Hoan tat!")
    return text_surface

def generate_province_name_map(original_image, color_to_province, fonts):
    """Tạo bản đồ tên tỉnh với kích thước chữ theo diện tích"""
    print("Dang tao ban do ten tinh (voi kich thuoc linh hoat)...")
    
    map_w, map_h = original_image.get_size()
    text_surface = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
    
    from engine.state_resource_loader import _color_to_state_cache
    
    # Gom các province theo state
    state_pixels = {}
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    
    for y in range(0, map_h, 10):
        for x in range(0, map_w, 10):
            rgb = tuple(arr[y, x])
            state = _color_to_state_cache.get(rgb)
            if state:
                state_name = state.name
                if state_name not in state_pixels:
                    state_pixels[state_name] = []
                state_pixels[state_name].append((x, y))
    
    # Tính trung tâm và diện tích
    state_data = []
    for state_name, pixels in state_pixels.items():
        if len(pixels) > 30:
            center_x = sum(p[0] for p in pixels) // len(pixels)
            center_y = sum(p[1] for p in pixels) // len(pixels)
            area = len(pixels)
            state_data.append((state_name, center_x, center_y, area))
    
    if not state_data:
        return text_surface
    
    # Sắp xếp và tính kích thước
    state_data.sort(key=lambda x: x[3], reverse=True)
    areas = [s[3] for s in state_data]
    min_area, max_area = min(areas), max(areas)
    
    for state_name, cx, cy, area in state_data:
        # Kích thước chữ từ 8px đến 18px cho tỉnh
        font_size = 8 + int(10 * (area - min_area) / (max_area - min_area + 1))
        font_size = max(8, min(18, font_size))
        
        try:
            temp_font = pygame.font.SysFont("arial", font_size, bold=True)
        except:
            temp_font = fonts["sm"]
        
        display_name = state_name.replace("STATE_", "").replace("_", " ").title()
        max_len = 12 if font_size > 14 else 15
        if len(display_name) > max_len:
            display_name = display_name[:max_len-2] + ".."
        
        text = temp_font.render(display_name, True, C_WHITE)
        text_rect = text.get_rect(center=(cx, cy))
        
        # Nền mờ nhạt hơn cho tỉnh
        padding = max(2, font_size // 8)
        bg_rect = pygame.Rect(text_rect.x - padding, text_rect.y - padding,
                              text_rect.width + padding * 2, text_rect.height + padding * 2)
        pygame.draw.rect(text_surface, (*C_PANEL, 160), bg_rect, border_radius=2)
        
        text_surface.blit(text, text_rect)
    
    print("-> Hoan tat!")
    return text_surface

def generate_combined_political_map(original_image, color_to_province, countries_data, countries_full, fonts):
    """Tạo bản đồ chính trị kết hợp tên quốc gia"""
    print("Dang tao ban do chinh tri + ten quoc gia...")
    
    # Tạo bản đồ chính trị
    political = generate_political_map(original_image, color_to_province, 
                                        countries_data, countries_full, 
                                        mode=MAP_MODE_POLITICAL)
    
    # Thêm tên quốc gia
    country_names = generate_country_name_map(original_image, color_to_province, countries_data, fonts)
    political.blit(country_names, (0, 0))
    
    return political

# ── Draw helpers ─────────────────────────────────────
def panel(screen, x, y, w, h, alpha=230):
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha)); screen.blit(s,(x,y))
    pygame.draw.rect(screen, C_BORDER, (x,y,w,h), 1)

def gold_border(screen, x, y, w, h, r=4):
    pygame.draw.rect(screen, C_GOLD, (x,y,w,h), 1, border_radius=r)

def text(screen, fonts, key, txt, x, y, color=None):
    s = fonts[key].render(str(txt), True, color or C_WHITE)
    screen.blit(s,(x,y)); return s

def row(screen, fonts, x, y, label, value, vcol=None):
    text(screen,fonts,"sm",label,x,y,C_GREY)
    vs = fonts["med"].render(str(value),True,vcol or C_WHITE)
    screen.blit(vs,(x+SIDEBAR_W-vs.get_width()-28,y))
    return y+26

def divider(screen, x, y, w):
    pygame.draw.line(screen,C_BORDER,(x+8,y),(x+w-8,y)); return y+10

def get_relations_color(value):
    if value >= 75: return (80, 220, 100)
    if value >= 50: return (80, 200, 120)
    if value >= 25: return (120, 200, 120)
    if value >= 0: return (180, 180, 100)
    if value >= -25: return (200, 150, 80)
    if value >= -50: return (200, 120, 60)
    if value >= -75: return (210, 80, 80)
    return (220, 50, 50)


# ── Tooltip ─────────────────────────────────────────
def draw_province_tooltip(screen, fonts, original_map, color_to_province, mx, my, cam_x, cam_y, zoom, screen_h):
    if mx >= SCREEN_W - SIDEBAR_W or my >= screen_h - HUD_H:
        return

    map_w, map_h = original_map.get_size()
    map_x = mx - cam_x
    map_y = my - cam_y
    sw2 = int(map_w * zoom)

    while map_x < 0:
        map_x += sw2
    while map_x >= sw2:
        map_x -= sw2

    if not (0 <= map_x < sw2 and 0 <= map_y < map_h * zoom):
        return

    rx = int(map_x / zoom)
    ry = int(map_y / zoom)
    if not (0 <= rx < map_w and 0 <= ry < map_h):
        return

    rgb = original_map.get_at((rx, ry))[:3]
    prov = color_to_province.get(rgb)
    if not prov:
        prov = find_closest_province(rgb, color_to_province, tolerance=5)
    if not prov or prov.is_sea or prov.is_lake:
        return

    owner = getattr(prov, "owner", None) or "Không có"
    owner_name = COUNTRY_NAMES.get(owner, owner)
    
    state = get_state_for_province(rgb)
    state_name = state.display_name() if state else "Không xác định"
    
    lines = [
        f"🏛️ {state_name}",
        f"👑 {owner_name}",
        f"📍 Tỉnh {prov.id}"
    ]
    
    if state and state.capped_resources:
        top_res = list(state.capped_resources.items())[:2]
        for res, amount in top_res:
            name, icon = RESOURCE_DISPLAY.get(res, (res, "📦"))
            lines.append(f"{icon} {name}: {amount}")
    
    width = max(fonts["sm"].size(line)[0] for line in lines) + 16
    height = len(lines) * (fonts["sm"].get_height() + 4) + 10
    tx = min(mx + 20, SCREEN_W - SIDEBAR_W - width - 10)
    ty = max(10, min(my + 20, screen_h - HUD_H - height - 10))

    panel(screen, tx, ty, width, height, 220)
    pygame.draw.rect(screen, C_GOLD, (tx, ty, width, height), 1, border_radius=4)
    for i, line in enumerate(lines):
        text(screen, fonts, "sm", line, tx + 8, ty + 8 + i * (fonts["sm"].get_height() + 4), C_WHITE)

def draw_build_panel(screen, fonts, game_state):
    """Panel xây dựng công trình - gọi khi nhấn B"""
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
    text(screen, fonts, "med", "X", close_btn.x + 8, close_btn.y + 5, C_WHITE)

# ── Leaderboard ─────────────────────────────────────
def draw_leaderboard(screen, fonts, game_state, x=16, y=16, width=260, max_rows=6):
    sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.gdp, reverse=True)
    height = 32 + max_rows * 18 + 14
    panel(screen, x, y, width, height, 230)
    pygame.draw.rect(screen, C_GOLD, (x, y, width, height), 1, border_radius=6)

    title = fonts["med"].render("BẢNG XẾP HẠNG GDP", True, C_GOLD)
    screen.blit(title, (x + 10, y + 8))
    ty = y + 32

    for idx, country in enumerate(sorted_countries[:max_rows]):
        display_name = COUNTRY_NAMES.get(country.tag, country.tag)
        if display_name is None:
            display_name = country.tag if country.tag else "Unknown"
        if display_name and len(display_name) > 14:
            display_name = display_name[:11] + "..."
        row_color = C_WHITE if country.tag == game_state.player_tag else C_GREY
        text(screen, fonts, "sm", f"{idx+1}. {display_name}", x + 10, ty, row_color)
        gdp_text = fonts["sm"].render(f"{country.gdp:.0f}M", True, row_color)
        screen.blit(gdp_text, (x + width - gdp_text.get_width() - 10, ty))
        ty += 18

    if game_state.player_tag not in [c.tag for c in sorted_countries[:max_rows]]:
        player = game_state.player_country
        if player:
            ty += 6
            text(screen, fonts, "sm", "...", x + 10, ty, C_GREY)
            ty += 18
            player_name = COUNTRY_NAMES.get(player.tag, player.tag)
            if player_name and len(player_name) > 14:
                player_name = player_name[:11] + "..."
            text(screen, fonts, "sm", f"* {player_name}", x + 10, ty, C_WHITE)
            gdp_text = fonts["sm"].render(f"{player.gdp:.0f}M", True, C_WHITE)
            screen.blit(gdp_text, (x + width - gdp_text.get_width() - 10, ty))


# ── Sidebar ──────────────────────────────────────────
def draw_sidebar(screen, fonts, tag, game_state, screen_h):
    if not tag or tag in ("SEA","LAKE"): return
    x = SCREEN_W - SIDEBAR_W

    panel(screen, x, 0, SIDEBAR_W, screen_h, 240)
    pygame.draw.line(screen, C_GOLD_DIM, (x,0),(x,screen_h), 2)

    raw = game_state.countries_data.get(tag,[100,100,100])
    c = tuple(int(v) for v in raw[:3])
    pygame.draw.rect(screen, c, (x,0,SIDEBAR_W,50))
    pygame.draw.line(screen, C_GOLD, (x,50),(x+SIDEBAR_W,50), 2)

    name = COUNTRY_NAMES.get(tag, tag)
    ns = fonts["title"].render(name,True,C_WHITE)
    if ns.get_width() > SIDEBAR_W-20: 
        ns = fonts["sm"].render(name,True,C_WHITE)
    screen.blit(ns,(x+10, (50-ns.get_height())//2))
    
    y = 60
    country = game_state.countries.get(tag)
    if country:
        # Dùng row đơn giản hơn
        y = row(screen,fonts,x,y,"Dân số", f"{country.population:.1f}M", C_GREEN)
        y = row(screen,fonts,x,y,"GDP", f"{country.gdp:.0f}M £", (180,220,255))
        y = divider(screen,x,y,SIDEBAR_W)
        y = row(screen,fonts,x,y,"Ngân khố", f"£{country.treasury:.0f}",
                C_GREEN if country.treasury>=0 else C_RED)
        y = row(screen,fonts,x,y,"Thuế", f"{country.tax_rate*100:.0f}%", (220,200,140))
        y = divider(screen,x,y,SIDEBAR_W)
        y = row(screen,fonts,x,y,"Quân đội", f"{country.army_size}k", (220,160,100))
        y = row(screen,fonts,x,y,"Uy tín", f"{country.prestige:.0f}", (200,200,100))
        y = divider(screen,x,y,SIDEBAR_W)
        
        # Báo cáo kinh tế gọn
        rep = game_state.economy_report.get(tag)
        if rep:
            dy = C_GREEN if rep["delta"]>=0 else C_RED
            y = row(screen,fonts,x,y,"Thu nhập", f"+{rep['income']:.0f}£", C_GREEN)
            y = row(screen,fonts,x,y,"Chi phí", f"-{rep['expense']:.0f}£", C_RED)
            y = row(screen,fonts,x,y,"Cân đối", f"{rep['delta']:+.0f}£", dy)
            y = divider(screen,x,y,SIDEBAR_W)
    
    # Hints gọn
    for i, txt in enumerate(["SPACE: Next Turn", "F2: Ngoại giao", "B: Xây dựng"]):
        hs = fonts["sm"].render(txt,True,(80,90,110))
        screen.blit(hs,(x+10, screen_h-40+i*16))

# ── HUD ──────────────────────────────────────────────
def draw_hud(screen, fonts, game_state, screen_w, screen_h):
    y0 = screen_h - HUD_H
    panel(screen,0,y0,screen_w,HUD_H,250)
    pygame.draw.line(screen,C_GOLD,(0,y0),(screen_w,y0),2)
    
    for i in range(HUD_H):
        alpha = int(200 - i * 2)
        s = pygame.Surface((screen_w, 1), pygame.SRCALPHA)
        s.fill((*C_PANEL, alpha))
        screen.blit(s, (0, y0 + i))

    tag  = game_state.player_tag
    mode = getattr(game_state,"player_mode","default")

    flag_r = pygame.Rect(8,y0+4,60,40)
    fl = get_flag(tag,mode,(60,40))
    if fl: 
        screen.blit(fl,flag_r.topleft)
        pygame.draw.rect(screen, (C_GOLD[0], C_GOLD[1], C_GOLD[2], 100), flag_r, 2, border_radius=4)
    else:
        raw = game_state.countries_data.get(tag,[100,100,100])
        pygame.draw.rect(screen,tuple(int(v)for v in raw[:3]),flag_r,border_radius=4)
        ft = fonts["med"].render(tag,True,C_WHITE)
        screen.blit(ft,ft.get_rect(center=flag_r.center))
    pygame.draw.rect(screen,C_GOLD,flag_r,2,border_radius=4)

    name_text = COUNTRY_NAMES.get(tag,tag)
    shadow = fonts["hud"].render(name_text, True, (0,0,0))
    screen.blit(shadow, (77, y0+(HUD_H-shadow.get_height())//2 + 1))
    ns = fonts["hud"].render(name_text, True, (220,200,140))
    screen.blit(ns,(76,y0+(HUD_H-ns.get_height())//2))

    country = game_state.countries.get(tag)
    if country:
        pound_icon = fonts["med"].render("£", True, C_GOLD)
        screen.blit(pound_icon, (265, y0+(HUD_H-pound_icon.get_height())//2))
        ts = fonts["med"].render(f"{country.treasury:.0f}", True,
             C_GREEN if country.treasury>=0 else C_RED)
        screen.blit(ts, (280, y0+(HUD_H-ts.get_height())//2))

    clock_icon = fonts["sm"].render("📅", True, C_GOLD)
    screen.blit(clock_icon, (screen_w//2 - 60, y0+(HUD_H-clock_icon.get_height())//2))
    
    ds = fonts["date"].render(game_state.current_date.full, True, C_GOLD)
    screen.blit(ds, (screen_w//2 - ds.get_width()//2, y0+(HUD_H-ds.get_height())//2))

    mx,my = pygame.mouse.get_pos()
    bw,bh = 150,36
    bx = screen_w-bw-16
    by = y0+(HUD_H-bh)//2
    btn = pygame.Rect(bx,by,bw,bh)
    hov = btn.collidepoint(mx,my)
    
    if hov:
        color1 = (65, 150, 85)
        color2 = (45, 110, 65)
    else:
        color1 = (45, 110, 65)
        color2 = (35, 80, 50)
    
    for i in range(bh):
        ratio = i / bh
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (bx, by + i), (bx + bw, by + i))
    
    pygame.draw.rect(screen, C_GOLD, btn, 2, border_radius=8)
    bt = fonts["hud"].render("▶ NEXT TURN", True, (200,255,210))
    screen.blit(bt, bt.get_rect(center=btn.center))
    return btn


# ── Cache helpers ───────────────────────────────────
_closest_cache = {}

def find_closest_province(rgb, color_to_province, tolerance=10):
    r, g, b = rgb
    key = (r, g, b, tolerance)
    if key in _closest_cache:
        return _closest_cache[key]
    
    best_prov = None
    best_dist = float('inf')
    
    for color, prov in color_to_province.items():
        cr, cg, cb = color
        dist = ((r-cr)**2 + (g-cg)**2 + (b-cb)**2) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_prov = prov
    
    result = best_prov if best_dist <= tolerance else None
    _closest_cache[key] = result
    return result


# ── Diplomacy Panel ─────────────────────────────────
def draw_diplomacy_panel(screen, fonts, game_state, mouse_pos):
    global diplomacy_selected_tag
    
    sw, sh = screen.get_size()
    panel_x = (sw - DIPLOMACY_PANEL_W) // 2
    panel_y = (sh - DIPLOMACY_PANEL_H) // 2
    
    panel(screen, panel_x, panel_y, DIPLOMACY_PANEL_W, DIPLOMACY_PANEL_H, 250)
    text(screen, fonts, "big", "NGHỊ TRÌNH NGOẠI GIAO", panel_x + 20, panel_y + 15, C_GOLD)
    
    country = game_state.player_country
    y = panel_y + 60
    
    close_btn = pygame.Rect(panel_x + DIPLOMACY_PANEL_W - 40, panel_y + 10, 30, 30)
    hover_close = close_btn.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (160, 45, 45) if hover_close else (90, 30, 30), close_btn, border_radius=4)
    text(screen, fonts, "med", "X", close_btn.x + 10, close_btn.y + 6, C_WHITE)
    
    relations_list = sorted(country.relations.items(), key=lambda x: x[1], reverse=True)
    
    for tag, relation in relations_list:
        rel_color = get_relations_color(relation)
        rel_name = COUNTRY_NAMES.get(tag, tag)
        
        row_rect = pygame.Rect(panel_x + 10, y - 5, DIPLOMACY_PANEL_W - 20, 40)
        if row_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (45, 55, 75), row_rect, border_radius=4)
            diplomacy_selected_tag = tag
        
        text(screen, fonts, "med", rel_name, panel_x + 20, y, C_WHITE)
        rel_text = f"{relation:+d}"
        text(screen, fonts, "med", rel_text, panel_x + 180, y, rel_color)
        
        improve_btn = pygame.Rect(panel_x + 250, y - 5, 95, 28)
        worsen_btn = pygame.Rect(panel_x + 355, y - 5, 95, 28)
        
        hover_improve = improve_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (40, 100, 60) if hover_improve else (30, 70, 40), improve_btn, border_radius=4)
        text(screen, fonts, "sm", "Cải thiện", improve_btn.x + 12, improve_btn.y + 6, C_WHITE)
        
        hover_worsen = worsen_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (140, 50, 50) if hover_worsen else (100, 30, 30), worsen_btn, border_radius=4)
        text(screen, fonts, "sm", "Làm xấu", worsen_btn.x + 15, worsen_btn.y + 6, C_WHITE)
        
        if hover_improve and pygame.mouse.get_pressed()[0]:
            country.relations[tag] = min(100, country.relations.get(tag, 0) + 10)
            pygame.time.wait(200)
        if hover_worsen and pygame.mouse.get_pressed()[0]:
            country.relations[tag] = max(-100, country.relations.get(tag, 0) - 10)
            pygame.time.wait(200)
        
        y += 42
        if y > panel_y + DIPLOMACY_PANEL_H - 80:
            break
    
    if diplomacy_selected_tag and diplomacy_selected_tag != country.tag:
        war_btn = pygame.Rect(panel_x + DIPLOMACY_PANEL_W - 160, panel_y + DIPLOMACY_PANEL_H - 50, 140, 35)
        hover_war = war_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (160, 40, 40) if hover_war else (120, 30, 30), war_btn, border_radius=4)
        text(screen, fonts, "med", "TUYÊN CHIẾN", war_btn.x + 15, war_btn.y + 8, C_WHITE)
        
        if hover_war and pygame.mouse.get_pressed()[0]:
            target_name = COUNTRY_NAMES.get(diplomacy_selected_tag, diplomacy_selected_tag)
            country.at_war_with.add(diplomacy_selected_tag)
            country.relations[diplomacy_selected_tag] = max(-100, country.relations.get(diplomacy_selected_tag, 0) - 50)
            game_state.last_event = {
                "title": "CHIẾN TRANH!",
                "desc": f"{COUNTRY_NAMES.get(country.tag, country.tag)} tuyên chiến với {target_name}.",
                "effect_text": f"Quan hệ với {target_name} -50"
            }
            pygame.time.wait(200)
    
    return close_btn


# ── LOBBY ────────────────────────────────────────────
def run_lobby(screen, fonts, original_map, pol_map, color_to_province, zoom_level):
    global game_state_ref
    sw,sh    = screen.get_size()
    map_w,map_h = original_map.get_size()
    zoom     = zoom_level
    cam_x    = cam_y = 0.0
    is_pan   = False
    last_pos = (0,0)
    sel_tag  = None
    sel_mode = "default"
    mode_idx = 0
    PANEL_H  = 110
    panel_y  = sh-PANEL_H
    exit_r   = pygame.Rect(sw-44,8,36,36)
    btn_st   = pygame.Rect(sw-200,panel_y+32,184,46)
    btn_prev = pygame.Rect(0,0,1,1)
    btn_next = pygame.Rect(0,0,1,1)

    def clamp(cx,cy):
        sw2=int(map_w*zoom); sh2=int(map_h*zoom)
        return cx%sw2, max(panel_y-sh2,min(0.0,cy))

    sc = pygame.transform.scale(pol_map,(int(map_w*zoom),int(map_h*zoom)))
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                oz=zoom
                zoom=max(zoom_level,min(zoom*(1.15 if event.y>0 else 1/1.15),8.0))
                if oz!=zoom:
                    ex,ey=pygame.mouse.get_pos()
                    cam_x=ex-(ex-cam_x)*(zoom/oz)
                    cam_y=ey-(ey-cam_y)*(zoom/oz)
                    cam_x,cam_y=clamp(cam_x,cam_y)
                    sc=pygame.transform.scale(pol_map,(int(map_w*zoom),int(map_h*zoom)))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex,ey=event.pos
                if event.button==1:
                    if exit_r.collidepoint(ex,ey): pygame.quit(); sys.exit()
                    elif btn_st.collidepoint(ex,ey) and sel_tag:
                        return sel_tag, sel_mode
                    elif btn_prev.collidepoint(ex,ey) and sel_tag:
                        av=avail_modes(sel_tag); mode_idx=(mode_idx-1)%len(av); sel_mode=av[mode_idx]
                    elif btn_next.collidepoint(ex,ey) and sel_tag:
                        av=avail_modes(sel_tag); mode_idx=(mode_idx+1)%len(av); sel_mode=av[mode_idx]
                    elif ey<panel_y:
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

                            if 0 <= rx < map_w and 0 <= ry < map_h:
                                rgb = original_map.get_at((rx, ry))[:3]
                                prov = color_to_province.get(rgb)
                                if not prov:
                                    prov = find_closest_province(rgb, color_to_province, tolerance=5)

                                if prov:
                                    owner = getattr(prov, "owner", None)
                                    if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                        sel_tag = owner
                                        print(f"✓ Chọn: {owner} tại ({rx},{ry}) RGB={rgb}")
                        is_pan = True
                        last_pos = event.pos
                elif event.button==3:
                    is_pan = True
                    last_pos = event.pos

            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button in(1,3): is_pan=False
            elif event.type==pygame.MOUSEMOTION and is_pan:
                ex,ey=event.pos
                cam_x+=ex-last_pos[0]; cam_y+=ey-last_pos[1]
                last_pos=event.pos; cam_x,cam_y=clamp(cam_x,cam_y)

        mx,my=pygame.mouse.get_pos()
        screen.fill(C_SEA)
        sw2=int(map_w*zoom)
        for ox in(0,-sw2,sw2): screen.blit(sc,(int(cam_x)+ox,int(cam_y)))

        ov=pygame.Surface((sw,PANEL_H),pygame.SRCALPHA); ov.fill((*C_BG,240))
        screen.blit(ov,(0,panel_y))
        pygame.draw.line(screen,C_GOLD,(0,panel_y),(sw,panel_y),2)

        t1=fonts["big"].render("Victoria 3 — Simple Engine",True,C_GOLD)
        t2=fonts["sm"].render("Click chon quoc gia  |  Giu chuot de keo  |  Lan chuot de zoom",True,C_GREY)
        screen.blit(t1,(20,panel_y+8)); screen.blit(t2,(20,panel_y+38))

        if sel_tag:
            name=COUNTRY_NAMES.get(sel_tag,sel_tag)
            av=avail_modes(sel_tag)
            fl=get_flag(sel_tag,sel_mode,(90,60))
            fr=pygame.Rect(sw//2-240,panel_y+10,90,60)
            if fl: screen.blit(fl,fr.topleft)
            else:
                raw=game_state_ref.countries_data.get(sel_tag,[80,80,80]) if game_state_ref else [80,80,80]
                pygame.draw.rect(screen,tuple(int(v)for v in raw[:3]),fr,border_radius=4)
            pygame.draw.rect(screen,C_GOLD,fr,1,border_radius=4)
            screen.blit(fonts["title"].render(name,True,C_WHITE),(fr.right+10,panel_y+10))

            TAG_X=fr.right+10; my2=panel_y+44
            btn_prev=pygame.Rect(TAG_X,my2,28,26)
            btn_next=pygame.Rect(TAG_X+200,my2,28,26)
            for br,lbl in((btn_prev,"<"),(btn_next,">")):
                hv=br.collidepoint(mx,my)
                pygame.draw.rect(screen,(60,80,100)if hv else(35,50,65),br,border_radius=4)
                pygame.draw.rect(screen,C_BORDER,br,1,border_radius=4)
                bs=fonts["med"].render(lbl,True,C_WHITE); screen.blit(bs,bs.get_rect(center=br.center))
            ml=fonts["med"].render(GOVT_LABELS.get(sel_mode,sel_mode),True,(160,210,255))
            screen.blit(ml,(TAG_X+34,my2+4))
            cs=fonts["sm"].render(f"{mode_idx+1}/{len(av)}",True,C_GREY)
            screen.blit(cs,(TAG_X+34,my2+22))
        else:
            hs=fonts["hud"].render("Click vao mot quoc gia tren ban do...",True,C_GREY)
            screen.blit(hs,(sw//2-hs.get_width()//2,panel_y+40))
            btn_prev=btn_next=pygame.Rect(0,0,1,1)

        ac=bool(sel_tag)
        bc=(55,150,75)if btn_st.collidepoint(mx,my)and ac else((40,120,60)if ac else(40,48,58))
        pygame.draw.rect(screen,bc,btn_st,border_radius=8)
        if ac: gold_border(screen,btn_st.x,btn_st.y,btn_st.w,btn_st.h,8)
        else: pygame.draw.rect(screen,C_BORDER,btn_st,1,border_radius=8)
        bs=fonts["hud"].render("VAO GAME  >",True,C_WHITE if ac else C_GREY)
        screen.blit(bs,bs.get_rect(center=btn_st.center))

        xh=exit_r.collidepoint(mx,my)
        pygame.draw.rect(screen,(160,45,45)if xh else(90,30,30),exit_r,border_radius=6)
        pygame.draw.rect(screen,(200,70,70),exit_r,1,border_radius=6)
        xs=fonts["title"].render("X",True,C_WHITE); screen.blit(xs,xs.get_rect(center=exit_r.center))

        pygame.display.flip(); clock.tick(60)


# ── GAME ─────────────────────────────────────────────
def run_game(screen, fonts, game_state, original_map, pol_map,
             color_to_province, init_zoom, combined_political, combined_province):
    global show_diplomacy, diplomacy_selected_tag, current_map_mode
    
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()
    zoom = init_zoom
    cam_x = cam_y = 0.0
    is_pan = False
    last_pos = (0, 0)
    sel_tag = game_state.player_tag
    cur_map = combined_political  # Mặc định là bản đồ chính trị + tên nước
    next_turn_cooldown = 0
    show_diplomacy = False
    diplomacy_selected_tag = None
    current_map_mode = MAP_MODE_POLITICAL
    show_build_panel = False

    def clamp(cx, cy):
        sw2 = int(map_w * zoom)
        sh2 = int(map_h * zoom)
        return cx % sw2, max(sh - HUD_H - sh2, min(0.0, cy))

    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))
    clock = pygame.time.Clock()

    while True:
        if next_turn_cooldown > 0:
            next_turn_cooldown -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    show_diplomacy = False
                    return
                elif event.key == pygame.K_SPACE and next_turn_cooldown == 0:
                    game_state.next_turn()
                    next_turn_cooldown = 10
                elif event.key == pygame.K_F2:
                    show_diplomacy = not show_diplomacy
                elif event.key == pygame.K_1:
                    current_map_mode = MAP_MODE_POLITICAL
                    cur_map = combined_political
                    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))
                    print("Switched to: Political Map")
                elif event.key == pygame.K_2:
                    current_map_mode = MAP_MODE_PROVINCE_NAMES
                    cur_map = combined_province
                    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))
                    print("Switched to: Province Map")
                elif event.key == pygame.K_b:
                    show_build_panel = not show_build_panel

            elif event.type == pygame.MOUSEWHEEL:
                oz = zoom
                zoom = max(init_zoom, min(zoom * (1.2 if event.y > 0 else 1 / 1.2), ZOOM_MAX))
                if oz != zoom:
                    mx, my = pygame.mouse.get_pos()
                    cam_x = mx - (mx - cam_x) * (zoom / oz)
                    cam_y = my - (my - cam_y) * (zoom / oz)
                    cam_x, cam_y = clamp(cam_x, cam_y)
                    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex, ey = event.pos
                if event.button == 1:  # Left click - chọn quốc gia
                    if ex < sw - SIDEBAR_W and ey < sh - HUD_H:
                        rx = int((ex - cam_x) / zoom)
                        ry = int((ey - cam_y) / zoom)
                        if 0 <= rx < map_w and 0 <= ry < map_h:
                            rgb = original_map.get_at((rx, ry))[:3]
                            prov = color_to_province.get(rgb)
                            if not prov:
                                prov = find_closest_province(rgb, color_to_province, tolerance=5)
                            owner = getattr(prov, "owner", None) if prov else None
                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                print(f"Selected: {owner} (left click)")
                        is_pan = True
                        last_pos = event.pos
                elif event.button == 3:  # Right click - mở diplomacy
                    if ex < sw - SIDEBAR_W and ey < sh - HUD_H:
                        rx = int((ex - cam_x) / zoom)
                        ry = int((ey - cam_y) / zoom)
                        if 0 <= rx < map_w and 0 <= ry < map_h:
                            rgb = original_map.get_at((rx, ry))[:3]
                            prov = color_to_province.get(rgb)
                            if not prov:
                                prov = find_closest_province(rgb, color_to_province, tolerance=5)
                            owner = getattr(prov, "owner", None) if prov else None
                            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                sel_tag = owner
                                show_diplomacy = True
                                print(f"Selected: {owner} (right click) - Diplomacy panel opened")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_pan = False

            elif event.type == pygame.MOUSEMOTION and is_pan:
                ex, ey = event.pos
                cam_x += ex - last_pos[0]
                cam_y += ey - last_pos[1]
                last_pos = event.pos
                cam_x, cam_y = clamp(cam_x, cam_y)

        # Render
        mx, my = pygame.mouse.get_pos()
        screen.fill(C_SEA)
        sw2 = int(map_w * zoom)
        for ox in (0, -sw2, sw2):
            screen.blit(sc, (int(cam_x) + ox, int(cam_y)))

        draw_sidebar(screen, fonts, sel_tag, game_state, sh)
        btn = draw_hud(screen, fonts, game_state, sw, sh)

        draw_leaderboard(screen, fonts, game_state, x=16, y=16, width=260, max_rows=6)

        if show_build_panel:
            draw_build_panel(screen, fonts, game_state)

        # Xử lý click nút Next Turn
        if pygame.mouse.get_pressed()[0] and next_turn_cooldown == 0:
            if btn.collidepoint(mx, my):
                game_state.next_turn()
                next_turn_cooldown = 10

        # Nút MENU
        menu_r = pygame.Rect(sw - SIDEBAR_W - 110, 8, 100, 30)
        mh = menu_r.collidepoint(mx, my)
        pygame.draw.rect(screen, (75, 45, 18) if mh else (45, 28, 12), menu_r, border_radius=6)
        gold_border(screen, menu_r.x, menu_r.y, menu_r.w, menu_r.h, 6)
        ms = fonts["sm"].render("< MENU", True, C_GOLD)
        screen.blit(ms, ms.get_rect(center=menu_r.center))
        if pygame.mouse.get_pressed()[0] and mh:
            show_diplomacy = False
            return

        help_text = fonts["sm"].render("F2: Diplomacy | L-Click: Select | R-Click: Select & Diplomacy", True, C_GOLD_DIM)
        screen.blit(help_text, (10, sh - HUD_H - help_text.get_height() - 5))

        # Diplomacy Panel
        if show_diplomacy:
            close_btn = draw_diplomacy_panel(screen, fonts, game_state, (mx, my))
            if close_btn.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                show_diplomacy = False
                pygame.time.wait(200)

        pygame.display.flip()
        clock.tick(FPS)

# ── ENTRY ────────────────────────────────────────────
def start_engine(game_state):
    global game_state_ref, country_name_surface, province_name_surface, current_map_mode
    game_state_ref = game_state

    print("Initializing Pygame...")
    pygame.init()
    pygame.font.init()

    from engine.fonts import load_vic3_fonts
    vic3_fonts = load_vic3_fonts()

    from engine.state_resource_loader import load_state_resources, build_color_cache
    state_resources = load_state_resources()
    build_color_cache(state_resources)
    
    print(f"Creating screen {SCREEN_W}x{SCREEN_H}...")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    
    print("Loading fonts...")
    fonts = load_fonts()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Loading flags from {base_dir}...")
    load_flags(base_dir)

    map_path = os.path.join(base_dir,"data","map_data","provinces.png")
    print(f"Loading map from {map_path}...")
    original_map = pygame.image.load(map_path).convert()
    
    print("Building color map...")
    color_to_province = {p.color:p for p in game_state.provinces.values()}

    full_path = os.path.join(base_dir,"data","countries_full.json")
    try: 
        with open(full_path, "r", encoding="utf-8") as f:
            countries_full = json.load(f)
        print(f"Loaded countries_full.json with {len(countries_full)} entries")
    except: 
        countries_full = {}
        print("No countries_full.json found")

    print("Generating political map...")
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
    province_name_surface = generate_province_name_map(original_map, color_to_province, fonts)

    map_w, map_h = original_map.get_size()
    init_zoom = max(SCREEN_W / map_w, SCREEN_H / map_h)
    print(f"Map size: {map_w}x{map_h}, initial zoom: {init_zoom:.2f}")

    print("Entering game loop...")
    while True:
        tag, mode = run_lobby(screen, fonts, original_map, pol_map,
                              color_to_province, init_zoom)
        print(f"Selected: {tag} / {mode}")
        game_state.player_tag = tag
        game_state.player_mode = mode
        
        for t in game_state.countries:
            if t != tag and t not in game_state.countries[tag].relations:
                game_state.countries[tag].relations[t] = 0
        
        run_game(screen, fonts, game_state, original_map, pol_map,
                 color_to_province, init_zoom, country_name_surface, province_name_surface)