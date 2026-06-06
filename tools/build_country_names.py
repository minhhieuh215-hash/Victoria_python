#!/usr/bin/env python3
"""Generate data/country_display_names.json from Vic3 definition files."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.country_names import load_country_display_names, NAME_OVERRIDES


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    names = load_country_display_names(base)
    out = os.path.join(base, "data", "country_display_names.json")
    export = {k: names[k] for k in sorted(names) if k not in NAME_OVERRIDES or names[k] != NAME_OVERRIDES.get(k)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(export)} names to {out}")


if __name__ == "__main__":
    main()
