import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}


class LiveSatelliteEngine:

    def __init__(self):
        self.sats = {}
        self.load_all()

    # ---------------------------------------------------------
    # LOAD JSON + TLE FOR EACH GROUP
    # ---------------------------------------------------------
    def load_all(self):
        for group, urls in GP_GROUPS.items():
            print(f"\n📡 Loading group: {group}")

            # load metadata JSON
            meta = requests.get(urls["json"], headers=HEADERS, timeout=30).json()
            print(f"✔ Loaded {len(meta)} metadata")

            # load TLE 3LE
            tle_text = requests.get(urls["tle"], headers=HEADERS, timeout=30).text
            tle_lines = [l.strip() for l in tle_text.split("\n") if l.strip()]

            # convert 3LE → dictionary
            tle_map = {}
            for i in range(0, len(tle_lines), 3):
                name = tle_lines[i][2:].strip()
                line1 = tle_lines[i + 1]
                line2 = tle_lines[i + 2]
                tle_map[name] = (line1, line2)

            print(f"✔ Loaded {len(tle_map)} TLE entries")

            # match metadata → TLE
            for entry in meta:
                name = entry["OBJECT_NAME"]
                if name not in tle_map:
                    continue

                line1, line2 = tle_map[name]
                satrec = Satrec.twoline2rv(line1, line2)

                norad = entry["NORAD_CAT_ID"]
                self.sats[norad] = {
                    "group": group,
                    "meta": entry,
                    "tle_line1": line1,
                    "tle_line2": line2,
                    "satrec": satrec
                }

        print(f"\n✨ TOTAL satellites with valid TLE: {len(self.sats)}")

    # ---------------------------------------------------------
    # COMPUTE POSITION
    # ---------------------------------------------------------
    def compute_position(self, norad):

        if norad not in self.sats:
            return None

        sat = self.sats[norad]["satrec"]
        meta = self.sats[norad]["meta"]
        group = self.sats[norad]["group"]

        t = datetime.now(timezone.utc)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)

        error, r, v = sat.sgp4(jd, fr)
        if error != 0:
            return None

        x, y, z = r

        lon = math.degrees(math.atan2(y, x))
        hyp = math.sqrt(x*x + y*y)
        lat = math.degrees(math.atan2(z, hyp))
        alt = math.sqrt(x*x + y*y + z*z) - 6378.137

        return {
            "norad_id": norad,
            "name": meta["OBJECT_NAME"],
            "group": group,
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat(),
            "meta": meta,
            "tle": {
                "line1": self.sats[norad]["tle_line1"],
                "line2": self.sats[norad]["tle_line2"]
            }
        }
