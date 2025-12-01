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

    # -------------------------------------
    # LOAD ALL GROUPS
    # -------------------------------------
    def load_all(self):
        for group, url in GP_GROUPS.items():
            print(f"📡 Loading {group} ...")

            try:
                data = requests.get(url, headers=HEADERS, timeout=30).json()
            except Exception as e:
                print("❌ Failed:", e)
                continue

            print(f"✔ {len(data)} satellites")

            for entry in data:
                try:
                    satrec = self.init_sgp4(entry)
                    norad = int(entry["NORAD_CAT_ID"])
                    self.sats[norad] = {
                        "group": group,
                        "meta": entry,
                        "satrec": satrec
                    }
                except Exception as err:
                    print("❌ init error:", err)

    # -------------------------------------
    # CORRECT GP JSON → SGP4 INIT
    # -------------------------------------
    def init_sgp4(self, e):
        s = Satrec()

        # Convert ISO8601 epoch to SGP4 epoch days since 1949
        epoch_dt = datetime.fromisoformat(e["EPOCH"].replace("Z", ""))
        epoch_days = (epoch_dt - datetime(1949, 12, 31)).total_seconds() / 86400.0

        # Correct parameter order for SGP4
        s.sgp4init(
            72,                        # WGS72 model
            'i',                       # improved mode
            int(e["NORAD_CAT_ID"]),    # satnum
            epoch_days,                # epoch
            e["BSTAR"],                # drag term
            e["MEAN_MOTION_DOT"],      # ndot
            e["MEAN_MOTION_DDOT"],     # nddot
            e["ECCENTRICITY"],         # eccentricity
            e["ARG_OF_PERICENTER"],    # argument of pericenter
            e["INCLINATION"],          # inclination (deg OK)
            e["MEAN_ANOMALY"],         # mean anomaly
            e["MEAN_MOTION"],          # mean motion
            e["RA_OF_ASC_NODE"]        # RAAN
        )

        return s

    # -------------------------------------
    # COMPUTE CURRENT POSITION
    # -------------------------------------
    def compute(self, norad):
        if norad not in self.sats:
            return None

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

