import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_tle_block(tle_text):
    """Parses a TLE group block into {norad: (line1, line2)}"""
    lines = tle_text.strip().splitlines()
    tle_map = {}
    i = 0

    while i < len(lines) - 2:
        if lines[i].startswith("1 ") and lines[i+1].startswith("2 "):
            line1 = lines[i].strip()
            line2 = lines[i+1].strip()
            satnum = int(line1[2:7])
            tle_map[satnum] = (line1, line2)
            i += 2
        else:
            i += 1

    return tle_map


class LiveSatelliteEngine:

    def __init__(self):
        self.sats = {}
        self.load_all()

    # ----------------------------------------------------
    # Load JSON + TLE for each group (FAST & SAFE)
    # ----------------------------------------------------
    def load_all(self):
        for group, gp_url in GP_GROUPS.items():

            print(f"\n📡 Loading group: {group}")

            # 1. Load GP metadata
            try:
                gp_data = requests.get(gp_url, headers=HEADERS, timeout=30).json()
            except Exception as e:
                print("❌ GP fetch failed:", e)
                continue

            print(f"✔ Loaded {len(gp_data)} metadata")

            # 2. Load TLE for whole group
            tle_url = f"https://celestrak.org/NORAD/elements/tle.php?GROUP={group}&FORMAT=tle"

            try:
                tle_text = requests.get(tle_url, headers=HEADERS, timeout=30).text
                tle_map = parse_tle_block(tle_text)
            except Exception as e:
                print("❌ TLE fetch failed:", e)
                continue

            print(f"✔ Loaded {len(tle_map)} TLE entries")

            # 3. Match metadata to TLE
            for entry in gp_data:
                norad = int(entry["NORAD_CAT_ID"])

                if norad not in tle_map:
                    continue

                line1, line2 = tle_map[norad]

                try:
                    satrec = Satrec.twoline2rv(line1, line2)
                except Exception:
                    continue

                self.sats[norad] = {
                    "meta": entry,
                    "group": group,
                    "line1": line1,
                    "line2": line2,
                    "satrec": satrec
                }

        print(f"\n✨ TOTAL satellites loaded with valid TLE: {len(self.sats)}")

    # ----------------------------------------------------
    # Compute current satellite position
    # ----------------------------------------------------
    def compute(self, norad):
        if norad not in self.sats:
            return None

        sat = self.sats[norad]
        satrec = sat["satrec"]

        t = datetime.now(timezone.utc)

        jd, fr = jday(
            t.year, t.month, t.day,
            t.hour, t.minute,
            t.second + t.microsecond / 1e6
        )

        e, r, v = satrec.sgp4(jd, fr)
        if e != 0:
            return None

        x, y, z = r

        lon = math.degrees(math.atan2(y, x))
        hyp = math.sqrt(x*x + y*y)
        lat = math.degrees(math.atan2(z, hyp))
        alt = math.sqrt(x*x + y*y + z*z) - 6378.137

        return {
            "norad_id": norad,
            "name": sat["meta"]["OBJECT_NAME"],
            "group": sat["group"],
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat(),
            "meta": sat["meta"],
            "tle": {
                "line1": sat["line1"],
                "line2": sat["line2"]
            }
        }

