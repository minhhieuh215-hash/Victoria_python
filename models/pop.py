# models/pop.py
class Pop:
    def __init__(self, culture, religion, profession, size, location):
        self.culture = culture      # Văn hóa (Việt, Kinh, Hoa...)
        self.religion = religion    # Tôn giáo (Phật giáo, Công giáo...)
        self.profession = profession # Nghề nghiệp (nông dân, công nhân, quý tộc...)
        self.size = size            # Số lượng
        self.location = None        # Province/State
        self.needs = {}             # Nhu cầu (gạo, vải, đồ gỗ...)
        self.political_power = 0    # Ảnh hưởng chính trị
        self.literacy = 0.2         # Tỷ lệ biết chữ
        self.militancy = 0          # Sự phản kháng
        self.consciousness = 0      # Ý thức chính trị