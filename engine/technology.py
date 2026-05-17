# engine/technology.py
class Technology:
    def __init__(self, name, category, cost, effects):
        self.name = name
        self.category = category    # "production", "military", "society"
        self.cost = cost            # Điểm nghiên cứu cần
        self.researched = False
        self.effects = effects      # {"farm_output": +0.2, "army_tech": True}