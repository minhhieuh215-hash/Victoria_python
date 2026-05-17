import pygame
import numpy as np
import sys
import os

def generate_political_map(original_image, color_to_province, countries_data):
    """
    Tô màu bản đồ chính trị dùng NumPy - nhanh hơn ~500x so với vòng lặp pixel.
    
    TRƯỚC (vòng lặp Python): ~60-120 giây cho ảnh 8000x4000
    SAU  (NumPy vectorized):  ~0.5-2 giây
    """
    print("Đang tô màu bản đồ chính trị (NumPy mode)...")

    # Chuyển pygame surface → numpy array shape (H, W, 3)
    arr = pygame.surfarray.array3d(original_image)  # shape: (W, H, 3)
    arr = arr.transpose(1, 0, 2)                     # → (H, W, 3) cho dễ xử lý

    H, W, _ = arr.shape
    output = arr.copy()

    # --- Bước 1: Xây lookup table màu → màu output ---
    # Mỗi province color → màu tô tương ứng
    color_lookup = {}

    for rgb_tuple, prov in color_to_province.items():
        if getattr(prov, 'is_sea', False):
            color_lookup[rgb_tuple] = (25, 45, 80)           # Biển (xanh đậm)
        elif getattr(prov, 'is_lake', False):
            color_lookup[rgb_tuple] = (25, 45, 80)        # Hồ nội địa (xanh nhạt hơn biển)
        else:
            owner_tag = getattr(prov, 'owner', None)
            if owner_tag and owner_tag in countries_data:
                color_lookup[rgb_tuple] = tuple(countries_data[owner_tag])  # Màu quốc gia
            else:
                color_lookup[rgb_tuple] = (140, 130, 120)    # Đất hoang

    # --- Bước 2: Tạo mảng màu output bằng vectorized lookup ---
    # Gộp R, G, B thành 1 số nguyên 32-bit để tra cứu nhanh
    # key = R*65536 + G*256 + B
    arr_u32 = (arr[:, :, 0].astype(np.uint32) * 65536
             + arr[:, :, 1].astype(np.uint32) * 256
             + arr[:, :, 2].astype(np.uint32))

    # Tạo lookup array (0 → 16777215 entries, chỉ fill những màu cần)
    lut_r = np.zeros(16777216, dtype=np.uint8)
    lut_g = np.zeros(16777216, dtype=np.uint8)
    lut_b = np.zeros(16777216, dtype=np.uint8)

    # Mặc định: copy màu gốc (giữ viền đen và màu chưa biết)
    # Chỉ ghi đè những màu có trong lookup
    for (r, g, b), (nr, ng, nb) in color_lookup.items():
        key = r * 65536 + g * 256 + b
        lut_r[key] = nr
        lut_g[key] = ng
        lut_b[key] = nb

    # Các màu không có trong lookup (viền đen, màu lạ) → giữ nguyên màu gốc
    # Đánh dấu màu nào đã được định nghĩa
    defined_keys = set()
    for (r, g, b) in color_lookup:
        defined_keys.add(r * 65536 + g * 256 + b)

    # Tạo mask: pixel nào CÓ trong lookup
    all_keys = arr_u32.ravel()
    in_lookup = np.zeros(16777216, dtype=bool)
    for k in defined_keys:
        in_lookup[k] = True

    mask = in_lookup[arr_u32]  # (H, W) bool

    # Áp dụng lookup table
    output_r = np.where(mask, lut_r[arr_u32], arr[:, :, 0])
    output_g = np.where(mask, lut_g[arr_u32], arr[:, :, 1])
    output_b = np.where(mask, lut_b[arr_u32], arr[:, :, 2])

    # Gộp lại thành array (H, W, 3)
    result = np.stack([output_r, output_g, output_b], axis=2)

    # Chuyển lại về pygame surface
    result_t = result.transpose(1, 0, 2)  # → (W, H, 3)
    pol_map = pygame.surfarray.make_surface(result_t)

    print("-> Tô màu bản đồ chính trị hoàn tất!")
    return pol_map


