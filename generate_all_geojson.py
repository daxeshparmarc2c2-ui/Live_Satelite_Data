import json
from sgp4.api import Satrec
from live_sat_engine import CELESTRAK_GROUPS, fetch_group, to_tle, compute_position

OUTPUT_DIR = "output/"

def build_group(group):
    data = fetch_group(group)
    print(f"📡 Loaded {len(data)} from {group}")

    features = []

    for e in data:
        try:
            l1, l2 = to_tle(e)
            sat = Satrec.twoline2rv(l1, l2)
            pos = compute_position(sat)
            if pos is None:
                continue
            lon, lat, alt, timestamp = pos
            feat = {
                "type": "Feature",
                "properties": {
                    "norad_id": int(e["NORAD_CAT_ID"]),
                    "name": e["OBJECT_NAME"],
                    "group": group,
                    "lat": lat,
                    "lon": lon,
                    "alt_km": alt,
                    "timestamp": timestamp,
                    "meta": e,
                },
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
            features.append(feat)

        except Exception as err:
            print("ERROR:", err)
            continue

    filepath = OUTPUT_DIR + group + ".geojson"
    with open(filepath, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

    print(f"✔ {group}.geojson → {len(features)} satellites\n")

for g in CELESTRAK_GROUPS:
    build_group(g)

