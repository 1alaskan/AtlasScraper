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
LOCAL_DESC_USE_HOLD = True                # hold tier A permits whose description says retail, mercantile, well pad etc. (Frederick carries no valuation or use field)
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
# Web checks on the top 60 of the first county-layer build (2026-11-06): fit confirmed for 42 rows; see step5-analysis/weld/web_checks_weld.md.
WEB_CHECKS = {
    'AGILENT TECHNOLOGIES US': ('strong', 'Pharmaceutical manufacturing (therapeutic nucleic acids: siRNA, antisense, CRISPR guide RNA) at the Frederick site, with a $725M manufacturing expansion under way; trade press (web check 2026-11-06).'),
    'J 2 CONTRACTING': ('weak', 'Sand and gravel pit operated by J-2 Contracting adjacent to Greeley city limits and 8th Street in Weld County, no plant described; state DRMS permit file M2023001 (web check 2026-11-06).'),
    'ASPHALT SPECIALTIES': ('weak', 'Family-owned heavy highway paving contractor; the ranked site is its Marcovich sand and gravel pit on US-85 and no asphalt plant at that site was confirmed; government vendor profile plus state air permit text (web check 2026-11-06).'),
    'USRL HUDSON': ('weak', 'Rail-served transload terminal at 2001 LCH Ave, Hudson, handling dry bulk, liquids and refined fuels (gasoline loading units); transload directory and job postings (web check 2026-11-06).'),
    'BOULDER SCIENTIFIC': ('strong', 'Specialty chemical and organometallic catalyst production plant at Specialty Place, Mead, one of the company two Colorado production sites; trade press plus state air permit naming catalyst manufacturing (web check 2026-11-06).'),
    'SCHLOSSER SIGNS': ('moderate', 'Designs, manufactures and installs commercial signs with in-house fabrication and a new paint booth, CNC router not confirmed on the web; company press release and Blue Book manufacturer listing (web check 2026-11-06).'),
    'RAPTOR MATERIALS': ('moderate', 'Sand, gravel and ready-mix concrete supplier; the Highway 66 site is its pit and ready-mix plant with screens on the air permit; Blue Book supplier profile plus state permits (web check 2026-11-06).'),
    'URSA MAJOR TECHNOLOGIES': ('strong', 'Rocket engine manufacturing, additive manufacturing and test at the 90-acre former Ball site at 19750 Weld County Road 7, Berthoud; trade press (BizWest) (web check 2026-11-06).'),
    'SVW FARMS': ('weak', 'Farm operator whose site is the Hunt Farms dirt mine south-east of Gilcrest, stripping topsoil and overburden for oil and gas reclamation with no processing equipment; state DRMS inspection M2021030 (web check 2026-11-06).'),
    'OLD SCHOOL INDUSTRIES': ('strong', 'Job machine shop in Dacono financing new DMG Mori and Brother CNC machining centers; NAICS machine-shop directory listing (web check 2026-11-06).'),
    'HIGH PLAINS STEEL SERVICES': ('strong', 'Structural steel fabricator and metal service center at 2055 Howard Smith Ave, Windsor, hiring fitter-welders and ironworkers; NAICS directory, job postings and Blue Book structural steel fabricator listing (web check 2026-11-06).'),
    'CEA GREELY': ('weak', 'Dairy anaerobic digester producing renewable natural gas at Morwai and Longs Peak dairies, per the state air permit; no company web page found (web check 2026-11-06).'),
    'PERFORMANCE EQUIPMENT SALES': ('moderate', 'Heavy construction equipment sales and rental dealer with a service operation at 2114 E I-25 Frontage Rd, Erie (east of I-25, Weld side), financing a service truck with a Vanair compressor; NAICS directory and company site (web check 2026-11-06).'),
    'CANDO RAIL AND TERMINALS': ('weak', 'Rail transload terminal (former Savage Rail, acquired by Cando) at the Great Western Industrial Park, Windsor, handling drilling-related and agricultural products; company transload page (web check 2026-11-06).'),
    'BURNCO COLORADO': ('moderate', 'Ready-mix concrete and aggregates producer (Westminster HQ) with a Windsor terminal concrete batch plant at 31005 Great Western Drive per the state air permit; Blue Book profile (web check 2026-11-06).'),
    'PIONEER PRESS OF GREELEY': ('strong', 'Commercial printing plant at 2965 27th Ave, Greeley, with a state air permit for printing and a new Sharp production press; chamber directory listing (web check 2026-11-06).'),
    'BLACK LABEL SERVICES': ('moderate', 'Oil and gas pipeline and related structures construction contractor (about 88 staff) with its own fabrication yard at 629 Gyrfalcon Ct, Windsor, financing a CNC plasma table and press brake; NAICS directory (web check 2026-11-06).'),
    'SCOTTS MIRACLE GRO': ('moderate', 'Hyponex (Scotts) mulch and soil processing and bagging plant at County Road 39, Hudson, per the state air and water permits; web search found no page for this plant (web check 2026-11-06).'),
    'SWIFT BEEF': ('strong', 'JBS beef slaughter and processing plant at 800 N 8th Ave, Greeley; USDA FSIS inspected establishment record (web check 2026-11-06).'),
    'WASTE MANAGEMENT DISPOSAL SERVICES OF COLORADO': ('weak', 'North Weld Landfill, a sanitary landfill at 40000 County Road 25, Ault; Waste Management location page and Weld County news (web check 2026-11-06).'),
    'COLORADO SAND': ('weak', 'Keenesburg No. 2 sand mine, about 3 miles north-east of Keenesburg in Weld County, extraction with screening only; state DRMS inspection M2019058 (web check 2026-11-06).'),
    'STERICYCLE': ('weak', 'Medical waste treatment and transfer plant in Dacono (plant associate roles, listed on the Weld County commercial solid waste facility list); company careers page and county list (web check 2026-11-06).'),
    'AGFINITY': ('weak', 'Farm cooperative bulk fuel and propane plant at Lucerne (an EPA risk management plan facility), not a processing plant; EPA RMP facility record and state air permit (web check 2026-11-06).'),
    'JW FABRICATION': ('strong', 'Metal fabrication shop in Ault building metal products from drawings with welding machines, press brakes and machining tools; production welder-fabricator job posting (web check 2026-11-06).'),
    'DESIGNLOGIC': ('strong', 'Precision CNC milling and turning of industrial, heavy equipment and defense parts in Windsor; Thomasnet supplier profile (web check 2026-11-06).'),
    'TV DAIRY': ('weak', 'Dairy operation and dairy wholesaler at 7678 County Rd 17, Fort Lupton, about 28 staff; the chiller in the UCC is milk cooling; NAICS directory (web check 2026-11-06).'),
    'CUTTING EDGE STEEL': ('strong', 'Fabricated structural metal manufacturer and laser processor (AS9100D, ISO 9001) at 101 Miller Dr, Dacono, about 72 staff, adding a Trumpf machine and cobot welder; NAICS directory and manufacturer directory (web check 2026-11-06).'),
    'PNEU LINE SUPPLY': ('strong', 'Injection molder (Class 7 cleanroom) and assembler of plastic fluidic and pneumatic components for medical and industrial customers in Greeley, adding a Nissei 55 ton press; company capabilities page (web check 2026-11-06).'),
    'CNE CREATIVE ENTERPRISES': ('moderate', 'Product development and consulting firm in Greeley with light fabrication on site (metal bending machine, plastic sheet butt welder in the UCC); City of Greeley business news and NAICS directory (web check 2026-11-06).'),
    'ECLIPSE ENGINEERING': ('strong', 'Engineered seal manufacturer (spring-energized, rotary lip and wear ring seals, machined on CNC lathes) at 2540 S Main St, Erie, about 23 staff; NAICS directory and business listing, but Erie straddles Boulder and Weld and the county of this address was not confirmed (web check 2026-11-06).'),
    'HUNGENBERG PRODUCE': ('moderate', 'Carrot, cabbage and onion grower-packer in Greeley (about 4,000 acres) processing cello and baby carrots with on-site packing; produce trade press (web check 2026-11-06).'),
    'BLACK EAGLE ENERGY SERVICES': ('strong', 'Blackeagle Energy Services fabrication shop in Berthoud building mechanical and structural equipment for energy, water and gas clients, hiring structural welders, with a state air permit for metal parts manufacturing at 230 Commerce Drive; job posting and trade press (web check 2026-11-06).'),
    'ROCK AND RAIL': ('moderate', 'Rail transload terminal at 27486 Weld County Road 13 with a concrete mixing facility and, per the state air permit, an asphalt plant; company operations page (web check 2026-11-06).'),
    'BAY STATE MILLING': ('strong', 'Flour mill and grain elevator at Platteville with shift miller and grain handler jobs; job postings and state air permit for milling and bagging (web check 2026-11-06).'),
    'IDENTITY PET NUTRITION': ('weak', 'Pet food brand headquarters and frozen product distribution in Windsor; products are co-manufactured in Ontario and Quebec, so no production on site; trade press (Pet Food Processing) (web check 2026-11-06).'),
    'WESTERN PROPPANTS': ('weak', 'Frac sand (proppant) supplier with a LaSalle rail terminal haul road on the state air permit; web returned only the trademark record, no plant confirmed (web check 2026-11-06).'),
    'AULT ASPHALT PLANT SITE': ('moderate', 'Connell Resources asphalt plant site per the state water permit (SIC 2951); the web confirms Connell operates asphalt facilities at its pits (Timnath file) but no page for the Ault site was found; state DRMS file (web check 2026-11-06).'),
    'WELD BESS STORAGE': ('weak', 'Battery energy storage construction site; Michels Power is the permittee and contractor, not the occupier, and the web did not confirm which Weld County BESS project this is; NextEra Weld Energy Storage page is a candidate only (web check 2026-11-06).'),
    'AURORA WATER NORTH CAMPUS': ('weak', 'City of Aurora water collector well field (Prairie Waters) near Fort Lupton; Velocity Constructors is the contractor, the City of Aurora is the owner; construction bid listing (web check 2026-11-06).'),
    'SUN MOUNTAIN': ('strong', 'Custom wood door manufacturing plant at 140 Commerce Drive, Berthoud, with a state air permit for wood sanding and coating; manufacturer facility record (BuildingClean) (web check 2026-11-06).'),
    'COVENANT PLUMBING AND HEATING': ('weak', 'Plumbing and heating contractor based in Ault; the compressor in the UCC is part of a pipe-lining system, no shop production; Angi contractor listing (web check 2026-11-06).'),
    'EATON FIRE PROTECTION DISTRICT': ('weak', 'Public fire district in Eaton; the UCC is SCBA breathing-air equipment, not plant air; state local government record and station listing (web check 2026-11-06).'),
}
# Checked, not confirmed in two lookups; the pipeline's own fit stands.
WEB_NOT_CONFIRMED_V3 = ['UNDERGROUND MANUFACTURING', 'QUANTUM JS CANNING', '5507 DISTILLING', 'LOUDWIRE DIESEL', 'JIMS AUTOMOTIVE MACHINE SHOP', 'IMPACT EQUIPMENT RENTALS', 'T AND T GRINDERS', 'LEGACY PIE', 'ABSOLUTE COUNTERTOPS AND MORE', 'BIG THOMPSON COMPOST', 'LIVE SHARP INDUSTRIES', 'SCHOTT MANUFACTURING SOLUTIONS', 'FOUR C SONS', 'J AND B MANUFACTURING', 'KEIBON', 'C SIMPSON FARMS', 'ARC COLORADO']
# Note: v3_signals reads WEB_DROPS on the UCC tier A and Mile High CRE paths only; 5507 Distilling is a tier B lien, so this entry
# records the finding but does not remove the row. It is carried as a flag in the analysis notes instead (no script change for Weld).
WEB_DROPS = {
    "5507 DISTILLING": "web check 2026-11-06: the UCC collateral itself places the distillation equipment on Fifth Street, Loveland (Larimer County); the Weld zip is a mailing address",
}
WEB_ADDRESS_OK = set()
PERSON_NAMED = set()
WEB_CHECKS_V3 = {}

# --------------------------------------------------------------------------- ties carried over from Step 3 (not from the scraped files)
KNOWN_TIES = [
    {"name_key": "HIRSH PRECISION PRODUCTS", "addr_keys": ["4300 GODDING HOLLOW"],
     "display": "Hirsh Precision Products, Inc., Frederick (Weld County)",
     "note": "tied by the Frederick permit layer: HIRSH PRECISION PRODUCTS INC is the business name on the parcel at 4300 Godding Hollow Pkwy (Weld County, Frederick lies wholly in Weld) and the 2022 county incentive agreement names the same address; the Census geocoder could not place the street"},
]
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
