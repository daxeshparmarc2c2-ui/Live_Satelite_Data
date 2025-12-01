import json
import os
from live_sat_engine import LiveSatelliteEngine

engine = LiveSatelliteEngine()

os.makedirs("output", exist_ok=True)

groups = {}

# Organize by group
for norad, sat in engine.sats.items():
    g = sat["group"]
    groups.setdefault(g, []).append(norad)

print("\n🌍 Generating GeoJSON files...\n")

for group, sats in groups.items():

    features = []

    for norad in sats:
        p = engine.compute(norad)
        if p is None:
            continue

        features.append({
            "type": "Feature",
            "properties": p,
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]}
        })

    output = {"type": "FeatureCollection", "features": features}

    with open(f"output/{group}.geojson", "w") as f:
        json.dump(output, f, indent=2)

    print(f"✔ {group}.geojson → {len(features)} satellites")

    print(f"✔ {outfile} → {len(features)} satellites")

