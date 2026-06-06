import pygame, numpy as np, sys, os, json, pickle

# ── Constants ──────────────────────────────────────
from config import (
    SCREEN_W, SCREEN_H, FPS, TITLE, ZOOM_MAX,
    C_BG, C_PANEL, C_BORDER, C_GOLD, C_GOLD_DIM,
    C_SEA, C_LAKE, C_WHITE, C_GREY, C_GREEN, C_RED,
    C_LAND_EMPTY, C_COLONIZABLE, COLONIZABLE_TYPES
)
from engine.state_resource_loader import RESOURCE_DISPLAY
from engine.state_resource_loader import get_state_for_province
from engine.country_names import get_country_display_name, COUNTRY_NAMES

SIDEBAR_W = 280
HUD_H     = 64
MONTH_FULL = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

GOVT_LABELS = {
    "default":"Mac dinh",           "absolute_monarchy":"Quan chu chuyen che",
    "republic":"Cong hoa",          "dictatorship":"Doc tai",
    "theocracy":"Than quyen",       "communist":"Cong san",
    "fascist":"Phat xit",           "subject":"Phu thuoc",
}

DIPLOMACY_PANEL_W = 530
DIPLOMACY_PANEL_H = 620
MAP_MODE_POLITICAL = 0
MAP_MODE_COUNTRY_NAMES = 1
MAP_MODE_PROVINCE_NAMES = 2
MAP_MODE_EPIDEMIC = 3

current_map_mode = MAP_MODE_POLITICAL
country_name_surface = None
province_name_surface = None
_cached_u32_map = None
_cached_state_borders_mask = None
_cached_coast_mask = None
pristine_pol_map = None
pristine_country_name_surface = None
pristine_combined_political = None
game_state_ref = None
show_diplomacy = False
show_build_panel = False
show_politics_panel = False
show_war_panel = False
diplomacy_selected_tag = None
_province_to_state_fast = {}  # fast lookup: province_color -> State object
countries_full = {}
_diplo_scroll = 0              # scroll offset for diplomacy detail view
_diplo_list_scroll = 0         # scroll offset for diplomacy country list
_leaderboard_open = False      # collapsible leaderboard state
_leaderboard_scroll = 0        # scroll offset for country leaderboard
_profile_tag = None            # selected country for profile panel
_profile_scroll = 0           # scroll offset for profile panel
_state_resources = None

# ── Global flags cache ──────────────────────────────
_flags = {}   # { TAG: { mode: Surface } }
_country_centers = {}   # { TAG: (cx, cy) }

# ── Fonts ───────────────────────────────────────────
def load_fonts():
    from engine.fonts import load_vic3_fonts
    return load_vic3_fonts()

def draw_button(screen, fonts, rect, text_str, bg_color, border_color, text_color, mouse_pos, font_key="sm"):
    hover = rect.collidepoint(mouse_pos)
    if hover:
        bg_draw = tuple(min(255, c + 25) for c in bg_color)
    else:
        bg_draw = bg_color
    pygame.draw.rect(screen, bg_draw, rect, border_radius=4)
    pygame.draw.rect(screen, border_color, rect, 1, border_radius=4)
    if border_color != bg_color and rect.width > 4 and rect.height > 4:
        pygame.draw.rect(screen, C_GOLD_DIM if hover else (min(255, bg_draw[0]+15), min(255, bg_draw[1]+15), min(255, bg_draw[2]+15)), 
                         (rect.x+1, rect.y+1, rect.width-2, rect.height-2), 1, border_radius=3)
    if text_str:
        s = fonts[font_key].render(text_str, True, text_color)
        screen.blit(s, s.get_rect(center=rect.center))
    return hover


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

_ranks = {}
_leaderboard_row_held = False
_hud_flag_held = False
_hud_pol_held = False
_leaderboard_btn_held = False
_menu_btn_held_global = False
_menu_open = False
_menu_mode = "main"  # main, save, load
_leaderboard_sort_by = "prestige"
_leaderboard_header_held = False
initial_game_state_backup_bytes = None

PARSED_LAWS = {}
_selected_law_category = None
_law_scroll = 0

def load_laws_from_txt(base_dir):
    global PARSED_LAWS
    PARSED_LAWS = {}
    d = os.path.join(base_dir, "data", "laws")
    if not os.path.exists(d):
        print(f"Laws directory not found: {d}")
        return
        
    for fn in os.listdir(d):
        if not fn.endswith(".txt"):
            continue
        path = os.path.join(d, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            category = fn.replace(".txt", "")
            
            rows = content.split("|-")
            for row in rows:
                if "{{" not in row:
                    continue
                import re
                match = re.search(r"\{\{iconbox\|([^|]+)\|([^|}]+)", row)
                if not match:
                    continue
                name = match.group(1).strip()
                desc = match.group(2).strip()
                
                lines = row.split("\n")
                reqs = []
                effects = []
                
                cell_idx = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("|-"):
                        continue
                    if line.startswith("|"):
                        cell_idx += 1
                        line = line[1:].strip()
                    
                    if not line:
                        continue
                        
                    if cell_idx == 2: # Requirements cell
                        clean_req = re.sub(r"\{\{[^|]+\|([^|}]+)[^}]*\}\}", r"\1", line)
                        clean_req = clean_req.replace("'''", "").replace("''", "").strip()
                        if clean_req and not clean_req.startswith("image="):
                            reqs.append(clean_req)
                    elif cell_idx == 3: # Effects cell
                        if line.startswith("*"):
                            clean_eff = line[1:].strip()
                            clean_eff = re.sub(r"\{\{[^|]+\|([^|}]+)[^}]*\}\}", r"\1", clean_eff)
                            clean_eff = clean_eff.replace("'''", "").replace("''", "").strip()
                            if clean_eff:
                                effects.append(clean_eff)
                                
                if not effects:
                    for line in lines:
                        line = line.strip()
                        if line.startswith("*"):
                            clean_eff = re.sub(r"\{\{[^|]+\|([^|}]+)[^}]*\}\}", r"\1", line[1:])
                            clean_eff = clean_eff.replace("'''", "").replace("''", "").strip()
                            if clean_eff:
                                effects.append(clean_eff)
                                
                PARSED_LAWS[name] = {
                    "category": category,
                    "desc": desc,
                    "requirements": [r for r in reqs if r and not r.startswith("{") and not r.startswith("image=")],
                    "effects": effects
                }
        except Exception as e:
            print(f"Error parsing law file {fn}: {e}")
            
    print(f"Parsed {len(PARSED_LAWS)} laws dynamically.")

def load_ranks(base_dir):
    global _ranks
    d = os.path.join(base_dir, "data", "rank")
    if not os.path.exists(d): 
        print(f"Directory not found: {d}")
        return
    for fn in os.listdir(d):
        if not fn.endswith(".png"): continue
        name = fn[:-4].lower()
        try:
            img = pygame.image.load(os.path.join(d, fn)).convert_alpha()
            _ranks[name] = img
        except Exception as e:
            print(f"Error loading rank image {fn}: {e}")
    print(f"Ranks: {len(_ranks)} classes loaded")
    load_laws_from_txt(base_dir)

_hud_icons = {}
def get_hud_icon(name):
    if name not in _hud_icons:
        path = os.path.join("data", "hud", f"{name}.png")
        if os.path.exists(path):
            try:
                _hud_icons[name] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"Error loading HUD icon {name}: {e}")
                _hud_icons[name] = None
        else:
            _hud_icons[name] = None
    return _hud_icons[name]

_regime_icons = {}
def get_regime_icon(r_type):
    if r_type not in _regime_icons:
        mapping = {
            "default": "Monarchy.png",
            "absolute_monarchy": "Monarchy.png",
            "republic": "Presidential Republic.png",
            "dictatorship": "Autocracy.png",
            "theocracy": "Theocracy.png",
            "communist": "Council Republic.png",
            "fascist": "Corporate State.png"
        }
        fn = mapping.get(r_type)
        if fn:
            path = os.path.join("data", "laws", fn)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    _regime_icons[r_type] = img
                except Exception as e:
                    print(f"Error loading regime icon {fn}: {e}")
                    _regime_icons[r_type] = None
            else:
                _regime_icons[r_type] = None
        else:
            _regime_icons[r_type] = None
    return _regime_icons[r_type]

_law_icons = {}
def get_law_icon(law_fn):
    if not law_fn:
        return None
    if law_fn not in _law_icons:
        path = os.path.join("data", "laws", law_fn)
        if os.path.exists(path):
            try:
                _law_icons[law_fn] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"Error loading law icon {law_fn}: {e}")
                _law_icons[law_fn] = None
        else:
            _law_icons[law_fn] = None
    return _law_icons[law_fn]

LAW_ICONS = {
    "Tự do Thương mại": "Law_merchant_fleet.png",
    "Thương mại tự do": "Law_merchant_fleet.png",
    "Luật Báo chí tự do": "Law_guaranteed_liberties.png",
    "Tự do ngôn luận": "Law_guaranteed_liberties.png",
    "Quyền Tự do ngôn luận": "Law_guaranteed_liberties.png",
    "Nghĩa vụ Quân sự": "Law_mass_conscription.png",
    "Nghĩa vụ Quân sự bắt buộc": "Law_mass_conscription.png",
    "Phổ thông đầu phiếu": "Law_universal_suffrage.png",
    "Tôn giáo Quốc giáo": "Law_state_religion.png",
    "Quyền lực Giáo hội tăng": "Law_state_religion.png",
    "Cải cách ruộng đất": "Law_organic_regulation.png",
    "Nghiệp đoàn lao động": "Law_affirmative_action.png",
    "BẤT HỢP PHÁP: Phổ thông đầu phiếu": "Law_universal_suffrage.png",
    "BẤT HỢP PHÁP: Tự do báo chí": "Law_guaranteed_liberties.png",
    "BẤT HỢP PHÁP: Tự do ngôn luận": "Law_guaranteed_liberties.png",
    "BẤT HỢP PHÁP: Nghiệp đoàn lao động": "Law_affirmative_action.png",
    "BẤT HỢP PHÁP: Thương mại tự do": "Law_merchant_fleet.png"
}

REGIME_SIGNATURE_LAWS = {
    "default": ["Monarchy", "Appointed Bureaucrats", "Freedom of Conscience"],
    "absolute_monarchy": ["Monarchy", "Autocracy", "Professional Army", "Secret Police"],
    "republic": ["Presidential Republic", "Universal Suffrage", "Appointed Bureaucrats"],
    "dictatorship": ["Autocracy", "Appointed Bureaucrats", "Secret Police"],
    "theocracy": ["Theocracy", "State Religion", "Hereditary Bureaucrats"],
    "communist": ["Council Republic", "Universal Suffrage", "Appointed Bureaucrats"],
    "fascist": ["Single-Party State", "Corporate State", "Secret Police"]
}

def resolve_law_icon_fn(law_id):
    fn = f"{law_id}.png"
    if os.path.exists(os.path.join("data", "laws", fn)):
        return fn
    clean = law_id.lower().replace(" ", "_")
    fn = f"Law_{clean}.png"
    if os.path.exists(os.path.join("data", "laws", fn)):
        return fn
    return None

def get_sol_icon_name(sol_val):
    if sol_val < 5.0:
        return "SOL_destitute"
    elif sol_val < 10.0:
        return "SOL_struggling"
    elif sol_val < 15.0:
        return "SOL_impoverished"
    elif sol_val < 20.0:
        return "SOL_middling"
    elif sol_val < 25.0:
        return "SOL_secure"
    elif sol_val < 30.0:
        return "SOL_prosperous"
    elif sol_val < 40.0:
        return "SOL_affluent"
    elif sol_val < 50.0:
        return "SOL_wealthy"
    elif sol_val < 60.0:
        return "SOL_lavish"
    else:
        return "SOL_opulent"

_country_rank_cache = {}
_cached_max_prestige = 0.0
_cached_avg_prestige = 0.0
_cached_overlord_map = {}

def get_country_rank(country, game_state):
    global _country_rank_cache, _cached_max_prestige, _cached_avg_prestige
    if country.tag in _country_rank_cache:
        return _country_rank_cache[country.tag]
        
    if not _country_rank_cache:
        sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.prestige, reverse=True)
        countries_list = list(game_state.countries.values())
        if not countries_list:
            _cached_max_prestige = 0.0
            _cached_avg_prestige = 0.0
        else:
            prestige_values = [c.prestige for c in countries_list]
            _cached_max_prestige = max(prestige_values)
            _cached_avg_prestige = sum(prestige_values) / len(countries_list)
            
        for idx, c in enumerate(sorted_countries):
            prestige = c.prestige
            if prestige >= 5.0 * _cached_avg_prestige or prestige >= 0.75 * _cached_max_prestige:
                rank_class = "great_power"
                rank_name = "Cuong quoc"
            elif prestige >= 2.5 * _cached_avg_prestige or prestige >= 0.5 * _cached_max_prestige:
                rank_class = "major_power"
                rank_name = "Dai cuong"
            elif prestige >= 0.6 * _cached_avg_prestige or prestige >= 0.15 * _cached_max_prestige:
                rank_class = "minor_power"
                rank_name = "Cuong quoc nho"
            else:
                rank_class = "insignificant_power"
                rank_name = "Nhuoc tieu"
            _country_rank_cache[c.tag] = (idx + 1, rank_class, rank_name)
            
    return _country_rank_cache.get(country.tag, (999, "insignificant_power", "Nhuoc tieu"))

def get_overlord(tag, game_state=None):
    global _cached_overlord_map
    gs = game_state or game_state_ref
    if not gs: return None
    
    if tag in _cached_overlord_map:
        return _cached_overlord_map[tag]
        
    for c_tag, c in gs.countries.items():
        if tag in getattr(c, 'subjects', set()):
            _cached_overlord_map[tag] = c_tag
            return c_tag
            
    _cached_overlord_map[tag] = None
    return None

_shaded_flags_cache = {}

def apply_flag_shader(surf):
    w, h = surf.get_size()
    shader = pygame.Surface((w, h), pygame.SRCALPHA)
    import math
    for x in range(w):
        wave1 = math.sin(x * 0.15) * 28
        wave2 = math.cos(x * 0.08) * 15
        for y in range(h):
            diag = (1.0 - (x / w + y / h) / 2.0) * 45
            edge_x = min(x, w - 1 - x) / w
            edge_y = min(y, h - 1 - y) / h
            edge_shade = (1.0 - min(1.0, (edge_x * 6.0) * (edge_y * 6.0))) * -55
            
            shade = int(128 + wave1 + wave2 + diag + edge_shade)
            shade = max(0, min(255, shade))
            
            if shade > 128:
                alpha = int((shade - 128) * 1.6)
                alpha = max(0, min(255, alpha))
                shader.set_at((x, y), (255, 255, 255, alpha))
            else:
                alpha = int((128 - shade) * 1.6)
                alpha = max(0, min(255, alpha))
                shader.set_at((x, y), (0, 0, 0, alpha))
    surf.blit(shader, (0, 0))

def get_flag(tag, mode="default", size=(72,48), overlord=None, game_state=None):
    if overlord is None:
        overlord = get_overlord(tag, game_state)
        
    cache_key = (tag, mode, size, overlord)
    if cache_key in _shaded_flags_cache:
        return _shaded_flags_cache[cache_key]

    entry = _flags.get(tag, {})
    if not entry:
        return None
    
    img = None
    if overlord:
        img = entry.get(f"subject_{overlord}") or entry.get(f"Subject_{overlord}") or entry.get(f"subject_{overlord.upper()}") or entry.get(f"subject_{overlord.lower()}")
        if not img:
            img = entry.get("subject") or entry.get("Subject")
            
    if not img and mode != "default":
        img = entry.get(mode) or entry.get(mode.lower()) or entry.get(mode.upper())
        
    if not img:
        img = entry.get("default")
        
    if img:
        scaled = pygame.transform.scale(img, size)
        apply_flag_shader(scaled)
        _shaded_flags_cache[cache_key] = scaled
        return scaled
    return None

def avail_modes(tag):
    entry = _flags.get(tag, {})
    if not entry:
        return ["default"]
    modes = sorted(list(entry.keys()))
    modes = [m for m in modes if not m.lower().startswith("subject")]
    if "default" in modes:
        modes.remove("default")
    modes.insert(0, "default")
    return modes


# ── Border masks ──────────────────────────────────────
def generate_state_border_mask(original_image, color_to_province):
    """Tạo mask viền giữa các bang. Dùng numpy LUT để đạt tốc độ tối đa."""
    global _cached_state_borders_mask, _cached_u32_map
    if _cached_state_borders_mask is not None:
        return _cached_state_borders_mask
        
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]
    
    from engine.state_resource_loader import _color_to_state_cache

    state_lut = np.zeros(16777216, dtype=np.uint32)
    for rgb, prov in color_to_province.items():
        state = _color_to_state_cache.get(rgb)
        if state:
            state_lut[rgb[0]*65536 + rgb[1]*256 + rgb[2]] = hash(state.name) % (2**32) or 1

    if _cached_u32_map is None:
        _cached_u32_map = (arr[:,:,0].astype(np.uint32)*65536 +
                           arr[:,:,1].astype(np.uint32)*256 +
                           arr[:,:,2].astype(np.uint32))
    state_map = state_lut[_cached_u32_map]

    mask = np.zeros((h, w), dtype=bool)
    mask[:, 1:] |= (state_map[:, 1:] != state_map[:, :-1]) & (state_map[:, 1:] != 0) & (state_map[:, :-1] != 0)
    mask[1:, :] |= (state_map[1:, :] != state_map[:-1, :]) & (state_map[1:, :] != 0) & (state_map[:-1, :] != 0)
    mask &= (state_map != 0)
    _cached_state_borders_mask = mask
    return mask

def generate_province_border_mask(original_image, color_to_province, countries_data):
    """
    Tạo mask cho viền tỉnh, CHỆ vẽ viền giữa các tỉnh khác quốc gia.
    Dùng numpy LUT → nhanh hơn ~100x so với Python loop.
    """
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]

    owner_lut = np.zeros(16777216, dtype=np.uint32)
    for rgb, prov in color_to_province.items():
        owner = getattr(prov, 'owner', None)
        if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
            owner_lut[rgb[0]*65536 + rgb[1]*256 + rgb[2]] = hash(owner) % (2**32) or 1

    global _cached_u32_map
    if _cached_u32_map is None:
        _cached_u32_map = (arr[:,:,0].astype(np.uint32)*65536 +
                           arr[:,:,1].astype(np.uint32)*256 +
                           arr[:,:,2].astype(np.uint32))
    owner_map = owner_lut[_cached_u32_map]

    mask = np.zeros((h, w), dtype=bool)
    mask[:, 1:] |= (owner_map[:, 1:] != owner_map[:, :-1]) & (owner_map[:, 1:] != 0) & (owner_map[:, :-1] != 0)
    mask[1:, :] |= (owner_map[1:, :] != owner_map[:-1, :]) & (owner_map[1:, :] != 0) & (owner_map[:-1, :] != 0)
    mask &= (owner_map != 0)
    return mask

def generate_province_border_mask_only(original_image, color_to_province):
    """Tạo mask viền cho TẤT CẢ các tỉnh. Dùng numpy LUT."""
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]

    prov_lut = np.zeros(16777216, dtype=np.uint32)
    for rgb, prov in color_to_province.items():
        prov_lut[rgb[0]*65536 + rgb[1]*256 + rgb[2]] = prov.id

    global _cached_u32_map
    if _cached_u32_map is None:
        _cached_u32_map = (arr[:,:,0].astype(np.uint32)*65536 +
                           arr[:,:,1].astype(np.uint32)*256 +
                           arr[:,:,2].astype(np.uint32))
    province_map = prov_lut[_cached_u32_map]

    mask = np.zeros((h, w), dtype=bool)
    mask[:, 1:] |= (province_map[:, 1:] != province_map[:, :-1]) & (province_map[:, 1:] != 0) & (province_map[:, :-1] != 0)
    mask[1:, :] |= (province_map[1:, :] != province_map[:-1, :]) & (province_map[1:, :] != 0) & (province_map[:-1, :] != 0)
    mask &= (province_map != 0)
    return mask


def generate_political_border_mask(original_image, color_to_province, countries_full):
    """Viền nhạt giữa các nước decentralized / unrecognized / colonial (giống Vic3). Dùng numpy LUT."""
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)
    h, w = arr.shape[:2]

    oid_lut = np.zeros(16777216, dtype=np.uint32)
    col_lut = np.zeros(16777216, dtype=np.uint8)  # 1 = colonizable

    for rgb, prov in color_to_province.items():
        owner = getattr(prov, "owner", None)
        if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
            k = rgb[0]*65536 + rgb[1]*256 + rgb[2]
            oid_lut[k] = hash(owner) % (2**32) or 1
            ctype = countries_full.get(owner, {}).get("type", "recognized")
            col_lut[k] = 1 if ctype in COLONIZABLE_TYPES else 0

    global _cached_u32_map
    if _cached_u32_map is None:
        _cached_u32_map = (arr[:,:,0].astype(np.uint32)*65536 +
                           arr[:,:,1].astype(np.uint32)*256 +
                           arr[:,:,2].astype(np.uint32))
    oid = oid_lut[_cached_u32_map]
    col = col_lut[_cached_u32_map].astype(bool)

    mask = np.zeros((h, w), dtype=bool)
    diff_h = (oid[:, 1:] != oid[:, :-1]) & (oid[:, 1:] != 0) & (oid[:, :-1] != 0)
    col_h = col[:, 1:] | col[:, :-1]
    mask[:, 1:] |= diff_h & col_h
    mask[:, :-1] |= diff_h & col_h

    diff_v = (oid[1:, :] != oid[:-1, :]) & (oid[1:, :] != 0) & (oid[:-1, :] != 0)
    col_v = col[1:, :] | col[:-1, :]
    mask[1:, :] |= diff_v & col_v
    mask[:-1, :] |= diff_v & col_v
    return mask

# ── Map generation ──────────────────────────────────
def generate_political_map(original_image, color_to_province, countries_data, countries_full, mode=MAP_MODE_POLITICAL):
    print("Dang to mau ban do...")
    arr = pygame.surfarray.array3d(original_image).transpose(1,0,2)
    lut_r = np.zeros(16777216, dtype=np.uint8)
    lut_g = np.zeros(16777216, dtype=np.uint8)
    lut_b = np.zeros(16777216, dtype=np.uint8)
    in_lut = np.zeros(16777216, dtype=bool)

    active_war_info = None
    player_is_side_a = True
    player_war_pair = None
    if game_state_ref:
        p_tag = game_state_ref.player_tag
        if p_tag and game_state_ref.player_country and game_state_ref.player_country.at_war_with:
            for pair, w_info in game_state_ref.active_wars.items():
                if p_tag in pair:
                    active_war_info = w_info
                    player_is_side_a = (pair[0] == p_tag)
                    player_war_pair = pair
                    break

    for rgb, prov in color_to_province.items():
        if getattr(prov,"is_sea",False):
            nr,ng,nb = C_SEA
        elif getattr(prov,"is_lake",False):
            nr,ng,nb = C_SEA  # Lakes same colour as sea
        else:
            owner = getattr(prov,"owner",None)
            if mode == MAP_MODE_EPIDEMIC and game_state_ref:
                infected_color = None
                for d_name, epi in game_state_ref.active_epidemics.items():
                    if prov.id in epi["provinces"]:
                        template = epi.get("template")
                        if template:
                            dc = template["color"]
                            if owner and owner in countries_data:
                                oc = countries_data[owner]
                                nr = int(dc[0] * 0.7 + oc[0] * 0.3)
                                ng = int(dc[1] * 0.7 + oc[1] * 0.3)
                                nb = int(dc[2] * 0.7 + oc[2] * 0.3)
                            else:
                                nr = int(dc[0] * 0.7 + 80 * 0.3)
                                ng = int(dc[1] * 0.7 + 80 * 0.3)
                                nb = int(dc[2] * 0.7 + 80 * 0.3)
                            infected_color = (nr, ng, nb)
                            break
                if infected_color:
                    nr, ng, nb = infected_color
                else:
                    nr, ng, nb = (80, 80, 80)
            elif active_war_info and player_war_pair:
                # We are at war! Show war coloring
                war_leader_a, war_leader_b = player_war_pair
                allies_a = active_war_info.get("allies_a", set())
                allies_b = active_war_info.get("allies_b", set())
                
                side_player = allies_a | {war_leader_a} if player_is_side_a else allies_b | {war_leader_b}
                side_enemy = allies_b | {war_leader_b} if player_is_side_a else allies_a | {war_leader_a}
                
                if owner in side_player:
                    nr, ng, nb = (46, 125, 50)  # Green
                elif owner in side_enemy:
                    nr, ng, nb = (198, 40, 40)  # Red
                elif owner and owner in countries_data:
                    nr, ng, nb = (120, 120, 120)  # Gray for uninvolved
                else:
                    nr, ng, nb = C_LAND_EMPTY
            else:
                # Normal coloring
                if owner and owner in countries_data:
                    v = countries_data[owner]
                    nr,ng,nb = int(v[0]),int(v[1]),int(v[2])
                else:
                    nr,ng,nb = C_LAND_EMPTY

        k = rgb[0]*65536+rgb[1]*256+rgb[2]
        lut_r[k]=nr; lut_g[k]=ng; lut_b[k]=nb; in_lut[k]=True

    global _cached_u32_map
    if _cached_u32_map is None:
        _cached_u32_map = (arr[:,:,0].astype(np.uint32)*65536 +
                           arr[:,:,1].astype(np.uint32)*256   +
                           arr[:,:,2].astype(np.uint32))
    u32 = _cached_u32_map
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
        h, w = arr.shape[:2]
        
        # Xây dựng owner map từ các tỉnh đất liền
        owner_lut = np.zeros(16777216, dtype=np.uint32)
        for rgb, prov in color_to_province.items():
            owner = getattr(prov, 'owner', None)
            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                owner_lut[rgb[0]*65536 + rgb[1]*256 + rgb[2]] = hash(owner) % (2**32) or 1
        owner_map = owner_lut[u32]
        
        # 1. Vẽ đường bờ biển (Coastline) - ranh giới giữa Đất liền và Biển/Hồ (cached)
        global _cached_coast_mask
        if _cached_coast_mask is None:
            land_lut = np.zeros(16777216, dtype=np.uint8)
            for rgb, prov in color_to_province.items():
                if not getattr(prov, 'is_sea', False) and not getattr(prov, 'is_lake', False):
                    land_lut[rgb[0]*65536 + rgb[1]*256 + rgb[2]] = 1
            is_land = (land_lut[u32] != 0)
            coast_mask = np.zeros((h, w), dtype=bool)
            coast_mask[:, 1:] |= (is_land[:, 1:] != is_land[:, :-1])
            coast_mask[1:, :] |= (is_land[1:, :] != is_land[:-1, :])
            _cached_coast_mask = coast_mask
        else:
            coast_mask = _cached_coast_mask
        
        # 2. Ranh giới Quốc gia trên đất liền (National Land Borders)
        national_border = np.zeros((h, w), dtype=bool)
        diff_h = (owner_map[:, 1:] != owner_map[:, :-1]) & (owner_map[:, 1:] != 0) & (owner_map[:, :-1] != 0)
        diff_v = (owner_map[1:, :] != owner_map[:-1, :]) & (owner_map[1:, :] != 0) & (owner_map[:-1, :] != 0)
        national_border[:, 1:] |= diff_h
        national_border[1:, :] |= diff_v
        
        # 3. Ranh giới Bang trong cùng quốc gia (State Borders)
        state_borders = generate_state_border_mask(original_image, color_to_province)
        state_borders &= ~national_border
        state_borders &= ~coast_mask
        
        # Tô màu đồng bộ, đẹp mắt và sắc nét
        result[state_borders] = np.array([90, 85, 80], dtype=np.uint8)      # Viền bang (xám nhạt mảnh)
        result[national_border] = np.array([35, 35, 35], dtype=np.uint8)    # Viền quốc gia đất liền (tối rõ nét)
        result[coast_mask] = np.array([30, 30, 30], dtype=np.uint8)         # Đường bờ biển (tối rõ nét)

    result = (result * 0.9).astype(np.uint8)

    print("-> Hoan tat!")
    return pygame.surfarray.make_surface(result.transpose(1,0,2))

