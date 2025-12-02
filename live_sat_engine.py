# live_sat_engine.py

import requests
import time
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}

SAFE_DELAY = 0.20   # Recommended safe mode


class LiveSatelliteEngine:

    def __init__(self):
        self.sats = {}   # {norad: {group, meta, satrec}}
        self.load_all_groups()

    # --------------------------------------------------
    # LOAD ALL GROUPS (metadata + TLE)
    # --------------------------------------------------
    def load_all_groups(self):
        for group, url in GP_GROUPS.items():

            print(f"\n📡 Loading group: {group}")

            try:
                gp = requests.get(url, headers=HEADERS, timeout=25).json()
            except Exception as e:
                print("❌ GP JSON error:", e)
                continue

            print(f"✔ Loaded {len(gp)} metadata")

            count_tle = 0
            for entry in gp:
                tle_url = f"https://celestrak.org/NORAD/elements/tle.php?CATNR={entry['NORAD_CAT_ID']}"

                try:
                    tle_text = requests.get(tle_url, headers=HEADERS, timeout=25).text.strip()
                    lines = tle_text.splitlines()
                    if len(lines) < 2:
                        continue

                    satrec = Satrec.twoline2rv(lines[0], lines[1])
                    self.sats[int(entry["NORAD_CAT_ID"])] = {
                        "group": group,
                        "meta": entry,
                        "tle1": lines[0],
                        "tle2": lines[1],
                        "satrec": satrec
                    }
                    count_tle += 1

                except:
                    pass

                time.sleep(SAFE_DELAY)

            print(f"✔ Loaded {count_tle} TLE entries")

        print(f"\n✨ TOTAL satellites with valid TLE: {len(self.sats)}\n")

    # --------------------------------------------------
    # COMPUTE SATELLITE POSITION NOW
    # --------------------------------------------------
    def compute_position(self, norad):
        if norad not in self.sats:
            return None

        sat = self.sats[norad]
        satrec = sat["satrec"]

        t = datetime.now(timezone.utc)
        jd, fr = jday(
            t.year, t.month, t.day,
            t.hour, t.minute, t.second + t.microsecond / 1e6
        )

        e, r, v = satrec.sgp4(jd, fr)
        if e != 0:
            return None

        x, y, z = r

        lon = math.degrees(math.atan2(y, x))
        hyp = math.sqrt(x * x + y * y)
        lat = math.degrees(math.atan2(z, hyp))
        alt = math.sqrt(x * x + y * y + z * z) - 6378.137

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
                "line1": sat["tle1"],
                "line2": sat["tle2"]
            }
        }
