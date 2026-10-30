#!/usr/bin/env python3
"""Adams County config for the v3 build: everything that is specific to Adams County and not to the method.

Scope, the local noise cuts, web checks (filled after the first ranked list was read), Step 3 ties and the ground-truth projects
with county Adams in the Step 3 overlay. The general word lists, the points table and the fit rules stay in v3_config.py and are
the same for every county. Nothing here was tuned to the ground truth.

Written 2026-10-30 for the first Adams run.
"""
import re

COUNTY = "Adams"                          # as it appears in the county columns (upper-cased for matching)
COUNTY_FULL = "Adams County"              # as the Census geocoder names it
AIRS_PREFIX = "001"                       # APCD AIRS ID county prefix = FIPS 08001 (checked: 158 rows carry it, 165 rows say county Adams, 10 of those with another prefix)
ZIP_SHARE_FILE = "adams_zip_share.json"   # share of each zip inside the county (Census 2020 ZCTA file), in the scripts folder; built 2026-10-30 by build_zip_share.py
LOCAL_LAYERS = False                      # no Adams permit or site plan loader yet (the v3 code reads Denver's layers only)

# Mailing cities. Denver is a city and a county, so the Denver config needs none of this. Adams County has no city of that name,
# so the mailing-city tests use these sets instead (v3_config defaults MAIL_CITIES to the county name and SPLIT_CITIES to empty,
# which keeps the Denver build byte-identical; checked 2026-10-30).
# MAIL_CITIES: mailing cities that sit wholly (or nearly wholly) inside Adams County. A row with one of these and no usable zip or
#   geocoder result is kept as "county unconfirmed", exactly as a Denver mailing address is in the Denver build.
# SPLIT_CITIES: mailing cities that straddle the county line (or, for Denver, whose mailing area reaches into unincorporated Adams
#   north of 52nd Ave). Their rows are placed by zip share and the Census geocoder only; a geocoder result outside Adams County drops
#   the row, a no-match keeps it only when the zip is at least half inside the county.
MAIL_CITIES = {"COMMERCE CITY", "BRIGHTON", "THORNTON", "NORTHGLENN", "FEDERAL HEIGHTS", "BENNETT", "LOCHBUIE", "HENDERSON",
               "STRASBURG", "WATKINS", "DUPONT", "EASTLAKE", "UNINC", "UNINC ADAMS COUNTY", "ADAMS COUNTY", "THORRNTON"}
SPLIT_CITIES = {"AURORA", "ARVADA", "WESTMINSTER", "DENVER", "BROOMFIELD"}

# County-specific noise cut for state water permits: airport construction and airline facilities. DEN itself is in Denver County;
# Adams County has the Colorado Air and Space Port (Front Range Airport) near Watkins.
WAT_AIRPORT = re.compile(r"air and space port|air & space port|space ?port|front range airport|front range pkwy|airport\b(?! blvd| boulevard| rd| road)|"
                         r"taxiway|taxilane|runway|airlines?\b|aircraft", re.I)
WAT_AIRPORT_SIC = {"4581", "4512", "4513"}

# --------------------------------------------------------------------------- web checks (filled after the first ranked list was read; see adams_analysis_notes.md)
WEB_CHECKS = {}
WEB_ADDRESS_OK = set()
WEB_DROPS = {}
WEB_CHECKS_V3 = {}
WEB_NOT_CONFIRMED_V3 = []

# --------------------------------------------------------------------------- ties carried over from Step 3 (not from the scraped files)
KNOWN_TIES = []
STEP3_OCCUPIERS = {}

# --------------------------------------------------------------------------- the Adams County ground-truth projects (names, aliases, addresses)
# From step3-validation/ground_truth_overlay.csv, county_clean = Adams (17 projects), plus the four overflow projects whose county is
# "Adams or another" in the overlay. Addresses are the ones the ground truth and the Step 3 back-tests recorded; none was tuned here.
GROUND_TRUTH = {
    "D05 Craft Beverage Warehouse": (["CRAFT BEVERAGE WAREHOUSE"], []),
    "D16 Metro Water Recovery (Hite substation)": (["METRO WATER RECOVERY"], ["6450 YORK"]),
    "D17 Vartega": (["VARTEGA"], ["5675 PECOS"]),
    "C18 CEMCO": (["CEMCO", "CALIFORNIA EXPANDED METAL"], ["9410 HEINZ", "480 OSAGE"]),
    "C19 Prost Brewing": (["PROST BREWING"], ["351 W 104"]),
    "C20 Amprius (cancelled)": (["AMPRIUS"], ["18875 E BROMLEY"]),
    "C21 VSK Energy (cancelled)": (["VSK ENERGY", "VIKRAM SOLAR"], []),
    "C22 Philip Morris ZYN campus": (["PHILIP MORRIS", "SWEDISH MATCH", "PMI US", "PMI U S"], []),
    "C23 Solid Power": (["SOLID POWER"], []),
    "C24 Pretred": (["PRETRED"], ["6550 DENALI"]),
    "C25 RK Industries": (["RK INDUSTRIES", "RK MECHANICAL", "RK MISSION CRITICAL"], ["3301 LEWISTON", "17450 E 32", "3800 XANTHIA"]),
    "X04 Wanderment Brewing": (["WANDERMENT"], ["800 E 64"]),
    "X05 Santa Monica Seafood": (["SANTA MONICA SEAFOOD"], ["1101 E 126"]),
    "X08 Boise Cascade door shop": (["BOISE CASCADE"], ["11011 E 104"]),
    "X11 AMP (AMP Robotics)": (["AMP ROBOTICS"], []),
    "X15 Izzio Bakery": (["IZZIO"], ["15101 GRANT", "15107 GRANT"]),
    "X16 Kiosk Information Systems": (["KIOSK INFORMATION SYSTEMS", "POSIFLEX"], []),
    # county not settled in the overlay (Adams or a neighbour); listed so a hit is reported, not to claim them for Adams
    "X02 Cerebral Brewing (Adams or Arapahoe)": (["CEREBRAL BREWING"], ["9990 E COLFAX"]),
    "X03 Curated Barrel Project (Jefferson or Adams)": (["CURATED BARREL", "CONFLUENCE SPIRITS"], ["5525 W 56"]),
    "X09 Creation Technologies (Adams or Jefferson)": (["CREATION TECHNOLOGIES"], ["1401 W 122"]),
    "X23 Stay Tuned Brewing (Jefferson or Adams)": (["STAY TUNED BREWING"], ["5127 W 64"]),
}
