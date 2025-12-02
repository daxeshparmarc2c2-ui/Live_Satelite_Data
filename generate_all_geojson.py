import json
from live_sat_engine import LiveSatelliteEngine

engine = LiveSatelliteEngine()
engine.load_all_groups()

print("\n🌍 Generating GeoJSON files...")

for group, sats in engine.data.items():
    features = []

    for norad, sat_data in sats.items():
        pos = engine.compute_position(sat_data["tle"])
        if pos is None:
            continue

        meta = sat_data["metadata"]
        tle = sat_data["tle"]

        feature = {
            "type": "Feature",
            "properties": {
                "norad_id": norad,
                "name": meta["OBJECT_NAME"],
                "group": group,
                **pos,
                "meta": meta,
                "tle": {
                    "line1": tle["l1"],
                    "line2": tle["l2"]
                }
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

    with open(f"output/{group}.geojson", "w") as f:
        json.dump(out, f)

    print(f"✔ {group}.geojson → {len(features)} satellites")
