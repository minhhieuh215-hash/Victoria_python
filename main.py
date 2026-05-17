import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.map_loader import load_provinces, load_states
from engine.country_loader import load_countries
from engine.history_loader import load_state_history
from game_ui import start_engine
from engine.game_state import GameState

def main():
    print("="*40)
    print("🚀 ĐANG KHỞI ĐỘNG VICTORIA PYTHON ENGINE")
    print("="*40)
    
    print("[1/5] Đang nạp dữ liệu Tỉnh (Provinces)...")
    provinces = load_provinces()  # Trả về dict: { id: Province_Object }
    
    print("[2/5] Đang nạp dữ liệu Bang (States)...")
    states = load_states(provinces)  # Trả về list các State_Object
    
    print("[3/5] Đang lập chỉ mục bản đồ (Color Mapping)...")
    color_to_province = {prov.color: prov for prov in provinces.values()}
    
    print("[4/5] Đang nạp dữ liệu Quốc gia (Countries)...")
    countries_data = load_countries()  # Trả về dict: { TAG: RGB_Color }
    
    print("[5/5] Đang phân chia lãnh thổ (History 1836)...")
    load_state_history(color_to_province)

    print("[*] Đang nạp dữ liệu vào Trạng thái trò chơi (GameState)...")
    
    # Chuyển list states thành dict { tên_bang: State_Object } để dễ tra cứu sau này
    states_dict = {s.name: s for s in states}
    
    # Khởi tạo Bộ não trung tâm
    game_state = GameState(provinces, states_dict, countries_data)
    
    print("="*40)
    print(f"✅ NẠP DỮ LIỆU THÀNH CÔNG! BẠN ĐANG CHƠI QUỐC GIA: {game_state.player_tag}")
    print("="*40)
    
    # Truyền DUY NHẤT đối tượng game_state chứa toàn bộ dữ liệu vào UI
    start_engine(game_state)

if __name__ == "__main__":
    main()