import requests
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from groups import GP_GROUPS


HEADERS = {"User-Agent": "Mozilla/5.0"}


class LiveSatelliteEngine:

    def __init__(self):
        self.meta = {}  # raw metadata JSON
        self.tle = {}   # TLE lines
        self.sat = {}   # Satrec objects
        self.load_all()

    # -------------------------------------------------
    # LOAD JSON + TLE for every group
    # -------------------------------------------------
    def load_all(self):

        for group, url in GP_GROUPS.items():

            print(f"\n📡 Loading group: {group}")

            # --- Load GP JSON metadata ---
            try:
                data = requests.get(url, headers=HEADERS, timeout=20).json()
            except Exception as e:
                print("❌ Could not load metadata:", e)
                continue

            print(f"✔ Loaded {len(data)} metadata")

            for entry in data:
                norad = int(entry["NORAD_CAT_ID"])

                # Add group information into metadata
                entry["GROUP"] = group
                self.meta[norad] = entry

                # ----------------------------------------
                # Load TLE for each NORAD
                # ----------------------------------------
                tle_url = f"https://celestrak.org/NORAD/elements/tle.php?CATNR={norad}"

                try:
                    tle_text = requests.get(tle_url, headers=HEADERS, timeout=20).text.strip()
                    lines = tle_text.splitlines()

                    if len(lines) >= 2:
                        line1 = lines[0].strip()
                        line2 = lines[1].strip()
                        self.tle[norad] = {"line1": line1, "line2": line2}

                        # Create Satrec object
                        satrec = Satrec.twoline2rv(line1, line2)
                        self.sat[norad] = satrec

                except Exception:
                    continue

            print(f"✔ Loaded {len(self.tle)} TLE entries")

        print(f"\n✨ TOTAL satellites with valid TLE: {len(self.sat)}\n")

    # -------------------------------------------------
    # COMPUTE LIVE POSITION USING SGP4
    # -------------------------------------------------
    def compute_position(self, norad):

        if norad not in self.sat:
            return None

        sat = self.sat[norad]
        meta = self.meta[norad]
        group = meta["GROUP"]

        # Current UTC timestamp
        t = datetime.now(timezone.utc)

        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute,
                      t.second + t.microsecond / 1e6)

        # Propagate
        e, r, v = sat.sgp4(jd, fr)

        if e != 0:
            return None

        # Convert ECI → lat/lon (simple approximation)
        x, y, z = r
        import math

        lon = math.degrees(math.atan2(y, x))
        hyp = (x * x + y * y) ** 0.5
        lat = math.degrees(math.atan2(z, hyp))

        alt = (x * x + y * y + z * z) ** 0.5 - 6378.137

        return {
            "norad_id": norad,
            "name": meta["OBJECT_NAME"],
            "group": group,
            "lat": lat,
            "lon": lon,
            "alt_km": alt,
            "timestamp": t.isoformat()
        }


