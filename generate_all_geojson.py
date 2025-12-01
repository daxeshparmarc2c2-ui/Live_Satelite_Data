import json
import os
from live_sat_engine import LiveSatelliteEngine
from groups import GP_GROUPS

os.makedirs("output", exist_ok=True)

engine = LiveSatelliteEngine()

for group in GP_GROUPS.keys():
    features = []

    for norad, sat in engine.sats.items():
        if sat["group"] != group:
            continue

        pos = engine.compute(norad)
        if pos is None:
            continue

        features.append({
            "type": "Feature",
            "properties": pos,
            "geometry": {
                "type": "Point",
                "coordinates": [pos["lon"], pos["lat"]]
            }
        })

    outfile = f"output/{group}.geojson"
    with open(outfile, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

    print(f"✔ {outfile} → {len(features)} satellites")

