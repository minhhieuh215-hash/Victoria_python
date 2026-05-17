class Law:
    def __init__(self, name, category, enactment_chance):
        self.name = name
        self.category = category    # "governance", "economy", "human_rights"
        self.enactment_chance = enactment_chance
        self.supporters = []        # Interest groups ủng hộ
        self.opposers = []          # Interest groups phản đối