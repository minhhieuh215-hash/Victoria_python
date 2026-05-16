class Province:
    def __init__(self, id, color):
        self.id = id
        self.color = color

        self.owner = None
        self.population = 0
        self.terrain = "plains"

        self.neighbors = []