GP_GROUPS = {
    "last-30-days": "last-30-days",
    "stations": "stations",
    "active": "active",
    "weather": "weather",
    "resource": "resource",
    "dmc": "dmc",
    "intelsat": "intelsat",
    "eutelsat": "eutelsat",
    "starlink": "starlink",
    "gnss": "gnss",
    "gps-ops": "gps-ops",
    "glo-ops": "glo-ops",
    "galileo": "galileo",
    "beidou": "beidou",
    "nnss": "nnss",
    "musson": "musson",
    "cosmos-1408-debris": "cosmos-1408-debris",
    "fengyun-1c-debris": "fengyun-1c-debris",
    "iridium-33-debris": "iridium-33-debris",
    "cosmos-2251-debris": "cosmos-2251-debris"
}

def gp_json_url(group):
    return f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=json"

def tle_url(group):
    return f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
