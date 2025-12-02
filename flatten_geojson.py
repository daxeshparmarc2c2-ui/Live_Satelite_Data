import json
import os
import glob

# Your original GeoJSON folder
INPUT_DIR = "output"

# New folder for flattened GeoJSON
OUTPUT_DIR = "flattened"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def flatten_properties(props):
    flat = {}

    # Keep original top-level fields
    for key in ["norad_id", "name", "group", "lat", "lon", "alt_km", "timestamp"]:
        flat[key] = props.get(key)

    # Flatten meta fields
    meta = props.get("meta", {})
    for mk, mv in meta.items():
        flat[f"meta_{mk.lower()}"] = mv

    # Flatten tle fields
    tle = props.get("tle", {})
    for tk, tv in tle.items():
        flat[f"tle_{tk.lower()}"] = tv

    return flat


print(f"🔍 Searching for GeoJSON files inside: {INPUT_DIR}/")

for file_path in glob.glob(f"{INPUT_DIR}/*.geojson"):
    print(f"📄 Flattening: {file_path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    flattened_features = []
    for feature in data.get("features", []):
        flattened_features.append({
            "type": "Feature",
            "properties": flatten_properties(feature["properties"]),
            "geometry": feature["geometry"]
        })

    out_name = os.path.basename(file_path)
    out_path = os.path.join(OUTPUT_DIR, out_name)

    with open(out_path, "w") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": flattened_features
        }, f, indent=2)

    print(f"✔ Saved flattened file → {out_path}")

print("🎉 Done! All flattened files created in /flattened/")

