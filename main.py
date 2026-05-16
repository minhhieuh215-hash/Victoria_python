import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.map_loader import load_provinces, load_states
from engine.country_loader import load_countries
from engine.history_loader import load_state_history
from game_ui import run_game

def main():
    print("="*40)
    print("🚀 ĐANG KHỞI ĐỘNG VICTORIA PYTHON ENGINE")
    print("="*40)
    
    print("[1/5] Đang nạp dữ liệu Tỉnh (Provinces)...")
    provinces = load_provinces()
    
    print("[2/5] Đang nạp dữ liệu Bang (States)...")
    states = load_states(provinces)
    
    print("[3/5] Đang lập chỉ mục bản đồ (Color Mapping)...")
    color_to_province = {prov.color: prov for prov in provinces.values()}
    
    print("[4/5] Đang nạp dữ liệu Quốc gia (Countries)...")
    countries_data = load_countries()
    
    print("[5/5] Đang phân chia lãnh thổ (History 1836)...")
    load_state_history(color_to_province)
    
    print("="*40)
    print("✅ NẠP DỮ LIỆU THÀNH CÔNG! ĐANG MỞ GIAO DIỆN...")
    print("="*40)
    
    # Khởi chạy màn hình UI và truyền dữ liệu map vào
    run_game(color_to_province)

if __name__ == "__main__":
    main()