# engine/diplomacy.py
class DiplomaticRelation:
    def __init__(self, country1, country2):
        self.relations = 0          # -100 đến 100
        self.treaties = []          # alliance, trade_agreement, defensive_pact
        self.infamy = 0             # Mức độ gây hấn