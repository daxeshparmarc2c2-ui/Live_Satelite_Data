import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

from groups import GP_GROUPS

HEADERS = {"User-Agent": "Mozilla/5.0"}


class LiveSatelliteEngine:

    def __init__(self):
        self.sats = {}  # {norad: {...}}
        self.load_all()

    # ----------------------------------------------------
    # Load GP JSON metadata + REAL TLE
    # ----------------------------------------------------
    def load_all(self):
        for group, url in GP_GROUPS.items():
            print(f"\n📡 Loading GP JSON for group: {group}")

            try:
                entries = requests.get(url, headers=HEADERS, timeout=20).json()
            except Exception as e:
                print("❌ GP fetch failed:", e)
                continue

            print(f"✔ Loaded {len(entries)} metadata entries")

            for meta in entries:
                norad = int(meta["NORAD_CAT_ID"])

                # Fetch REAL TLE
                tle_url = f"https://celestrak.org/NORAD/elements/tle.php?CATNR={norad}"
                tle_text = requests.get(tle_url, headers=HEADERS, timeout=20).text.strip()

                lines = tle_text.splitlines()
                if len(lines) < 2:
                    print(f"❌ No TLE for {norad}")
                    continue

                # Sometimes name line is included
                if len(lines) == 3:
                    line1 = lines[1].strip()
                    line2 = lines[2].strip()
                else:
                    line1 = lines[-2].strip()
                    line2 = lines[-1].strip()

                try:
                    satrec = Satrec.twoline2rv(line1, line2)
                except Exception as err:
                    print(f"❌ TLE parse error for {norad}: {err}")
                    continue

                self.sats[norad] = {
                    "group": group,
                    "meta": meta,
                    "line1": line1,
                    "line2": line2,
                    "satrec": satrec
                }

        print(f"\n✨ Total satellites loaded with TLE: {len(self.sats)}")

    # ----------------------------------------------------
    # Compute current satellite position (SGP4)
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
            # Propagation error — skip
            return None

        x, y, z = r

        # Convert TEME position to Earth lat/lon/alt
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

            # FULL metadata included!
            "meta": sat["meta"],

            # Keep full TLE too
            "tle": {
                "line1": sat["line1"],
                "line2": sat["line2"]
            }
        }
