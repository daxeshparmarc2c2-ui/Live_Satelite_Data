import json
from live_sat_engine import LiveSatelliteEngine

engine = LiveSatelliteEngine()

print("\n🌍 Generating GeoJSON files...\n")

# Each group in metadata
groups = sorted(list(set([v["GROUP"] for v in engine.meta.values()])))

for group in groups:

    features = []

    for norad, m in engine.meta.items():

        if m["GROUP"] != group:
            continue

        pos = engine.compute_position(norad)
        if not pos:
            continue

        # ------------------------------------
        # FLATTEN META FIELDS INTO PROPERTIES
        # ------------------------------------
        flat_meta = {}
        for key, val in m.items():
            if key == "GROUP":
                continue
            flat_meta[f"meta_{key}"] = val

        # ------------------------------------
        # FLATTEN TLE
        # ------------------------------------
        flat_tle = {
            "tle_line1": engine.tle[norad]["line1"],
            "tle_line2": engine.tle[norad]["line2"]
        }

        # ------------------------------------
        # Merge position + meta + TLE
        # ------------------------------------
        props = {**pos, **flat_meta, **flat_tle}

        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "Point",
                "coordinates": [pos["lon"], pos["lat"]]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    out_path = f"output/{group}.geojson"

    with open(out_path, "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"✔ {group}.geojson → {len(features)} satellites")

print("\n🎉 All GeoJSON files updated!\n")

