import pygame
import sys
import os

def generate_political_map(original_image, color_to_province, countries_data):
    """
    Tạo ra một bản đồ mới được tô màu theo cục diện chính trị các quốc gia năm 1836.
    """
    print("Đang tiến hành tô màu bản đồ chính trị thế giới...")
    # Tạo một bản sao trống có cùng kích thước với ảnh gốc
    pol_map = original_image.copy()
    
    width, height = original_image.get_size()
    for y in range(height):
        for x in range(width):
            raw_color = original_image.get_at((x, y))
            rgb_tuple = (raw_color.r, raw_color.g, raw_color.b)
            
            # Giữ nguyên viền đen ngăn cách giữa các tỉnh
            if rgb_tuple == (0, 0, 0):
                continue
                
            if rgb_tuple in color_to_province:
                prov = color_to_province[rgb_tuple]
                
                # Nếu được xác định là biển từ default.map -> Tô màu xanh đại dương
                if getattr(prov, 'is_sea', False):
                    pol_map.set_at((x, y), (25, 45, 80))
                else:
                    owner_tag = getattr(prov, 'owner', None)
                    # Nếu vùng đất có quốc gia sở hữu -> Tô màu quốc gia đó
                    if owner_tag and owner_tag in countries_data:
                        pol_map.set_at((x, y), countries_data[owner_tag])
                    else:
                        # Đất hoang/Vô chủ thì tô màu xám đất mặc định
                        pol_map.set_at((x, y), (140, 130, 120))
                        
    print("-> Tô màu bản đồ chính trị hoàn tất!")
    return pol_map

def run_game(color_to_province, countries_data):
    pygame.init()
    
    screen_width, screen_height = 1280, 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Victoria 3 Python Engine - Map Viewer")

    # Xác định đường dẫn tuyệt đối đến file ảnh bản đồ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        base_dir = current_dir
    else:
        base_dir = os.path.dirname(current_dir)
    map_path = os.path.join(base_dir, "data", "map_data", "provinces.png")
    
    original_map = pygame.image.load(map_path).convert()
    # Tạo bản đồ chính trị từ dữ liệu đã nạp
    political_map = generate_political_map(original_map, color_to_province, countries_data)
    
    map_w, map_h = original_map.get_size()
    camera_x, camera_y = 0, 0
    zoom_level = screen_height / map_h 
    
    # Biến quản lý chế độ hiển thị (True: Bản đồ chính trị, False: Bản đồ tỉnh gốc)
    show_political = True
    
    current_active_map = political_map if show_political else original_map
    scaled_map = pygame.transform.scale(current_active_map, (int(map_w * zoom_level), int(map_h * zoom_level)))
    
    is_panning = False
    last_mouse_pos = (0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # ẤN PHÍM SPACE ĐỂ CHUYỂN ĐỔI CHẾ ĐỘ MAP
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_political = not show_political
                    current_active_map = political_map if show_political else original_map
                    scaled_map = pygame.transform.scale(current_active_map, (int(map_w * zoom_level), int(map_h * zoom_level)))
                    print(f"Chuyển sang chế độ: {'Bản đồ chính trị' if show_political else 'Bản đồ tỉnh gốc'}")

            # Thu phóng bằng con lăn chuột (Zoom tập trung vào vị trí con trỏ)
            elif event.type == pygame.MOUSEWHEEL:
                old_zoom = zoom_level
                if event.y > 0: zoom_level *= 1.2
                elif event.y < 0: zoom_level /= 1.2
                zoom_level = max(0.05, min(zoom_level, 5.0))
                
                if old_zoom != zoom_level:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    camera_x = mouse_x - (mouse_x - camera_x) * (zoom_level / old_zoom)
                    camera_y = mouse_y - (mouse_y - camera_y) * (zoom_level / old_zoom)
                    scaled_map = pygame.transform.scale(current_active_map, (int(map_w * zoom_level), int(map_h * zoom_level)))

            # Click chuột trái xem thông tin chi tiết / Giữ chuột phải kéo bản đồ
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Chuột trái
                    mouse_x, mouse_y = event.pos
                    real_x = int((mouse_x - camera_x) / zoom_level)
                    real_y = int((mouse_y - camera_y) / zoom_level)
                    
                    if 0 <= real_x < map_w and 0 <= real_y < map_h:
                        clicked_color = original_map.get_at((real_x, real_y))
                        rgb_tuple = (clicked_color.r, clicked_color.g, clicked_color.b)
                        
                        if rgb_tuple in color_to_province:
                            prov = color_to_province[rgb_tuple]
                            print(f"\n--- THÔNG TIN VÙNG ĐẤT ---")
                            print(f"Mã màu tỉnh: {rgb_tuple}")
                            print(f"Loại địa hình: {'Biển 🌊' if getattr(prov, 'is_sea', False) else 'Đất liền ⛰️'}")
                            print(f"Quốc gia sở hữu (TAG): {getattr(prov, 'owner', 'Vô chủ')}")
                        else:
                            print("Click vào đường biên giới đen!")
                            
                elif event.button == 3: # Chuột phải
                    is_panning = True
                    last_mouse_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3: is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    mouse_x, mouse_y = event.pos
                    camera_x += mouse_x - last_mouse_pos[0]
                    camera_y += mouse_y - last_mouse_pos[1]
                    last_mouse_pos = event.pos

        screen.fill((20, 20, 20))
        screen.blit(scaled_map, (camera_x, camera_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()