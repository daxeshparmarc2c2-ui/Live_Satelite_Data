import json
from live_sat_engine import LiveSatelliteEngine
from groups import GP_GROUPS

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

        features.append({
            "type": "Feature",
            "properties": pos,
            "geometry": {
                "type": "Point",
                "coordinates": [pos["lon"], pos["lat"]]
            }
        })

    with open(f"output/{group}.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)

    print(f"✔ {group}.geojson → {len(features)} satellites")
