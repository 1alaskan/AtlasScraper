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

# --------------------------------------------------------------------------- web checks (filled after the first ranked list was read)
# 50 named companies in the first ranked list's top 50 were searched on 2026-10-30 (two searches each; see adams/webcheck_top50_notes.md).
# 31 returned a usable page and are recorded here; 19 did not and keep the fit the records give them (WEB_NOT_CONFIRMED_V3).
# No site was shown to be outside Adams County, so WEB_DROPS is empty. Two to watch: Claremont Foods (production site unconfirmed) and
# Kelley Trucking (HQ in Jefferson County; the Adams record is a gravel pit).
WEB_CHECKS = {
    'ARDENT MILLS': ('strong', 'Flour mill in Commerce City; company site (web check 2026-10-30) describes an equipment update and capacity expansion, groundbreaking summer 2024, completion targeted end of 2026.'),
    'FORGE NANO': ('strong', 'Builds atomic layer deposition coating equipment on site and runs daily lab experiments at a 40,000 sq ft Thornton facility; trade press (web check 2026-10-30).'),
    'TRUSTILE DOORS': ('strong', 'Manufactures architectural MDF doors at 1111 E 71st Ave (Denver mailing address, zip 80229); trade directory (web check 2026-10-30).'),
    'DA PACKAGING': ('strong', 'Contract blending and packaging of lubricants and industrial fluids at the former Crystal Packaging plant in Henderson; trade press (web check 2026-10-30).'),
    'CITY OF WESTMINSTER': ('weak', 'Municipal wastewater treatment plant (Big Dry Creek facility) at 13150 Huron St; city website (web check 2026-10-30). Public utility, not production.'),
    'S AND W PRECISION MACHINING': ('strong', 'CNC job shop in Commerce City: vertical milling, turning, 5-axis, live tooling, sawing, assembly, AS9100; trade directory (web check 2026-10-30).'),
    'QUIKRETE DENVER': ('strong', 'Manufactures packaged cement mortars, grouts, stucco and waterproofing products at 2660 W 64th Ave (zip 80221); trade directory (web check 2026-10-30).'),
    'PRETRED': ('strong', 'Processes end-of-life tires and manufactures recycled-rubber road barriers in a 152,000 sq ft Aurora plant at Denali Logistics Park; local EDC press (web check 2026-10-30).'),
    'CLAREMONT FOODS': ('moderate', 'Contract food manufacturer and packer (gluten-free, organic, kosher); trade blog and 2012 local press which placed its plant near Niwot (web check 2026-10-30). Westminster site unconfirmed.'),
    'WESTERN INDUSTRIAL CONTRACTORS': ('moderate', 'Construction contractor installing material handling and mechanical systems in client plants, HQ 14805 E Moncrieff Pl Aurora; business directory (web check 2026-10-30). Own shop work unconfirmed.'),
    'CANDO RAIL AND TERMINALS': ('weak', 'Rail transload and tank car cleaning terminal (Savage Irondale) at 9101 Yosemite St, Henderson; rail services directory (web check 2026-10-30). Logistics, not production.'),
    'COBLACO SERVICES': ('strong', 'Industrial coatings firm: surface prep, media blasting, high-performance coatings, pipeline coating and lining, at 11905 E 124th Ave Henderson; business directory (web check 2026-10-30).'),
    'DENVER MACHINE SHOP': ('moderate', 'Listed as a machine shop and apprenticeship sponsor at 9762 Hanover Ct E, Henderson; training directory (web check 2026-10-30). Shop work not described on page.'),
    'CNC PROS COLORADO': ('weak', 'CNC machine tool dealer offering a range of machine tools in the Southwest; trade press (web check 2026-10-30). Distributor, not a production shop.'),
    'H AND H ENTERPRISES H AND H METALS': ('strong', 'Sheet metal fabrication: laser cutting, bending, welding, punching, routing, sawing for Denver metro; company site (web check 2026-10-30). Address not on page.'),
    'CARLISLE EPS HOLDING': ('strong', 'Insulfoam plant making EPS foam board insulation and insulated sheathing at 12601 E 33rd Ave Unit 110, Aurora; trade directory (web check 2026-10-30).'),
    'MCCALLIN STEEL STORAGE SYSTEMS': ('strong', 'Manufactures racking and conveyor systems for steel service centers, based in Commerce City; trade press (web check 2026-10-30).'),
    'VEOLIA ES TECHNICAL SOLUTIONS': ('strong', '24/7 solvent recycling plant in Henderson: fractional distillation, tank blending, rail handling; new larger column added; company site (web check 2026-10-30).'),
    'PROTOCAST': ('strong', 'Foundry and machine shop casting aluminum, magnesium and zinc (investment, sand, permanent mold, die) at 3900 E 68th Ave, Commerce City; business directory (web check 2026-10-30).'),
    'RUSH ENTERPRISES': ('moderate', 'Truck dealership at 6955 E 50th Ave, Commerce City, with on-site collision center and heated paint booth; company site (web check 2026-10-30). Service shop air, not production.'),
    'ALLIED DEMOLITION': ('weak', 'Demolition fill and C&D recycling yard accepting concrete, asphalt, brick and wood at 7901 Hwy 85, Commerce City; waste directory (web check 2026-10-30). Mobile crushing, no plant air.'),
    'SWARCO COLORADO PAINT': ('strong', 'Manufactures waterborne and solventborne traffic paints and plural-component systems in an automated plant at 2851 Walden St, Aurora; company site (web check 2026-10-30).'),
    'SASHCO': ('strong', 'Manufactures acrylic latex and rubber-based joint sealants at 14802 Grant St, Thornton; trade directory (web check 2026-10-30).'),
    'METRO WATER RECOVERY': ('weak', 'Regional wastewater treatment plant (Robert W. Hite facility) at 6450 York St; industry directory (web check 2026-10-30). Public utility, not production.'),
    'BENNETT CREEK RANCH': ('weak', 'Thornburg Pit sand and gravel mine, 78 acres near Bennett, excavation and haul-off only; Adams County permit filing (web check 2026-10-30).'),
    'MARINI DIESEL': ('moderate', 'Heavy-duty parts distributor in Commerce City with engine machine shop, flywheel resurfacing, driveline and DPF cleaning; trade press (web check 2026-10-30).'),
    'KELLEY TRUCKING': ('weak', 'Heavy construction, hauling and mine stripping contractor with portable crushing, HQ Golden; the Adams site is a gravel mine; industry directory (web check 2026-10-30).'),
    'AGFINITY': ('weak', 'Agricultural cooperative; Brighton location is an agronomy sales base for crop inputs; job listing and local press (web check 2026-10-30). Not production.'),
    'INTERTAPE POLYMER': ('moderate', 'IPG lists 1095 S 4th Ave, Brighton as a company location; tapes and films maker but site products not stated; company site (web check 2026-10-30).'),
    'MILL ROCK PACKAGING': ('strong', 'All Packaging Company, a Mill Rock unit, makes printed paperboard folding cartons at its Aurora plant; trade press (web check 2026-10-30).'),
    'VEXOR CUSTOM WOODWORKING TOOLS': ('strong', 'Family-owned Denver maker of custom cutting tools, router bits and shaper cutters for over 30 years; trade press (web check 2026-10-30).'),
}
WEB_NOT_CONFIRMED_V3 = ['KAIRUS', 'VALHALLA INDUSTRIES', 'WARD PRECISION MANUFACTURING', 'GINZEL ENTERPRISES', 'DURALUX FINISH', 'GENESEE WESTER', 'IMPERIAL MACHINING', 'DG METAL', 'SKYLINE MOTORS', 'AGOV UNDERGROUND', 'DURANGO TIRE SHOP', 'FLASHFILL SERVICES', 'CRYOSHIELD INDUSTRIAL SERVICES', 'MT UNDERGROUND', 'HOLCIM WCR', 'CHERRY CREEK RECYCLING', 'QUATTRO MACHINING SERVICES', 'MECHFI DESIGNS', 'HARRELSON']
WEB_DROPS = {}
WEB_ADDRESS_OK = set()
WEB_CHECKS_V3 = {}

