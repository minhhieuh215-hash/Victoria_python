# engine/diplomacy.py
class DiplomaticAction:
    @staticmethod
    def improve_relations(country, target, amount=5):
        """Cải thiện quan hệ"""
        if target not in country.relations:
            country.relations[target] = 0
        country.relations[target] = min(100, country.relations[target] + amount)
        return f"Quan hệ với {target} +{amount}"
    
    @staticmethod
    def worsen_relations(country, target, amount=5):
        """Làm xấu quan hệ"""
        if target not in country.relations:
            country.relations[target] = 0
        country.relations[target] = max(-100, country.relations[target] - amount)
        return f"Quan hệ với {target} -{amount}"
    
    @staticmethod
    def declare_war(declarer, target, war_goal=None):
        """Tuyên chiến"""
        if target in declarer.at_war_with:
            return False
        
        declarer.at_war_with.add(target)
        if target in declarer.relations:
            declarer.relations[target] = min(-100, declarer.relations[target] - 50)
        
        # Các đồng minh có thể bị kéo vào
        return True
    
    @staticmethod
    def form_alliance(country1, country2):
        """Tạo liên minh"""
        # Cần quan hệ > 50
        if country1.relations.get(country2.tag, 0) < 50:
            return False
        if country2.relations.get(country1.tag, 0) < 50:
            return False
        
        country1.allies.add(country2.tag)
        country2.allies.add(country1.tag)
        return True