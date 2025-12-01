import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ----------------------------------------------------------
# Convert GP JSON → REAL TLE LINES
# ----------------------------------------------------------
def convert_gp_to_tle(entry):
    satnum = int(entry["NORAD_CAT_ID"])
    classification = entry["CLASSIFICATION_TYPE"]

    # International Designator
    intldes = entry["OBJECT_ID"].replace("-", "")

    # Epoch
    epoch = datetime.fromisoformat(entry["EPOCH"].replace("Z", ""))
    epoch_year = epoch.year % 100
    epoch_day = (
        epoch.timetuple().tm_yday +
        epoch.hour / 24.0 +
        epoch.minute / 1440.0 +
        epoch.second / 86400.0
    )

    # Eccentricity → 7-digit string
    ecc_str = f"{float(entry['ECCENTRICITY']):.7f}".split(".")[1]

    # TLE Line 1
    line1 = (
        f"1 {satnum:05d}{classification} {intldes:<8}"
        f"{epoch_year:02d}{epoch_day:012.8f} "
        f"{entry['MEAN_MOTION_DOT']: .8f} "
        f"{entry['MEAN_MOTION_DDOT']: .8f} "
        f"{entry['BSTAR']: .8f} 0 9999"
    )

    # TLE Line 2
    line2 = (
        f"2 {satnum:05d} "
        f"{entry['INCLINATION']:8.4f} "
        f"{entry['RA_OF_ASC_NODE']:8.4f} "
        f"{ecc_str:7s} "
        f"{entry['ARG_OF_PERICENTER']:8.4f} "
        f"{entry['MEAN_ANOMALY']:8.4f} "
        f"{entry['MEAN_MOTION']:11.8f} 0"
    )

    return line1, line2


# ----------------------------------------------------------
# Satellite Engine
# ----------------------------------------------------------
class LiveSatelliteEngine:

    def __init__(self):
        self.sats = {}
        self.load_all()

    # -------------------------------------
    def load_all(self):
        for group, url in GP_GROUPS.items():
            print(f"📡 Loading {group} ...")

            try:
                data = requests.get(url, headers=HEADERS, timeout=30).json()
            except:
                print("❌ Failed download")
                continue

            print(f"✔ {len(data)} satellites")

            for entry in data:
                try:
                    line1, line2 = convert_gp_to_tle(entry)
                    satrec = Satrec.twoline2rv(line1, line2)

                    self.sats[int(entry["NORAD_CAT_ID"])] = {
                        "group": group,
                        "meta": entry,
                        "satrec": satrec
                    }

                except Exception as e:
                    print("❌ TLE conversion error:", e)

    # -------------------------------------
    # COMPUTE POSITION
    # -------------------------------------
    def compute(self, norad):
        if norad not in self.sats:
            return None

        t = datetime.now(timezone.utc)

        jd, fr = jday(
            t.year, t.month, t.day,
            t.hour, t.minute,
            t.second + t.microsecond / 1e6
        )

        satrec = self.sats[norad]["satrec"]
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
            "name": self.sats[norad]["meta"]["OBJECT_NAME"],
            "group": self.sats[norad]["group"],
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat(),
            "meta": self.sats[norad]["meta"]
        }

