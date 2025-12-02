import json
import os
import glob

INPUT_DIR = "."
OUTPUT_DIR = "flattened"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def flatten_properties(props):
    flat = {}

    # Keep main fields
    for k in ["norad_id", "name", "group", "lat", "lon", "alt_km", "timestamp"]:
        flat[k] = props.get(k)

    # Flatten metadata
    meta = props.get("meta", {})
    for mk, mv in meta.items():
        flat[f"meta_{mk.lower()}"] = mv

    # Flatten TLE fields
    tle = props.get("tle", {})
    for tk, tv in tle.items():
        flat[f"tle_{tk.lower()}"] = tv

    return flat


print("🔍 Searching for GeoJSON files...")

# Process all original GeoJSON files (not inside flattened/)
for file in glob.glob("*.geojson"):
    print(f"📄 Flattening {file}")

    with open(file, "r") as f:
        data = json.load(f)

    new_features = []
    for feat in data.get("features", []):
        new_features.append({
            "type": "Feature",
            "properties": flatten_properties(feat["properties"]),
            "geometry": feat["geometry"]
        })

    output_file = os.path.join(OUTPUT_DIR, file)

    with open(output_file, "w") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": new_features
        }, f, indent=2)

    print(f"✔ Saved flattened → {output_file}")

print("🎉 Flattening complete!")
