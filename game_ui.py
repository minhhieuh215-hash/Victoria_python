import pygame
import sys
import os

def run_game(color_to_province):
    pygame.init()
    
    screen_width, screen_height = 1280, 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Victoria 3 Python Engine - Map Viewer V2")

    print("Đang nạp ảnh bản đồ lên giao diện...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        base_dir = current_dir
    else:
        base_dir = os.path.dirname(current_dir)
        
    map_path = os.path.join(base_dir, "data", "map_data", "provinces.png")
    
    # 1. Load ảnh gốc giữ nguyên tỷ lệ
    original_map = pygame.image.load(map_path).convert()
    map_w, map_h = original_map.get_size()
    
    # 2. Thiết lập Camera và Zoom ban đầu
    camera_x, camera_y = 0, 0
    # Tính toán để vừa mở lên là bản đồ vừa khít chiều cao màn hình
    zoom_level = screen_height / map_h 
    
    # Ảnh hiển thị thực tế (đã được thu phóng)
    scaled_map = pygame.transform.scale(original_map, (int(map_w * zoom_level), int(map_h * zoom_level)))
    
    # Các biến dùng để kéo thả bản đồ
    is_panning = False
    last_mouse_pos = (0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # --- TÍNH NĂNG ZOOM (LĂN CHUỘT) ---
            elif event.type == pygame.MOUSEWHEEL:
                old_zoom = zoom_level
                if event.y > 0: # Lăn lên -> Phóng to
                    zoom_level *= 1.2
                elif event.y < 0: # Lăn xuống -> Thu nhỏ
                    zoom_level /= 1.2
                
                # Giới hạn mức độ zoom (đừng để nhỏ quá hoặc to quá gây lag máy)
                zoom_level = max(0.05, min(zoom_level, 5.0))
                
                if old_zoom != zoom_level:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    # Thuật toán tính toán lại camera để zoom tập trung vào ngay con trỏ chuột
                    camera_x = mouse_x - (mouse_x - camera_x) * (zoom_level / old_zoom)
                    camera_y = mouse_y - (mouse_y - camera_y) * (zoom_level / old_zoom)
                    
                    # Tạo lại ảnh với kích thước mới
                    scaled_map = pygame.transform.scale(original_map, (int(map_w * zoom_level), int(map_h * zoom_level)))

            # --- TÍNH NĂNG KÉO & CLICK (BẤM CHUỘT) ---
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # CHUỘT TRÁI: Click xem thông tin Tỉnh
                    mouse_x, mouse_y = event.pos
                    
                    # Thuật toán dịch ngược: Từ tọa độ màn hình -> tọa độ ảnh gốc ban đầu
                    real_x = int((mouse_x - camera_x) / zoom_level)
                    real_y = int((mouse_y - camera_y) / zoom_level)
                    
                    if 0 <= real_x < map_w and 0 <= real_y < map_h:
                        clicked_color = original_map.get_at((real_x, real_y))
                        rgb_tuple = (clicked_color.r, clicked_color.g, clicked_color.b)
                        
                        if rgb_tuple in color_to_province:
                            prov = color_to_province[rgb_tuple]
                            print(f"\n--- THÔNG TIN VÙNG ĐẤT ---")
                            print(f"Mã màu RGB: {rgb_tuple}")
                            print(f"Thuộc về Quốc gia (TAG): {getattr(prov, 'owner', 'Đất tự do / Chưa ai chiếm')}")
                        else:
                            print("Click vào viền đen hoặc viền nước!")
                            
                elif event.button == 3: # CHUỘT PHẢI: Bắt đầu cầm bản đồ kéo đi
                    is_panning = True
                    last_mouse_pos = event.pos

            # --- DỪNG KÉO BẢN ĐỒ ---
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3: 
                    is_panning = False

            # --- TÍNH TOÁN KHI ĐANG KÉO BẢN ĐỒ ---
            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - last_mouse_pos[0]
                    dy = mouse_y - last_mouse_pos[1]
                    
                    camera_x += dx
                    camera_y += dy
                    last_mouse_pos = event.pos

        # Vẽ mọi thứ ra màn hình
        screen.fill((30, 30, 30))
        screen.blit(scaled_map, (camera_x, camera_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()