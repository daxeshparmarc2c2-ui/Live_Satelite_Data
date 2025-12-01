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

    def load_all(self):
        for group, url in GP_GROUPS.items():
            print(f"📡 Loading {group} ...")

            try:
                data = requests.get(url, headers=HEADERS, timeout=30).json()
            except:
                print("❌ Failed to load group")
                continue

            print(f"✔ {len(data)} satellites")

            for e in data:
                try:
                    satrec = self.init_sgp4(e)
                    norad = int(e["NORAD_CAT_ID"])
                    self.sats[norad] = {
                        "group": group,
                        "meta": e,
                        "satrec": satrec
                    }
                except Exception as err:
                    print("   ❌ init error:", err)

    def init_sgp4(self, e):
        s = Satrec()
        s.sgp4init(
            72,                         # gravity model
            e["EPHEMERIS_TYPE"],        # ephemeris type
            int(e["NORAD_CAT_ID"]),     # NORAD ID
            e["EPOCH"],                 # epoch timestamp
            e["MEAN_MOTION_DOT"],       # first time derivative
            e["MEAN_MOTION_DDOT"],      # second time derivative
            e["BSTAR"],                 # drag term
            e["INCLINATION"],           # radians? No → degrees OK
            e["RA_OF_ASC_NODE"],
            e["ECCENTRICITY"],
            e["ARG_OF_PERICENTER"],
            e["MEAN_ANOMALY"],
            e["MEAN_MOTION"]
        )
        return s

    def compute(self, norad):
        sat = self.sats[norad]["satrec"]
        meta = self.sats[norad]["meta"]
        group = self.sats[norad]["group"]

        t = datetime.now(timezone.utc)

        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute,
                      t.second + t.microsecond/1e6)

        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
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
            "meta": meta
        }
