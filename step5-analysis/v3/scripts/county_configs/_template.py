"""County settings for build_v3.py --county <name>. Copy this file to <name>.py (lower case) and fill it in.

Only UPPER_CASE names are read. Do not edit v3_config.py or the points table for a new county.
"""
import re

COUNTY = "Adams"                     # city/county spelling used in the data, title case
COUNTY_FULL = "Adams County"
AIRS_PREFIX = "001"                  # APCD AIRS ID county prefix = county FIPS code (Denver 031, Adams 001, Arapahoe 005, Jefferson 059); check against the APCD file
ZIP_SHARE_FILE = "adams_zip_share.json"   # {zip: share of that zip inside the county}, from the Census 2020 ZCTA-to-county file; lives in this scripts folder
LOCAL_LAYERS = False                 # True only for a county with permit and site plan loaders (today: Denver only)

# Optional, all default to empty:
# WAT_AIRPORT = re.compile(r"...", re.I)   # water permit rows to drop as airport or base
# WAT_AIRPORT_SIC = set()
# WEB_CHECKS = {}; WEB_CHECKS_V3 = {}; WEB_ADDRESS_OK = set(); WEB_DROPS = {}; WEB_NOT_CONFIRMED_V3 = []
# KNOWN_TIES = []                    # Step 3 entity merges
# STEP3_OCCUPIERS = {}               # Step 3 address-to-occupier findings
# GROUND_TRUTH = {}                  # known projects in this county, for the in_ground_truth check
