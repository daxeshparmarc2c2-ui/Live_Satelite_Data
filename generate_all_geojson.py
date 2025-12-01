import json
from live_sat_engine import LiveSatelliteEngine

engine = LiveSatelliteEngine()

print("\n🌍 Generating GeoJSON files...")

for group in set([v["GROUP"] for v in engine.meta.values()]):
    features = []

    for norad, meta in engine.meta.items():
        if meta["GROUP"] != group:
            continue

        pos = engine.compute(norad)
        if pos is None:
            continue

        feat = {
            "type": "Feature",
            "properties": pos,
            "geometry": {
                "type": "Point",
                "coordinates": [pos["lon"], pos["lat"]]
            }
        }

        features.append(feat)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(f"output/{group}.geojson", "w") as f:
        json.dump(geojson, f)

    print(f"✔ {group}.geojson → {len(features)} satellites")

print("\n🎉 All files generated!")
