import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}


class LiveSatelliteEngine:

    def __init__(self):
        self.meta = {}     # GP metadata
        self.tle = {}      # TLE lines
        self.load_all()

    # ----------------------------------------------------------
    # LOAD ALL GROUPS → metadata + TLE
    # ----------------------------------------------------------
    def load_all(self):
        for group, url in GP_GROUPS.items():
            print(f"\n📡 Loading group: {group}")

            # --- Load GP JSON metadata ---
            try:
                gp_data = requests.get(url, headers=HEADERS, timeout=30).json()
                print(f"✔ Loaded {len(gp_data)} metadata")
            except Exception as e:
                print(f"❌ GP JSON load failed: {e}")
                continue

            for entry in gp_data:
                norad = int(entry["NORAD_CAT_ID"])
                entry["GROUP"] = group
                self.meta[norad] = entry

            # --- Load group TLE ---
            tle_url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"

            try:
                tle_text = requests.get(tle_url, headers=HEADERS, timeout=30).text.strip()
            except Exception as e:
                print(f"❌ TLE fetch failed: {e}")
                continue

            tle_lines = [line.strip() for line in tle_text.split("\n") if line.strip()]
            count = 0

            for i in range(0, len(tle_lines), 3):
                try:
                    line1 = tle_lines[i + 1]
                    line2 = tle_lines[i + 2]
                    norad = int(line1[2:7])
                    self.tle[norad] = (line1, line2)
                    count += 1
                except:
                    continue

            print(f"✔ Loaded {count} TLE entries")

        print(f"\n✨ TOTAL satellites with valid TLE: {len(self.tle)}")

    # ----------------------------------------------------------
    # COMPUTE POSITION
    # ----------------------------------------------------------
    def compute(self, norad):
        if norad not in self.tle:
            return None

        line1, line2 = self.tle[norad]
        meta = self.meta.get(norad, {})

        sat = Satrec.twoline2rv(line1, line2)

        t = datetime.now(timezone.utc)
        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute,
                      t.second + t.microsecond / 1e6)

        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            return None

        x, y, z = r
        lon = math.degrees(math.atan2(y, x))
        lat = math.degrees(math.atan2(z, math.sqrt(x*x + y*y)))
        alt = math.sqrt(x*x + y*y + z*z) - 6378.137

        return {
            "norad_id": norad,
            "name": meta.get("OBJECT_NAME"),
            "group": meta.get("GROUP"),
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat(),
            "meta": meta,
            "tle": {"line1": line1, "line2": line2}
        }


