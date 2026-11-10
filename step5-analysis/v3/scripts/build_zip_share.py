#!/usr/bin/env python3
"""Build <county>_zip_share.json for build_v3.py from the Census 2020 ZCTA-to-county relationship file.

    python3 build_zip_share.py adams            # writes adams_zip_share.json in this folder
    python3 build_zip_share.py adams 001        # county FIPS given explicitly (3 digits, Colorado)
    python3 build_zip_share.py denver --check   # rebuild and compare with the committed file, write nothing

Share = land area of the ZCTA inside the county / total land area of the ZCTA. That is exactly how
denver_zip_share.json was built (run with --check to confirm). Water area is not counted.

The relationship file is downloaded once to census_cache/ next to this script (6.8 MB, national) and
reused. Standard library only.
"""
import csv
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "census_cache")
REL_URL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt"
REL_FILE = os.path.join(CACHE_DIR, "tab20_zcta520_county20_natl.txt")
STATE_FIPS = "08"  # Colorado

# Colorado county FIPS codes (last three digits). Same values as AIRS_PREFIX in county_configs/.
COLORADO_FIPS = {
    "adams": "001", "alamosa": "003", "arapahoe": "005", "archuleta": "007", "baca": "009", "bent": "011",
    "boulder": "013", "broomfield": "014", "chaffee": "015", "cheyenne": "017", "clear_creek": "019",
    "conejos": "021", "costilla": "023", "crowley": "025", "custer": "027", "delta": "029", "denver": "031",
    "dolores": "033", "douglas": "035", "eagle": "037", "elbert": "039", "el_paso": "041", "fremont": "043",
    "garfield": "045", "gilpin": "047", "grand": "049", "gunnison": "051", "hinsdale": "053", "huerfano": "055",
    "jackson": "057", "jefferson": "059", "kiowa": "061", "kit_carson": "063", "lake": "065", "la_plata": "067",
    "larimer": "069", "las_animas": "071", "lincoln": "073", "logan": "075", "mesa": "077", "mineral": "079",
    "moffat": "081", "montezuma": "083", "montrose": "085", "morgan": "087", "otero": "089", "ouray": "091",
    "park": "093", "phillips": "095", "pitkin": "097", "prowers": "099", "pueblo": "101", "rio_blanco": "103",
    "rio_grande": "105", "routt": "107", "saguache": "109", "san_juan": "111", "san_miguel": "113",
    "sedgwick": "115", "summit": "117", "teller": "119", "washington": "121", "weld": "123", "yuma": "125",
}


def fetch_relationship_file():
    if os.path.exists(REL_FILE) and os.path.getsize(REL_FILE) > 1_000_000:
        return REL_FILE
    os.makedirs(CACHE_DIR, exist_ok=True)
    print("downloading", REL_URL)
    with urllib.request.urlopen(REL_URL, timeout=120) as resp, open(REL_FILE, "wb") as out:
        out.write(resp.read())
    return REL_FILE


def zip_share(county_geoid):
    shares = {}
    with open(fetch_relationship_file(), encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            if row["GEOID_COUNTY_20"] != county_geoid or not row["GEOID_ZCTA5_20"]:
                continue
            total = int(row["AREALAND_ZCTA5_20"])
            if total:
                shares[row["GEOID_ZCTA5_20"]] = int(row["AREALAND_PART"]) / total
    return dict(sorted(shares.items()))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    state = next((a.split("=", 1)[1] for a in argv if a.startswith("--state=")), STATE_FIPS)   # e.g. --state=06 for California; default Colorado
    check = "--check" in argv
    if not args:
        sys.exit(__doc__)
    county = args[0].lower()
    fips3 = args[1] if len(args) > 1 else COLORADO_FIPS.get(county)
    if not fips3:
        sys.exit("unknown county slug %r; pass the 3-digit county FIPS as the second argument" % county)
    shares = zip_share(state + fips3)
    if not shares:
        sys.exit("no ZCTA rows found for county GEOID %s" % (state + fips3))
    out_path = os.path.join(HERE, "%s_zip_share.json" % county)
    whole = sum(1 for v in shares.values() if v >= 0.999)
    print("%s (FIPS %s%s): %d zips, %d wholly inside the county" % (county, state, fips3, len(shares), whole))
    if check:
        if not os.path.exists(out_path):
            sys.exit("nothing to check: %s does not exist" % out_path)
        ref = json.load(open(out_path))
        max_diff = max(abs(shares.get(z, 0) - ref.get(z, 0)) for z in set(ref) | set(shares))
        print("same zip set: %s; max abs diff vs committed file: %.3g" % (set(ref) == set(shares), max_diff))
        return 0 if set(ref) == set(shares) and max_diff < 1e-9 else 1
    if os.path.exists(out_path):
        sys.exit("%s already exists; delete it first if you mean to rebuild it" % out_path)
    with open(out_path, "w") as fh:
        json.dump(shares, fh)
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
