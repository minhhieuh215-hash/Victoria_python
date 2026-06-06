# engine/fonts.py
import pygame
import os
from typing import Optional

FONT_SIZES = {
    "big"  : 26,
    "title": 20,
    "med"  : 16,
    "sm"   : 13,
    "hud"  : 17,
    "date" : 20,
}

FONT_BOLD_KEYS = {"big", "title", "med", "hud", "date"}


def load_vic3_fonts(base_dir: Optional[str] = None) -> dict:
    """Load font EBGaramond từ data/fonts/."""
    if base_dir is None:
        # Lấy thư mục gốc (Victoria-code)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ĐƯỜNG DẪN ĐÚNG: Victoria-code/data/fonts/
    font_dir = os.path.join(base_dir, "data", "fonts")
    bold_path = os.path.join(font_dir, "EBGaramond-SemiBold.ttf")
    reg_path = os.path.join(font_dir, "EBGaramond-Regular.ttf")

    print(f"Looking for fonts in: {font_dir}")
    print(f"  Bold exists: {os.path.exists(bold_path)}")
    print(f"  Regular exists: {os.path.exists(reg_path)}")

    has_bold = os.path.exists(bold_path)
    has_reg = os.path.exists(reg_path)

    fonts = {}
    for key, size in FONT_SIZES.items():
        is_bold = key in FONT_BOLD_KEYS
        try:
            if has_bold and is_bold:
                fonts[key] = pygame.font.Font(bold_path, size)
                print(f"  Loaded {key} from EBGaramond-Bold.ttf")
            elif has_reg:
                fonts[key] = pygame.font.Font(reg_path, size)
                print(f"  Loaded {key} from EBGaramond-Regular.ttf")
            else:
                raise FileNotFoundError
        except Exception:
            # Fallback system font
            for sysname in ["segoeui", "tahoma", "arial"]:
                try:
                    fonts[key] = pygame.font.SysFont(sysname, size, bold=is_bold)
                    print(f"  Loaded {key} from system font: {sysname}")
                    break
                except:
                    pass
            else:
                fonts[key] = pygame.font.SysFont("arial", size)

    return fonts