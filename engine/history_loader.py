import os
import re

def load_state_history(provinces_dict):
    """
    provinces_dict: Truyền vào từ điển { (R,G,B): Province_Object } 
    để hàm này gán trực tiếp thuộc tính .owner cho từng Province.
    """
    folder_path = "data/common/history/states"

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue

        with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
            content = file.read()

            # Tách nội dung theo từ khóa "create_state" để dễ dàng lấy dữ liệu từng mảng
            blocks = content.split("create_state")
            
            # Bỏ qua phần tử đầu tiên (vì nó là râu ria trước khi có create_state)
            for block in blocks[1:]:
                # Tìm chữ "country = c:TAG" (có thể có hoặc không có ngoặc kép)
                country_match = re.search(r'country\s*=\s*\"?c:([A-Z0-9]+)\"?', block)
                
                # Tìm khối "owned_provinces = { ... }"
                provinces_match = re.search(r"owned_provinces\s*=\s*\{([^}]+)\}", block)

                if country_match and provinces_match:
                    owner_tag = country_match.group(1)
                    prov_list = provinces_match.group(1).split()

                    for hex_pid in prov_list:
                        # Làm sạch chuỗi Hex
                        hex_str = hex_pid.replace('"', '').lstrip('x')
                        if len(hex_str) != 6:
                            continue

                        # Chuyển Hex sang RGB
                        r = int(hex_str[0:2], 16)
                        g = int(hex_str[2:4], 16)
                        b = int(hex_str[4:6], 16)
                        target_color = (r, g, b)

                        # Nếu Province này có tồn tại trên bản đồ, gán chủ sở hữu cho nó!
                        if target_color in provinces_dict:
                            provinces_dict[target_color].owner = owner_tag

    print("Đã chia chác lãnh thổ xong cho năm 1836!")