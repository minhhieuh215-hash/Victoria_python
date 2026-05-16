import os
import re
import colorsys

def load_countries():
    countries = {}
    folder_path = "data/common/country_definitions"

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
            
        with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
            current_tag = None
            
            for line in file:
                # Bỏ qua các dòng comment (bắt đầu bằng #)
                line = line.split('#')[0].strip() 
                if not line:
                    continue
                    
                # Bắt đầu một quốc gia mới (VD: GBR = { )
                tag_match = re.match(r"^([A-Z0-9]{3})\s*=\s*\{", line)
                if tag_match:
                    current_tag = tag_match.group(1)
                    continue
                    
                # Nếu đang ở trong block của 1 quốc gia và tìm thấy chữ "color"
                if current_tag and "color" in line:
                    # Regex này lấy ra hệ màu và 3 con số
                    color_match = re.search(r"color\s*=\s*(hsv360|hsv)?\s*\{\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", line)
                    
                    if color_match:
                        color_type = color_match.group(1)
                        v1 = float(color_match.group(2))
                        v2 = float(color_match.group(3))
                        v3 = float(color_match.group(4))
                        
                        # Chuyển đổi các hệ màu hsv/hsv360 về RGB chuẩn (0-255)
                        if color_type == "hsv360":
                            r, g, b = colorsys.hsv_to_rgb(v1/360.0, v2/100.0, v3/100.0)
                            rgb = (int(r*255), int(g*255), int(b*255))
                        elif color_type == "hsv":
                            r, g, b = colorsys.hsv_to_rgb(v1, v2, v3)
                            rgb = (int(r*255), int(g*255), int(b*255))
                        else:
                            # Nếu không có chữ hsv, nó là RGB thường
                            rgb = (int(v1), int(v2), int(v3))
                            
                        # Lưu vào từ điển { "GBR": (252, 178, 229), "GER": (147, 130, 110) }
                        countries[current_tag] = rgb
                        current_tag = None # Reset để chờ lấy TAG nước tiếp theo
                        
    return countries

# Code test thử xem có chạy mượt không
if __name__ == "__main__":
    my_countries = load_countries()
    print(f"Đã load thành công {len(my_countries)} quốc gia!")
    print(f"Màu của Anh (GBR) là: {my_countries.get('GBR')}")
    print(f"Màu của Đại Nam (DAI) là: {my_countries.get('DAI')}")