# --------------------------------------------------------------------------- ties carried over from Step 3 (not from the scraped files)
# Kairus Inc is the entity behind the Philip Morris (PMI U.S.) ZYN plant: the Step 2 back-test found Kairus Inc as the grantee of the
# 148-acre Adams County parcel at 25301 to 25315 E 48th Ave (parcel 0181917301001), as the company on the Adams County incentive
# agreement of 2024-07-09 (PrimeGov), and the state water permit at 25315 E 48th Ave carries SIC 2131 (chewing and smoking tobacco).
# Aurora's permits at that address are filed as "Project Waterfall". See step3-validation/adams/validation_adams_notes.md.
KNOWN_TIES = [
    {"name_key": "KAIRUS", "addr_keys": ["25315 E 48", "25301 E 48"],
     "display": "Philip Morris International, PMI U.S. ZYN plant (Kairus Inc), Aurora (Adams County)",
     "note": "tied to Philip Morris / PMI U.S. by the Step 2 back-test: Kairus Inc holds the parcel, signed the Adams County incentive agreement and is the water permit operator at 25315 E 48th Ave"},
]
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
    "C22 Philip Morris ZYN campus": (["PHILIP MORRIS", "SWEDISH MATCH", "PMI US", "PMI U S", "KAIRUS"], ["25315 E 48", "25301 E 48"]),
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
