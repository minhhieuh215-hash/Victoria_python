# engine/politics.py
class InterestGroup:
    def __init__(self, name, ideology):
        self.name = name            # "Landowners", "Industrialists", "Military"
        self.ideology = ideology
        self.clout = 0              # Ảnh hưởng (dựa trên POPs ủng hộ)
        self.leader = None
        self.opinion = 0            # Thái độ với chính phủ