#!/usr/bin/env python3
"""Denver County config for the v3 build: everything that is specific to Denver and not to the method.

Scope, the Denver-only noise cut, the web checks carried over from the first run, the two Step 3 ties and the 17 ground-truth
projects. The general word lists, the points table and the fit rules stay in v3_config.py and are the same for every county.
Nothing here was tuned to the ground truth.
"""
import re

COUNTY = "Denver"                       # as it appears in city and county columns (upper-cased for matching)
COUNTY_FULL = "Denver County"           # as the Census geocoder names it
AIRS_PREFIX = "031"                     # APCD AIRS ID county prefix
ZIP_SHARE_FILE = "denver_zip_share.json"  # share of each zip inside the county (Census 2020 ZCTA file), in the scripts folder
LOCAL_LAYERS = True                     # Denver permit and site plan layers exist (county sources from Step 3/4)

# County-specific noise cut for state water permits: airport construction and airline facilities at DEN
WAT_AIRPORT = re.compile(r"\bDEN\b|\bDIA\b|airport|pe[nñ]a\b|taxiway|taxilane|concourse|worldport|airlines?\b|aircraft|cargo facility|"
                         r"general use building|fuel facility|jet expansion", re.I)
WAT_AIRPORT_SIC = {"4581", "4512", "4513"}

# --------------------------------------------------------------------------- web checks carried over from the first run (2026-10-10)
# key: name key (v3_lib.nk). value: (fit level, text). These are kept as they were written; none was re-checked in this run.
WEB_CHECKS = {
    "CONAGRA FOODS PACKAGED FOODS": ("strong", "gluten-free bakery (bread, buns, bagels) at this address (web check 2026-10-10, company careers page)"),
    "KING SOOPERS": ("strong", "bakery plant at 60 Yuma St (web check 2026-10-10, baking trade directory)"),
    "QUALITY LININGS AND PAINTING": ("strong", "industrial lining and coating contractor (web check 2026-10-10); paint booth on the air permit, SIC 3479 on the water permit"),
    "DAWN FOOD PRODUCTS": ("strong", "bakery mix manufacturing at 4500 Lipan St (web check 2026-10-10, baking trade directory)"),
    "NESTLE PURINA PETCARE": ("strong", "pet food factory, 350+ employees (web check 2026-10-10, local press)"),
    "CARGILL": ("strong", "animal feed mill with packing lines, acquired 2024 (web check 2026-10-10, company release; street address not confirmed by that page)"),
    "TITAN FITTINGS": ("strong", "makes stainless fittings, valves and hose assemblies with in-house CNC machining (web check 2026-10-10, company site)"),
    "FRITO LAY": ("strong", "snack and tortilla production at this address (web check 2026-10-10, baking trade directory)"),
    "AMCOR RIGID PACKAGING": ("strong", "rigid plastic bottle and container maker (web check 2026-10-10, company level); SIC 3086 on the water permit; Denver site itself not confirmed on the web"),
    "BLAZY SUSAN": ("moderate", "smoking accessories brand (web check 2026-10-10); filings show a packaging line and CNC equipment, so some on-site packing is likely but not confirmed"),
    "BIG METAL ADDITIVE": ("strong", "large-format metal additive manufacturing plus CNC machining (web check 2026-10-10); street address not confirmed by that page"),
    "INTERTECH PLASTICS": ("strong", "custom injection moulder, 50+ machines (web check 2026-10-10, industry directory)"),
    "NEVER SUMMER INDUSTRIES": ("strong", "snowboard and ski factory in Denver (web check 2026-10-10); street address not confirmed by that page"),
    "VASQUEZ READY MIX": ("moderate", "ready-mix concrete batch plant (web check 2026-10-10); batch plants use air for silos and gates, modest demand"),
    "303 AUTO CARE": ("moderate", "oil change and vehicle service shop (web check 2026-10-10); small shop air"),
    "ELECTRIC EQUIPMENT AND ENGINEERING": ("strong", "makes switchboards, load centres and electrical controls (web check 2026-10-10, Thomasnet)"),
    "COLORADO PREFARE FOODS": ("moderate", "meal kit kitchen at 4823 Lima St (web check 2026-10-10, business listing)"),
    "HOLCIM WCR": ("moderate", "concrete batch plant on the air permit; modest air demand; web check did not confirm the site"),
    "GUYS FLOOR SERVICE": ("moderate", "flooring and carpet dealer (web check 2026-10-10); the filing is for a stone-cutting robot, so some fabrication"),
    "KOKOPELLI OUTDOOR": ("weak", "headquarters office and retail store, no manufacturing on site (web check 2026-10-10, BusinessDen); the financed injection mould is probably at a contract maker"),
    "VEXOR CUSTOM WOODWORKING TOOLS": ("strong", "makes custom woodworking cutting tools, in-house lathe and milling (web check 2026-10-10, trade press)"),
    "CNC PROS COLORADO": ("weak", "machine tool distributor, not a manufacturer (web check 2026-10-10); the filing is a consigned demo machine"),
}
# Street addresses the first run showed on the strength of its web check (the address has no suite and is in no site-based source).
WEB_ADDRESS_OK = {"INTERTECH PLASTICS", "DENCOL SUPPLY", "303 AUTO CARE", "GUYS FLOOR SERVICE",
                  "DIRECT POLYMERS"}          # Direct Polymers: address confirmed by the 2026-10-11 check (trade directory)
