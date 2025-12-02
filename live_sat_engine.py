import requests
from datetime import datetime, timezone
import math
import time
from sgp4.api import Satrec, jday
from groups import GP_GROUPS, gp_json_url, tle_url


HEADERS = {"User-Agent": "Mozilla/5.0"}


class LiveSatelliteEngine:

    def __init__(self):
        self.data = {}  # combined per group

    # -----------------------------------------------------
    # Load metadata + TLE for all groups
    # -----------------------------------------------------
    def load_all_groups(self):
        for group, group_key in GP_GROUPS.items():
            print(f"\n📡 Loading group: {group}")

            # ---------------- META JSON ----------------
            meta = requests.get(gp_json_url(group), headers=HEADERS, timeout=30).json()
            print(f"✔ Loaded {len(meta)} metadata")

            # Convert metadata into dict by NORAD
            meta_dict = {int(e["NORAD_CAT_ID"]): e for e in meta}

            # ---------------- TLE BULK DOWNLOAD ----------------
            tle_text = requests.get(tle_url(group), headers=HEADERS, timeout=30).text
            lines = tle_text.strip().splitlines()
            tle_dict = {}

            for i in range(0, len(lines) - 2, 3):
                name = lines[i].strip()
                l1 = lines[i+1].strip()
                l2 = lines[i+2].strip()
                satnum = int(l1[2:7])
                tle_dict[satnum] = {"name": name, "l1": l1, "l2": l2}

            print(f"✔ Loaded {len(tle_dict)} TLE entries")

            # ------------- MERGE TLE + METADATA -------------
            merged = {}
            for norad, tle in tle_dict.items():
                if norad in meta_dict:
                    merged[norad] = {
                        "metadata": meta_dict[norad],
                        "tle": tle
                    }

            print(f"✔ Final merged satellites: {len(merged)}")

            self.data[group] = merged

    # -----------------------------------------------------
    # Compute satellite position from TLE
    # -----------------------------------------------------
    def compute_position(self, tle):
        line1 = tle["l1"]
        line2 = tle["l2"]

        sat = Satrec.twoline2rv(line1, line2)

        t = datetime.now(timezone.utc)
        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute, t.second + t.microsecond/1e6)

        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            return None

        x, y, z = r
        lon = math.degrees(math.atan2(y, x))
        hyp = math.sqrt(x*x + y*y)
        lat = math.degrees(math.atan2(z, hyp))
        alt = math.sqrt(x*x + y*y + z*z) - 6378.137

        return {
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat()
        }
