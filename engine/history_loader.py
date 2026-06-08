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
            
            
            for block in blocks[1:]:
                country_match = re.search(r'country\s*=\s*\"?c:([A-Z0-9]+)\"?', block)
                
                provinces_match = re.search(r"owned_provinces\s*=\s*\{([^}]+)\}", block)

                if country_match and provinces_match:
                    owner_tag = country_match.group(1)
                    prov_list = provinces_match.group(1).split()

                    for hex_pid in prov_list:
                        # Làm sạch chuỗi: bỏ ngoặc kép, khoảng trắng thừa, và chữ 'x' hoặc 'X' ở đầu
                        hex_str = hex_pid.replace('"', '').strip().lstrip('x').lstrip('X')
                        
                        if len(hex_str) != 6:
                            continue

                        # DÙNG TRY-EXCEPT ĐỂ BẮT RÁC: Nếu chuỗi 6 ký tự nhưng không phải Hex hợp lệ, bỏ qua!
                        try:
                            r = int(hex_str[0:2], 16)
                            g = int(hex_str[2:4], 16)
                            b = int(hex_str[4:6], 16)
                            target_color = (r, g, b)

                            # Nếu Province này có tồn tại trên bản đồ, gán chủ sở hữu cho nó!
                            if target_color in provinces_dict:
                                provinces_dict[target_color].owner = owner_tag
                        except ValueError:
                            # Kệ nó, bỏ qua các chuỗi tào lao trong file game
                            continue

    try:
        import sys
        sys.stdout.buffer.write(("Đã chia chác lãnh thổ xong cho năm 1836!\n").encode("utf-8"))
    except Exception:
        print("State history assignment complete for 1836!")