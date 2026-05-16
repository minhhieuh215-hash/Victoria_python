import pygame
import sys
import os

def run_game(color_to_province):

    pygame.init()
    screen_width, screen_height = 1280, 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Victoria 3 Python Engine - Map Viewer")

    # Load ảnh map gốc lên
    print("Đang nạp ảnh bản đồ lên giao diện...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    map_path = os.path.join(base_dir, "data", "map_data", "provinces.png")

    print(f"Đường dẫn tuyệt đối: {map_path}")
    map_image = pygame.image.load(map_path).convert()
    
    # Biến để điều khiển camera (di chuyển bản đồ)
    camera_x, camera_y = 0, 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Xử lý sự kiện CLICK CHUỘT
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Chuột trái
                    mouse_x, mouse_y = event.pos
                    
                    # Tính toán tọa độ thực tế trên ảnh (cộng thêm tọa độ camera)
                    real_x = mouse_x - camera_x
                    real_y = mouse_y - camera_y
                    
                    # Bắt lỗi nếu click ra ngoài rìa bức ảnh
                    if 0 <= real_x < map_image.get_width() and 0 <= real_y < map_image.get_height():
                        # Lấy màu Pixel tại điểm vừa click
                        clicked_color = map_image.get_at((real_x, real_y))
                        rgb_tuple = (clicked_color.r, clicked_color.g, clicked_color.b)
                        
                        # Đối chiếu màu này vào hệ thống Dữ liệu
                        if rgb_tuple in color_to_province:
                            prov = color_to_province[rgb_tuple]
                            print(f"--- THÔNG TIN VÙNG ĐẤT ---")
                            print(f"Mã màu (RGB): {rgb_tuple}")
                            print(f"Tọa độ: X:{real_x}, Y:{real_y}")
                            print(f"Chủ sở hữu (TAG): {getattr(prov, 'owner', 'Không có/Đất trống')}")
                        else:
                            print("Click vào viền đen hoặc vùng không xác định!")

        # Vẽ ảnh lên màn hình tại tọa độ của Camera
        screen.fill((30, 30, 30)) # Nền màu xám tối
        screen.blit(map_image, (camera_x, camera_y))
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()