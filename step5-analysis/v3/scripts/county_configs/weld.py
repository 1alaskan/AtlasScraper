#!/usr/bin/env python3
"""Weld County config for the v3 build: everything that is specific to Weld County and not to the method.

Scope, the local noise cuts, web checks (filled after the first ranked list is read), Step 3 ties and the ground-truth projects
with county Weld in the Step 3 overlay. The general word lists, the points table and the fit rules stay in v3_config.py and are
the same for every county. Nothing here was tuned to the ground truth.

Written 2026-11-05 for the first Weld run. LOCAL_LAYERS starts False (first pass without county layers); the Step 3 county files
are added once the Weld scrape step has finished.
"""
import re

COUNTY = "Weld"                           # as it appears in the county columns (upper-cased for matching)
COUNTY_FULL = "Weld County"               # as the Census geocoder names it
AIRS_PREFIX = "123"                       # APCD AIRS ID county prefix = FIPS 08123 (checked 2026-11-05: 712 rows carry 123 with county Weld, 27 carry 123 with county Denver (office address), 12 portable sources say Weld)
ZIP_SHARE_FILE = "weld_zip_share.json"    # share of each zip inside the county (Census 2020 ZCTA file), in the scripts folder; built 2026-11-05 by build_zip_share.py (43 zips, 26 wholly inside)
LOCAL_LAYERS = True                       # Weld Step 3 files (pulled 2026-11-06), read through v3_local.py; first pass was run with False
LOCAL_PERMIT_FILES = ["weld/scrape_frederick_building_permits.csv"]
LOCAL_PLAN_FILES = ["weld/scrape_weld_county_planning_cases.csv", "weld/scrape_weld_county_site_plan_reviews.csv",
                    "weld/scrape_frederick_development_applications.csv", "weld/scrape_greeley_trakit_projects.csv",
                    "weld/scrape_fort_lupton_planning_projects.csv"]
LOCAL_PERMIT_LABEL = "Weld county permits (Frederick)"
LOCAL_PLAN_LABEL = "Weld county planning cases"
# No slot in the method (Matthew's decision 2026-11-06, side list): weld/scrape_weld_incentive_agreements.csv,
# weld/scrape_weld_county_property_sales.csv, weld/scrape_weld_county_personal_property_accounts.csv.

# Mailing cities. Weld County has no city of that name, so the mailing-city tests use these sets.
# MAIL_CITIES: mailing cities that sit wholly (or nearly wholly) inside Weld County. A row with one of these and no usable zip or
#   geocoder result is kept as "county unconfirmed".
# SPLIT_CITIES: mailing cities that straddle the county line (Windsor, Johnstown and Berthoud with Larimer; Erie and Longmont with
#   Boulder; Brighton, Lochbuie, Thornton and Northglenn with Adams) or whose mailing area reaches into unincorporated Weld (Fort Collins,
#   Loveland, Boulder, Broomfield). Their rows are placed by zip share and the Census geocoder only.
MAIL_CITIES = {"GREELEY", "EVANS", "FORT LUPTON", "FT LUPTON", "FT. LUPTON", "FREDERICK", "FIRESTONE", "DACONO", "MILLIKEN",
               "PLATTEVILLE", "MEAD", "HUDSON", "KEENESBURG", "KERSEY", "LASALLE", "LA SALLE", "SEVERANCE", "EATON", "AULT",
               "GILCREST", "GARDEN CITY", "PIERCE", "NUNN", "GROVER", "GILL", "GALETON", "BRIGGSDALE", "NEW RAYMER", "RAYMER",
               "STONEHAM", "HEREFORD", "CARR", "LUCERNE", "WATTENBERG", "ROGGEN", "UNINC", "UNINC WELD COUNTY", "WELD COUNTY", "WELD"}
SPLIT_CITIES = {"WINDSOR", "JOHNSTOWN", "BERTHOUD", "ERIE", "LONGMONT", "BRIGHTON", "LOCHBUIE", "THORNTON", "NORTHGLENN",
                "FORT COLLINS", "FT COLLINS", "LOVELAND", "BOULDER", "BROOMFIELD", "LAFAYETTE"}

# County-specific noise cut for state water permits: airports and airline facilities. Weld County has the Greeley-Weld County Airport,
# Erie Municipal Airport, Platte Valley Airpark (Hudson) and Fort Lupton's small airfield.
WAT_AIRPORT = re.compile(r"airport\b(?! blvd| boulevard| rd| road)|airpark|taxiway|taxilane|runway|airlines?\b|aircraft|hangar", re.I)
WAT_AIRPORT_SIC = {"4581", "4512", "4513"}

# --------------------------------------------------------------------------- web checks (filled after the first ranked list is read)
WEB_CHECKS = {}
WEB_NOT_CONFIRMED_V3 = []
WEB_DROPS = {}
WEB_ADDRESS_OK = set()
PERSON_NAMED = set()
WEB_CHECKS_V3 = {}

# --------------------------------------------------------------------------- ties carried over from Step 3 (not from the scraped files)
KNOWN_TIES = []
STEP3_OCCUPIERS = {}

# --------------------------------------------------------------------------- the Weld County ground-truth projects (names, aliases, addresses)
# From step3-validation/ground_truth_overlay.csv, county_clean = Weld (6 projects, one of them a best guess). Addresses are the ones the
# ground truth, the Step 4 statewide notes and the Weld back-test recorded; none was tuned here.
GROUND_TRUTH = {
    "C34 Colorado Premium": (["COLORADO PREMIUM"], ["2400 W 29"]),
    "C35 Hirsh Precision": (["HIRSH PRECISION"], []),
    "C36 Sphere Renewables": (["SPHERE RENEWABLES"], ["13516 CR 8", "13516 COUNTY ROAD 8", "13516 WCR 8"]),
    "X26 Agilent (Frederick expansion)": (["AGILENT"], []),
    "X27 Microvast (Windsor, consolidated away; county unconfirmed)": (["MICROVAST"], []),
    "X28 TFP Nutrition": (["TFP NUTRITION", "TEXAS FARM PRODUCTS", "J D HEISKELL", "JD HEISKELL"], ["450 N FRONT"]),
}
