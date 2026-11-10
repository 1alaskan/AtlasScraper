#!/usr/bin/env python3
"""Alameda County, California config for the v3 build. First California county (2026-11-10).

Run against step4-scrape/california/v3_inputs/alameda (made by step4-scrape/california/scripts/build_v3_inputs.py), not against
step4-scrape. The points table, word lists and fit rules are the Colorado ones, unchanged. What differs is which sources exist:
California has no machinery-lien, registration, air permit or press layer yet, so this build scores stormwater enrolments and
named state incentive awards only. Nothing here was tuned to any known project.
"""
import re
from v3_lib import WAT, INC

COUNTY = "Alameda"
COUNTY_FULL = "Alameda County"
AIRS_PREFIX = "001"                       # county FIPS 06001; unused (no California air permit layer yet) but required by the loader
ZIP_SHARE_FILE = "ca_alameda_zip_share.json"   # python3 build_zip_share.py ca_alameda 001 --state=06
LOCAL_LAYERS = False                      # no city permit or planning pulls yet

# Every incorporated city and the main unincorporated communities sit wholly inside the county.
MAIL_CITIES = {"ALAMEDA", "ALBANY", "BERKELEY", "DUBLIN", "EMERYVILLE", "FREMONT", "HAYWARD", "LIVERMORE", "NEWARK", "OAKLAND", "PIEDMONT",
               "PLEASANTON", "SAN LEANDRO", "UNION CITY", "CASTRO VALLEY", "SAN LORENZO", "SUNOL"}

# California source names and wording (hooks added 2026-11-10; the defaults are the Colorado names)
SOURCE_LABELS = {WAT: "California stormwater enrolments (SMARTS)", INC: "California incentive awards (California Competes, CAEATFA)"}
WAT_DATE_WORD = "processed"
INCENTIVE_WORDING = "California state incentive award"
INCENTIVE_CITY_ONLY_OK = True             # Matthew, 2026-11-10: score the awards. They name the city, not the street address.
LOCAL_INCENTIVE_FILES = ["ca_incentive_awards.csv"]   # single-city awards only; multi-site awards are a side list and are not scored

# Water record types in the adapter file
OPERATING_WATER = ("CA IGP", "CA NEC")
CONSTRUCTION_WATER = ("CA CGP",)
WAT_AIRPORT = re.compile(r"oakland (?:international )?airport|\bOAK\b|port of oakland|airport dr", re.I)   # local cut: airport and seaport works

PERSON_NAMED = set()
GROUND_TRUTH = {}
