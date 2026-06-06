import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.map_loader import load_provinces, load_states
from engine.country_loader import load_countries, load_countries_full
from engine.history_loader import load_state_history
from engine.economy import init_countries   # Cách này đúng
from engine.game_state import GameState
from engine.events import init_events
from models.market import Market
from game_ui import start_engine
from engine.country_names import init_country_names

import json
import random

def main():
    provinces = load_provinces()
    states = load_states(provinces)
    color_to_province = {prov.color: prov for prov in provinces.values()}
    countries_data = load_countries()   # { TAG: (R,G,B) }
    name_count = len(init_country_names())
    load_state_history(color_to_province)
    countries_full = load_countries_full()

    market = Market()
    countries_obj = init_countries(countries_data, countries_full)

    starting_subjects = {
        "GBR": ["CAN", "AST", "CEY"],
        "FRA": ["ALD"],
        "SPA": ["CUB"],
    }
    for overlord_tag, subject_tags in starting_subjects.items():
        if overlord_tag in countries_obj:
            for s_tag in subject_tags:
                if s_tag in countries_obj:
                    countries_obj[overlord_tag].subjects.add(s_tag)

    states_dict = {s.name: s for s in states}

    for state in states:
        owner_counts = {}
        for prov in state.provinces:
            owner = getattr(prov, 'owner', None)
            if owner and owner not in ("SEA", "LAKE", "Không có / Đất trống"):
                owner_counts[owner] = owner_counts.get(owner, 0) + 1
        if owner_counts:
            state.owner = max(owner_counts, key=lambda x: owner_counts[x])

    for country in countries_obj.values():
        country.states = {s.name: s for s in states if s.owner == country.tag}
        num_states = len(country.states)
        if num_states > 0:
            state_pop = country.population / num_states
            for state in country.states.values():
                state.population = state_pop
                num_provs = len(state.provinces)
                if num_provs > 0:
                    prov_pop_count = int((state_pop * 1000000) / num_provs)
                    for prov in state.provinces:
                        prov.population = prov_pop_count

    for prov in provinces.values():
        if not getattr(prov, 'population', 0):
            if prov.owner == "Không có / Đất trống" or not prov.owner:
                prov.population = random.randint(5000, 50000)
            elif prov.owner in ("SEA", "LAKE"):
                prov.population = 0

    game_state = GameState(provinces, states_dict, countries_data,
                           countries_obj, market)
    
    game_state = init_events(game_state)
    start_engine(game_state)

if __name__ == "__main__":
    main()