# Dropped after the first run's web check: the production site is outside Denver County.
WEB_DROPS = {
    "VALOR PEAK DISTILLERY": "web check 2026-10-10: the distillery is in Longmont",
    "BRON TAPES HOLDINGS": "web check 2026-10-10: the new site is in Centennial",
}
# Added in this run (v3) for named companies in the new top 50 that had no check. Filled by the 2026-10-11 searches; see analysis_notes_v3.md.
WEB_CHECKS_V3 = {
    "ACME MANUFACTURING": ("strong", "maker of metal products: threaded rod, chain, landscape edging, door hardware; headquartered in Denver "
                                     "(web check 2026-10-11, company site; street address not confirmed by that page)"),
    "DIRECT POLYMERS": ("strong", "plastics recycling plant producing flakes and pellets at 3601 E 44th Ave (web check 2026-10-11, recycling trade directory)"),
}
# Searched on 2026-10-11 with no usable result; fit stays on the records alone.
WEB_NOT_CONFIRMED_V3 = ["VERDE PRICKLY PEAR"]

# --------------------------------------------------------------------------- ties carried over from Step 3 (not from the scraped files)
# PepsiCo: the Step 3 back-test found the plant permits filed under 19301 E 70th Ave and the air permit under 19300 E 72nd Ave.
KNOWN_TIES = [
    {"name_key": "CB MANUFACTURING", "addr_keys": ["19301 E 70"],
     "display": "PepsiCo Beverages North America (CB Manufacturing Company, Inc.), High Point plant",
     "note": "tied to PepsiCo / CB Manufacturing by the Step 3 back-test: plant permits are filed under 19301 E 70th Ave, the air permit under 19300 E 72nd Ave"},
]
# An occupier named in a Step 3 record. The row stays an address row; only its label and fit come from Step 3.
STEP3_OCCUPIERS = {
    "4301 FOREST": {
        "display": "Safeway milk plant (occupier named in a Step 3 record, not in the scraped files)",
        "fit": ("strong", "dairy processing plant; a 2025 city application at this address is named 'Safeway Milk Plant - Compressor Building Addition' "
                          "(Step 3 notes). The compressors may be refrigeration, not air"),
        "confidence": "address confirmed; occupier from a Step 3 record, not from the scraped files",
    },
}

# --------------------------------------------------------------------------- the 17 Denver ground-truth projects (names, aliases, addresses)
GROUND_TRUTH = {
    "D01 PepsiCo": (["PEPSI", "CB MANUFACTURING"], ["19300 E 72", "19301 E 70", "7190 TOWER", "6972 ARGONNE", "3801 BRIGHTON"]),
    "D02 Swire Coca-Cola (cancelled)": (["SWIRE COCA", "COCA COLA"], ["3825 YORK"]),
    "D03 4 Noses Brewing": (["4 NOSES", "FOUR NOSES", "4NB HOLDINGS"], ["4040 DAHLIA"]),
    "D04 Wilding Brands Canworks": (["WILDING BRANDS", "DENVER BEER"], ["4455 JASON"]),
    "D06 Full Frame Beer": (["FULL FRAME BEER"], ["1139 20"]),
    "D07 BrewDog Denver": (["BREWDOG"], ["3950 WYNKOOP"]),
    "D08 Monolith Brewing": (["MONOLITH BREW"], ["1290 S BROADWAY"]),
    "D09 Cheetah Coalition": (["CHEETAH COALITION", "GOLDSPOT", "FLOWER SHOP BEER", "NEON BUZZ"], ["4970 LOWELL"]),
    "D10 Rebel Bread": (["REBEL BREAD"], ["675 S BROADWAY"]),
    "D11 Elemental Bakery": (["ELEMENTAL BAKERY"], ["3875 STEELE"]),
    "D12 Azure Printed Homes": (["AZURE PRINTED"], []),
    "D13 Vinyl Me Please plant": (["VINYL ME PLEASE", "VINYL MEDIA PRESSING"], ["4201 BRIGHTON"]),
    "D14 SRM Concrete": (["SRM CONCRETE", "SMYRNA READY MIX"], ["5150 BRIGHTON", "1145 QUIVAS"]),
    "D15 Maybell Quantum": (["MAYBELL QUANTUM"], ["3821 STEELE"]),
    "X06 NextRun hub (Direct Polymers)": (["DIRECT POLYMERS", "NEXTRUN"], ["3600 E 45", "3601 E 44"]),
    "X12 Crazy Shirts": (["CRAZY SHIRTS"], ["4747 IVY"]),
    "X13 Sara Gabriel": (["SARA GABRIEL"], ["1325 S INCA"]),
}