def run_game(color_to_province, countries_data):
    pygame.init()
    screen_width, screen_height = 1280, 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Victoria 3 Python Engine - Map Viewer")

    # Tự động tìm đường dẫn file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        base_dir = current_dir
    else:
        base_dir = os.path.dirname(current_dir)
    map_path = os.path.join(base_dir, "data", "map_data", "provinces.png")
    
    # Load và tô màu ảnh
    original_map = pygame.image.load(map_path).convert()
    political_map = generate_political_map(original_map, color_to_province, countries_data)
    
    map_w, map_h = original_map.get_size()
    
    # --- 1. SETUP ZOOM & CAMERA ---
    # Ép tỷ lệ zoom ban đầu để bản đồ vừa khít màn hình
    min_zoom = max(screen_width / map_w, screen_height / map_h)
    zoom_level = min_zoom 
    camera_x, camera_y = 0, 0
    
    # Hàm kẹp chốt camera: Y giới hạn, X wrap vòng quanh
    def clamp_camera(cam_x, cam_y, z_level):
        scaled_w = int(map_w * z_level)
        scaled_h = int(map_h * z_level)
        cam_y = max(screen_height - scaled_h, min(0, cam_y))
        # X wrap: cuộn vòng quanh như địa cầu
        cam_x = cam_x % scaled_w
        return cam_x, cam_y

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
                
            # ĐỔI BẢN ĐỒ KHI NHẤN DẤU CÁCH
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_political = not show_political
                    current_active_map = political_map if show_political else original_map
                    scaled_map = pygame.transform.scale(current_active_map, (int(map_w * zoom_level), int(map_h * zoom_level)))
                    print(f"Chuyển sang chế độ: {'Bản đồ chính trị' if show_political else 'Bản đồ tỉnh gốc'}")

            # ZOOM BẰNG CON LĂN CHUỘT
            elif event.type == pygame.MOUSEWHEEL:
                old_zoom = zoom_level
                if event.y > 0: zoom_level *= 1.2
                elif event.y < 0: zoom_level /= 1.2
                
                # Khóa zoom không cho nhỏ hơn kích thước màn hình
                zoom_level = max(min_zoom, min(zoom_level, 5.0))
                
                if old_zoom != zoom_level:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    camera_x = mouse_x - (mouse_x - camera_x) * (zoom_level / old_zoom)
                    camera_y = mouse_y - (mouse_y - camera_y) * (zoom_level / old_zoom)
                    
                    # Cập nhật chốt camera sau khi zoom
                    camera_x, camera_y = clamp_camera(camera_x, camera_y, zoom_level)
                    scaled_map = pygame.transform.scale(current_active_map, (int(map_w * zoom_level), int(map_h * zoom_level)))

            # CLICK / KÉO CHUỘT
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Chuột trái → kéo map
                    is_panning = True
                    last_mouse_pos = event.pos

                elif event.button == 3:  # Chuột phải → xem info tỉnh
                    mouse_x, mouse_y = event.pos
                    real_x = int((mouse_x - camera_x) / zoom_level)
                    real_y = int((mouse_y - camera_y) / zoom_level)

                    if 0 <= real_x < map_w and 0 <= real_y < map_h:
                        clicked_color = original_map.get_at((real_x, real_y))
                        rgb_tuple = (clicked_color.r, clicked_color.g, clicked_color.b)

                        if rgb_tuple in color_to_province:
                            prov = color_to_province[rgb_tuple]
                            print(f"\n--- THÔNG TIN VÙNG ĐẤT ---")
                            print(f"RGB: {rgb_tuple} | Biển/Hồ: {'🌊 Có' if getattr(prov, 'is_sea', False) else '⛰️ Không'}")
                            print(f"Quốc gia sở hữu (TAG): {getattr(prov, 'owner', 'Vô chủ')}")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    mouse_x, mouse_y = event.pos
                    camera_x += mouse_x - last_mouse_pos[0]
                    camera_y += mouse_y - last_mouse_pos[1]
                    last_mouse_pos = event.pos
                    
                    # Cập nhật chốt camera lúc kéo
                    camera_x, camera_y = clamp_camera(camera_x, camera_y, zoom_level)

        screen.fill((19, 41, 63))  # màu biển làm nền
        scaled_w = int(map_w * zoom_level)
        # Vẽ bản đồ chính
        screen.blit(scaled_map, (camera_x, camera_y))
        # Vẽ bản đồ thứ 2 bên phải để wrap (Alaska hiện khi kéo sang phải)
        screen.blit(scaled_map, (camera_x - scaled_w, camera_y))
        # Vẽ thêm bên phải nếu cần
        screen.blit(scaled_map, (camera_x + scaled_w, camera_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()