# generate_all_geojson.py

import json
import os
from live_sat_engine import LiveSatelliteEngine
from groups import GP_GROUPS

os.makedirs("output", exist_ok=True)

engine = LiveSatelliteEngine()

print("\n🌍 Generating GeoJSON files...")

for group in GP_GROUPS.keys():
    features = []

    for norad, sat in engine.sats.items():
        if sat["group"] != group:
            continue

        pos = engine.compute_position(norad)
        if not pos:
            continue

        feature = {
            "type": "Feature",
            "properties": {
                "norad_id": pos["norad_id"],
                "name": pos["name"],
                "group": pos["group"],
                "lat": pos["lat"],
                "lon": pos["lon"],
                "alt_km": pos["alt_km"],
                "timestamp": pos["timestamp"],
                "meta": pos["meta"],
                "tle": pos["tle"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [pos["lon"], pos["lat"]]
            }
        }
        features.append(feature)

    out = {
        "type": "FeatureCollection",
        "features": features
    }

    outfile = f"output/{group}.geojson"
    with open(outfile, "w") as f:
        json.dump(out, f)

    print(f"✔ {group}.geojson → {len(features)} satellites")
