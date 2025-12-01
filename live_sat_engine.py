import requests
import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP={}&FORMAT=json"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

CELESTRAK_GROUPS = [
    "last-30-days",
    "stations",
    "active",
    "weather",
    "resource",
    "dmc",
    "intelsat",
    "eutelsat",
    "starlink",
    "gnss",
    "gps-ops",
    "glo-ops",
    "galileo",
    "beidou",
    "nnss",
    "musson",
    "cosmos-1408-debris",
    "fengyun-1c-debris",
    "iridium-33-debris",
    "cosmos-2251-debris",
]

def fetch_group(name):
    url = BASE_URL.format(name)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        return r.json()
    except:
        return []

def to_ttle_date(entry):
    dt = datetime.fromisoformat(entry["EPOCH"].replace("Z", ""))
    epoch_year = dt.year % 100
    epoch_day = dt.timetuple().tm_yday + (
        dt.hour / 24 + dt.minute / 1440 + dt.second / 86400
    )
    return epoch_year, epoch_day

def to_tle(entry):
    satnum = int(entry["NORAD_CAT_ID"])
    intl = entry["OBJECT_ID"].replace("-", "")

    epoch_year, epoch_day = to_ttle_date(entry)

    ndot = float(entry["MEAN_MOTION_DOT"])
    nddot = float(entry["MEAN_MOTION_DDOT"])
    bstar = float(entry["BSTAR"])

    line1 = (
        f"1 {satnum:05d}U {intl:8s} "
        f"{epoch_year:02d}{epoch_day:012.8f} "
        f"{ndot: .8f} {nddot: .8f} {bstar: .8f} 0 9999"
    )

    ecc = int(float(entry["ECCENTRICITY"]) * 1e7)

    line2 = (
        f"2 {satnum:05d} "
        f"{float(entry['INCLINATION']):8.4f} "
        f"{float(entry['RA_OF_ASC_NODE']):8.4f} "
        f"{ecc:07d} "
        f"{float(entry['ARG_OF_PERICENTER']):8.4f} "
        f"{float(entry['MEAN_ANOMALY']):8.4f} "
        f"{float(entry['MEAN_MOTION']):11.8f} 0"
    )

    return line1, line2

def compute_position(satrec):
    now = datetime.now(timezone.utc)
    jd, fr = jday(
        now.year, now.month, now.day,
        now.hour, now.minute, now.second
    )
    e, r, v = satrec.sgp4(jd, fr)
    if e != 0:
        return None
    x, y, z = r
    lon = math.degrees(math.atan2(y, x))
    hyp = math.sqrt(x*x + y*y)
    lat = math.degrees(math.atan2(z, hyp))
    alt = math.sqrt(x*x + y*y + z*z) - 6378.137
    return lon, lat, alt, now.isoformat()