def _cluster_landmasses(pixels, link_dist=22, merge_dist=70):
    """Gom pixel mau thanh cac khoi dat lien thong (luc dia / dao rieng) dung spatial grid hashing O(N)."""
    n = len(pixels)
    if n == 0:
        return []

    parent = list(range(n))
    def find(i):
        path = []
        while parent[i] != i:
            path.append(i)
            i = parent[i]
        for node in path:
            parent[node] = i
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    grid = {}
    for idx, (x, y) in enumerate(pixels):
        cell = (x // link_dist, y // link_dist)
        grid.setdefault(cell, []).append(idx)

    link2 = link_dist * link_dist
    for cell, indices in grid.items():
        cx, cy = cell
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbor_cell = (cx + dx, cy + dy)
                if neighbor_cell in grid:
                    for i in indices:
                        xi, yi = pixels[i]
                        for j in grid[neighbor_cell]:
                            if j <= i:
                                continue
                            dx_val = xi - pixels[j][0]
                            dy_val = yi - pixels[j][1]
                            if dx_val * dx_val + dy_val * dy_val <= link2:
                                union(i, j)

    groups = {}
    for i in range(n):
        r = find(i)
        groups.setdefault(r, []).append(pixels[i])

    landmasses = []
    for pts in groups.values():
        if len(pts) < 6:
            continue
        cx = sum(p[0] for p in pts) // len(pts)
        cy = sum(p[1] for p in pts) // len(pts)
        landmasses.append({"cx": cx, "cy": cy, "area": len(pts), "points": pts})

    if not landmasses:
        return []

    landmasses.sort(key=lambda m: -m["area"])
    used = [False] * len(landmasses)
    merged = []
    merge2 = merge_dist * merge_dist

    for i, lm in enumerate(landmasses):
        if used[i]:
            continue
        cluster = [lm]
        used[i] = True
        for j, lm2 in enumerate(landmasses):
            if used[j]:
                continue
            dx = lm["cx"] - lm2["cx"]
            dy = lm["cy"] - lm2["cy"]
            if dx * dx + dy * dy <= merge2:
                cluster.append(lm2)
                used[j] = True
        total = sum(c["area"] for c in cluster)
        cx = sum(c["cx"] * c["area"] for c in cluster) // total
        cy = sum(c["cy"] * c["area"] for c in cluster) // total
        all_pts = []
        for c in cluster:
            all_pts.extend(c["points"])
        merged.append({"cx": cx, "cy": cy, "area": total, "points": all_pts})

    return merged


def _landmass_angle(points):
    import numpy as np
    sample = points[:: max(1, len(points) // 120)]
    if len(sample) < 3:
        return 0.0
    xs = np.array([p[0] for p in sample], dtype=float)
    ys = np.array([p[1] for p in sample], dtype=float)
    try:
        cov = np.cov(xs, ys)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        idx = int(np.argmax(eigenvalues))
        vx, vy = eigenvectors[:, idx]
        angle = float(np.degrees(np.arctan2(vy, vx)))
        return max(-30, min(30, angle))
    except Exception:
        return 0.0


def generate_country_name_map(original_image, color_to_province, countries_data, fonts):
    """Ten quoc gia tren map: moi khoi dat (dao / luc dia) mot nhan, dao gan nhau gop chung."""
    print("Dang tao ban do ten quoc gia (Victoria 3 style)...")

    map_w, map_h = original_image.get_size()
    text_surface = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)

    global _country_centers
    _country_centers = {}

    country_pixels = {}
    step = 8
    for y in range(0, map_h, step):
        for x in range(0, map_w, step):
            rgb = tuple(arr[y, x])
            prov = color_to_province.get(rgb)
            if not prov:
                continue
            owner = getattr(prov, "owner", None)
            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                country_pixels.setdefault(owner, []).append((x, y))

    link_dist = max(24, min(map_w, map_h) // 90)
    merge_dist = max(350, min(map_w, map_h) // 3)

    labels = []
    for owner, pixels in country_pixels.items():
        if len(pixels) < 8:
            continue
        landmasses = _cluster_landmasses(pixels, link_dist=link_dist, merge_dist=merge_dist)
        if not landmasses:
            continue

        # Populate country centers with the largest landmass's center
        _country_centers[owner] = (landmasses[0]["cx"], landmasses[0]["cy"])

        max_area = max(m["area"] for m in landmasses)
        min_show = max(8, int(max_area * 0.015))

        for mass in landmasses:
            if mass["area"] < min_show:
                continue
            labels.append((
                owner,
                mass["cx"],
                mass["cy"],
                mass["area"],
                _landmass_angle(mass["points"]),
            ))

    if not labels:
        return text_surface

    areas = [lb[3] for lb in labels]
    min_area, max_area = min(areas), max(areas)

    semi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fonts", "EBGaramond-SemiBold.ttf")
    reg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fonts", "EBGaramond-Regular.ttf")

    labels.sort(key=lambda x: x[3], reverse=True)

    for owner, cx, cy, area, angle in labels:
        font_size = 18 + int(50 * ((area - min_area) / (max_area - min_area + 1)) ** 0.3)
        font_size = max(18, min(68, font_size))

        try:
            temp_font = pygame.font.Font(semi_path, font_size)
        except OSError:
            try:
                temp_font = pygame.font.Font(reg_path, font_size)
            except OSError:
                temp_font = fonts["sm"]

        name = get_country_display_name(owner)
        if not name or len(name) < 2:
            continue

        max_len = 24 if font_size > 20 else 22
        if len(name) > max_len:
            name = name[: max_len - 2] + ".."

        try:
            text_surf = temp_font.render(name, True, (255, 255, 255))
            shadow_surf = temp_font.render(name, True, (0, 0, 0))
        except pygame.error:
            continue

        if abs(angle) > 3:
            text_surf = pygame.transform.rotate(text_surf, -angle)
            shadow_surf = pygame.transform.rotate(shadow_surf, -angle)

        tr = text_surf.get_rect(center=(cx, cy))
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            text_surface.blit(shadow_surf, (tr.x + dx, tr.y + dy))
        text_surface.blit(text_surf, tr.topleft)

    print(f"-> Hoan tat! {len(labels)} nhan ten.")
    return text_surface

def generate_province_name_map(original_image, color_to_province, fonts):
    """Tạo bản đồ tên tỉnh với kích thước chữ theo diện tích - Bỏ qua để tối ưu tốc độ load"""
    print("Bypass generate_province_name_map to speed up startup...")
    map_w, map_h = original_image.get_size()
    return pygame.Surface((map_w, map_h), pygame.SRCALPHA)

def generate_combined_political_map(original_image, color_to_province, countries_data, countries_full, fonts):
    """Tạo bản đồ chính trị kết hợp tên quốc gia"""
    print("Dang tao ban do chinh tri + ten quoc gia...")
    political = generate_political_map(original_image, color_to_province,
                                        countries_data, countries_full,
                                        mode=MAP_MODE_POLITICAL)
    country_names = generate_country_name_map(original_image, color_to_province, countries_data, fonts)
    political.blit(country_names, (0, 0))
    return political


def build_province_state_lookup(game_state):
    """Xây dựng index O(1): province_color -> State object."""
    global _province_to_state_fast
    _province_to_state_fast.clear()
    for state in game_state.states.values():
        for prov in state.provinces:
            _province_to_state_fast[prov.color] = state
    print(f"-> Province-State fast index: {len(_province_to_state_fast)} entries")


def generate_state_level_map(original_image, color_to_province, game_state):
    """Bản đồ kiểu Victoria 3: tô màu theo Bang với viền bang/quốc gia rõ ràng."""
    print("Generating unified map (Victoria 3 style)...")
    map_w, map_h = original_image.get_size()
    arr = pygame.surfarray.array3d(original_image).transpose(1, 0, 2)

    # LUT approach for speed
    lut_r = np.zeros(16777216, dtype=np.uint8)
    lut_g = np.zeros(16777216, dtype=np.uint8)
    lut_b = np.zeros(16777216, dtype=np.uint8)
    lut_s = np.zeros(16777216, dtype=np.int32)   # state_id
    lut_c = np.zeros(16777216, dtype=np.int32)   # country_id
    in_lut = np.zeros(16777216, dtype=bool)

    # Build state flat colors
    country_state_lists = {}
    for state in game_state.states.values():
        owner = state.owner or ""
        country_state_lists.setdefault(owner, []).append(state.name)

    state_color_map = {}   # state_name -> (R,G,B)
    state_id_map = {}      # state_name -> int
    state_ctr = 1
    country_id_map = {}    # country_tag -> int
    country_ctr = 1

    for owner, snames in country_state_lists.items():
        if owner not in country_id_map:
            country_id_map[owner] = country_ctr; country_ctr += 1
        base = game_state.countries_data.get(owner, [120, 120, 120])
        br, bg, bb = int(base[0]), int(base[1]), int(base[2])
        for i, sname in enumerate(snames):
            state_color_map[sname] = (br, bg, bb)
            state_id_map[sname] = state_ctr; state_ctr += 1

    # Đăng ký country_id cho tất cả các nước (kể cả nước nhỏ không có bang)
    for tag in game_state.countries_data:
        if tag not in country_id_map:
            country_id_map[tag] = country_ctr; country_ctr += 1

    # Province color -> state name lookup
    prov_to_state = {}
    for state in game_state.states.values():
        for prov in state.provinces:
            prov_to_state[prov.color] = state

    for rgb, prov in color_to_province.items():
        k = rgb[0] * 65536 + rgb[1] * 256 + rgb[2]
        if getattr(prov, "is_sea", False) or getattr(prov, "is_lake", False):
            nr, ng, nb = C_SEA
            sid, cid = -1, -1
        else:
            state = prov_to_state.get(rgb)
            if state and state.name in state_color_map:
                nr, ng, nb = state_color_map[state.name]
                sid = state_id_map.get(state.name, 0)
                owner = state.owner or ""
                cid = country_id_map.get(owner, 0)
            elif getattr(prov, "owner", None) and prov.owner in game_state.countries_data:
                # Tỉnh có chủ nhưng không thuộc bang nào → dùng màu quốc gia trực tiếp
                v = game_state.countries_data[prov.owner]
                nr, ng, nb = int(v[0]), int(v[1]), int(v[2])
                # Gán country_id để vẽ viền quốc gia đúng
                cid = country_id_map.get(prov.owner, 0)
                if cid == 0:
                    country_id_map[prov.owner] = country_ctr
                    cid = country_ctr; country_ctr += 1
                sid = 0
            else:
                nr, ng, nb = C_LAND_EMPTY
                sid, cid = 0, 0
        lut_r[k] = nr; lut_g[k] = ng; lut_b[k] = nb
        lut_s[k] = sid; lut_c[k] = cid
        in_lut[k] = True

    u32 = (arr[:, :, 0].astype(np.uint32) * 65536 +
           arr[:, :, 1].astype(np.uint32) * 256 +
           arr[:, :, 2].astype(np.uint32))
    mask = in_lut[u32]
    result = np.stack([
        np.where(mask, lut_r[u32], arr[:, :, 0]),
        np.where(mask, lut_g[u32], arr[:, :, 1]),
        np.where(mask, lut_b[u32], arr[:, :, 2]),
    ], axis=2).astype(np.uint8)

    sid_arr = np.where(mask, lut_s[u32], -2).astype(np.int32)
    cid_arr = np.where(mask, lut_c[u32], -2).astype(np.int32)

    # Draw borders
    land = sid_arr >= 0

    # 1. Province transitions (where the source province image color changes)
    diff_p_h = (arr[:-1, :, :] != arr[1:, :, :]).any(axis=2) & land[:-1, :] & land[1:, :]
    diff_p_v = (arr[:, :-1, :] != arr[:, 1:, :]).any(axis=2) & land[:, :-1] & land[:, 1:]

    # 2. State transitions within same country
    diff_s_h = (sid_arr[:-1, :] != sid_arr[1:, :]) & land[:-1, :] & land[1:, :] & (cid_arr[:-1, :] == cid_arr[1:, :])
    diff_s_v = (sid_arr[:, :-1] != sid_arr[:, 1:]) & land[:, :-1] & land[:, 1:] & (cid_arr[:, :-1] == cid_arr[:, 1:])

    # 3. Country transitions
    diff_c_h = (cid_arr[:-1, :] != cid_arr[1:, :]) & land[:-1, :] & land[1:, :] & (cid_arr[:-1, :] > 0) & (cid_arr[1:, :] > 0)
    diff_c_v = (cid_arr[:, :-1] != cid_arr[:, 1:]) & land[:, :-1] & land[:, 1:] & (cid_arr[:, :-1] > 0) & (cid_arr[:, 1:] > 0)

    prov_bdr  = np.array([80,  80,  80],  dtype=np.uint8)  # faint province border
    state_bdr = np.array([45,  45,  45],  dtype=np.uint8)  # medium state border
    ctry_bdr  = np.array([8,   8,   8],   dtype=np.uint8)  # thick country border

    # Set province borders
    result[:-1, :][diff_p_h] = prov_bdr
    result[1:,  :][diff_p_h] = prov_bdr
    result[:, :-1][diff_p_v] = prov_bdr
    result[:, 1: ][diff_p_v] = prov_bdr

    # Overwrite with state borders
    result[:-1, :][diff_s_h] = state_bdr
    result[1:,  :][diff_s_h] = state_bdr
    result[:, :-1][diff_s_v] = state_bdr
    result[:, 1: ][diff_s_v] = state_bdr

    # Overwrite with country borders
    result[:-1, :][diff_c_h] = ctry_bdr
    result[1:,  :][diff_c_h] = ctry_bdr
    result[:, :-1][diff_c_v] = ctry_bdr
    result[:, 1: ][diff_c_v] = ctry_bdr

    result = (result * 0.92).astype(np.uint8)
    print("-> State-level map done!")
    return pygame.surfarray.make_surface(result.transpose(1, 0, 2))

_vignette_surface = None

def draw_map_vignette(screen):
    global _vignette_surface
    sw, sh = screen.get_size()
    if _vignette_surface is None or _vignette_surface.get_size() != (sw, sh):
        _vignette_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for i in range(16):
            w = 8
            rect = pygame.Rect(i * w, i * w, sw - 2 * i * w, sh - 2 * i * w)
            alpha = int((1.0 - (i / 16)) ** 1.5 * 180)
            if alpha > 0:
                pygame.draw.rect(_vignette_surface, (0, 0, 0, alpha), rect, w, border_radius=12)
    screen.blit(_vignette_surface, (0, 0))

# ── Draw helpers ─────────────────────────────────────
def panel(screen, x, y, w, h, alpha=240):
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha))
    screen.blit(s,(x,y))
    pygame.draw.rect(screen, C_BORDER, (x,y,w,h), 1, border_radius=4)
    if w > 4 and h > 4:
        pygame.draw.rect(screen, C_GOLD_DIM, (x+2, y+2, w-4, h-4), 1, border_radius=3)

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

def draw_text_input_modal(screen, fonts, title, default_text=""):
    import pygame
    sw, sh = screen.get_size()
    
    # Text input state
    txt = default_text
    clock = pygame.time.Clock()
    
    # Dim background
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    
    mw, mh = 400, 200
    mx = sw // 2 - mw // 2
    my = sh // 2 - mh // 2
    
    input_rect = pygame.Rect(mx + 30, my + 80, mw - 60, 36)
    btn_confirm = pygame.Rect(mx + 30, my + 140, 150, 38)
    btn_cancel = pygame.Rect(mx + mw - 180, my + 140, 150, 38)
    
    # Flash cursor
    tick = 0
    
    pygame.time.wait(150)  # debounce previous click
    
    # Store a copy of screen before modal to draw it behind overlay
    screen_snapshot = screen.copy()
    
    while True:
        tick += 1
        m_pos = pygame.mouse.get_pos()
        m_click = pygame.mouse.get_pressed()[0]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.time.wait(150)
                    return txt.strip()
                elif event.key == pygame.K_ESCAPE:
                    pygame.time.wait(150)
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    txt = txt[:-1]
                else:
                    # Append unicode char if printable
                    if event.unicode and event.unicode.isprintable():
                        # Maximum length constraint
                        if len(txt) < 32:
                            txt += event.unicode
                            
        # Redraw background snapshot
        screen.blit(screen_snapshot, (0, 0))
        # Draw dim overlay
        screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        panel(screen, mx, my, mw, mh, 255)
        pygame.draw.rect(screen, C_GOLD, (mx, my, mw, mh), 2, border_radius=8)
        
        # Title
        title_s = fonts["med"].render(title, True, C_GOLD)
        screen.blit(title_s, title_s.get_rect(centerx=sw // 2, y=my + 20))
        
        # Text input box
        pygame.draw.rect(screen, (22, 28, 35), input_rect, border_radius=4)
        pygame.draw.rect(screen, C_BORDER, input_rect, 1, border_radius=4)
        
        # Render text
        text_s = fonts["med"].render(txt, True, C_WHITE)
        screen.blit(text_s, (input_rect.x + 8, input_rect.y + 6))
        
        # Cursor
        if (tick // 30) % 2 == 0:
            cursor_x = input_rect.x + 8 + fonts["med"].size(txt)[0]
            pygame.draw.line(screen, C_GOLD, (cursor_x, input_rect.y + 8), (cursor_x, input_rect.y + 28), 2)
            
        # Draw buttons
        confirm_hov = btn_confirm.collidepoint(m_pos)
        pygame.draw.rect(screen, (35, 80, 50) if confirm_hov else (20, 50, 30), btn_confirm, border_radius=4)
        pygame.draw.rect(screen, C_GOLD if confirm_hov else C_BORDER, btn_confirm, 1, border_radius=4)
        cf_s = fonts["med"].render("Xác nhận", True, C_WHITE)
        screen.blit(cf_s, cf_s.get_rect(center=btn_confirm.center))
        
        cancel_hov = btn_cancel.collidepoint(m_pos)
        pygame.draw.rect(screen, (100, 40, 40) if cancel_hov else (60, 20, 20), btn_cancel, border_radius=4)
        pygame.draw.rect(screen, C_GOLD if cancel_hov else C_BORDER, btn_cancel, 1, border_radius=4)
        cc_s = fonts["med"].render("Hủy bỏ", True, C_WHITE)
        screen.blit(cc_s, cc_s.get_rect(center=btn_cancel.center))
        
        if m_click:
            if confirm_hov:
                pygame.time.wait(150)
                return txt.strip()
            elif cancel_hov:
                pygame.time.wait(150)
                return None
                
        pygame.display.flip()
        clock.tick(60)

def _rgb_color(data, default=(120, 120, 120)):
    """Safe (R,G,B) from countries_data entry."""
    if not data:
        return default
    try:
        parts = list(data)[:3]
        if len(parts) < 3:
            return default
        return tuple(int(v) for v in parts)
    except (TypeError, ValueError):
        return default


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
    if is_ui_blocking_click((mx, my), game_state_ref):
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
    owner_name = get_country_display_name(owner, owner)
    
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
    tx = min(mx + 20, SCREEN_W - width - 10)
    ty = max(HUD_H + 10, min(my + 20, screen_h - height - 10))

    panel(screen, tx, ty, width, height, 220)
    pygame.draw.rect(screen, C_GOLD, (tx, ty, width, height), 1, border_radius=4)
    for i, line in enumerate(lines):
        text(screen, fonts, "sm", line, tx + 8, ty + 8 + i * (fonts["sm"].get_height() + 4), C_WHITE)

def draw_build_tooltip(screen, fonts, text_str, mx, my):
    sw, sh = screen.get_size()
    tw, th = 320, 80
    tx, ty = mx + 15, my + 15
    if tx + tw > sw:
        tx = mx - tw - 15
    if ty + th > sh:
        ty = my - th - 15
    # Render tooltip background
    s = pygame.Surface((tw, th), pygame.SRCALPHA)
    s.fill((20, 20, 20, 245))
    screen.blit(s, (tx, ty))
    pygame.draw.rect(screen, C_GOLD, (tx, ty, tw, th), 1, border_radius=4)
    # Word wrap text_str
    words = text_str.split(" ")
    lines = []
    curr = []
    for w in words:
        if fonts["sm"].size(" ".join(curr + [w]))[0] <= tw - 20:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    # Draw lines
    line_y = ty + 10
    for line in lines[:3]:
        text(screen, fonts, "sm", line, tx + 10, line_y, C_WHITE)
        line_y += 18

def draw_build_panel(screen, fonts, game_state, selected_state=None):
    """Vẽ bảng xây dựng công trình theo tỉnh bang, phân loại hai cột với giới hạn cấp độ và địa hình."""
    sw, sh = screen.get_size()
    panel_w, panel_h = 1000, 530
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    panel(screen, panel_x, panel_y, panel_w, panel_h, 250)
    text(screen, fonts, "med", "XAY DUNG CONG TRINH", panel_x + 20, panel_y + 12, C_GOLD)
    
    country = game_state.player_country
    if not country:
        return False
        
    # Nút đóng
    close_btn = pygame.Rect(panel_x + panel_w - 35, panel_y + 8, 28, 28)
    if draw_button(screen, fonts, close_btn, "X", (120, 40, 40), C_GOLD, C_WHITE, pygame.mouse.get_pos(), "med"):
        if pygame.mouse.get_pressed()[0]:
            pygame.time.wait(200)
            return True
            
    if not selected_state:
        text(screen, fonts, "sm", "Vui long chon 1 bang tren ban do (Click trai len mot tinh tren ban do)", panel_x + 20, panel_y + 120, C_GREY)
        return False
        
    if selected_state.owner != game_state.player_tag:
        text(screen, fonts, "sm", "Ban chi co the xay dung tren cac bang thuoc chu quyen cua minh!", panel_x + 20, panel_y + 120, C_RED)
        state_owner = selected_state.owner or "Khong ro"
        text(screen, fonts, "sm", f"Bang nay thuoc: {get_country_display_name(state_owner, state_owner)}", panel_x + 20, panel_y + 155, C_GREY)
        return False

    state_display = getattr(selected_state, 'display_name', None)
    if callable(state_display):
        state_display = state_display()
    elif state_display is None:
        state_display = getattr(selected_state, 'name', 'Unknown')
    text(screen, fonts, "sm", f"Xay dung tai: {state_display}", panel_x + 20, panel_y + 36, C_GREY)

    # Pre-calculate state terrains
    has_plains = any(getattr(p, 'terrain', 'plains') == 'plains' for p in selected_state.provinces)
    has_mountains_or_hills = any(getattr(p, 'terrain', 'plains') in ('mountains', 'hills') for p in selected_state.provinces)
    has_non_desert = any(getattr(p, 'terrain', 'plains') != 'desert' for p in selected_state.provinces)
    
    global _state_resources
    has_port_resource = False
    if _state_resources and selected_state.name in _state_resources:
        has_port_resource = _state_resources[selected_state.name].has_port

    # Lists for two columns:
    # (Display Name, Cost, Type, Desc, Max Level, Terrain check lambda, Error message)
    col_left_data = [
        ("[RYE] Trang trai Rye", 50, "rye_farm", "Tang luong thuc & dan so (Dong bang)", 3, lambda s: has_plains, "Yeu cau dat Dong bang"),
        ("[LIV] Gia suc", 50, "livestock_ranches", "Nuoi gia suc & thuc pham (Dong bang)", 3, lambda s: has_plains, "Yeu cau dat Dong bang"),
        ("[COT] Don dien Bong", 50, "cotton_plantation", "San xuat vai soi (Dong bang)", 3, lambda s: has_plains, "Yeu cau dat Dong bang"),
        ("[VIN] Don dien Nho", 60, "vineyard", "San xuat ruou & trai cay (Dong bang)", 3, lambda s: has_plains, "Yeu cau dat Dong bang"),
        ("[COAL] Mo Than", 100, "coal_mine", "Mo khai thac than da (Nui/Doi)", 3, lambda s: has_mountains_or_hills, "Yeu cau dat Nui hoac Doi"),
        ("[IRON] Mo Sat", 100, "iron_mine", "Mo khai thac quang sat (Nui/Doi)", 3, lambda s: has_mountains_or_hills, "Yeu cau dat Nui hoac Doi"),
        ("[LOG] Trai cua Go", 80, "logging_camp", "San xuat lam san & go (Khong sa mac)", 3, lambda s: has_non_desert, "Khong the xay tren Sa mac")
    ]

    col_right_data = [
        ("[FOOD] CN Thuc pham", 200, "food_industry", "San xuat & che bien thuc pham", 3, lambda s: True, ""),
        ("[TEX] Det may", 200, "textile_mill", "San xuat & det quan ao", 3, lambda s: True, ""),
        ("[STEEL] Nha may Thep", 250, "steel_mill", "Luyen kim & che tao thep", 3, lambda s: True, ""),
        ("[ARMS] Mo vu khi", 250, "arms_industry", "San xuat & che tao sung dan", 3, lambda s: True, ""),
        ("[BARR] Doanh trai", 150, "barracks", "Tuyen dung & tang cuong quan doi", 3, lambda s: True, ""),
        ("[UNIV] Dai hoc", 300, "university", "Dao tao tri thuc & nghien cuu (Max 1)", 1, lambda s: True, ""),
        ("[PORT] Cang bien", 150, "port", "Giao thuong & van tai bien (Max 1)", 1, lambda s: has_port_resource, "Yeu cau bang co bien (has_port)"),
        ("[RAIL] Duong sat", 200, "railway", "Ha tang giao thong (Max 1)", 1, lambda s: True, ""),
        ("[SKY] Nha choc troi", 500, "skyscraper", "Co quan hanh chinh cao cap (Max 1)", 1, lambda s: True, "")
    ]

    mx, my = pygame.mouse.get_pos()
    
    # Left Column Title
    text(screen, fonts, "med", "NONG THON & KHAI THAC (RURAL & EXTRACTION)", panel_x + 20, panel_y + 65, C_GOLD)
    pygame.draw.line(screen, C_BORDER, (panel_x + 20, panel_y + 87), (panel_x + 470, panel_y + 87), 1)
    
    # Right Column Title
    text(screen, fonts, "med", "DO THI & PHAT TRIEN (URBAN & DEVELOPMENT)", panel_x + 510, panel_y + 65, C_GOLD)
    pygame.draw.line(screen, C_BORDER, (panel_x + 510, panel_y + 87), (panel_x + 960, panel_y + 87), 1)

    # Render Left Column
    y = panel_y + 95
    for name, cost, btype, desc, max_lvl, terrain_check, err_msg in col_left_data:
        lvl = sum(b.level for b in selected_state.get_buildings_by_type(btype))
        terrain_ok = terrain_check(selected_state)
        level_ok = (lvl < max_lvl)
        can_build = terrain_ok and level_ok and (country.treasury >= cost)
        
        btn = pygame.Rect(panel_x + 20, y, 450, 42)
        bg_col = (40, 90, 55) if can_build else (50, 50, 50)
        border_col = C_GOLD if can_build else C_GREY
        
        hover = draw_button(screen, fonts, btn, "", bg_col, border_col, C_WHITE, (mx, my), "sm")
        
        # Display Text inside button
        text(screen, fonts, "sm", name, panel_x + 30, y + 12, C_WHITE)
        lvl_str = f"Lvl {lvl}/{max_lvl}"
        text(screen, fonts, "sm", lvl_str, panel_x + 280, y + 12, (200, 200, 200) if level_ok else C_RED)
        cost_text = f"£{cost}"
        text(screen, fonts, "sm", cost_text, panel_x + 410, y + 12, C_GOLD if country.treasury >= cost else C_RED)
        
        if hover:
            tooltip_text = desc if terrain_ok else f"Khong the xay: {err_msg}"
            draw_build_tooltip(screen, fonts, tooltip_text, mx, my)
            if can_build and pygame.mouse.get_pressed()[0]:
                country.treasury -= cost
                selected_state.add_building(btype)
                print(f"Built {btype} level {lvl+1} in state {selected_state.name}, cost: £{cost}")
                game_state.last_event = {
                    "title": "XAY DUNG XONG",
                    "desc": f"Da xay dung {name} cap {lvl+1} tai bang {selected_state.display_name}.",
                    "effect_text": f"Ngan kho -£{cost}"
                }
                pygame.time.wait(200)
                
        y += 46

    # Render Right Column
    y = panel_y + 95
    for name, cost, btype, desc, max_lvl, terrain_check, err_msg in col_right_data:
        lvl = sum(b.level for b in selected_state.get_buildings_by_type(btype))
        terrain_ok = terrain_check(selected_state)
        level_ok = (lvl < max_lvl)
        can_build = terrain_ok and level_ok and (country.treasury >= cost)
        
        btn = pygame.Rect(panel_x + 510, y, 450, 42)
        bg_col = (40, 90, 55) if can_build else (50, 50, 50)
        border_col = C_GOLD if can_build else C_GREY
        
        hover = draw_button(screen, fonts, btn, "", bg_col, border_col, C_WHITE, (mx, my), "sm")
        
        # Display Text inside button
        text(screen, fonts, "sm", name, panel_x + 520, y + 12, C_WHITE)
        lvl_str = f"Lvl {lvl}/{max_lvl}"
        text(screen, fonts, "sm", lvl_str, panel_x + 770, y + 12, (200, 200, 200) if level_ok else C_RED)
        cost_text = f"£{cost}"
        text(screen, fonts, "sm", cost_text, panel_x + 900, y + 12, C_GOLD if country.treasury >= cost else C_RED)
        
        if hover:
            tooltip_text = desc if terrain_ok else f"Khong the xay: {err_msg}"
            draw_build_tooltip(screen, fonts, tooltip_text, mx, my)
            if can_build and pygame.mouse.get_pressed()[0]:
                country.treasury -= cost
                selected_state.add_building(btype)
                print(f"Built {btype} level {lvl+1} in state {selected_state.name}, cost: £{cost}")
                game_state.last_event = {
                    "title": "XAY DUNG XONG",
                    "desc": f"Da xay dung {name} cap {lvl+1} tai bang {selected_state.display_name}.",
                    "effect_text": f"Ngan kho -£{cost}"
                }
                pygame.time.wait(200)
                
        y += 44
        
    return False

def update_regime_from_laws(country):
    gov_principle = country.active_laws.get("Governance Principles", "Monarchy")
    dist_power = country.active_laws.get("Distribution of Power", "Autocracy")
    
    new_gov = "default"
    if gov_principle in ("Monarchy", "Social Monarchy"):
        new_gov = "absolute_monarchy"
    elif gov_principle in ("Presidential Republic", "Parliamentary Republic"):
        if dist_power == "Autocracy":
            new_gov = "dictatorship"
        else:
            new_gov = "republic"
    elif gov_principle == "Theocracy":
        new_gov = "theocracy"
    elif gov_principle == "Council Republic":
        new_gov = "communist"
    elif gov_principle == "Corporate State":
        new_gov = "fascist"
    elif gov_principle == "Chiefdom":
        new_gov = "default"
    elif gov_principle == "Colonial Administration":
        new_gov = "default"
        
    country.government = new_gov

def draw_law_tooltip(screen, fonts, law_name, mx, my, sw, sh):
    data = PARSED_LAWS.get(law_name)
    if not data:
        return
        
    tx, ty_t = mx + 15, my + 15
    tw, th_t = 360, 220
    
    if tx + tw > sw:
        tx = mx - tw - 15
    if ty_t + th_t > sh:
        ty_t = my - th_t - 15
        
    panel(screen, tx, ty_t, tw, th_t, 255)
    pygame.draw.rect(screen, C_GOLD, (tx, ty_t, tw, th_t), 1, border_radius=4)
    
    text(screen, fonts, "med", law_name.upper(), tx + 12, ty_t + 10, C_GOLD)
    
    desc = data.get("desc", "")
    desc_words = desc.split(" ")
    desc_lines = []
    curr = []
    for w in desc_words:
        test = " ".join(curr + [w])
        if fonts["sm"].size(test)[0] <= tw - 24:
            curr.append(w)
        else:
            desc_lines.append(" ".join(curr))
            curr = [w]
    if curr:
        desc_lines.append(" ".join(curr))
        
    dy_t = ty_t + 35
    for d_line in desc_lines[:2]:
        text(screen, fonts, "sm", d_line, tx + 12, dy_t, C_WHITE)
        dy_t += 14
        
    # Requirements
    reqs = data.get("requirements", [])
    if reqs:
        dy_t += 4
        req_str = ", ".join(reqs)
        req_words = req_str.split(" ")
        req_lines = []
        curr_r = []
        for w in req_words:
            test = " ".join(curr_r + [w])
            if fonts["sm"].size(test)[0] <= tw - 24:
                curr_r.append(w)
            else:
                req_lines.append(" ".join(curr_r))
                curr_r = [w]
        if curr_r:
            req_lines.append(" ".join(curr_r))
            
        text(screen, fonts, "sm", "Yêu cầu:", tx + 12, dy_t, (180, 220, 255))
        dy_t += 14
        for r_line in req_lines[:2]:
            text(screen, fonts, "sm", f"  • {r_line}", tx + 12, dy_t, (150, 200, 255))
            dy_t += 14
        
    # Effects
    effects = data.get("effects", [])
    if effects:
        dy_t += 4
        text(screen, fonts, "sm", "Hiệu ứng:", tx + 12, dy_t, C_GOLD_DIM)
        dy_t += 14
        for eff in effects[:3]:
            if len(eff) > 50:
                eff = eff[:47] + "..."
            text(screen, fonts, "sm", f" • {eff}", tx + 12, dy_t, C_GREEN)
            dy_t += 14

CATEGORY_DISPLAY = {
    "Governance Principles": "Nguyên tắc Cai trị (Governance Principles)",
    "Distribution of Power": "Phân chia Quyền lực (Distribution of Power)",
    "Bureaucracy": "Hệ thống Quan liêu (Bureaucracy)",
    "Internal Security": "An ninh Nội bộ (Internal Security)",
    "Caste Hegemony": "Hệ thống Đẳng cấp (Caste Hegemony)",
    "Army Model": "Mô hình Quân đội (Army Model)",
    "Navy Model": "Mô hình Hải quân (Navy Model)"
}

def draw_politics_panel(screen, fonts, game_state):
    """Vẽ bảng chọn chế độ chính trị và luật pháp."""
    global show_politics_panel, _selected_law_category, _law_scroll
    sw, sh = screen.get_size()
    panel_w, panel_h = 1000, 530
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    panel(screen, panel_x, panel_y, panel_w, panel_h, 250)
    pygame.draw.rect(screen, C_GOLD, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=6)
    
    text(screen, fonts, "med", "CHÍNH TRỊ VÀ LUẬT PHÁP (POLITICS & LAWS)", panel_x + 20, panel_y + 12, C_GOLD)
    
    country = game_state.player_country
    if not country:
        return False
        
    # Initialize active_laws if not present or empty
    if not hasattr(country, "active_laws") or not country.active_laws:
        gov = country.government
        gov_principle = "Monarchy"
        dist_power = "Autocracy"
        if gov == "republic":
            gov_principle = "Presidential Republic"
            dist_power = "Universal Suffrage"
        elif gov == "dictatorship":
            gov_principle = "Presidential Republic"
            dist_power = "Autocracy"
        elif gov == "theocracy":
            gov_principle = "Theocracy"
            dist_power = "Autocracy"
        elif gov == "communist":
            gov_principle = "Council Republic"
            dist_power = "Universal Suffrage"
        elif gov == "fascist":
            gov_principle = "Corporate State"
            dist_power = "Single-Party State"
        
        country.active_laws = {
            "Governance Principles": gov_principle,
            "Distribution of Power": dist_power,
            "Bureaucracy": "Appointed Bureaucrats",
            "Internal Security": "No Home Affairs",
            "Caste Hegemony": "Caste System Codified",
            "Army Model": "Professional Army",
            "Navy Model": "Merchant Navy"
        }
        # Populate country.laws compatibility mapping
        for category, law_name in country.active_laws.items():
            for l in PARSED_LAWS.keys():
                if PARSED_LAWS[l].get("category") == category:
                    country.laws[l] = (l == law_name)
                    
    cur_gov = country.government
    cur_label = GOVT_LABELS.get(cur_gov, cur_gov) or "Mac dinh"
    text(screen, fonts, "sm", f"Chính thể: {cur_label.upper()} | Quốc gia: {country.tag}", panel_x + 380, panel_y + 15, (180, 220, 255))
    
    mx, my = pygame.mouse.get_pos()
    
    # Nút đóng
    close_btn = pygame.Rect(panel_x + panel_w - 35, panel_y + 8, 28, 28)
    if draw_button(screen, fonts, close_btn, "X", (120, 40, 40), C_GOLD, C_WHITE, (mx, my), "med"):
        if pygame.mouse.get_pressed()[0]:
            pygame.time.wait(200)
            return True  # Close panel
            
    columns = [
        {
            "title": "Cơ cấu Quyền lực (Power Structure)",
            "categories": ["Governance Principles", "Distribution of Power"]
        },
        {
            "title": "Kinh tế & Hành chính (Economy & Admin)",
            "categories": ["Bureaucracy", "Internal Security", "Caste Hegemony"]
        },
        {
            "title": "Hệ thống Quân sự (Military System)",
            "categories": ["Army Model", "Navy Model"]
        }
    ]
    
    col_y_start = panel_y + 55
    col_w = 300
    col_gap = 25
    
    hovered_tooltip_law = None
    modal_open = (_selected_law_category is not None)
    
    # Render the 3 Columns
    for col_idx, col_data in enumerate(columns):
        cx = panel_x + 25 + col_idx * (col_w + col_gap)
        
        # Column title
        text(screen, fonts, "med", col_data["title"], cx, col_y_start, C_GOLD)
        pygame.draw.line(screen, C_BORDER, (cx, col_y_start + 24), (cx + col_w, col_y_start + 24), 1)
        
        y = col_y_start + 35
        for category in col_data["categories"]:
            active_law = country.active_laws.get(category)
            if not active_law:
                fallbacks = {
                    "Governance Principles": "Monarchy",
                    "Distribution of Power": "Autocracy",
                    "Bureaucracy": "Appointed Bureaucrats",
                    "Internal Security": "No Home Affairs",
                    "Caste Hegemony": "Caste System Codified",
                    "Army Model": "Professional Army",
                    "Navy Model": "Merchant Navy"
                }
                active_law = fallbacks.get(category, "Monarchy")
                country.active_laws[category] = active_law
                
            box_r = pygame.Rect(cx, y, col_w, 120)
            
            # Hover / click checks only if modal is not open
            hover = False
            if not modal_open:
                hover = box_r.collidepoint(mx, my)
                
            bg_col = (50, 42, 34) if hover else (32, 28, 24)
            border_col = C_GOLD if hover else C_BORDER
            
            pygame.draw.rect(screen, bg_col, box_r, border_radius=6)
            pygame.draw.rect(screen, border_col, box_r, 1, border_radius=6)
            
            # Category display name
            disp_name = CATEGORY_DISPLAY.get(category, category)
            text(screen, fonts, "sm", disp_name, cx + 10, y + 8, C_GOLD_DIM)
            
            # Active Law Name & Icon
            icon_fn = resolve_law_icon_fn(active_law)
            icon_img = get_law_icon(icon_fn) if icon_fn else None
            if icon_img:
                scaled_icon = pygame.transform.smoothscale(icon_img, (32, 32))
                screen.blit(scaled_icon, (cx + 10, y + 32))
                law_text_x = cx + 50
            else:
                law_text_x = cx + 12
                
            text(screen, fonts, "med", active_law, law_text_x, y + 36, C_WHITE)
            
            # Subtitle / Effect preview or enactment progress
            enacting = getattr(country, 'enacting_law', None)
            if enacting and enacting["category"] == category:
                progress_text = f"Cai cach: {enacting['law_name']} ({3 - enacting['turns_left']}/3 luot)"
                text(screen, fonts, "sm", progress_text, cx + 12, y + 74, (255, 180, 50))
                # Draw a nice progress bar
                bar_w = col_w - 24
                bar_x = cx + 12
                bar_y = y + 95
                pygame.draw.rect(screen, (50, 40, 30), (bar_x, bar_y, bar_w, 8), border_radius=4)
                done_w = int(bar_w * (3 - enacting["turns_left"]) / 3.0)
                if done_w > 0:
                    pygame.draw.rect(screen, (255, 180, 50), (bar_x, bar_y, done_w, 8), border_radius=4)
            else:
                law_data = PARSED_LAWS.get(active_law)
                eff_text = ""
                if law_data:
                    effs = law_data.get("effects", [])
                    eff_text = effs[0] if effs else law_data.get("desc", "")
                if len(eff_text) > 42:
                    eff_text = eff_text[:39] + ".."
                text(screen, fonts, "sm", eff_text, cx + 12, y + 74, C_GREY)
            
            if hover:
                hovered_tooltip_law = active_law
                if pygame.mouse.get_pressed()[0]:
                    _selected_law_category = category
                    _law_scroll = 0
                    pygame.time.wait(150)
                    
            y += 120 + 15
            
    # Draw Choices Modal Overlay if active
    if _selected_law_category:
        category = _selected_law_category
        laws_in_cat = [name for name, d in PARSED_LAWS.items() if d.get("category") == category]
        
        mw, mh = 640, 480
        mx_pos = (sw - mw) // 2
        my_pos = (sh - mh) // 2
        
        # Overlay back shadow to dim underlying controls
        dim_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 100))
        screen.blit(dim_surf, (0, 0))
        
        panel(screen, mx_pos, my_pos, mw, mh, 255)
        pygame.draw.rect(screen, C_GOLD, (mx_pos, my_pos, mw, mh), 2, border_radius=6)
        
        text(screen, fonts, "med", f"CẢI CÁCH LUẬT: {category.upper()}", mx_pos + 20, my_pos + 12, C_GOLD)
        
        # Close button for modal
        close_rect = pygame.Rect(mx_pos + mw - 35, my_pos + 8, 28, 28)
        if draw_button(screen, fonts, close_rect, "X", (120, 40, 40), C_GOLD, C_WHITE, (mx, my), "med"):
            if pygame.mouse.get_pressed()[0]:
                _selected_law_category = None
                pygame.time.wait(150)
                
        list_x = mx_pos + 20
        list_y = my_pos + 50
        list_w = mw - 40
        list_h = mh - 70
        
        row_h = 52
        row_gap = 6
        max_visible = 7
        
        # Scroll Buttons
        if len(laws_in_cat) > max_visible:
            up_rect = pygame.Rect(list_x + list_w - 22, list_y, 20, 20)
            down_rect = pygame.Rect(list_x + list_w - 22, list_y + list_h - 20, 20, 20)
            
            # Draw Up Arrow
            if draw_button(screen, fonts, up_rect, "▲", (45, 38, 30), C_GOLD, C_WHITE, (mx, my), "sm"):
                if pygame.mouse.get_pressed()[0] and _law_scroll > 0:
                    _law_scroll -= 1
                    pygame.time.wait(80)
            # Draw Down Arrow
            if draw_button(screen, fonts, down_rect, "▼", (45, 38, 30), C_GOLD, C_WHITE, (mx, my), "sm"):
                if pygame.mouse.get_pressed()[0] and _law_scroll < len(laws_in_cat) - max_visible:
                    _law_scroll += 1
                    pygame.time.wait(80)
                    
        visible_laws = laws_in_cat[_law_scroll : _law_scroll + max_visible]
        for idx, law_name in enumerate(visible_laws):
            item_y = list_y + idx * (row_h + row_gap)
            row_rect = pygame.Rect(list_x, item_y, list_w - 30, row_h)
            
            is_active = (country.active_laws.get(category) == law_name)
            hover_row = row_rect.collidepoint(mx, my)
            
            if is_active:
                bg_c = (25, 60, 35)
                border_c = C_GOLD
            elif hover_row:
                bg_c = (55, 65, 75)
                border_c = C_GOLD_DIM
            else:
                bg_c = (42, 34, 28)
                border_c = C_BORDER
                
            pygame.draw.rect(screen, bg_c, row_rect, border_radius=4)
            pygame.draw.rect(screen, border_c, row_rect, 1, border_radius=4)
            
            # Law icon
            fn = resolve_law_icon_fn(law_name)
            icon_img = get_law_icon(fn) if fn else None
            if icon_img:
                scaled = pygame.transform.smoothscale(icon_img, (32, 32))
                screen.blit(scaled, (row_rect.x + 10, row_rect.y + (row_h - 32) // 2))
                t_x = row_rect.x + 52
            else:
                t_x = row_rect.x + 12
                
            text(screen, fonts, "med", law_name, t_x, row_rect.y + 6, C_WHITE if (is_active or hover_row) else C_GREY)
            
            # Small description snippet under name
            law_d = PARSED_LAWS.get(law_name, {})
            desc_snippet = law_d.get("desc", "")
            if len(desc_snippet) > 60:
                desc_snippet = desc_snippet[:57] + "..."
            text(screen, fonts, "sm", desc_snippet, t_x, row_rect.y + 32, C_GREY)
            
            if hover_row:
                hovered_tooltip_law = law_name
                if pygame.mouse.get_pressed()[0] and not is_active:
                    country.enacting_law = {
                        "category": category,
                        "law_name": law_name,
                        "turns_left": 3
                    }
                    _selected_law_category = None
                    pygame.time.wait(200)
                    break

    # Finally, draw law tooltip if hovered
    if hovered_tooltip_law:
        draw_law_tooltip(screen, fonts, hovered_tooltip_law, mx, my, sw, sh)
        
    return False

def draw_war_panel(screen, fonts, game_state):
    """Vẽ bảng thông tin chiến tranh và lôi kéo đồng minh."""
    global show_war_panel
    sw, sh = screen.get_size()
    panel_w, panel_h = 1000, 530
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    # Draw panel background (1836 vibe charcoal, border gold)
    pygame.draw.rect(screen, (28, 25, 23), (panel_x, panel_y, panel_w, panel_h), border_radius=6)
    pygame.draw.rect(screen, C_GOLD, (panel_x, panel_y, panel_w, panel_h), 1, border_radius=6)
    
    text(screen, fonts, "med", "BANG CHIEN TRANH (WAR PANEL)", panel_x + 20, panel_y + 12, C_GOLD)
    
    # Nút đóng
    mx, my = pygame.mouse.get_pos()
    close_btn = pygame.Rect(panel_x + panel_w - 35, panel_y + 8, 28, 28)
    if draw_button(screen, fonts, close_btn, "X", (120, 40, 40), C_GOLD, C_WHITE, (mx, my), "med"):
        if pygame.mouse.get_pressed()[0]:
            pygame.time.wait(200)
            show_war_panel = False
            return

    player_tag = game_state.player_tag
    player_war_pair = None
    player_war_info = None
    
    for pair, w_info in game_state.active_wars.items():
        if player_tag in pair:
            player_war_pair = pair
            player_war_info = w_info
            break

    if not player_war_info or not player_war_pair:
        # Player is not at war
        text(screen, fonts, "title", "QUOC GIA CUA BAN DANG HOA BINH", panel_x + 100, panel_y + 180, C_WHITE)
        text(screen, fonts, "med", "Khong co cuoc chien nao dang dien ra co su tham gia cua ban.", panel_x + 100, panel_y + 240, C_GREY)
        text(screen, fonts, "sm", "Ban do hien thi o che do binh thuong.", panel_x + 100, panel_y + 280, C_GREY)
        return

    # Player is at war!
    leader_us = player_war_pair[0]
    leader_them = player_war_pair[1]
    player_is_side_a = (leader_us == player_tag)
    
    if not player_is_side_a:
        leader_us, leader_them = leader_them, leader_us
        allies_us = player_war_info.get("allies_b", set())
        allies_them = player_war_info.get("allies_a", set())
        dead_us = player_war_info.get("dead_b", 0)
        dead_them = player_war_info.get("dead_a", 0)
        war_score = -player_war_info.get("score", 0.0)
    else:
        allies_us = player_war_info.get("allies_a", set())
        allies_them = player_war_info.get("allies_b", set())
        dead_us = player_war_info.get("dead_a", 0)
        dead_them = player_war_info.get("dead_b", 0)
        war_score = player_war_info.get("score", 0.0)

    us_country = game_state.countries[leader_us]
    them_country = game_state.countries[leader_them]
    
    # Calculate total military power (army sizes)
    power_us = us_country.army_size + sum(game_state.countries[t].army_size for t in allies_us if t in game_state.countries)
    power_them = them_country.army_size + sum(game_state.countries[t].army_size for t in allies_them if t in game_state.countries)

    # 1. Left Side: Your Side
    col_x_us = panel_x + 30
    col_y = panel_y + 60
    text(screen, fonts, "med", "PHE TA (YOUR SIDE)", col_x_us, col_y, (100, 220, 140))
    pygame.draw.line(screen, C_BORDER, (col_x_us, col_y + 24), (col_x_us + 380, col_y + 24), 1)
    
    participants_us = [leader_us] + sorted(list(allies_us))
    for idx, t in enumerate(participants_us[:5]):
        row_y = col_y + 35 + idx * 26
        if t in game_state.countries:
            c_p = game_state.countries[t]
            # Flag
            fl_p = get_flag(t, getattr(c_p, 'government', 'default'), (24, 16), game_state=game_state)
            if fl_p:
                screen.blit(fl_p, (col_x_us, row_y))
            else:
                raw = game_state.countries_data.get(t, [100, 100, 100])
                pygame.draw.rect(screen, tuple(int(v) for v in raw[:3]), (col_x_us, row_y, 24, 16), border_radius=2)
            
            # Country name
            c_name = get_country_display_name(t, t)
            if t == leader_us:
                c_name += " (Lãnh đạo)"
            text(screen, fonts, "sm", c_name, col_x_us + 36, row_y, C_WHITE)
            
            # Army size
            army_size_str = f"{c_p.army_size}k quan"
            army_s = fonts["sm"].render(army_size_str, True, C_WHITE)
            screen.blit(army_s, (col_x_us + 380 - army_s.get_width(), row_y))
            
    # Stats at fixed positions
    text(screen, fonts, "sm", f"Thuong vong: {dead_us:,} linh", col_x_us, col_y + 175, C_RED)
    text(screen, fonts, "sm", f"Tong quan luc: {power_us}k quan", col_x_us, col_y + 195, C_WHITE)

    # 2. Right Side: Enemy Side
    col_x_them = panel_x + 590
    text(screen, fonts, "med", "PHE DICH (ENEMY SIDE)", col_x_them, col_y, (240, 110, 110))
    pygame.draw.line(screen, C_BORDER, (col_x_them, col_y + 24), (col_x_them + 380, col_y + 24), 1)
    
    participants_them = [leader_them] + sorted(list(allies_them))
    for idx, t in enumerate(participants_them[:5]):
        row_y = col_y + 35 + idx * 26
        if t in game_state.countries:
            c_p = game_state.countries[t]
            # Flag
            fl_p = get_flag(t, getattr(c_p, 'government', 'default'), (24, 16), game_state=game_state)
            if fl_p:
                screen.blit(fl_p, (col_x_them, row_y))
            else:
                raw = game_state.countries_data.get(t, [100, 100, 100])
                pygame.draw.rect(screen, tuple(int(v) for v in raw[:3]), (col_x_them, row_y, 24, 16), border_radius=2)
            
            # Country name
            c_name = get_country_display_name(t, t)
            if t == leader_them:
                c_name += " (Lãnh đạo)"
            text(screen, fonts, "sm", c_name, col_x_them + 36, row_y, C_WHITE)
            
            # Army size
            army_size_str = f"{c_p.army_size}k quan"
            army_s = fonts["sm"].render(army_size_str, True, C_WHITE)
            screen.blit(army_s, (col_x_them + 380 - army_s.get_width(), row_y))
            
    # Stats at fixed positions
    text(screen, fonts, "sm", f"Thuong vong: {dead_them:,} linh", col_x_them, col_y + 175, C_RED)
    text(screen, fonts, "sm", f"Tong quan luc: {power_them}k quan", col_x_them, col_y + 195, C_WHITE)

    # 3. Center: War Score
    center_x = panel_x + 430
    text(screen, fonts, "sm", "DIEM CHIEN TRANH", center_x + 10, col_y, C_GOLD)
    score_val_str = f"{war_score:+.1f}%"
    text(screen, fonts, "title", score_val_str, center_x + 30, col_y + 25, (100, 220, 140) if war_score >= 0 else (240, 110, 110))
    
    # Visual gauge bar
    gauge_x = center_x + 10
    gauge_y = col_y + 75
    gauge_w = 120
    gauge_h = 16
    pygame.draw.rect(screen, (50, 40, 40), (gauge_x, gauge_y, gauge_w, gauge_h), border_radius=4)
    # Map -100..100 war score to gauge fill
    fill_percent = (war_score + 100.0) / 200.0
    fill_percent = max(0.0, min(1.0, fill_percent))
    fill_w = int(gauge_w * fill_percent)
    if fill_w > 0:
        pygame.draw.rect(screen, (100, 220, 140) if war_score >= 0 else (240, 110, 110), (gauge_x, gauge_y, fill_w, gauge_h), border_radius=4)
    pygame.draw.rect(screen, C_GOLD_DIM, (gauge_x, gauge_y, gauge_w, gauge_h), 1, border_radius=4)
    
    # 4. Sway Allies section at the bottom
    sway_y = panel_y + 280
    text(screen, fonts, "med", "LOI KEO DONG MINH (SWAY NEUTRAL NATIONS)", panel_x + 20, sway_y, C_GOLD)
    pygame.draw.line(screen, C_BORDER, (panel_x + 20, sway_y + 24), (panel_x + 980, sway_y + 24), 1)

    # Find neutral countries (not at war, not player, not colonizable)
    neutrals = []
    for tag, c in game_state.countries.items():
        if tag == player_tag or c.is_colonizable:
            continue
        if c.at_war_with:
            continue
        if tag in allies_us or tag in allies_them:
            continue
        neutrals.append((tag, c))

    neutrals = sorted(neutrals, key=lambda pair_item: us_country.relations.get(pair_item[0], 0), reverse=True)

    # Render a list of 4 neutral countries that can be swayed
    sway_start_x = panel_x + 20
    sway_card_w = 230
    sway_card_h = 180
    card_gap = 13
    
    for idx, (tag, c_obj) in enumerate(neutrals[:4]):
        cx = sway_start_x + idx * (sway_card_w + card_gap)
        cy = sway_y + 35
        
        card_rect = pygame.Rect(cx, cy, sway_card_w, sway_card_h)
        pygame.draw.rect(screen, (36, 32, 28), card_rect, border_radius=6)
        pygame.draw.rect(screen, C_BORDER, card_rect, 1, border_radius=6)
        
        # Display flag and name
        fl_neutral = get_flag(tag, getattr(c_obj, 'government', 'default'), (48, 32))
        if fl_neutral: screen.blit(fl_neutral, (cx + 10, cy + 10))
        text(screen, fonts, "med", get_country_display_name(tag, tag)[:15], cx + 66, cy + 10, C_WHITE)
        
        rel = us_country.relations.get(tag, 0)
        rel_color = (100, 220, 140) if rel >= 20 else ((240, 110, 110) if rel <= -20 else C_WHITE)
        text(screen, fonts, "sm", f"Quan he: {rel:+}", cx + 10, cy + 50, rel_color)
        text(screen, fonts, "sm", f"Quan luc: {c_obj.army_size}k quan", cx + 10, cy + 72, C_WHITE)
        
        # Sway Chance and Cost
        chance = max(0, min(100, int(50 + rel * 0.5)))
        text(screen, fonts, "sm", f"Ty le thanh cong: {chance}%", cx + 10, cy + 95, C_GOLD_DIM)
        
        sway_btn = pygame.Rect(cx + 10, cy + 125, sway_card_w - 20, 36)
        can_sway = (us_country.treasury >= 150) and (rel >= -30)
        
        btn_bg = (40, 90, 55) if can_sway else (50, 50, 50)
        btn_border = C_GOLD if can_sway else C_GREY
        
        hover_btn = draw_button(screen, fonts, sway_btn, "Loi keo (-150L)", btn_bg, btn_border, C_WHITE, (mx, my), "sm")
        if hover_btn:
            if rel < -30:
                draw_build_tooltip(screen, fonts, "Khong the loi keo: Quan he qua thap (yeu cau >= -30)", mx, my)
            elif us_country.treasury < 150:
                draw_build_tooltip(screen, fonts, "Khong the loi keo: Thieu ngan kho (yeu cau 150L)", mx, my)
            
            if can_sway and pygame.mouse.get_pressed()[0]:
                import random
                us_country.treasury -= 150
                success = (random.randint(1, 100) <= chance)
                if success:
                    allies_us.add(tag)
                    if "allies_a" not in player_war_info: player_war_info["allies_a"] = set()
                    if "allies_b" not in player_war_info: player_war_info["allies_b"] = set()
                    if player_is_side_a:
                        player_war_info["allies_a"].add(tag)
                    else:
                        player_war_info["allies_b"].add(tag)
                    
                    us_country.relations[tag] = min(100, rel + 15)
                    game_state.last_event = {
                        "title": "LOI KEO THANH CONG!",
                        "desc": f"Quoc gia {get_country_display_name(tag, tag)} da dong y tham chien cung ban chong lai ke thu!",
                        "effect_text": "Quan he +15, tham chien"
                    }
                    game_state.needs_map_update = True
                else:
                    us_country.relations[tag] = max(-100, rel - 10)
                    game_state.last_event = {
                        "title": "LOI KEO THAT BAI",
                        "desc": f"Quoc gia {get_country_display_name(tag, tag)} da tu choi tham chien cung ban.",
                        "effect_text": "Quan he -10"
                    }
                pygame.time.wait(200)
                break

def draw_event_popup(screen, fonts, game_state):
    """Vẽ hộp thoại sự kiện (Random và Lịch sử) ở trung tâm màn hình."""
    ev = game_state.last_event
    if not ev:
        return
        
    sw, sh = screen.get_size()
    panel_w, panel_h = 540, 380
    panel_x = (sw - panel_w) // 2
    panel_y = (sh - panel_h) // 2
    
    # Làm mờ nền toàn màn hình
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    
    # Khung chính
    panel(screen, panel_x, panel_y, panel_w, panel_h, 255)
    pygame.draw.rect(screen, C_GOLD, (panel_x, panel_y, panel_w, panel_h), 1, border_radius=4)
    pygame.draw.rect(screen, (180, 140, 30), (panel_x+1, panel_y+1, panel_w-2, 2))  # top accent line
    
    # Tiêu đề sự kiện
    title_str = ev.get("title", "SỰ KIỆN QUỐC GIA")
    title_s = fonts["title"].render(title_str, True, C_GOLD)
    screen.blit(title_s, title_s.get_rect(centerx=panel_x + panel_w // 2, y=panel_y + 15))
    
    # Phân tách tiêu đề
    pygame.draw.line(screen, C_GOLD_DIM, (panel_x + 20, panel_y + 45), (panel_x + panel_w - 20, panel_y + 45))
    
    # Nội dung mô tả sự kiện (hỗ trợ xuống dòng tự động)
    desc_str = ev.get("desc", "")
    desc_font = fonts["med"]
    max_text_w = panel_w - 50
    
    # Hàm wrap chữ
    words = desc_str.split(" ")
    lines = []
    curr_line = []
    for w in words:
        test_line = " ".join(curr_line + [w])
        if desc_font.size(test_line)[0] <= max_text_w:
            curr_line.append(w)
        else:
            lines.append(" ".join(curr_line))
            curr_line = [w]
    if curr_line:
        lines.append(" ".join(curr_line))
        
    dy = panel_y + 60
    for line in lines[:6]:  # Tối đa hiển thị 6 dòng mô tả
        s = desc_font.render(line, True, C_WHITE)
        screen.blit(s, (panel_x + 25, dy))
        dy += desc_font.get_height() + 4
        
    country = game_state.player_country
    mx, my = pygame.mouse.get_pos()
    
    # Vẽ các nút lựa chọn
    if not ev.get("options"):
        # Sự kiện đơn giản: chỉ có 1 nút Tiếp tục
        btn_y = panel_y + panel_h - 55
        btn_r = pygame.Rect(panel_x + 40, btn_y, panel_w - 80, 38)
        
        effect_text = ev.get("effect_text", "Tiếp tục")
        label = f"Xác nhận ({effect_text})"
        
        hover = btn_r.collidepoint(mx, my)
        pygame.draw.rect(screen, (30, 80, 50) if hover else (20, 50, 30), btn_r, border_radius=6)
        pygame.draw.rect(screen, C_GOLD if hover else C_BORDER, btn_r, 1, border_radius=6)
        
        ls = fonts["med"].render(label, True, C_WHITE)
        screen.blit(ls, ls.get_rect(center=btn_r.center))
        
        if hover and pygame.mouse.get_pressed()[0]:
            from engine.events import apply_event
            apply_event(ev, country)
            if ev.get("is_game_over"):
                game_state.force_exit_to_lobby = True
            game_state.last_event = None
            pygame.time.wait(200)
            
    else:
        # Sự kiện có nhiều lựa chọn (options)
        options = ev.get("options", [])
        opt_count = len(options)
        
        # Tính toán vị trí các nút bắt đầu từ dưới lên
        btn_h = 36
        btn_gap = 6
        total_opt_h = opt_count * btn_h + (opt_count - 1) * btn_gap
        
        btn_start_y = panel_y + panel_h - total_opt_h - 20
        
        for opt in options:
            btn_r = pygame.Rect(panel_x + 25, btn_start_y, panel_w - 50, btn_h)
            hover = btn_r.collidepoint(mx, my)
            
            pygame.draw.rect(screen, (70, 50, 30) if hover else (40, 30, 20), btn_r, border_radius=4)
            pygame.draw.rect(screen, C_GOLD if hover else C_BORDER, btn_r, 1, border_radius=4)
            
            opt_name = opt["name"]
            opt_effect = opt["effect_desc"]
            
            ns = fonts["sm"].render(opt_name, True, C_WHITE)
            es = fonts["sm"].render(f" ({opt_effect})", True, (200, 200, 150))
            
            total_w = ns.get_width() + es.get_width()
            start_x = btn_r.x + (btn_r.width - total_w) // 2
            
            screen.blit(ns, (start_x, btn_r.y + (btn_h - ns.get_height()) // 2))
            screen.blit(es, (start_x + ns.get_width(), btn_r.y + (btn_h - es.get_height()) // 2))
            
            if hover and pygame.mouse.get_pressed()[0]:
                event_obj = ev.get("event_obj")
                if event_obj:
                    event_obj.execute_option(country, game_state, opt["index"])
                else:
                    action_type = opt.get("action_type")
                    if action_type:
                        from engine.game_state import execute_custom_peace_action
                        execute_custom_peace_action(game_state, opt)
                    elif "effect" in opt and opt["effect"]:
                        try:
                            opt["effect"](country, game_state)
                        except TypeError:
                            opt["effect"](country)
                
                if ev.get("is_game_over"):
                    game_state.force_exit_to_lobby = True
                
                game_state.last_event = None
                pygame.time.wait(200)
                break
            btn_start_y += btn_h + btn_gap
                
def save_game(game_state, filepath):
    import pickle
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(game_state, f)

def draw_in_game_menu(screen, fonts, game_state):
    global _menu_open, _menu_mode
    import pickle
    import os
    import sys
    from engine.country_names import get_country_display_name
    from game_ui import build_province_state_lookup, draw_button

    sw, sh = screen.get_size()
    mx, my = pygame.mouse.get_pos()
    
    # 1. Overlay làm mờ màn hình game sau lưng
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    # 2. Left-aligned Panel
    pw, ph = 360, sh
    px, py = 0, 0
    
    panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (*C_PANEL, 245), (0, 0, pw, ph))
    screen.blit(panel_surf, (px, py))
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    saves_dir = os.path.join(base_dir, "data", "saves")
    os.makedirs(saves_dir, exist_ok=True)
    
    bx = 30
    btn_w, btn_h = 300, 45
    
    if _menu_mode == "main":
        # Title
        title_s = fonts["title"].render("TRÌNH ĐƠN CHÍNH", True, C_GOLD)
        screen.blit(title_s, title_s.get_rect(centerx=px + pw // 2, y=py + 40))
        pygame.draw.line(screen, C_GOLD_DIM, (px + 20, py + 85), (px + pw - 20, py + 85), 2)
        
        by = py + 120
        
        # Resume
        resume_rect = pygame.Rect(bx, by, btn_w, btn_h)
        resume_hov = draw_button(screen, fonts, resume_rect, "TIẾP TỤC CHƠI", (30, 45, 35), C_GOLD, C_WHITE, (mx, my), "med")
        if resume_hov and pygame.mouse.get_pressed()[0]:
            _menu_open = False
            pygame.time.wait(200)
            
        # Save Game
        save_rect = pygame.Rect(bx, by + 65, btn_w, btn_h)
        save_hov = draw_button(screen, fonts, save_rect, "LƯU TIẾN TRÌNH", (30, 40, 50), C_GOLD, C_WHITE, (mx, my), "med")
        if save_hov and pygame.mouse.get_pressed()[0]:
            _menu_mode = "save"
            pygame.time.wait(200)
            
        # Load Game
        load_rect = pygame.Rect(bx, by + 130, btn_w, btn_h)
        load_hov = draw_button(screen, fonts, load_rect, "TẢI TIẾN TRÌNH", (30, 40, 50), C_GOLD, C_WHITE, (mx, my), "med")
        if load_hov and pygame.mouse.get_pressed()[0]:
            _menu_mode = "load"
            pygame.time.wait(200)
            
        # Switch Country
        switch_rect = pygame.Rect(bx, by + 210, btn_w, btn_h)
        switch_hov = draw_button(screen, fonts, switch_rect, "CHUYỂN QUỐC GIA", (50, 40, 60), C_GOLD, C_WHITE, (mx, my), "med")
        if switch_hov and pygame.mouse.get_pressed()[0]:
            _menu_open = False
            _menu_mode = "main"
            pygame.time.wait(200)
            return "exit_lobby"
            
        # Exit to Desktop
        exit_rect = pygame.Rect(bx, by + 275, btn_w, btn_h)
        exit_hov = draw_button(screen, fonts, exit_rect, "THOÁT GAME", (70, 30, 30), C_GOLD, C_WHITE, (mx, my), "med")
        if exit_hov and pygame.mouse.get_pressed()[0]:
            pygame.quit()
            sys.exit()
            
    elif _menu_mode in ("save", "load"):
        is_save = (_menu_mode == "save")
        title_text = "LƯU TIẾN TRÌNH" if is_save else "TẢI TIẾN TRÌNH"
        title_s = fonts["title"].render(title_text, True, C_GOLD)
        screen.blit(title_s, title_s.get_rect(centerx=px + pw // 2, y=py + 40))
        pygame.draw.line(screen, C_GOLD_DIM, (px + 20, py + 85), (px + pw - 20, py + 85), 2)
        
        by = py + 110
        slot_h = 42
        
        for i in range(1, 6):
            slot_rect = pygame.Rect(bx, by + (i - 1) * 55, btn_w, slot_h)
            filepath = os.path.join(saves_dir, f"slot_{i}.sav")
            exists = os.path.exists(filepath)
            
            slot_label = f"Slot {i}: Trống"
            if exists:
                try:
                    with open(filepath, 'rb') as f:
                        gs = pickle.load(f)
                    c_name = get_country_display_name(gs.player_tag)
                    date_str = gs.current_date.short
                    slot_label = f"Slot {i}: {c_name} ({date_str})"
                except Exception as ex_err:
                    print(f"Error reading slot {i}: {ex_err}")
                    slot_label = f"Slot {i}: File lỗi"
            
            bg_col = (25, 35, 45) if exists or is_save else (18, 22, 28)
            border_col = C_GOLD if exists or is_save else (60, 60, 60)
            text_col = C_WHITE if exists or is_save else C_GREY
            
            slot_hov = draw_button(screen, fonts, slot_rect, slot_label, bg_col, border_col, text_col, (mx, my), "sm")
            
            if slot_hov and pygame.mouse.get_pressed()[0]:
                if is_save:
                    try:
                        save_game(game_state, filepath)
                        print(f"Saved game to slot {i}")
                        pygame.time.wait(250)
                    except Exception as ex_err:
                        print(f"Failed to save game to slot {i}: {ex_err}")
                else:
                    if exists:
                        try:
                            with open(filepath, 'rb') as f:
                                loaded_state = pickle.load(f)
                            game_state.__dict__.update(loaded_state.__dict__)
                            game_state.needs_map_update = True
                            build_province_state_lookup(game_state)
                            print(f"Loaded game from slot {i}")
                            _menu_open = False
                            _menu_mode = "main"
                            pygame.time.wait(250)
                            return "loaded"
                        except Exception as ex_err:
                            print(f"Failed to load game from slot {i}: {ex_err}")
                            
        # Quay lại
        back_rect = pygame.Rect(bx, py + ph - 80, btn_w, btn_h)
        back_hov = draw_button(screen, fonts, back_rect, "QUAY LẠI", (45, 28, 12), C_GOLD, C_GOLD, (mx, my), "sm")
        if back_hov and pygame.mouse.get_pressed()[0]:
            _menu_mode = "main"
            pygame.time.wait(200)

    return None


# ── Leaderboard ─────────────────────────────────────
_RANK_MEDALS = ["🥇", "🥈", "🥉"]
_RANK_COLORS = [
    (255, 215, 0),    # Gold
    (192, 192, 192),  # Silver
    (205, 127, 50),   # Bronze
    (180, 200, 220),  # 4th
    (160, 185, 210),  # 5th
    (140, 170, 200),  # 6th
    (120, 155, 185),  # 7th
    (100, 140, 170),  # 8th
]

def draw_leaderboard(screen, fonts, game_state, x=12, y=12, width=290, max_rows=8, mouse_pos=(0, 0)):
    """BXH Uy tính: nút lớn hiển thị Rank Logo -> click mở panel sổ cái đầy đủ bên tay trái (Victoria 3 style).
    Returns the toggle button Rect.
    """
    global _leaderboard_open, _profile_tag, _leaderboard_row_held, _leaderboard_btn_held, _leaderboard_sort_by, _leaderboard_header_held
    
    country = game_state.player_country
    if not country:
        return pygame.Rect(x, y, 0, 0)
        
    rank_num, rank_class, rank_name = get_country_rank(country, game_state)
    rank_img = _ranks.get(rank_class)

    # ─────────────────────────────────────────
    # TOGGLE BUTTON (Prestige Rank Badge - Only Logo and Number)
    # ─────────────────────────────────────────
    btn_w, btn_h = 42, 50
    btn = pygame.Rect(x, y, btn_w, btn_h)
    hov = btn.collidepoint(mouse_pos)



    # Draw Rank Badge Image
    if rank_img:
        scaled = pygame.transform.smoothscale(rank_img, (btn_w, btn_h))
        screen.blit(scaled, btn.topleft)
    else:
        pygame.draw.rect(screen, (30, 30, 30), btn, border_radius=6)
        pygame.draw.rect(screen, C_GOLD_DIM, btn, 1, border_radius=6)

    # Draw the rank number inside the logo (centered, no '#' character)
    rk_s = fonts["sm"].render(str(rank_num), True, C_GOLD if hov else C_WHITE)
    text_rect = rk_s.get_rect(center=(btn.centerx, btn.y + btn_h // 2 + 2))
    
    # Tiny shadow behind text for readability
    shadow_s = fonts["sm"].render(str(rank_num), True, (0, 0, 0))
    screen.blit(shadow_s, (text_rect.x + 1, text_rect.y + 1))
    screen.blit(rk_s, text_rect.topleft)

    if not _leaderboard_open:
        return btn

    # ─────────────────────────────────────────
    # EXPANDED PANEL (Left-aligned, Full height scrollable ledger)
    # ─────────────────────────────────────────
    sw, sh = screen.get_size()
    px = 12
    py = y + btn_h + 8 
    pw = 480
    ph = sh - py - 20 

    # Semi-transparent panel
    bg_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    bg_surf.fill((*C_PANEL, 245))
    screen.blit(bg_surf, (px, py))
    pygame.draw.rect(screen, C_GOLD, (px, py, pw, ph), 1, border_radius=8)
    pygame.draw.rect(screen, (180, 140, 30), (px+1, py+1, pw-2, 2))  # top accent line

    # Title: SỔ CÁI QUỐC GIA - UY TÍN
    title_s = fonts["med"].render("📊 SỔ CÁI QUỐC GIA - UY TÍN", True, C_GOLD)
    screen.blit(title_s, (px + 15, py + 12))
    
    # Close button 'X' inside the panel
    close_rect = pygame.Rect(px + pw - 30, py + 10, 20, 20)
    close_hov = close_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (160, 45, 45) if close_hov else (90, 30, 30), close_rect, border_radius=4)
    cx_s = fonts["sm"].render("X", True, C_WHITE)
    screen.blit(cx_s, cx_s.get_rect(center=close_rect.center))
    
    if close_hov and pygame.mouse.get_pressed()[0]:
        import game_ui as _gui_m
        _gui_m._leaderboard_open = False
        pygame.time.wait(200)

    # Column titles header line
    header_y = py + 40
    pygame.draw.rect(screen, (30, 40, 50), (px + 1, header_y, pw - 2, 24))
    pygame.draw.line(screen, C_BORDER, (px, header_y), (px + pw, header_y))
    pygame.draw.line(screen, C_BORDER, (px, header_y + 24), (px + pw, header_y + 24))

    # Click collision areas for sortable headers
    rect_hang = pygame.Rect(px + 5, header_y, 40, 24)
    rect_uytin = pygame.Rect(px + 220, header_y, 60, 24)
    rect_gdp = pygame.Rect(px + 280, header_y, 70, 24)
    rect_sol = pygame.Rect(px + 350, header_y, 50, 24)
    rect_dancu = pygame.Rect(px + 400, header_y, 75, 24)
    
    m_clicked = pygame.mouse.get_pressed()[0]
    if m_clicked:
        if not _leaderboard_header_held:
            mx, my = mouse_pos
            if rect_hang.collidepoint(mx, my) or rect_uytin.collidepoint(mx, my):
                _leaderboard_sort_by = "prestige"
                pygame.time.wait(100)
            elif rect_gdp.collidepoint(mx, my):
                _leaderboard_sort_by = "gdp"
                pygame.time.wait(100)
            elif rect_sol.collidepoint(mx, my):
                _leaderboard_sort_by = "sol"
                pygame.time.wait(100)
            elif rect_dancu.collidepoint(mx, my):
                _leaderboard_sort_by = "population"
                pygame.time.wait(100)
            _leaderboard_header_held = True
    else:
        _leaderboard_header_held = False

    # Headers text with highlighting
    headers = [
        ("Hạng", px + 10, "prestige"),
        ("Cờ", px + 50, None),
        ("Quốc gia", px + 85, None),
        ("Uy tín", px + 225, "prestige"),
        ("GDP", px + 285, "gdp"),
        ("SoL", px + 355, "sol"),
        ("Dân cư", px + 405, "population")
    ]
    for h_txt, h_x, sort_key in headers:
        is_active = (sort_key is not None and _leaderboard_sort_by == sort_key)
        if sort_key:
            col_color = C_GOLD if is_active else C_GOLD_DIM
            # Hover check
            mx, my = mouse_pos
            rect_h = pygame.Rect(h_x - 5, header_y, 45, 24)
            if rect_h.collidepoint(mx, my) and not is_active:
                col_color = C_WHITE
        else:
            col_color = C_GOLD_DIM
            
        text_s = fonts["sm"].render(h_txt, True, col_color)
        screen.blit(text_s, (h_x, header_y + 4))

    # Scrollable rows area
    list_y = header_y + 25
    list_h = ph - 40 - 25 - 10
    
    # Sort all countries based on _leaderboard_sort_by
    if _leaderboard_sort_by == "gdp":
        sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.gdp, reverse=True)
    elif _leaderboard_sort_by == "sol":
        sorted_countries = sorted(
            game_state.countries.values(),
            key=lambda c: 10.0 + c.literacy * 15.0 + (c.gdp / max(0.1, c.population)) * 2.0,
            reverse=True
        )
    elif _leaderboard_sort_by == "population":
        sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.population, reverse=True)
    else:
        sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.prestige, reverse=True)
    
    # Max scroll calculation for mouse wheel scroll limits
    total_h = len(sorted_countries) * 32
    max_scroll = max(0, total_h - list_h)
    import game_ui as _gui_m
    _gui_m._leaderboard_scroll = max(0, min(max_scroll, _gui_m._leaderboard_scroll))

    # Set clipping region
    old_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(px, list_y, pw, list_h))

    ry = list_y - _gui_m._leaderboard_scroll
    for idx, c_obj in enumerate(sorted_countries):
        is_player = (c_obj.tag == game_state.player_tag)
        row_rect = pygame.Rect(px + 4, ry, pw - 8, 30)
        
        # Row click detection: click opens profile panel
        row_hover = row_rect.collidepoint(mouse_pos)
        if row_hover and pygame.mouse.get_pressed()[0]:
            if not _leaderboard_row_held:
                _gui_m._profile_tag = c_obj.tag
                _leaderboard_row_held = True
                pygame.time.wait(200)
        else:
            # reset row held if mouse not pressed
            if not pygame.mouse.get_pressed()[0]:
                _leaderboard_row_held = False
        
        # Draw alternate backgrounds or player highlight
        if is_player:
            pygame.draw.rect(screen, (30, 60, 40, 150), row_rect, border_radius=4)
            pygame.draw.rect(screen, C_GREEN, row_rect, 1, border_radius=4)
        elif row_hover:
            pygame.draw.rect(screen, (40, 45, 55, 120), row_rect, border_radius=4)
        elif idx % 2 == 0:
            pygame.draw.rect(screen, (22, 30, 40, 100), row_rect, border_radius=4)
            
        # Draw Rank
        rank_num, rank_class, rank_name = get_country_rank(c_obj, game_state)
        rank_img = _ranks.get(rank_class)
        if rank_img:
            scaled_emblem = pygame.transform.smoothscale(rank_img, (24, 28))
            screen.blit(scaled_emblem, (px + 12, ry + 1))
        else:
            pygame.draw.rect(screen, (30, 30, 30), (px + 12, ry + 1, 24, 28), border_radius=3)
            
        rk_text = str(idx + 1)
        rk_s = fonts["sm"].render(rk_text, True, C_GOLD if is_player else C_WHITE)
        text_rect = rk_s.get_rect(center=(px + 12 + 12, ry + 15))
        
        # Shadow for readability
        shadow_s = fonts["sm"].render(rk_text, True, (0, 0, 0))
        screen.blit(shadow_s, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(rk_s, text_rect.topleft)
        
        # Draw Flag
        flag_box = pygame.Rect(px + 50, ry + 4, 30, 22)
        fl = get_flag(c_obj.tag, "default", size=(30, 22), game_state=game_state)
        if fl:
            screen.blit(fl, flag_box.topleft)
        else:
            raw_c = game_state.countries_data.get(c_obj.tag, [100, 100, 100])
            pygame.draw.rect(screen, tuple(int(v) for v in raw_c[:3]), flag_box, border_radius=2)
        pygame.draw.rect(screen, C_BORDER, flag_box, 1, border_radius=2)
        
        # Draw Country Name
        cname = get_country_display_name(c_obj.tag, c_obj.tag)
        max_n_w = 135
        while cname and fonts["sm"].size(cname)[0] > max_n_w:
            cname = cname[:-1]
        cname_s = fonts["sm"].render(cname, True, C_WHITE)
        screen.blit(cname_s, (px + 85, ry + 6))
        
        # Draw Prestige
        prestige_s = fonts["sm"].render(str(int(c_obj.prestige)), True, C_GOLD)
        screen.blit(prestige_s, (px + 225, ry + 6))
        
        # Draw GDP
        gdp_val = c_obj.gdp
        gdp_str = f"£{gdp_val/1000:.1f}B" if gdp_val >= 1000 else f"£{int(gdp_val)}M"
        gdp_s = fonts["sm"].render(gdp_str, True, (150, 220, 150))
        screen.blit(gdp_s, (px + 285, ry + 6))
        
        # Draw SoL
        sol_val = 10.0 + c_obj.literacy * 15.0 + (c_obj.gdp / max(0.1, c_obj.population)) * 2.0
        sol_s = fonts["sm"].render(f"{sol_val:.1f}", True, C_GOLD)
        screen.blit(sol_s, (px + 355, ry + 6))
        
        # Draw Population
        pop_str = f"{c_obj.population:.1f}M"
        pop_s = fonts["sm"].render(pop_str, True, C_GREY)
        screen.blit(pop_s, (px + 405, ry + 6))
        
        ry += 32
        
    # Restore clipping
    screen.set_clip(old_clip)

    # Draw Scrollbar
    if max_scroll > 0:
        sb_w = 4
        sb_h = int(list_h * (list_h / total_h))
        sb_y = list_y + int((list_h - sb_h) * (_gui_m._leaderboard_scroll / max_scroll))
        pygame.draw.rect(screen, C_BORDER, (px + pw - 6, list_y, sb_w, list_h), border_radius=2)
        pygame.draw.rect(screen, C_GOLD, (px + pw - 6, sb_y, sb_w, sb_h), border_radius=2)

    return btn

def draw_country_profile(screen, fonts, game_state, tag, mouse_pos):
    """Vẽ bảng thông tin chi tiết quốc gia bên tay trái."""
    global _profile_tag
    
    if not tag:
        return
        
    c_obj = game_state.countries.get(tag)
    if not c_obj:
        return
        
    sw, sh = screen.get_size()
    pw, ph = 460, sh - HUD_H
    px, py = 0, HUD_H
    
    # Draw panel background
    panel(screen, px, py, pw, ph, 250)
    pygame.draw.line(screen, C_GOLD, (px + pw - 1, py), (px + pw - 1, py + ph), 2)
    
    # Title display name
    cname = get_country_display_name(tag, tag).upper()
    title_s = fonts["title"].render(cname, True, C_GOLD)
    screen.blit(title_s, (px + 60, py + 12))
    
    # Subtitle: Market info
    overlord_tag = None
    for k, v in game_state.countries.items():
        if tag in getattr(v, "subjects", set()):
            overlord_tag = k
            break
            
    if overlord_tag:
        market_name = get_country_display_name(overlord_tag, overlord_tag)
        market_str = f"Quốc gia ở Thị trường {market_name}"
    else:
        market_str = f"Quốc gia ở Thị trường {get_country_display_name(tag, tag)}"
        
    sub_s = fonts["sm"].render(market_str, True, C_GREY)
    screen.blit(sub_s, (px + 60, py + 38))
    
    # Curved back arrow button (top left)
    back_btn = pygame.Rect(px + 12, py + 14, 30, 30)
    back_hov = back_btn.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (50, 60, 70) if back_hov else (30, 40, 50), back_btn, border_radius=6)
    pygame.draw.rect(screen, C_GOLD_DIM, back_btn, 1, border_radius=6)
    arrow_s = fonts["med"].render("↺", True, C_GOLD)
    screen.blit(arrow_s, arrow_s.get_rect(center=back_btn.center))
    
    if back_hov and pygame.mouse.get_pressed()[0]:
        _profile_tag = None
        pygame.time.wait(200)
        return

    # Close 'X' button (top right)
    close_btn = pygame.Rect(px + pw - 42, py + 14, 30, 30)
    close_hov = close_btn.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (160, 45, 45) if close_hov else (90, 30, 30), close_btn, border_radius=6)
    pygame.draw.rect(screen, C_GOLD_DIM, close_btn, 1, border_radius=6)
    x_s = fonts["med"].render("X", True, C_WHITE)
    screen.blit(x_s, x_s.get_rect(center=close_btn.center))
    
    if close_hov and pygame.mouse.get_pressed()[0]:
        _profile_tag = None
        pygame.time.wait(200)
        return

    # Divider line
    pygame.draw.line(screen, C_GOLD_DIM, (px + 15, py + 70), (px + pw - 15, py + 70))
    
    # Left Column: Flag, Ruler, Government
    lx = px + 20
    # Big Flag
    flag_r = pygame.Rect(lx, py + 85, 140, 95)
    fl = get_flag(tag, getattr(c_obj, "government", "default"), size=(140, 95), game_state=game_state)
    if fl:
        screen.blit(fl, flag_r.topleft)
    else:
        raw_c = game_state.countries_data.get(tag, [100, 100, 100])
    # Leader / Ruler Portrait
    portrait_center = (lx + 70, py + 265)
    pygame.draw.circle(screen, C_GOLD, portrait_center, 52, 2)
    pygame.draw.circle(screen, (18, 30, 45), portrait_center, 50)
    
    # Stylized silhouette inside circle
    pygame.draw.polygon(screen, C_GOLD, [
        (lx + 52, py + 250), (lx + 50, py + 235), (lx + 60, py + 245),
        (lx + 70, py + 230), (lx + 80, py + 245), (lx + 90, py + 235),
        (lx + 88, py + 250)
    ])
    pygame.draw.circle(screen, C_WHITE, (lx + 70, py + 270), 22)
    pygame.draw.polygon(screen, C_GREY, [
        (lx + 45, py + 300), (lx + 95, py + 300), (lx + 80, py + 275), (lx + 60, py + 275)
    ])
    
    # Government Regime Box
    gov_rect = pygame.Rect(lx, py + 335, 140, 75)
    pygame.draw.rect(screen, (22, 28, 35), gov_rect, border_radius=6)
    pygame.draw.rect(screen, C_BORDER, gov_rect, 1, border_radius=6)
    
    gov_title_s = fonts["sm"].render("Chính phủ:", True, C_GREY)
    screen.blit(gov_title_s, (lx + 10, py + 340))
    
    gov_val = GOVT_LABELS.get(c_obj.government, "Mặc định")
    gov_font = fonts["sm"]
    if gov_font.size(gov_val)[0] > 120:
        gov_lines = [gov_val[:14], gov_val[14:]]
    else:
        gov_lines = [gov_val]
        
    gy = py + 358
    for gl in gov_lines:
        gl_s = gov_font.render(gl, True, C_WHITE)
        screen.blit(gl_s, (lx + 10, gy))
        gy += 16
        
    # Right Column: Country info list
    rx = px + 180
    ry = py + 85
    
    rank_num, rank_class, rank_name = get_country_rank(c_obj, game_state)
    
    # 1. Rank
    text(screen, fonts, "sm", "Xếp hạng", rx, ry, C_GREY)
    rank_str = f"{rank_name} {rank_num}"
    text(screen, fonts, "sm", rank_str, rx, ry + 15, C_WHITE)
    rank_img = _ranks.get(rank_class)
    if rank_img:
        scaled_r = pygame.transform.smoothscale(rank_img, (22, 26))
        screen.blit(scaled_r, (px + pw - 40, ry + 4))
    ry += 35
    
    # 2. Power Bloc
    text(screen, fonts, "sm", "Khối Quyền lực", rx, ry, C_GREY)
    leads = getattr(c_obj, 'leads_bloc', False)
    member_of_bloc_leader = None
    for k, v in game_state.countries.items():
        if tag in getattr(v, 'power_bloc', set()):
            member_of_bloc_leader = k
            break
            
    if leads:
        bloc_name = getattr(c_obj, 'power_bloc_name', '')
        if not bloc_name:
            bloc_name = f"Khối {get_country_display_name(tag, tag)}"
        bloc_members = getattr(c_obj, 'power_bloc', set())
        bloc_member_names = [get_country_display_name(m, m) for m in bloc_members]
        if bloc_member_names:
            bloc_val = f"{bloc_name} ({len(bloc_member_names)} TV: {', '.join(bloc_member_names)})"
        else:
            bloc_val = f"{bloc_name} (Chưa có TV)"
    elif member_of_bloc_leader:
        leader_obj = game_state.countries.get(member_of_bloc_leader)
        bloc_name = getattr(leader_obj, 'power_bloc_name', '') if leader_obj else ''
        if not bloc_name:
            bloc_name = f"Khối {get_country_display_name(member_of_bloc_leader, member_of_bloc_leader)}"
        bloc_val = f"Thành viên ({bloc_name})"
    else:
        bloc_val = "Không liên kết"
        
    if len(bloc_val) > 28:
        bloc_val = bloc_val[:25] + "..."
    text(screen, fonts, "sm", bloc_val, rx, ry + 15, C_WHITE)
    ry += 35
    
    # 2b. Alliance / Allies
    text(screen, fonts, "sm", "Liên minh (Đồng minh)", rx, ry, C_GREY)
    allies = getattr(c_obj, 'allies', set())
    if allies:
        alliance_name = getattr(c_obj, 'alliance_name', '')
        if not alliance_name:
            for a in allies:
                a_obj = game_state.countries.get(a)
                if a_obj and getattr(a_obj, 'alliance_name', ''):
                    alliance_name = a_obj.alliance_name
                    break
        ally_names = [get_country_display_name(a, a) for a in allies]
        if alliance_name:
            ally_val = f"{alliance_name} ({len(allies)} TV: {', '.join(ally_names)})"
        else:
            ally_val = f"{', '.join(ally_names)} (Tổng: {len(allies)})"
    else:
        ally_val = "Không có"
    if len(ally_val) > 28:
        ally_val = ally_val[:25] + "..."
    text(screen, fonts, "sm", ally_val, rx, ry + 15, C_WHITE)
    ry += 35
    
    # 3. Battalions
    text(screen, fonts, "sm", "Tiểu đoàn (Quân đội)", rx, ry, C_GREY)
    army_val = f"{c_obj.army_size // 1000} + 0"
    text(screen, fonts, "sm", army_val, rx, ry + 15, C_WHITE)
    soldier_s = fonts["sm"].render("⚔️", True, C_GOLD)
    screen.blit(soldier_s, (px + pw - 40, ry + 8))
    ry += 35
    
    # 4. GDP
    text(screen, fonts, "sm", "GDP", rx, ry, C_GREY)
    gdp_val = c_obj.gdp
    gdp_str = f"£{gdp_val/1000:.2f}B" if gdp_val >= 1000 else f"£{int(gdp_val)}M"
    text(screen, fonts, "sm", gdp_str, rx, ry + 15, (150, 220, 150))
    gdp_b = fonts["sm"].render("🪙", True, C_GOLD)
    screen.blit(gdp_b, (px + pw - 40, ry + 8))
    ry += 35
    
    # 5. GDP Ownership
    text(screen, fonts, "sm", "Quyền sở hữu GDP", rx, ry, C_GREY)
    text(screen, fonts, "sm", "100.0%", rx, ry + 15, C_WHITE)
    ry += 35
    
    # 6. Population
    text(screen, fonts, "sm", "Dân cư (Dân số)", rx, ry, C_GREY)
    text(screen, fonts, "sm", f"{c_obj.population:.2f}M", rx, ry + 15, C_WHITE)
    ry += 35
    
    # 7. Literacy
    text(screen, fonts, "sm", "Tỷ lệ Học thức", rx, ry, C_GREY)
    text(screen, fonts, "sm", f"{c_obj.literacy*100:.1f}%", rx, ry + 15, C_WHITE)
    ry += 35
    
    # 8. Standard of Living
    text(screen, fonts, "sm", "Mức sống", rx, ry, C_GREY)
    sol_val = 10.0 + c_obj.literacy * 15.0 + (c_obj.gdp / max(0.1, c_obj.population)) * 2.0
    if sol_val < 10.0:
        sol_desc = f"Chật vật ({sol_val:.1f})"
        sol_col = C_RED
    elif sol_val < 15.0:
        sol_desc = f"Đủ ăn ({sol_val:.1f})"
        sol_col = C_WHITE
    elif sol_val < 20.0:
        sol_desc = f"Thịnh vượng ({sol_val:.1f})"
        sol_col = C_GREEN
    else:
        sol_desc = f"Xa hoa ({sol_val:.1f})"
        sol_col = C_GOLD
    text(screen, fonts, "sm", sol_desc, rx, ry + 15, sol_col)
    ry += 35
    
    # 9. Religion
    text(screen, fonts, "sm", "Tôn giáo Quốc gia", rx, ry, C_GREY)
    rel_map = {"DAI": "Nho Giáo", "QNG": "Nho Giáo", "TUR": "Hồi giáo", 
               "GBR": "Cơ đốc giáo", "USA": "Cơ đốc giáo", "FRA": "Cơ đốc giáo",
               "PRU": "Cơ đốc giáo", "AUS": "Cơ đốc giáo", "RUS": "Cơ đốc giáo"}
    religion = rel_map.get(tag, "Đa thần giáo")
    text(screen, fonts, "sm", religion, rx, ry + 15, C_WHITE)
    ry += 35
    
    # 10. Culture
    text(screen, fonts, "sm", "Văn hóa Chính", rx, ry, C_GREY)
    cult_map = {"DAI": "Việt Nam", "GBR": "Anh", "USA": "Mỹ", "FRA": "Pháp",
                "PRU": "Đức", "AUS": "Đức", "RUS": "Nga", "QNG": "Trung Hoa"}
    culture = cult_map.get(tag, "Bản địa")
    text(screen, fonts, "sm", culture, rx, ry + 15, C_WHITE)
    ry += 35
    
    # Bottom Section: Modifiers
    pygame.draw.line(screen, C_GOLD_DIM, (px + 15, py + ph - 85), (px + pw - 15, py + ph - 85))
    
    text(screen, fonts, "med", "SỬ ĐỔI & NHẬT KÝ", px + 20, py + ph - 80, C_GOLD)
    
    mod_map = {
        "GBR": ("Đế quốc mặt trời không bao giờ lặn", "Tăng 15% uy tín quốc gia", "20 năm"),
        "DAI": ("Dư chấn Khởi nghĩa Tây Sơn", "Giảm 5% ổn định xã hội", "10 năm"),
        "FRA": ("Tác động Cách mạng Pháp", "Tăng 10% ý thức tự do dân cư", "15 năm"),
        "USA": ("Thử thách Lập quốc", "Tăng 10% tốc độ di cư", "30 năm")
    }
    
    mod_title, mod_desc, mod_time = mod_map.get(tag, ("Ổn định kinh tế", "Tăng nhẹ mức tăng trưởng kinh tế", "5 năm"))
    text(screen, fonts, "sm", f"📌 {mod_title} ({mod_time})", px + 20, py + ph - 55, C_WHITE)
    text(screen, fonts, "sm", f"   {mod_desc}", px + 20, py + ph - 35, C_GREY)

def is_ui_blocking_click(pos, game_state=None):
    """Kiểm tra xem click chuột có đè lên bất kỳ panel UI nào hay không."""
    global game_state_ref
    if game_state is None:
        game_state = game_state_ref
    if not game_state:
        return False
        
    ex, ey = pos
    sw, sh = pygame.display.get_surface().get_size()
    import game_ui as _gui
    
    # 1. Hộp thoại sự kiện chặn hoàn toàn click trên map
    if game_state.last_event:
        return True
        
    # 2. ESC Menu chặn hoàn toàn click trên map
    if getattr(_gui, "_menu_open", False):
        return True
        
    # 3. Bảng Luật pháp & Chính trị
    if getattr(_gui, "show_politics_panel", False):
        if getattr(_gui, "_selected_law_category", None):
            return True # Bảng chọn luật (Choices Modal Overlay) chặn toàn màn hình
        px, py = (sw - 1000) // 2, (sh - 530) // 2
        if pygame.Rect(px, py, 1000, 530).collidepoint(ex, ey):
            return True
            
    # 4. Bảng Xây dựng công trình
    if getattr(_gui, "show_build_panel", False):
        px, py = (sw - 1000) // 2, (sh - 530) // 2
        if pygame.Rect(px, py, 1000, 530).collidepoint(ex, ey):
            return True
            
    # 5. Bảng Chiến tranh
    if getattr(_gui, "show_war_panel", False):
        px, py = (sw - 1000) // 2, (sh - 530) // 2
        if pygame.Rect(px, py, 1000, 530).collidepoint(ex, ey):
            return True
            
    # 6. Bảng Ngoại giao
    if getattr(_gui, "show_diplomacy", False):
        px, py = (sw - DIPLOMACY_PANEL_W) // 2, (sh - DIPLOMACY_PANEL_H) // 2
        if pygame.Rect(px, py, DIPLOMACY_PANEL_W, DIPLOMACY_PANEL_H).collidepoint(ex, ey):
            return True
            
    # 7. Hồ sơ quốc gia (Profile bên trái)
    if getattr(_gui, "_profile_tag", None):
        if ex <= 460 and ey > HUD_H:
            return True
            
    # 8. Bảng xếp hạng (Leaderboard collapsible)
    if getattr(_gui, "_leaderboard_open", False):
        if pygame.Rect(12, HUD_H + 70, 480, sh - (HUD_H + 70) - 20).collidepoint(ex, ey):
            return True
    if pygame.Rect(12, HUD_H + 12, 42, 50).collidepoint(ex, ey):
        # Nút huy hiệu mở rộng / đóng bảng xếp hạng
        return True
        
    # 9. Các ô HUD nổi
    # Left Card
    if pygame.Rect(8, 8, 500, 64).collidepoint(ex, ey):
        return True
    # War HUD button (if player country is at war)
    player_country = game_state.player_country
    if player_country and player_country.at_war_with:
        if pygame.Rect(520, 22, 140, 36).collidepoint(ex, ey):
            return True
    # Right Card (Date / Next Turn)
    if ey <= 76 and ex >= sw - 420:
        return True
        
    # 10. Nút Menu góc dưới cùng bên phải
    if pygame.Rect(sw - 110, sh - 40, 100, 30).collidepoint(ex, ey):
        return True
        
    return False

# ── HUD ──────────────────────────────────────────────
def draw_hud(screen, fonts, game_state, screen_w, screen_h):
    global _hud_flag_held
    tag = game_state.player_tag
    mode = getattr(game_state, "player_mode", "default")
    country = game_state.player_country
    if not country:
        return pygame.Rect(0, 0, 0, 0)
        
    mx, my = pygame.mouse.get_pos()

    # Calculate date width for dynamic right card sizing
    date_str = game_state.current_date.full
    ds = fonts["date"].render(date_str, True, C_GOLD)
    
    # Position Next Turn Button and Right Card
    bw, bh = 150, 36
    bx = screen_w - bw - 24
    by = 22
    btn = pygame.Rect(bx, by, bw, bh)
    
    date_x = bx - ds.get_width() - 20
    date_y = by + (bh - ds.get_height()) // 2
    
    rx = date_x - 20
    rw = screen_w - rx - 8
    
    # ── Draw Background Panels ─────────────────────────
    # Left Card Background (Flag & Stats) - Borderless
    left_surf = pygame.Surface((500, 64), pygame.SRCALPHA)
    left_surf.fill((*C_PANEL, 240))
    screen.blit(left_surf, (8, 8))
    
    # Right Card Background (Date & Next Turn) - Borderless
    right_surf = pygame.Surface((rw, 64), pygame.SRCALPHA)
    right_surf.fill((*C_PANEL, 240))
    screen.blit(right_surf, (rx, 8))

    # Solid red HUD war button (no flashing) with brighter border when at war
    if country.at_war_with:
        war_btn_rect = pygame.Rect(520, 22, 140, 36)
        import game_ui as _gui
        # Solid red background (150, 30, 30), border color (180, 40, 40)
        if draw_button(screen, fonts, war_btn_rect, "⚔️ WAR PANEL", (150, 30, 30), (180, 40, 40), C_WHITE, (mx, my), "sm"):
            if pygame.mouse.get_pressed()[0]:
                _gui.show_war_panel = not _gui.show_war_panel
                _gui.show_build_panel = False
                _gui.show_politics_panel = False
                _gui.show_diplomacy = False
                pygame.time.wait(200)
    
    # 1. Draw Flag inside Left Card
    flag_r = pygame.Rect(16, 16, 68, 48)
    fl = get_flag(tag, mode, size=(68, 48), game_state=game_state)
    if fl:
        screen.blit(fl, flag_r.topleft)
    else:
        raw = game_state.countries_data.get(tag, [100, 100, 100])
        pygame.draw.rect(screen, tuple(int(v) for v in raw[:3]), flag_r, border_radius=4)
        
    # Flag click handling
    flag_hover = flag_r.collidepoint(mx, my)
    if pygame.mouse.get_pressed()[0] and flag_hover:
        if not _hud_flag_held:
            import game_ui as _gui_m
            if _gui_m._profile_tag == tag:
                _gui_m._profile_tag = None
            else:
                _gui_m._profile_tag = tag
            _hud_flag_held = True
    else:
        _hud_flag_held = False
        
    # 2. Draw Stats Columns (Shifted left to use the space left by rank badge)
    col_x = [100, 200, 300, 400]
    
    # Calculate player stats
    bureaucracy = int(150 + country.prestige * 3.5 - (country.army_size * 0.25))
    authority_map = {
        "absolute_monarchy": 500, "dictatorship": 400, "communist": 300,
        "fascist": 450, "republic": 200, "theocracy": 350, "default": 250
    }
    authority = authority_map.get(country.government, 250)
    num_relations = len(country.allies) + len(country.trade_agreements) + len(country.defense_pacts)
    influence = int(300 + country.prestige * 5 - (num_relations * 40))
    
    rep = game_state.economy_report.get(tag)
    treasury_change = rep["delta"] if rep else 0.0
    
    r1_vals = [
        (f"+{bureaucracy}" if bureaucracy >= 0 else str(bureaucracy), True, "Hud_bureaucracy", C_GREEN if bureaucracy >= 0 else C_RED),
        (f"+{authority}" if authority >= 0 else str(authority), True, "Hud_authority", C_GREEN if authority >= 0 else C_RED),
        (f"+{influence}" if influence >= 0 else str(influence), True, "Hud_influence", C_GREEN if influence >= 0 else C_RED),
        (f"{treasury_change:+.0f}" if treasury_change != 0 else "0", treasury_change >= 0, "£", C_GREEN if treasury_change >= 0 else C_RED)
    ]
    
    sol_val = 10.0 + country.literacy * 15.0 + (country.gdp / max(0.1, country.population)) * 2.0
    r2_vals = [
        (f"{country.population:.1f}M", "Hud_population", C_WHITE),
        (f"{country.literacy*100:.1f}%", "Hud_literacy", C_WHITE),
        (f"{sol_val:.1f}", get_sol_icon_name(sol_val), C_GOLD),
        (f"{int(country.gdp)}M", "GDP", (180, 220, 255))
    ]
    
    for i in range(4):
        cx = col_x[i]
        
        # Row 1 drawing
        val_str, is_pos, icon_key, val_color = r1_vals[i]
        icon_img = get_hud_icon(icon_key)
        
        if icon_img:
            screen.blit(icon_img, (cx, 10))
            icon_w = icon_img.get_width()
        else:
            icon_s = fonts["sm"].render(icon_key, True, C_GOLD)
            screen.blit(icon_s, (cx, 14))
            icon_w = icon_s.get_width()
            
        val_s = fonts["sm"].render(val_str, True, val_color)
        screen.blit(val_s, (cx + icon_w + 6, 14))
        
        # Draw small bar under Row 1 (centered at Y = 36)
        bar_x = cx
        bar_y = 36
        bar_w = 75
        bar_h = 3
        pygame.draw.rect(screen, (30, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=1)
        fill_w = int(bar_w * 0.75) if i < 3 else min(bar_w, max(0, int(bar_w * (country.treasury / 2000.0))))
        pygame.draw.rect(screen, C_GOLD_DIM if i < 3 else (C_GREEN if is_pos else C_RED), (bar_x, bar_y, fill_w, bar_h), border_radius=1)
        
        # Row 2 drawing
        val_str2, icon_key2, val_color2 = r2_vals[i]
        icon_img2 = get_hud_icon(icon_key2)
        
        if icon_img2:
            screen.blit(icon_img2, (cx, 42))
            icon_w2 = icon_img2.get_width()
        else:
            icon_s2 = fonts["sm"].render(icon_key2, True, C_GOLD)
            screen.blit(icon_s2, (cx, 46))
            icon_w2 = icon_s2.get_width()
            
        val_s2 = fonts["sm"].render(val_str2, True, val_color2)
        screen.blit(val_s2, (cx + icon_w2 + 6, 46))

    # Center HUD Info: Historical Age & Epidemic Warning / Research Progress
    center_x = screen_w // 2
    
    age_map = {
        "Age of Revolution": "Kỷ nguyên Cách mạng",
        "Age of Industrialisation": "Kỷ nguyên Công nghiệp hóa",
        "Age of Imperialism": "Kỷ nguyên Đế quốc chủ nghĩa"
    }
    age_name = age_map.get(getattr(game_state, "current_age", "Age of Industrialisation"), "Kỷ nguyên Công nghiệp hóa")
    
    age_s = fonts["med"].render(age_name, True, C_GOLD)
    screen.blit(age_s, age_s.get_rect(centerx=center_x, y=14))
    
    # Check if player has infected provinces
    player_infected = False
    for d_name, epi in game_state.active_epidemics.items():
        for p_id in epi["provinces"]:
            p_obj = game_state.provinces.get(p_id)
            if p_obj and p_obj.owner == tag:
                player_infected = True
                break
        if player_infected:
            break
            
    if player_infected:
        # Flashing alert notice: "⚠️ LÃNH THỔ CÓ DỊCH BỆNH"
        flash = (pygame.time.get_ticks() // 500) % 2 == 0
        warn_color = (255, 100, 100) if flash else (180, 50, 50)
        warn_s = fonts["sm"].render("⚠️ CẢNH BÁO DỊCH BỆNH!", True, warn_color)
        screen.blit(warn_s, warn_s.get_rect(centerx=center_x, y=42))
    else:
        if hasattr(country, "research_points"):
            base_cost = 100.0
            age = getattr(game_state, "current_age", "Age of Industrialisation")
            cost_mult = 0.8 if age == "Age of Revolution" else (1.2 if age == "Age of Imperialism" else 1.0)
            tech_cost = base_cost * cost_mult
            
            tech_count = len(getattr(country, "technologies", []))
            research_s = fonts["sm"].render(f"Công nghệ: {tech_count} | Nghiên cứu: {int(country.research_points)}/{int(tech_cost)}", True, (150, 200, 255))
            screen.blit(research_s, research_s.get_rect(centerx=center_x, y=42))

    # 3. Date & Next Turn Button
    draw_button(screen, fonts, btn, "▶ NEXT TURN", (35, 90, 50), (35, 90, 50), (200, 255, 210), (mx, my), "hud")
    screen.blit(ds, (date_x, date_y))
    
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


# ── Diplomacy Panel ───────────────────────────────────────
_diplo_detail_tag = None

def draw_diplomacy_panel(screen, fonts, game_state, mouse_pos):
    global diplomacy_selected_tag, show_diplomacy, _diplo_detail_tag, _diplo_scroll, _diplo_list_scroll
    
    sw, sh = screen.get_size()
    PW, PH = DIPLOMACY_PANEL_W, DIPLOMACY_PANEL_H
    px = (sw - PW) // 2
    py = (sh - PH) // 2

    panel(screen, px, py, PW, PH, 250)

    close_btn = pygame.Rect(px + PW - 36, py + 8, 28, 28)
    close_hov = close_btn.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (160, 45, 45) if close_hov else (90, 30, 30), close_btn, border_radius=5)
    pygame.draw.rect(screen, C_GOLD_DIM, close_btn, 1, border_radius=5)
    xs = fonts["med"].render("X", True, C_WHITE)
    screen.blit(xs, xs.get_rect(center=close_btn.center))
    if close_hov and pygame.mouse.get_pressed()[0]:
        show_diplomacy = False
        _diplo_detail_tag = None
        _diplo_scroll = 0
        _diplo_list_scroll = 0
        pygame.time.wait(200)

    country = game_state.player_country
    if not country:
        return close_btn

    # ──────────────────────────────────────────────────────────────
    # DETAIL VIEW
    # ──────────────────────────────────────────────────────────────
    if _diplo_detail_tag and _diplo_detail_tag in game_state.countries:
        target      = game_state.countries[_diplo_detail_tag]
        target_name = get_country_display_name(_diplo_detail_tag, _diplo_detail_tag)
        rel         = country.relations.get(_diplo_detail_tag, 0)
        rel_color   = get_relations_color(rel)
        at_war      = _diplo_detail_tag in country.at_war_with
        allied      = _diplo_detail_tag in country.allies
        has_trade   = _diplo_detail_tag in country.trade_agreements
        has_nap     = _diplo_detail_tag in country.non_aggression_pacts
        has_def     = _diplo_detail_tag in country.defense_pacts
        expelled    = _diplo_detail_tag in country.expelled_diplomats
        is_subject  = _diplo_detail_tag in country.subjects
        in_bloc     = _diplo_detail_tag in country.power_bloc

        # Row 1: back (left) — close button stays top-right from panel()
        back_btn = pygame.Rect(px + 8, py + 8, 108, 26)
        bh = back_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (50, 80, 110) if bh else (30, 55, 80), back_btn, border_radius=5)
        pygame.draw.rect(screen, C_GOLD_DIM, back_btn, 1, border_radius=5)
        bs = fonts["sm"].render("<< Danh sach", True, C_WHITE)
        screen.blit(bs, bs.get_rect(center=back_btn.center))
        if bh and pygame.mouse.get_pressed()[0]:
            _diplo_detail_tag = None
            _diplo_scroll = 0
            pygame.time.wait(200)

        pygame.draw.line(screen, C_GOLD_DIM, (px + 8, py + 38), (px + PW - 8, py + 38))

        # Row 2: flag + country name (left-aligned, no overlap with back)
        y_hdr = py + 44
        tc = _rgb_color(game_state.countries_data.get(_diplo_detail_tag))
        flag_rect = pygame.Rect(px + 12, y_hdr, 24, 26)
        pygame.draw.rect(screen, tc, flag_rect, border_radius=3)
        pygame.draw.rect(screen, C_GOLD, flag_rect, 1, border_radius=3)
        name_max_w = (px + PW - 8 - close_btn.width) - (flag_rect.right + 12)
        tn = fonts["title"].render(target_name, True, C_GOLD)
        if tn.get_width() > name_max_w:
            short = target_name
            while short and fonts["title"].render(short + "...", True, C_GOLD).get_width() > name_max_w:
                short = short[:-1]
            tn = fonts["title"].render((short + "...") if short else "...", True, C_GOLD)
        screen.blit(tn, (flag_rect.right + 10, y_hdr + 2))

        pygame.draw.line(screen, C_GOLD_DIM, (px + 8, y_hdr + 32), (px + PW - 8, y_hdr + 32))

        # ── Quick Stats ──
        y = y_hdr + 40
        cols4 = (PW - 16) // 4
        for i, (lbl, val) in enumerate([
            ("Dan so", f"{target.population:.1f}M"),
            ("GDP",    f"{int(target.gdp)}M"),
            ("Quan",   f"{target.army_size}k"),
            ("Uy tin", f"{int(target.prestige)}"),
        ]):
            bx = px + 8 + i * cols4
            pygame.draw.rect(screen, (25, 35, 48), (bx, y, cols4 - 4, 38), border_radius=4)
            pygame.draw.rect(screen, C_BORDER, (bx, y, cols4 - 4, 38), 1, border_radius=4)
            ls = fonts["sm"].render(lbl, True, C_GREY)
            vs = fonts["med"].render(val, True, C_WHITE)
            screen.blit(ls, (bx + 4, y + 2))
            screen.blit(vs, (bx + 4, y + 18))
        y += 46

        # ── Relations bar ──
        rl = fonts["sm"].render(f"Quan he: {rel:+d}", True, rel_color)
        screen.blit(rl, (px + 8, y)); y += 18
        bw = PW - 16
        pygame.draw.rect(screen, (30, 30, 45), (px + 8, y, bw, 12), border_radius=5)
        fw = int(bw * (rel + 100) / 200)
        if fw > 0:
            pygame.draw.rect(screen, rel_color, (px + 8, y, fw, 12), border_radius=5)
        pygame.draw.rect(screen, C_BORDER, (px + 8, y, bw, 12), 1, border_radius=5)
        y += 20

        # ── Status badges ──
        bx2 = px + 8
        status_badges = []
        if at_war:
            status_badges.append(("CHIEN TRANH", (170, 35, 35)))
        if allied:
            status_badges.append(("DONG MINH", (35, 130, 60)))
        if has_trade:
            status_badges.append(("HT THUONG MAI", (45, 100, 155)))
        if has_nap:
            status_badges.append(("HT KHONG XL", (75, 75, 140)))
        if has_def:
            status_badges.append(("HT PHONG THU", (55, 95, 55)))
        if expelled:
            status_badges.append(("DA TRUC XUAT", (110, 75, 35)))
        if is_subject:
            status_badges.append(("CHU HAU", (90, 70, 120)))
        if in_bloc:
            status_badges.append(("KHOI QLC", (60, 90, 130)))
        for badge_text, badge_col in status_badges:
            bsf = fonts["sm"].render(badge_text, True, C_WHITE)
            brect = pygame.Rect(bx2, y, bsf.get_width() + 10, 17)
            if bx2 + brect.width > px + PW - 8:
                bx2 = px + 8; y += 20
            pygame.draw.rect(screen, badge_col, brect, border_radius=3)
            screen.blit(bsf, (bx2 + 5, y + 1))
            bx2 += brect.width + 8
        y += 24

        pygame.draw.line(screen, C_GOLD_DIM, (px + 8, y), (px + PW - 8, y)); y += 6

        # ──────────────────────────────────────────────────────────
        # SCROLLABLE ACTION AREA
        # ──────────────────────────────────────────────────────────
        action_top = y
        clip = pygame.Rect(px + 4, action_top, PW - 8, py + PH - action_top - 4)
        screen.set_clip(clip)
        ey = action_top - _diplo_scroll  # effective y (shifted by scroll)

        BW = (PW - 20) // 2 - 4   # button width in 2-col grid
        BH = 30                    # button height

        def sec(title):
            """Draw section header."""
            nonlocal ey
            if clip.top <= ey <= clip.bottom:
                hs = fonts["sm"].render(f"--- {title} ---", True, C_GOLD_DIM)
                screen.blit(hs, (px + 8, ey))
            ey += 22

        def btn_row(items):
            """Draw a row of 1-2 action buttons.
            items = list of (label, enabled, callback)
            """
            nonlocal ey
            items = [(label, enabled, cb) for label, enabled, cb in items if label]
            if not items:
                return
            for col_i, (label, enabled, callback) in enumerate(items):
                bx3 = px + 8 + col_i * (BW + 8)
                brect2 = pygame.Rect(bx3, ey, BW, BH)
                if clip.top - BH <= ey <= clip.bottom:
                    bg   = (35, 80, 50) if enabled else (40, 42, 48)
                    bord = C_GOLD       if enabled else C_BORDER
                    hover2 = brect2.collidepoint(mouse_pos)
                    if hover2 and enabled:
                        bg = tuple(min(255, c + 20) for c in bg)
                    pygame.draw.rect(screen, bg, brect2, border_radius=4)
                    pygame.draw.rect(screen, bord, brect2, 1, border_radius=4)
                    ls2 = fonts["sm"].render(label, True, C_WHITE if enabled else C_GREY)
                    screen.blit(ls2, ls2.get_rect(center=brect2.center))
                    if hover2 and enabled and pygame.mouse.get_pressed()[0]:
                        callback()
                        pygame.time.wait(200)
            ey += BH + 6

        # ─── 1. QUAN HE ───────────────────────────────────
        sec("QUAN HE (Relations)")
        def _rel_now():
            return country.relations.get(_diplo_detail_tag, 0)

        def do_improve():
            r = _rel_now()
            country.relations[_diplo_detail_tag] = min(100, r + 10)
            if not hasattr(country, 'relations_modified_this_turn'):
                country.relations_modified_this_turn = set()
            country.relations_modified_this_turn.add(_diplo_detail_tag)
            game_state.last_event = {"title": "CAI THIEN QUAN HE", "desc": f"+10 quan he voi {target_name}.", "effect_text": "Quan he +10"}
        def do_decrease():
            r = _rel_now()
            country.relations[_diplo_detail_tag] = max(-100, r - 10)
            if not hasattr(country, 'relations_modified_this_turn'):
                country.relations_modified_this_turn = set()
            country.relations_modified_this_turn.add(_diplo_detail_tag)
            game_state.last_event = {"title": "LAM XAU QUAN HE", "desc": f"-10 quan he voi {target_name}.", "effect_text": "Quan he -10"}
        def do_expel():
            country.expelled_diplomats.add(_diplo_detail_tag)
            r = _rel_now()
            country.relations[_diplo_detail_tag] = max(-100, r - 25)
            game_state.last_event = {"title": "TRUC XUAT", "desc": f"Truc xuat ngoai giao {target_name}.", "effect_text": "Quan he -25"}
        def do_guarantee():
            country.guarantees.add(_diplo_detail_tag)
            r = _rel_now()
            country.relations[_diplo_detail_tag] = min(100, r + 15)
            game_state.last_event = {"title": "DAM BAO DOC LAP", "desc": f"Dam bao doc lap {target_name}.", "effect_text": "+15 quan he"}
            
        if not hasattr(country, 'relations_modified_this_turn'):
            country.relations_modified_this_turn = set()
        rel_modified = _diplo_detail_tag in country.relations_modified_this_turn
        
        btn_row([
            ("Cai thien (+10)", not at_war and not expelled and not rel_modified, do_improve),
            ("Lam xau (-10)",   not at_war and not rel_modified, do_decrease),
        ])
        btn_row([
            ("Truc xuat Ngoai giao", not at_war and not expelled, do_expel),
            ("Dam bao Doc lap",      rel >= 20 and not at_war and target.gdp < country.gdp, do_guarantee),
        ])
        ey += 4

        # ─── 2. HIEP UOC ──────────────────────────────────
        sec("HIEP UOC (Treaties)")
        def do_trade_treaty():
            if not hasattr(country, 'trade_agreements'): country.trade_agreements = set()
            if not hasattr(target, 'trade_agreements'):  target.trade_agreements  = set()
            if _diplo_detail_tag in country.trade_agreements: return
            country.trade_agreements.add(_diplo_detail_tag)
            target.trade_agreements.add(country.tag)
            country.relations[_diplo_detail_tag] = min(100, rel + 10)
            bonus = max(5, int(10 + rel // 10))
            country.treasury += bonus; target.treasury += bonus
            game_state.last_event = {"title": "HIEP UOC THUONG MAI", "desc": f"Ky voi {target_name}.", "effect_text": f"+{bonus}L ca hai ben"}
        def do_nap():
            if not hasattr(country, 'non_aggression_pacts'): country.non_aggression_pacts = set()
            if not hasattr(target,  'non_aggression_pacts'): target.non_aggression_pacts  = set()
            if _diplo_detail_tag in country.non_aggression_pacts: return
            country.non_aggression_pacts.add(_diplo_detail_tag)
            target.non_aggression_pacts.add(country.tag)
            country.relations[_diplo_detail_tag] = min(100, rel + 5)
            game_state.last_event = {"title": "HT KHONG XAM LUOC", "desc": f"Ky voi {target_name}.", "effect_text": "Khong tan cong nhau"}
        def do_def_pact():
            if not hasattr(country, 'defense_pacts'): country.defense_pacts = set()
            if not hasattr(target,  'defense_pacts'): target.defense_pacts  = set()
            if _diplo_detail_tag in country.defense_pacts: return
            country.defense_pacts.add(_diplo_detail_tag)
            target.defense_pacts.add(country.tag)
            country.relations[_diplo_detail_tag] = min(100, rel + 15)
            game_state.last_event = {"title": "HT PHONG THU CHUNG", "desc": f"Ky voi {target_name}.", "effect_text": "Bao ve nhau khi bi tan cong"}
        def do_alliance():
            if _diplo_detail_tag in country.allies: return
            alliance_name = getattr(country, 'alliance_name', None)
            if not alliance_name:
                alliance_name = draw_text_input_modal(screen, fonts, "Dat ten Lien minh", f"Lien minh {get_country_display_name(country.tag, country.tag)}")
                if not alliance_name:
                    return
            country.allies.add(_diplo_detail_tag); target.allies.add(country.tag)
            country.alliance_name = alliance_name
            target.alliance_name = alliance_name
            country.relations[_diplo_detail_tag] = min(100, rel + 20)
            game_state.last_event = {"title": "LIEN MINH!", "desc": f"Lien minh voi {target_name}.", "effect_text": f"Ky {alliance_name}"}
        def do_break_ally():
            country.allies.discard(_diplo_detail_tag); target.allies.discard(country.tag)
            country.relations[_diplo_detail_tag] = max(-100, rel - 15)
            if not country.allies and hasattr(country, 'alliance_name'):
                delattr(country, 'alliance_name')
            if not target.allies and hasattr(target, 'alliance_name'):
                delattr(target, 'alliance_name')
            game_state.last_event = {"title": "HUY LIEN MINH", "desc": f"Huy voi {target_name}.", "effect_text": "Quan he -15"}
        btn_row([
            ("HT Thuong mai" + (" (HH)" if has_trade else ""),  rel >= 0 and not at_war and not has_trade, do_trade_treaty),
            ("HT Khong XL"   + (" (HH)" if has_nap else ""),   rel >= 0 and not at_war and not has_nap,   do_nap),
        ])
        btn_row([
            ("Phong thu Chung" + (" (HH)" if has_def else ""),  rel >= 30 and not at_war and not has_def, do_def_pact),
            ("Huy Lien minh" if allied else ("Moi vao Lien minh" if getattr(country, 'alliance_name', None) else "Tao Lien minh"), allied or (rel >= 50 and not at_war), do_break_ally if allied else do_alliance),
        ])
        ey += 4

        # ─── 3. NGOAI GIAO CHIEN ──────────────────────────
        sec("PHAT DONG NGOAI GIAO (Diplomatic Play)")
        def do_diplo_play():
            import random
            if country.prestige >= target.prestige * 1.2:
                b2 = random.randint(10, 30); country.treasury += b2; country.prestige -= 30
                country.relations[_diplo_detail_tag] = max(-100, rel - 20)
                game_state.last_event = {"title": "NGOAI GIAO CHIEN", "desc": f"Thanh cong voi {target_name}.", "effect_text": f"+{b2}L, Uy tin -30"}
            else:
                country.prestige -= 15; country.relations[_diplo_detail_tag] = max(-100, rel - 10)
                game_state.last_event = {"title": "ND CHIEN THAT BAI", "desc": "That bai.", "effect_text": "Uy tin -15, Quan he -10"}
        def do_war():
            country.at_war_with.add(_diplo_detail_tag); target.at_war_with.add(country.tag)
            country.allies.discard(_diplo_detail_tag)
            country.relations[_diplo_detail_tag] = max(-100, rel - 50)
            
            # Initialize active_wars record immediately
            # Ensure both tags are not None so sorted() receives comparable values
            if country.tag is None or _diplo_detail_tag is None:
                return
            pair = tuple(sorted((country.tag, _diplo_detail_tag)))
            if pair not in game_state.active_wars:
                game_state.active_wars[pair] = {
                    "score": 0.0,
                    "battles_count": 0,
                    "allies_a": set(),
                    "allies_b": set(),
                    "dead_a": 0,
                    "dead_b": 0
                }
                
            game_state.last_event = {"title": "CHIEN TRANH!", "desc": f"Tuyen chien voi {target_name}.", "effect_text": "Quan he -50"}
            game_state.needs_map_update = True
        def do_peace():
            country.at_war_with.discard(_diplo_detail_tag); target.at_war_with.discard(country.tag)
            country.relations[_diplo_detail_tag] = max(-100, rel - 10)
            game_state.last_event = {"title": "HOA BINH", "desc": f"Cau hoa voi {target_name}.", "effect_text": "Chien tranh ket thuc"}
            game_state.needs_map_update = True
        btn_row([
            ("Ngoai giao Chien",  not at_war and country.prestige >= 30, do_diplo_play),
            ("Tuyen Chien",       not at_war, do_war),
        ])
        btn_row([
            ("De nghi Hoa binh",  at_war, do_peace),
        ])
        ey += 4

        # ─── 4. KINH TE ───────────────────────────────────
        if not hasattr(country, 'trade_action_done_this_turn'):
            country.trade_action_done_this_turn = set()
        if not hasattr(country, 'total_trade_actions_this_turn'):
            country.total_trade_actions_this_turn = 0
            
        trade_done = _diplo_detail_tag in country.trade_action_done_this_turn
        trade_count = country.total_trade_actions_this_turn

        sec("KINH TE & THUONG MAI (Economy & Trade)")
        def do_trade_action():
            if _diplo_detail_tag in getattr(country, 'trade_action_done_this_turn', set()):
                return
            if getattr(country, 'total_trade_actions_this_turn', 0) >= 3:
                return
            b3 = max(5, int(10 + rel // 10))
            country.treasury += b3; target.treasury += b3
            country.relations[_diplo_detail_tag] = min(100, rel + 3)
            if not hasattr(country, 'trade_action_done_this_turn'):
                country.trade_action_done_this_turn = set()
            country.trade_action_done_this_turn.add(_diplo_detail_tag)
            country.total_trade_actions_this_turn = getattr(country, 'total_trade_actions_this_turn', 0) + 1
            game_state.last_event = {"title": "THUONG MAI", "desc": f"Trao doi voi {target_name}.", "effect_text": f"+{b3}L ca hai ben"}
        def do_invest():
            country.treasury -= 100; target.gdp += 5; country.gdp += 2
            country.relations[_diplo_detail_tag] = min(100, rel + 8)
            game_state.last_event = {"title": "DAU TU NN", "desc": f"Dau tu vao {target_name}.", "effect_text": "-100L, +5 GDP ho"}
            
        trade_label = f"Trao doi Thuong mai ({trade_count}/3)"
        btn_row([
            (trade_label,    rel >= 0 and not at_war and not trade_done and trade_count < 3,        do_trade_action),
            ("Dau tu Nuoc ngoai(-100L)", rel >= 20 and not at_war and country.treasury >= 100, do_invest),
        ])
        ey += 4

        # ─── 5. LOI KEO ───────────────────────────────────
        sec("LOI KEO (Sways)")
        def do_bribe():
            country.treasury -= 50; country.relations[_diplo_detail_tag] = min(100, rel + 25)
            game_state.last_event = {"title": "HOI LO", "desc": f"Hoi lo quan chuc {target_name}.", "effect_text": "-50L, Quan he +25"}
        def do_sway():
            country.prestige -= 10; country.relations[_diplo_detail_tag] = min(100, rel + 15)
            game_state.last_event = {"title": "LOI KEO", "desc": f"Loi keo {target_name}.", "effect_text": "-10 uy tin, Quan he +15"}
        def do_cultural():
            country.relations[_diplo_detail_tag] = min(100, rel + 8)
            game_state.last_event = {"title": "KET NOI VAN HOA", "desc": f"Ket noi voi {target_name}.", "effect_text": "Quan he +8"}
        btn_row([
            ("Hoi lo Quan chuc (-50L)", country.treasury >= 50,  do_bribe),
            ("Loi keo Sway (-10 UT)",   country.prestige >= 10, do_sway),
        ])
        btn_row([
            ("Ket noi Van hoa", True, do_cultural),
        ])
        ey += 4

        # ─── 6. KHOI QUYEN LUC ────────────────────────────
        sec("KHOI QUYEN LUC (Power Blocs)")
        def do_invite_bloc():
            if not hasattr(country, 'power_bloc'): country.power_bloc = set()
            country.power_bloc.add(_diplo_detail_tag)
            country.relations[_diplo_detail_tag] = min(100, rel + 10)
            game_state.last_event = {"title": "MOI VAO KHOI", "desc": f"Moi {target_name} vao khoi.", "effect_text": "Quan he +10"}
        def do_create_bloc():
            bloc_name = draw_text_input_modal(screen, fonts, "Dat ten Khoi Quyen luc", f"Khoi {get_country_display_name(country.tag, country.tag)}")
            if not bloc_name:
                return
            country.prestige -= 50
            country.leads_bloc = True
            country.power_bloc_name = bloc_name
            if not hasattr(country, 'power_bloc'): country.power_bloc = set()
            game_state.last_event = {"title": "TAO KHOI QLC", "desc": f"Da tao khoi {bloc_name}.", "effect_text": "Uy tin -50, dan dau khoi"}
        btn_row([
            ("Moi vao Khoi QLC", rel >= 20 and not at_war and getattr(country, 'leads_bloc', False), do_invite_bloc),
            ("Tao Khoi QLC (-50UT)", country.prestige >= 50 and not getattr(country, 'leads_bloc', False) and get_country_rank(country, game_state)[1] == "great_power", do_create_bloc),
        ])
        ey += 4

        # ─── 7. CHU HAU ───────────────────────────────────
        sec("CHU HAU & BAO HO (Subjects & Protectorates)")
        def do_protectorate():
            country.subjects.add(_diplo_detail_tag)
            r = _rel_now()
            country.relations[_diplo_detail_tag] = min(100, r + 30)
            game_state.last_event = {"title": "BAO HO QUOC", "desc": f"{target_name} la bao ho.", "effect_text": "Quan he +30"}
        def do_puppet():
            country.subjects.add(_diplo_detail_tag)
            target.treasury = max(0, target.treasury - 50)
            r = _rel_now()
            country.relations[_diplo_detail_tag] = min(100, r + 20)
            game_state.last_event = {"title": "GIA LAM CHU HAU", "desc": f"{target_name} tro thanh chu hau.", "effect_text": "Quan he +20, thu phi"}
        def do_tribute():
            import random
            if random.random() < 0.35:
                trib = max(20, int(target.treasury * 0.1))
                country.treasury += trib; target.treasury -= trib
                game_state.last_event = {"title": "GI DAU", "desc": f"{target_name} gi dau!", "effect_text": f"+{trib}L cong pham"}
            else:
                country.relations[_diplo_detail_tag] = max(-100, rel - 15)
                game_state.last_event = {"title": "TU CHOI", "desc": f"{target_name} tu choi!", "effect_text": "Quan he -15"}
        btn_row([
            ("De nghi Bao ho",   rel >= 40 and not at_war and country.gdp > target.gdp * 3, do_protectorate),
            ("Gia lam Chu hau",  rel >= 30 and not at_war and country.prestige > target.prestige, do_puppet),
        ])
        btn_row([
            ("Yeu cau Gi dau",   country.prestige > target.prestige * 1.5, do_tribute),
        ])
        ey += 4

        # ─── 8. QUAN LY CHU HAU ───────────────────────────
        if is_subject:
            sec("QUAN LY CHU HAU (Subject Management)")
            def do_autonomy():
                country.subjects.discard(_diplo_detail_tag)
                country.relations[_diplo_detail_tag] = min(100, rel + 20)
                game_state.last_event = {"title": "CAP TU TRI", "desc": f"{target_name} duoc tu tri.", "effect_text": "Quan he +20"}
            btn_row([
                ("Cap Quyen tu tri", True, do_autonomy),
            ])

        screen.set_clip(None)

        # Scroll indicator & arrows
        total_action_h = ey + _diplo_scroll - action_top
        visible_h = clip.height
        if total_action_h > visible_h:
            si = fonts["sm"].render("v Cuon xuong (mouse wheel)", True, C_GREY)
            screen.blit(si, si.get_rect(centerx=px + PW // 2, y=py + PH - 20))

        return close_btn

    # ──────────────────────────────────────────────────────────────
    # LIST VIEW
    # ──────────────────────────────────────────────────────────────
    ts = fonts["title"].render("NGHI TRINH NGOAI GIAO", True, C_GOLD)
    screen.blit(ts, ts.get_rect(centerx=px + PW // 2, y=py + 10))
    sub = fonts["sm"].render("Chon quoc gia -> Chi tiet de thao tac", True, C_GREY)
    screen.blit(sub, sub.get_rect(centerx=px + PW // 2, y=py + 32))
    pygame.draw.line(screen, C_GOLD_DIM, (px + 8, py + 50), (px + PW - 8, py + 50))

    list_top = py + 56
    list_h = PH - 64
    list_clip = pygame.Rect(px + 4, list_top, PW - 8, list_h)
    screen.set_clip(list_clip)

    player_center = _country_centers.get(country.tag) if '_country_centers' in globals() else None
    
    def get_diplo_priority(item):
        target_tag = item[0]
        relation_val = item[1]
        target_center = _country_centers.get(target_tag) if '_country_centers' in globals() else None
        if player_center and target_center:
            dist2 = (player_center[0] - target_center[0])**2 + (player_center[1] - target_center[1])**2
        else:
            dist2 = 999999999
        return (dist2, -relation_val)
        
    relations_list = sorted(country.relations.items(), key=get_diplo_priority)
    row_h = 40
    max_scroll = max(0, len(relations_list) * row_h - list_h)
    _diplo_list_scroll = min(_diplo_list_scroll, max_scroll)

    y = list_top - _diplo_list_scroll
    for tag, relation in relations_list:
        if y + row_h < list_top:
            y += row_h
            continue
        if y > list_top + list_h:
            break
        if tag not in game_state.countries:
            continue
        rel_color = get_relations_color(relation)
        rel_name = get_country_display_name(tag, tag) or tag

        row_rect = pygame.Rect(px + 6, y - 3, PW - 12, row_h - 4)
        hov = row_rect.collidepoint(mouse_pos) and list_clip.collidepoint(mouse_pos)
        if hov:
            pygame.draw.rect(screen, (32, 48, 68), row_rect, border_radius=4)
            pygame.draw.rect(screen, C_GOLD_DIM, row_rect, 1, border_radius=4)

        # Country color dot
        tc2 = _rgb_color(game_state.countries_data.get(tag))
        pygame.draw.circle(screen, tc2, (px + 18, y + 14), 8)
        pygame.draw.circle(screen, C_GOLD_DIM, (px + 18, y + 14), 8, 1)

        ct_obj = game_state.countries.get(tag)
        status = ""
        if ct_obj:
            if tag in country.at_war_with: status = "[WAR]"
            elif tag in country.allies:    status = "[ALLY]"

        ns2 = fonts["sm"].render(f"{status} {rel_name[:22]}", True, C_WHITE)
        screen.blit(ns2, (px + 32, y + 9))

        # Relation bar
        bx4 = px + 268
        pygame.draw.rect(screen, (35, 35, 48), (bx4, y + 12, 90, 10), border_radius=4)
        fw2 = int(90 * (relation + 100) / 200)
        if fw2 > 0:
            pygame.draw.rect(screen, rel_color, (bx4, y + 12, fw2, 10), border_radius=4)
        pygame.draw.rect(screen, C_BORDER, (bx4, y + 12, 90, 10), 1, border_radius=4)
        rs2 = fonts["sm"].render(f"{relation:+d}", True, rel_color)
        screen.blit(rs2, (bx4 + 96, y + 9))

        # Detail button
        det_btn = pygame.Rect(px + PW - 88, y + 3, 80, 26)
        dh = det_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (45, 70, 100) if dh else (25, 45, 70), det_btn, border_radius=4)
        pygame.draw.rect(screen, C_GOLD_DIM, det_btn, 1, border_radius=4)
        ds3 = fonts["sm"].render("Chi tiet >>", True, C_WHITE)
        screen.blit(ds3, ds3.get_rect(center=det_btn.center))
        if dh and pygame.mouse.get_pressed()[0]:
            _diplo_detail_tag = tag
            _diplo_scroll = 0
            pygame.time.wait(200)

        y += row_h

    screen.set_clip(None)
    if max_scroll > 0:
        scroll_hint = fonts["sm"].render("Cuon chuot de xem them", True, C_GREY)
        screen.blit(scroll_hint, scroll_hint.get_rect(centerx=px + PW // 2, y=py + PH - 22))
    elif len(relations_list) == 0:
        empty = fonts["sm"].render("Chua co quan he — R-Click tren ban do", True, C_GREY)
        screen.blit(empty, empty.get_rect(centerx=px + PW // 2, y=list_top + 40))

    return close_btn




# ── LOBBY ────────────────────────────────────────────
def run_lobby(screen, fonts, original_map, pol_map, color_to_province, zoom_level):
    global game_state_ref
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()
    zoom = zoom_level
    cam_x = cam_y = 0.0
    is_pan = False
    last_pos = (0, 0)
    sel_tag = None
    sel_mode = "default"
    mode_idx = 0
    PANEL_H = 110
    panel_y = sh - PANEL_H
    btn_st = pygame.Rect(sw - 200, panel_y + 32, 180, 46)
    btn_exit = pygame.Rect(sw - 390, panel_y + 32, 180, 46)
    btn_prev = pygame.Rect(0, 0, 1, 1)
    btn_next = pygame.Rect(0, 0, 1, 1)
    
    diff_val = "normal"
    cheat_val = False
    
    diff_x = sw // 2 - 120
    diff_buttons = [
        ("De", "easy", pygame.Rect(diff_x + 80, panel_y + 10, 50, 26)),
        ("BT", "normal", pygame.Rect(diff_x + 135, panel_y + 10, 50, 26)),
        ("Kho", "hard", pygame.Rect(diff_x + 190, panel_y + 10, 50, 26))
    ]
    cheat_buttons = [
        ("Bat", True, pygame.Rect(diff_x + 80, panel_y + 50, 60, 26)),
        ("Tat", False, pygame.Rect(diff_x + 145, panel_y + 50, 60, 26))
    ]

    def clamp(cx, cy):
        sw2 = int(map_w * zoom)
        sh2 = int(map_h * zoom)
        return cx % sw2, max(panel_y - sh2, min(0.0, cy))

    sc = pygame.transform.scale(pol_map, (int(map_w * zoom), int(map_h * zoom)))
    clock = pygame.time.Clock()

    while True:
        _country_rank_cache.clear()
        _cached_overlord_map.clear()
        m_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEWHEEL:
                oz = zoom
                zoom = max(zoom_level, min(zoom * (1.15 if event.y > 0 else 1 / 1.15), 8.0))
                if oz != zoom:
                    ex, ey = pygame.mouse.get_pos()
                    cam_x = ex - (ex - cam_x) * (zoom / oz)
                    cam_y = ey - (ey - cam_y) * (zoom / oz)
                    cam_x, cam_y = clamp(cam_x, cam_y)
                    sc = pygame.transform.scale(pol_map, (int(map_w * zoom), int(map_h * zoom)))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                ex, ey = event.pos
                if event.button == 1:
                    m_clicked = True
                    # Check difficulty buttons
                    for label, val, rect in diff_buttons:
                        if rect.collidepoint(ex, ey):
                            diff_val = val
                            pygame.time.wait(100)
                    # Check cheat buttons
                    for label, val, rect in cheat_buttons:
                        if rect.collidepoint(ex, ey):
                            cheat_val = val
                            pygame.time.wait(100)
                            
                    if btn_exit.collidepoint(ex, ey):
                        pygame.time.wait(150)
                        return None, None, None, None
                    elif btn_st.collidepoint(ex, ey) and sel_tag:
                        pygame.time.wait(150)
                        return sel_tag, sel_mode, diff_val, cheat_val
                    elif btn_prev.collidepoint(ex, ey) and sel_tag:
                        av = avail_modes(sel_tag)
                        mode_idx = (mode_idx - 1) % len(av)
                        sel_mode = av[mode_idx]
                    elif btn_next.collidepoint(ex, ey) and sel_tag:
                        av = avail_modes(sel_tag)
                        mode_idx = (mode_idx + 1) % len(av)
                        sel_mode = av[mode_idx]
                    elif ey < panel_y:
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
                                        if get_overlord(owner) is not None:
                                            print(f"Cannot select subject country {owner}!")
                                            continue
                                        if sel_tag != owner:
                                            sel_tag = owner
                                            mode_idx = 0
                                            sel_mode = "default"
                                        print(f"✓ Chọn: {owner} tại ({rx},{ry}) RGB={rgb}")
                        is_pan = True
                        last_pos = event.pos
                elif event.button == 3:
                    is_pan = True
                    last_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    is_pan = False
            elif event.type == pygame.MOUSEMOTION and is_pan:
                ex, ey = event.pos
                cam_x += ex - last_pos[0]
                cam_y += ey - last_pos[1]
                last_pos = event.pos
                cam_x, cam_y = clamp(cam_x, cam_y)

        mx, my = pygame.mouse.get_pos()
        screen.fill(C_SEA)
        sw2 = int(map_w * zoom)
        for ox in (0, -sw2, sw2):
            screen.blit(sc, (int(cam_x) + ox, int(cam_y)))

        ov = pygame.Surface((sw, PANEL_H), pygame.SRCALPHA)
        ov.fill((*C_PANEL, 240))
        screen.blit(ov, (0, panel_y))

        if sel_tag:
            name = get_country_display_name(sel_tag, sel_tag)
            av = avail_modes(sel_tag)
            fl = get_flag(sel_tag, sel_mode, (90, 60))
            fr = pygame.Rect(30, panel_y + 10, 90, 60)
            if fl:
                screen.blit(fl, fr.topleft)
            else:
                raw = game_state_ref.countries_data.get(sel_tag, [80, 80, 80]) if game_state_ref else [80, 80, 80]
            screen.blit(fonts["title"].render(name, True, C_WHITE), (fr.right + 15, panel_y + 10))

            btn_prev = btn_next = pygame.Rect(0, 0, 1, 1)
        else:
            hs = fonts["hud"].render("Click vao mot quoc gia tren ban do...", True, C_GREY)
            screen.blit(hs, (30, panel_y + 40))
            btn_prev = btn_next = pygame.Rect(0, 0, 1, 1)

        # Draw Difficulty
        text(screen, fonts, "sm", "Do kho:", diff_x, panel_y + 15, C_GREY)
        for label, val, rect in diff_buttons:
            is_active = (diff_val == val)
            hov = rect.collidepoint(mx, my)
            if is_active:
                bg = (35, 65, 45)
                border = C_GOLD
                text_col = C_WHITE
            elif hov:
                bg = (30, 45, 60)
                border = C_GOLD
                text_col = C_WHITE
            else:
                bg = (20, 26, 35)
                border = C_BORDER
                text_col = C_GREY
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, border, rect, 1, border_radius=4)
            lbl_s = fonts["sm"].render(label, True, text_col)
            screen.blit(lbl_s, lbl_s.get_rect(center=rect.center))

        # Draw Cheat Mode
        text(screen, fonts, "sm", "Cheat mode:", diff_x, panel_y + 55, C_GREY)
        for label, val, rect in cheat_buttons:
            is_active = (cheat_val == val)
            hov = rect.collidepoint(mx, my)
            if is_active:
                bg = (35, 65, 45)
                border = C_GOLD
                text_col = C_WHITE
            elif hov:
                bg = (30, 45, 60)
                border = C_GOLD
                text_col = C_WHITE
            else:
                bg = (20, 26, 35)
                border = C_BORDER
                text_col = C_GREY
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, border, rect, 1, border_radius=4)
            lbl_s = fonts["sm"].render(label, True, text_col)
            screen.blit(lbl_s, lbl_s.get_rect(center=rect.center))

        # Draw Exit Button
        exit_hov = btn_exit.collidepoint(mx, my)
        exit_bg = (100, 40, 40) if exit_hov else (60, 25, 25)
        exit_border = C_GOLD if exit_hov else C_BORDER
        pygame.draw.rect(screen, exit_bg, btn_exit, border_radius=8)
        pygame.draw.rect(screen, exit_border, btn_exit, 1, border_radius=8)
        exit_lbl = fonts["hud"].render("THOAT", True, C_WHITE)
        screen.blit(exit_lbl, exit_lbl.get_rect(center=btn_exit.center))

        ac = bool(sel_tag)
        bc = (55, 150, 75) if btn_st.collidepoint(mx, my) and ac else ((40, 120, 60) if ac else (40, 48, 58))
        pygame.draw.rect(screen, bc, btn_st, border_radius=8)
        if ac:
            gold_border(screen, btn_st.x, btn_st.y, btn_st.w, btn_st.h, 8)
        else:
            pygame.draw.rect(screen, C_BORDER, btn_st, 1, border_radius=8)
        bs = fonts["hud"].render("VAO GAME  >", True, C_WHITE if ac else C_GREY)
        screen.blit(bs, bs.get_rect(center=btn_st.center))

        pygame.display.flip()
        clock.tick(60)

        pygame.display.flip(); clock.tick(60)


# ── GAME ─────────────────────────────────────────────
def run_game(screen, fonts, game_state, original_map, pol_map,
             color_to_province, init_zoom, combined_political, combined_province):
    global show_diplomacy, diplomacy_selected_tag, current_map_mode, _leaderboard_btn_held, _leaderboard_open, country_name_surface, _menu_btn_held_global
    
    sw, sh = screen.get_size()
    map_w, map_h = original_map.get_size()
    zoom = init_zoom
    cam_x = cam_y = 0.0
    is_pan = False
    last_pos = (0, 0)
    sel_tag = game_state.player_tag
    cur_map = combined_political  # Dùng bản đồ phím 1 cũ làm mặc định
    next_turn_cooldown = 0
    show_diplomacy = False
    diplomacy_selected_tag = None
    current_map_mode = MAP_MODE_POLITICAL
    show_build_panel = False
    global show_politics_panel, show_war_panel
    show_politics_panel = False
    show_war_panel = False
    selected_state = None
    selected_province = None

    def clamp(cx, cy):
        sw2 = int(map_w * zoom)
        sh2 = int(map_h * zoom)
        return cx % sw2, max(sh - sh2, min(float(HUD_H), cy))

    sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))
    clock = pygame.time.Clock()

    while True:
        _country_rank_cache.clear()
        _cached_overlord_map.clear()
        if getattr(game_state, 'force_exit_to_lobby', False):
            game_state.force_exit_to_lobby = False
            show_diplomacy = False
            return

        if next_turn_cooldown > 0:
            next_turn_cooldown -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Nếu menu đang mở, chỉ nhận phím ESC để tắt menu, bỏ qua tất cả các sự kiện khác
            import game_ui as _gui_m
            if _gui_m._menu_open:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    _gui_m._menu_open = False
                    pygame.time.wait(150)
                continue

            # Nếu có sự kiện đang kích hoạt, đóng băng tất cả thao tác chuột/phím khác
            if game_state.last_event is not None:
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    _gui_m._menu_open = not _gui_m._menu_open
                    _gui_m._menu_mode = "main"
                    show_diplomacy = False
                elif event.key == pygame.K_c:
                    if getattr(game_state, 'cheat_mode', False):
                        player_country = game_state.player_country
                        if player_country:
                            player_country.treasury += 1000
                            player_country.prestige += 100
                            game_state.last_event = {
                                "title": "CHEAT MODE KÍCH HOẠT",
                                "desc": "Bạn đã sử dụng cheat code để nhận thêm tài nguyên:\n\n+1,000 Ngân khố (L)\n+100 Uy tín (Prestige)",
                                "effect_text": "Xác nhận"
                            }
                elif event.key == pygame.K_SPACE and next_turn_cooldown == 0:
                    game_state.next_turn()
                    next_turn_cooldown = 10
                elif event.key == pygame.K_v:
                    show_diplomacy = not show_diplomacy
                    if show_diplomacy:
                        show_build_panel = False
                        show_politics_panel = False
                        show_war_panel = False
                elif event.key == pygame.K_1:
                    current_map_mode = MAP_MODE_POLITICAL
                    game_state.needs_map_update = True
                    print("Map mode: Political (Key 1)")
                elif event.key == pygame.K_2:
                    # Deactivated: Only keep original map
                    pass
                elif event.key == pygame.K_3:
                    current_map_mode = MAP_MODE_EPIDEMIC
                    game_state.needs_map_update = True
                    print("Map mode: Epidemic (Key 3)")
                elif event.key == pygame.K_b:
                    show_build_panel = not show_build_panel
                    if show_build_panel:
                        show_diplomacy = False
                        show_politics_panel = False
                        show_war_panel = False
                elif event.key == pygame.K_p:
                    show_politics_panel = not show_politics_panel
                    if show_politics_panel:
                        show_build_panel = False
                        show_diplomacy = False
                        show_war_panel = False
                elif event.key == pygame.K_w:
                    show_war_panel = not show_war_panel
                    if show_war_panel:
                        show_build_panel = False
                        show_politics_panel = False
                        show_diplomacy = False

            elif event.type == pygame.MOUSEWHEEL:
                # Scroll diplomacy panel if open, else zoom map
                if show_diplomacy and _diplo_detail_tag:
                    import game_ui as _gui_ref
                    _gui_ref._diplo_scroll = max(0, _gui_ref._diplo_scroll - event.y * 30)
                elif show_diplomacy:
                    import game_ui as _gui_ref
                    _gui_ref._diplo_list_scroll = max(0, _gui_ref._diplo_list_scroll - event.y * 40)
                elif _leaderboard_open:
                    import game_ui as _gui_ref
                    sorted_countries = sorted(game_state.countries.values(), key=lambda c: c.prestige, reverse=True)
                    total_h = len(sorted_countries) * 32
                    list_h = sh - (HUD_H + 12) - 58 - 32 - 44
                    max_scroll = max(0, total_h - list_h)
                    _gui_ref._leaderboard_scroll = max(0, min(max_scroll, _gui_ref._leaderboard_scroll - event.y * 30))
                else:
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
                is_panel_clicked = is_ui_blocking_click((ex, ey), game_state)
                    
                if event.button == 1:  # Left click - chọn quốc gia / bắt đầu pan
                    if not is_panel_clicked:
                        is_pan = True
                        last_pos = event.pos
                        _click_start = event.pos  # sẽ dùng ở MOUSEBUTTONUP
                elif event.button == 3:  # Right click - mở diplomacy
                    if not is_panel_clicked:
                        scaled_w = int(map_w * zoom)
                        map_x = ex - cam_x
                        while map_x < 0:
                            map_x += scaled_w
                        while map_x >= scaled_w:
                            map_x -= scaled_w
                        rx = int(map_x / zoom)
                        ry = int((ey - cam_y) / zoom)
                        if 0 <= rx < map_w and 0 <= ry < map_h:
                            rgb = original_map.get_at((rx, ry))[:3]
                            prov = color_to_province.get(rgb)
                            if not prov:
                                prov = find_closest_province(rgb, color_to_province, tolerance=5)
                            if prov and not getattr(prov, "is_sea", False) and not getattr(prov, "is_lake", False):
                                selected_province = prov
                                selected_state = _province_to_state_fast.get(prov.color)
                                owner = getattr(prov, "owner", None)
                                if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                    sel_tag = owner
                                    show_diplomacy = True
                                    if owner != game_state.player_tag:
                                        import game_ui as _gui
                                        _gui._diplo_detail_tag = owner
                                        _gui._diplo_scroll = 0
                                        player = game_state.player_country
                                        if player and owner not in player.relations:
                                            player.relations[owner] = 0
                                    print(f"Selected: {owner} (right click) - Diplomacy opened")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Nếu khoảng cách di chuyển nhỏ (<= 5px) → đây là click thật, chọn tỉnh/bang
                    ex, ey = event.pos
                    sx, sy = last_pos
                    if abs(ex - sx) <= 5 and abs(ey - sy) <= 5:
                        is_panel_clicked = is_ui_blocking_click((ex, ey), game_state)
                            
                        if not is_panel_clicked:
                            scaled_w = int(map_w * zoom)
                            map_x = ex - cam_x
                            while map_x < 0:
                                map_x += scaled_w
                            while map_x >= scaled_w:
                                map_x -= scaled_w
                            rx = int(map_x / zoom)
                            ry = int((ey - cam_y) / zoom)
                            if 0 <= rx < map_w and 0 <= ry < map_h:
                                rgb = original_map.get_at((rx, ry))[:3]
                                prov = color_to_province.get(rgb)
                                if not prov:
                                    prov = find_closest_province(rgb, color_to_province, tolerance=5)
                                if prov and not getattr(prov, "is_sea", False) and not getattr(prov, "is_lake", False):
                                    selected_province = prov
                                    selected_state = _province_to_state_fast.get(prov.color)
                                    owner = getattr(prov, "owner", None)
                                    if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                                        sel_tag = owner
                                    sname = selected_state.name if selected_state else "None"
                                    print(f"Selected Province: {prov.id}, State: {sname}, Owner: {owner}")
                    is_pan = False

            elif event.type == pygame.MOUSEMOTION and is_pan:
                ex, ey = event.pos
                cam_x += ex - last_pos[0]
                cam_y += ey - last_pos[1]
                last_pos = event.pos
                cam_x, cam_y = clamp(cam_x, cam_y)

        # Check if map needs update (e.g. from province colonization/purchase/conquest)
        if getattr(game_state, 'needs_map_update', False):
            game_state.needs_map_update = False
            print("Regenerating map surfaces dynamically...")
            is_political = (cur_map is combined_political)
            
            # Regenerate country names dynamically to erase dead country names (e.g. Lima)
            country_name_surface = generate_country_name_map(original_map, color_to_province,
                                                             game_state.countries_data, fonts)
            
            # Regenerate political base map
            pol_map_new = generate_political_map(original_map, color_to_province,
                                                 game_state.countries_data, countries_full, mode=current_map_mode)
            pol_map.blit(pol_map_new, (0, 0))
            
            # Update combined_political in-place
            combined_political.fill((0, 0, 0, 0))
            combined_political.blit(pol_map, (0, 0))
            if country_name_surface is not None:
                combined_political.blit(country_name_surface, (0, 0))
            
            # Regenerate state map (disabled)
            pass
            
            cur_map = combined_political if is_political else combined_province
            sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))

        # Render
        mx, my = pygame.mouse.get_pos()
        screen.fill(C_SEA)
        sw2 = int(map_w * zoom)
        for ox in (0, -sw2, sw2):
            screen.blit(sc, (int(cam_x) + ox, int(cam_y)))
        draw_map_vignette(screen)

        # draw_sidebar disabled to maximize map view space
        pass
        btn = draw_hud(screen, fonts, game_state, sw, sh)

        # BXH collapsible: draw + get toggle button rect
        ldb_btn = draw_leaderboard(screen, fonts, game_state,
                                   x=12, y=HUD_H + 12, width=290, max_rows=8,
                                   mouse_pos=(mx, my))
        # Handle toggle click (simple press check)
        if pygame.mouse.get_pressed()[0] and ldb_btn.collidepoint(mx, my):
            if not _leaderboard_btn_held:
                import game_ui as _gui_m
                _gui_m._leaderboard_open = not _gui_m._leaderboard_open
                _leaderboard_btn_held = True
        else:
            _leaderboard_btn_held = False

        # Draw country profile if a country tag is selected
        import game_ui as _gui
        if _gui._profile_tag:
            draw_country_profile(screen, fonts, game_state, _gui._profile_tag, (mx, my))

        if show_build_panel:
            should_close = draw_build_panel(screen, fonts, game_state, selected_state)
            if should_close:
                show_build_panel = False
            # Draw helper text at the bottom of build panel
            if selected_state is None:
                hint_s = fonts["sm"].render("Click tren ban do truoc de chon bang!", True, C_GOLD)
                screen.blit(hint_s, hint_s.get_rect(centerx=sw // 2, y=sh - 30))

        if show_politics_panel:
            should_close = draw_politics_panel(screen, fonts, game_state)
            if should_close:
                show_politics_panel = False

        if show_war_panel:
            draw_war_panel(screen, fonts, game_state)

        # Xử lý click nút Next Turn
        if pygame.mouse.get_pressed()[0] and next_turn_cooldown == 0:
            if btn.collidepoint(mx, my):
                game_state.next_turn()
                next_turn_cooldown = 10

        # Nút MENU
        menu_r = pygame.Rect(sw - 110, sh - 40, 100, 30)
        mh = draw_button(screen, fonts, menu_r, "< MENU", (45, 28, 12), C_GOLD, C_GOLD, (mx, my), "sm")
        if pygame.mouse.get_pressed()[0] and mh:
            if not _menu_btn_held_global:
                import game_ui as _gui_m
                _gui_m._menu_open = not _gui_m._menu_open
                _gui_m._menu_mode = "main"
                _menu_btn_held_global = True
                pygame.time.wait(150)
        else:
            _menu_btn_held_global = False

        help_text = fonts["sm"].render(
            "SPACE: Turn | V: Ngoai giao | B: Xay dung | P: Chinh tri | L/R-Click | Cuon: Zoom/Diplo",
            True, C_GOLD_DIM)
        map_area_w = sw
        if help_text.get_width() > map_area_w - 20:
            line1 = fonts["sm"].render(
                "SPACE: Turn | V: Ngoai giao | B: Xay dung | P: Chinh tri",
                True, C_GOLD_DIM)
            line2 = fonts["sm"].render(
                "L-Click: Chon quoc gia/bang | R-Click: Ngoai giao | Cuon chuot: Zoom hoac cuon panel",
                True, C_GOLD_DIM)
            screen.blit(line1, (10, sh - line1.get_height() * 2 - 10))
            screen.blit(line2, (10, sh - line2.get_height() - 5))
        else:
            screen.blit(help_text, (10, sh - help_text.get_height() - 5))

        # Diplomacy Panel
        if show_diplomacy:
            close_btn = draw_diplomacy_panel(screen, fonts, game_state, (mx, my))
            if close_btn.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                show_diplomacy = False
                pygame.time.wait(200)

        # Draw menu popup if open
        import game_ui as _gui_m
        if _gui_m._menu_open:
            menu_res = draw_in_game_menu(screen, fonts, game_state)
            if menu_res == "exit_lobby":
                show_diplomacy = False
                return
            elif menu_res == "loaded":
                sel_tag = game_state.player_tag
                selected_state = None
                selected_province = None
                show_diplomacy = False
                diplomacy_selected_tag = None
                _gui_m._profile_tag = None
                color_to_province.clear()
                for p in game_state.provinces.values():
                    color_to_province[p.color] = p
                
                # Force map regeneration immediately on load
                print("Force regenerating map on load...")
                country_name_surface = generate_country_name_map(original_map, color_to_province,
                                                                 game_state.countries_data, fonts)
                pol_map_new = generate_political_map(original_map, color_to_province,
                                                     game_state.countries_data, countries_full, mode=current_map_mode)
                pol_map.blit(pol_map_new, (0, 0))
                combined_political.fill((0, 0, 0, 0))
                combined_political.blit(pol_map, (0, 0))
                if country_name_surface is not None:
                    combined_political.blit(country_name_surface, (0, 0))
                
                is_political = (cur_map is combined_political or cur_map is combined_province)
                cur_map = combined_political if is_political else combined_province
                sc = pygame.transform.scale(cur_map, (int(map_w * zoom), int(map_h * zoom)))
                game_state.needs_map_update = False

        # Event Popup (Vẽ đè lên trên cùng)
        if game_state.last_event:
            draw_event_popup(screen, fonts, game_state)
        elif getattr(game_state, 'event_queue', None):
            game_state.last_event = game_state.event_queue.pop(0)

        pygame.display.flip()
        clock.tick(FPS)

def run_main_menu(screen, fonts, game_state):
    global _menu_btn_held_global
    import os
    import pickle
    
    sw, sh = screen.get_size()
    
    # Load menu background image
    base_dir = os.path.dirname(os.path.abspath(__file__))
    menu_bg_path = os.path.join(base_dir, "data", "menu", "images.png")
    try:
        menu_bg = pygame.image.load(menu_bg_path).convert()
    except Exception as e:
        print(f"Failed to load menu background: {e}")
        menu_bg = pygame.Surface((sw, sh))
        menu_bg.fill((10, 15, 22))
    
    menu_bg = pygame.transform.scale(menu_bg, (sw, sh))
    
    clock = pygame.time.Clock()
    
    # Check if a save exists for "Continue" button
    saves_dir = os.path.join(base_dir, "data", "saves")
    has_saves = False
    newest_slot = None
    newest_time = 0
    if os.path.exists(saves_dir):
        for i in range(1, 6):
            filepath = os.path.join(saves_dir, f"slot_{i}.sav")
            if os.path.exists(filepath):
                has_saves = True
                mtime = os.path.getmtime(filepath)
                if mtime > newest_time:
                    newest_time = mtime
                    newest_slot = filepath
                    
    # Sub-menu state
    menu_view = "main"  # main, load, new_game_popup
    selected_diff = "normal"  # easy, normal, hard
    selected_cheat = False
    
    # Pre-render logo & subtitle to optimize
    logo_s = fonts["title"].render("VICTORIA 3", True, C_GOLD)
    sub_s = fonts["sm"].render("SIMPLE ENGINE", True, C_GOLD_DIM)
    sp_s = fonts["sm"].render("CHƠI ĐƠN (Single Player)", True, C_GREY)
    
    while True:
        mx, my = pygame.mouse.get_pos()
        m_clicked = pygame.mouse.get_pressed()[0]
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if menu_view != "main":
                        menu_view = "main"
                        pygame.time.wait(200)
                        
        screen.blit(menu_bg, (0, 0))
        
        # 1. Main Menu panel on the left (matching the screenshot style)
        px, py = 80, 80
        pw, ph = 360, 560
        
        panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*C_PANEL, 230), (0, 0, pw, ph), border_radius=8)
        screen.blit(panel_surf, (px, py))
        
        screen.blit(logo_s, logo_s.get_rect(centerx=px + pw // 2, y=py + 30))
        screen.blit(sub_s, sub_s.get_rect(centerx=px + pw // 2, y=py + 75))
        pygame.draw.line(screen, C_GOLD, (px + 20, py + 95), (px + pw - 20, py + 95), 2)
        screen.blit(sp_s, (px + 30, py + 115))
        
        btn_w, btn_h = 300, 42
        bx = px + 30
        
        # Check hover and click helper
        def draw_menu_btn(rect, label, enabled=True, active=False):
            hov = rect.collidepoint(mx, my) and enabled
            if active:
                bg = (35, 65, 45)
                border = C_GOLD
                text_col = C_WHITE
            elif hov:
                bg = (30, 45, 60)
                border = C_GOLD
                text_col = C_WHITE
            else:
                bg = (20, 26, 35) if enabled else (15, 17, 20)
                border = C_GOLD_DIM if enabled else (60, 60, 60)
                text_col = C_WHITE if enabled else C_GREY
            
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, border, rect, 1, border_radius=6)
            lbl = fonts["med"].render(label, True, text_col)
            screen.blit(lbl, lbl.get_rect(center=rect.center))
            return hov
            
        if menu_view == "main":
            # Continue Button
            by = py + 140
            continue_rect = pygame.Rect(bx, by, btn_w, btn_h)
            continue_hov = draw_menu_btn(continue_rect, "TIẾP TỤC", enabled=has_saves)
            if continue_hov and m_clicked:
                pygame.time.wait(200)
                return "continue"
                
            # New Game Button
            by += 55
            new_game_rect = pygame.Rect(bx, by, btn_w, btn_h)
            new_game_hov = draw_menu_btn(new_game_rect, "TRÒ CHƠI MỚI")
            if new_game_hov and m_clicked:
                pygame.time.wait(200)
                return "new_game"
                
            # Load Game Button
            by += 55
            load_rect = pygame.Rect(bx, by, btn_w, btn_h)
            load_hov = draw_menu_btn(load_rect, "TẢI TIẾN TRÌNH")
            if load_hov and m_clicked:
                menu_view = "load"
                pygame.time.wait(200)
                
            # Exit Button
            by += 110
            exit_rect = pygame.Rect(bx, by, btn_w, btn_h)
            exit_hov = draw_menu_btn(exit_rect, "THOÁT RA DESKTOP")
            if exit_hov and m_clicked:
                pygame.time.wait(200)
                return "exit"
                
        elif menu_view == "load":
            by = py + 140
            for i in range(1, 6):
                slot_rect = pygame.Rect(bx, by + (i - 1) * 55, btn_w, btn_h)
                filepath = os.path.join(saves_dir, f"slot_{i}.sav")
                exists = os.path.exists(filepath)
                
                slot_label = f"Slot {i}: Trống"
                if exists:
                    try:
                        with open(filepath, 'rb') as f:
                            gs = pickle.load(f)
                        c_name = get_country_display_name(gs.player_tag)
                        date_str = gs.current_date.short
                        slot_label = f"Slot {i}: {c_name} ({date_str})"
                    except Exception as ex_err:
                        print(f"Error reading slot {i}: {ex_err}")
                        slot_label = f"Slot {i}: File lỗi"
                
                slot_hov = draw_menu_btn(slot_rect, slot_label, enabled=exists)
                if slot_hov and m_clicked and exists:
                    try:
                        with open(filepath, 'rb') as f:
                            loaded_state = pickle.load(f)
                        game_state.__dict__.update(loaded_state.__dict__)
                        print(f"Loaded game from slot {i}")
                        pygame.time.wait(200)
                        return "load"
                    except Exception as err:
                        print(f"Failed to load: {err}")
            
            # Back Button
            back_rect = pygame.Rect(bx, py + ph - 60, btn_w, btn_h)
            back_hov = draw_menu_btn(back_rect, "QUAY LẠI")
            if back_hov and m_clicked:
                menu_view = "main"
                pygame.time.wait(200)
                

                
        pygame.display.flip()
        clock.tick(FPS)

def reset_to_pristine_state(game_state, original_map, pol_map, color_to_province, combined_political):
    global country_name_surface, pristine_pol_map, pristine_country_name_surface, pristine_combined_political, initial_game_state_backup_bytes
    print("Resetting game state and maps to pristine 1836 layout...")
    
    # 1. Restore game_state dict from pristine backup
    if 'initial_game_state_backup_bytes' in globals() and initial_game_state_backup_bytes is not None:
        import pickle
        game_state.__dict__.update(pickle.loads(initial_game_state_backup_bytes).__dict__)
    
    # 2. Rebuild indices
    build_province_state_lookup(game_state)
    color_to_province.clear()
    for p in game_state.provinces.values():
        color_to_province[p.color] = p
        
    # 3. Restore maps by copying/blitting from pristine surfaces
    if pristine_pol_map is not None:
        pol_map.blit(pristine_pol_map, (0, 0))
    if pristine_country_name_surface is not None:
        if country_name_surface is None:
            country_name_surface = pristine_country_name_surface.copy()
        else:
            country_name_surface.blit(pristine_country_name_surface, (0, 0))
    if pristine_combined_political is not None:
        combined_political.blit(pristine_combined_political, (0, 0))
    
    game_state.needs_map_update = False

# ── ENTRY ────────────────────────────────────────────
def start_engine(game_state):
    global game_state_ref, country_name_surface, province_name_surface, current_map_mode, countries_full
    game_state_ref = game_state

    from engine.country_names import init_country_names
    init_country_names()

    print("Initializing Pygame...")
    pygame.init()
    pygame.font.init()

    from engine.fonts import load_vic3_fonts
    vic3_fonts = load_vic3_fonts()

    from engine.state_resource_loader import load_state_resources, build_color_cache
    global _state_resources
    _state_resources = load_state_resources()
    build_color_cache(_state_resources)
    
    print(f"Creating screen {SCREEN_W}x{SCREEN_H}...")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    
    print("Loading fonts...")
    fonts = load_fonts()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Loading flags and ranks from {base_dir}...")
    load_flags(base_dir)
    load_ranks(base_dir)

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

    print("Generating maps... (may take ~30s first time)")

    # 1. Generate base pixel array once (shared across all generation calls)
    import time
    t0 = time.time()

    # 2. Political map (for lobby)
    print("  [1/5] Political map...")
    pol_map = generate_political_map(original_map, color_to_province,
                                     game_state.countries_data, countries_full)
    print(f"        done in {time.time()-t0:.1f}s")

    # 3. Country name overlay (generated ONCE, reused everywhere)
    t1 = time.time()
    print("  [2/5] Country name overlay...")
    country_name_surface = generate_country_name_map(original_map, color_to_province,
                                                      game_state.countries_data, fonts)
    print(f"        done in {time.time()-t1:.1f}s")

    # 4. Combined political map = pol_map + name overlay
    combined_political = pol_map.copy()
    combined_political.blit(country_name_surface, (0, 0))

    # Backup the original pristine maps for resetting
    global pristine_pol_map, pristine_country_name_surface, pristine_combined_political
    pristine_pol_map = pol_map.copy()
    pristine_country_name_surface = country_name_surface.copy() if country_name_surface is not None else None
    pristine_combined_political = combined_political.copy()

    # 5. Province name map (generated ONCE)
    t2 = time.time()
    print("  [3/5] Province name map...")
    province_name_surface = generate_province_name_map(original_map, color_to_province, fonts)
    print(f"        done in {time.time()-t2:.1f}s")

    # 6. State-level map (Victoria 3 style) - deactivated to save loading time
    state_level_map = combined_political

    # 7. Build province-state fast lookup index
    t4 = time.time()
    print("  [5/5] Province-State index...")
    build_province_state_lookup(game_state)
    print(f"        done in {time.time()-t4:.1f}s")

    print(f"  Total map generation: {time.time()-t0:.1f}s")

    map_w, map_h = original_map.get_size()
    init_zoom = max(SCREEN_W / map_w, SCREEN_H / map_h)
    print(f"Map size: {map_w}x{map_h}, initial zoom: {init_zoom:.2f}")

    # Back up the initial pristine game state for "New Game" resets
    import pickle
    global initial_game_state_backup_bytes
    initial_game_state_backup_bytes = pickle.dumps(game_state)

    print("Entering main menu loop...")
    while True:
        action = run_main_menu(screen, fonts, game_state)
        if action == "exit":
            pygame.quit()
            sys.exit()
        elif action == "continue":
            # Load the most recent save slot
            saves_dir = os.path.join(base_dir, "data", "saves")
            newest_slot = None
            newest_time = 0
            for i in range(1, 6):
                filepath = os.path.join(saves_dir, f"slot_{i}.sav")
                if os.path.exists(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime > newest_time:
                        newest_time = mtime
                        newest_slot = filepath
            if newest_slot:
                try:
                    with open(newest_slot, 'rb') as f:
                        loaded_state = pickle.load(f)
                    game_state.__dict__.update(loaded_state.__dict__)
                    game_state.needs_map_update = True
                    build_province_state_lookup(game_state)
                    
                    # Sync color_to_province
                    color_to_province.clear()
                    for p in game_state.provinces.values():
                        color_to_province[p.color] = p
                    
                    # Set up relations if missing
                    tag = game_state.player_tag
                    for t in game_state.countries:
                        if t != tag and t not in game_state.countries[tag].relations:
                            game_state.countries[tag].relations[t] = 0
                            
                    run_game(screen, fonts, game_state, original_map, pol_map,
                             color_to_province, init_zoom, combined_political, state_level_map)
                except Exception as ex_err:
                    print(f"Failed to continue game: {ex_err}")
                finally:
                    reset_to_pristine_state(game_state, original_map, pol_map, color_to_province, combined_political)
            continue
        elif action == "load":
            build_province_state_lookup(game_state)
            color_to_province.clear()
            for p in game_state.provinces.values():
                color_to_province[p.color] = p
            tag = game_state.player_tag
            for t in game_state.countries:
                if t != tag and t not in game_state.countries[tag].relations:
                    game_state.countries[tag].relations[t] = 0
            game_state.needs_map_update = True
            try:
                run_game(screen, fonts, game_state, original_map, pol_map,
                         color_to_province, init_zoom, combined_political, state_level_map)
            finally:
                reset_to_pristine_state(game_state, original_map, pol_map, color_to_province, combined_political)
            continue
        elif action == "new_game":
            lobby_res = run_lobby(screen, fonts, original_map, pol_map,
                                  color_to_province, init_zoom)
            if lobby_res[0] is None:
                continue
            tag, mode, difficulty, cheat_mode = lobby_res
            print(f"Selected: {tag} / {mode} (Diff: {difficulty}, Cheat: {cheat_mode})")
            
            import pickle
            game_state.__dict__.update(pickle.loads(initial_game_state_backup_bytes).__dict__)
            build_province_state_lookup(game_state)
            game_state.player_tag = tag
            game_state.player_mode = mode
            game_state.difficulty = difficulty
            game_state.cheat_mode = cheat_mode

            # Sync color_to_province
            color_to_province.clear()
            for p in game_state.provinces.values():
                color_to_province[p.color] = p
            
            # Grant starting funds
            player_country = game_state.countries.get(tag)
            if player_country:
                player_country.treasury += 1000
                print(f"Granted +1000 starting gold to player country {tag}")
            
            for t in game_state.countries:
                if t != tag and t not in game_state.countries[tag].relations:
                    game_state.countries[tag].relations[t] = 0
            
            game_state.needs_map_update = True
            try:
                run_game(screen, fonts, game_state, original_map, pol_map,
                         color_to_province, init_zoom, combined_political, state_level_map)
            finally:
                reset_to_pristine_state(game_state, original_map, pol_map, color_to_province, combined_political)