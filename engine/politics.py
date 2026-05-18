"""
Hệ thống chính trị đơn giản hóa.
"""
import random

from config import COLONIZABLE_TYPES

GOVERNMENT_TYPES = {
    "default":            {"tax_bonus": 0.00, "pop_happiness": 0.0,  "prestige_gain": 0.1},
    "absolute_monarchy":  {"tax_bonus": 0.05, "pop_happiness":-0.1,  "prestige_gain": 0.2},
    "republic":           {"tax_bonus":-0.02, "pop_happiness": 0.2,  "prestige_gain": 0.1},
    "dictatorship":       {"tax_bonus": 0.08, "pop_happiness":-0.2,  "prestige_gain": 0.0},
    "theocracy":          {"tax_bonus": 0.03, "pop_happiness": 0.1,  "prestige_gain": 0.3},
    "communist":          {"tax_bonus": 0.10, "pop_happiness":-0.3,  "prestige_gain":-0.1},
}


def apply_government_bonus(country):
    """Áp dụng bonus chính phủ vào tax_rate và prestige."""
    gov = GOVERNMENT_TYPES.get(country.government, GOVERNMENT_TYPES["default"])
    country.tax_rate = max(0.05, min(0.40,
        0.15 + gov["tax_bonus"]))
    country.prestige += gov["prestige_gain"]


def monthly_politics_tick(countries: dict, player_tag: str):
    """
    Xử lý chính trị mỗi tháng:
    - Áp dụng bonus chính phủ
    - AI quốc gia lớn có thể tăng quân
    """
    for tag, country in countries.items():
        if country.is_colonizable:
            continue
        apply_government_bonus(country)

        # AI: quốc gia giàu tự động tăng quân
        if tag != player_tag and country.treasury > 200 and random.random() < 0.05:
            country.army_size += 5
            country.treasury  -= 50

# Trong politics.py, thêm:
def get_relations_color(value: int) -> tuple:
    """Trả về màu cho quan hệ ngoại giao"""
    if value >= 75:
        return (80, 220, 100)   # Xanh đậm - Đồng minh
    if value >= 50:
        return (80, 200, 120)   # Xanh - Thân thiện
    if value >= 25:
        return (120, 200, 120)  # Xanh nhạt
    if value >= 0:
        return (180, 180, 100)  # Vàng - Trung lập
    if value >= -25:
        return (200, 150, 80)   # Cam nhạt
    if value >= -50:
        return (200, 120, 60)   # Cam - Căng thẳng
    if value >= -75:
        return (210, 80, 80)    # Đỏ nhạt
    return (220, 50, 50)        # Đỏ đậm - Thù địch