#!/usr/bin/env python3
"""Step 5 v3 fixed inputs that are not in the Step 4 files: word lists for the noise cuts and fit rules, the web checks
carried over from the first run, two ties carried over from Step 3, and the 17 ground-truth projects.

Nothing here was tuned to the ground truth. The ground-truth list is used only by build_v3.gt_match, after ranking, for the in_ground_truth column and the report.
"""
import re

# --------------------------------------------------------------------------- UCC tier A classes
# Compressed air named in the filing (30 points unless a cut or the weak tier applies first).
UCC_AIR = re.compile(r"compressor|compressed air|atlas copco|ingersoll rand|sullair|kaeser|gardner denver|quincy|air dryer", re.I)
# Production machinery (25 points). Matched on the Step 4 flag words and on the visible collateral text.
UCC_MACH = re.compile(
    r"\bcnc\b|machining cent(?:er|re)|\blathe|press brake|laser|plasma (?:cutter|table)|water\s?jet|injection mold|mold(?:ing)? machin|"
    r"packaging (?:line|machine)|bottling line|canning line|\brobot(?!ic total)|\bhaas\b|okuma|dmg mori|mazak|trumpf|amada|fanuc|doosan dnm|"
    r"turning cent(?:er|re)|milling machine|\bwelder|conveyor|extruder|kiln|shredder|granulator|edgebander|irradiator|"
    r"process chiller|chillers?\b|e-brake|punch press|stamping press|hydraulic press|grinder|brewhouse|fermenter|paint booth|powder coat", re.I)
# Cuts, applied in this order after the scope and no-business-word cuts.
UCC_FORKLIFT = re.compile(r"forklift|fork lift|lift truck|pallet truck|orderpicker|scissor lift|excavator|skid steer|loader\b|telehandler|"
                          r"material handling equipment|hyster|\byale\b|manitou|pneumatic[- ](?:tire|tyre|sit)|electric-pneumatic", re.I)
UCC_PAVING = re.compile(r"pneumatic roller|asphalt paver|slipform|wirtgen|cold milling|milling machines? s/n|paver\b", re.I)
UCC_LAUNDRY = re.compile(r"alliance laundry|laundr|dry\s?clean|sankosha|washer|speed queen", re.I)
UCC_PHARM_COPIER = re.compile(r"cardinal health|canon financial", re.I)
UCC_TOWABLE = re.compile(r"towable|\bp185\b|pa185|hp150|hp375|375hd|\b185\s?cfm|tow[- ]behind|portable (?:air )?compressor", re.I)
UCC_TOWABLE_LENDER = re.compile(r"faris machinery", re.I)
UCC_RESTAURANT = re.compile(r"espresso|pizza|fryer|dishwasher|chick-fil-a|restaurant|mil-tek|baler|dough|commissary|blast chiller|kettle|"
                            r"total station|trimble|walk[- ]in cooler|oven, deck", re.I)
UCC_RESTAURANT_NAME = re.compile(r"\b(?:coffee|pasta|pizza|hospitality|chick-fil-a|restaurant|cafe|kitchen|grill|bar)\b", re.I)
AGENT_LENDER = re.compile(r"\bCHTD\b|\bCSC\b|CORPORATION SERVICE COMPANY|\bC ?T CORPORATION|FINANCIAL AGENT SERVICES", re.I)
VENDORS = re.compile(r"MAZAK|TRUMPF|MULTIVAC|METHODS MACHINE|HARTWIG|PRODUCTIVITY INC|CNC ASSOCIATES|STAR CNC|YAMAZEN|FANUC|YASKAWA|REISER|"
                     r"MITSUI SEIKI|MARUKA|HAITIAN|GROB")

# --------------------------------------------------------------------------- water permit cuts
WAT_WASTE = re.compile(r"wastewater|water quality|detention|hauling|crystal clean|enviro\b|recovery facility|recycle america|landfill|transfer station", re.I)
WAT_AIRPORT = re.compile(r"\bDEN\b|\bDIA\b|airport|pe[nñ]a\b|taxiway|taxilane|concourse|worldport|airlines?\b|aircraft|cargo facility|"
                         r"general use building|fuel facility|jet expansion", re.I)
WAT_AIRPORT_SIC = {"4581", "4512", "4513"}
WAT_PORTABLE = re.compile(r"statewide|portable", re.I)
WAT_RETAIL_NAME = re.compile(r"coffee|king soopers #|costco|\bstore\b|station #|school|elementary|\bpark\b|fire station|substation|pump station|"
                             r"solar|landings|\bRTD\b|\bCDOT\b|water campus", re.I)
OPERATING_WATER = ("COR900000", "CONOX000", "CO-", "COG5", "COP", "COE", "COX")   # record_type prefixes that name an operator, not a contractor
CONSTRUCTION_WATER = ("COR400000", "COG080000", "COG317000", "COG604000", "COG608000", "COG318000", "R-factor", "COR070000")

# --------------------------------------------------------------------------- air permit cuts
AIR_GENERATOR = re.compile(r"generator|\begen\b|fire pump|power generation|engine for electric", re.I)
AIR_PROCESS = re.compile(r"paint|booth|plating|batch plant|boiler|baking|bakery|manufactur|\bmfg\b|facility[- ]wide|dynamom|cleaning|"
                         r"distribution|sugar|silo|\bcbp\b|haps?\b", re.I)
AIR_INSTITUTION = re.compile(r"hospital|health|medical center|crematory|cremation|mortuary|cemetery|correction|city (?:&|and) county|"
                             r"water dep|data center|coresite|iron mountain|intelishift|airlines?|westin|hotel|t-mobile|raymond james|"
                             r"kiewit|convention|constructors|millstone weber|flatiron|denver department", re.I)
AIR_APEN = re.compile(r"permit exempt|apen only|apen exempt", re.I)
AIR_MODERATE = re.compile(r"batch plant|ready mix|\bcbp\b|dynamom", re.I)

# --------------------------------------------------------------------------- permits
IND_ZONE = re.compile(r"^(?:I-A|I-B|I-MX|M-IMX|I-0|I-1|I-2)")
NOT_PRODUCTION_PARCEL = re.compile(r"CHURCH|SCHOOL|PRESCHOOL|MEETING HALL|MISC RECREATION|HEALTH CLUB|MORTUARY|CEMETERY|CONV STORE|AUTO DEALER|"
                                   r"VETERINARY|SERVICE STATION")
SKIP_CLASSES = {"Special Event", "Change of Contractor"}
NEW_CLASSES = {"New Building", "Addition", "Foundation Only/Excavation", "Phased Construction", "New Non-Building Structure"}

# --------------------------------------------------------------------------- fit words (order: maker word, trade word, weak word)
FIT_STRONG = re.compile(
    r"\b(manufactur\w*|mfg|machining|machine|fabricat\w*|brew\w*|distill\w*|baker\w*|baking|foods?|roast\w*|plastics|metals?|tools?|tooling|"
    r"packaging|woodwork\w*|cabinet\w*|millwork|foundry|composites|aerospace|robotics|semiconductors?|chocolate\w*|confection\w*|creamery|"
    r"tortill\w*|winery|cidery|molding|castings?|forge|extrusions?|stamping|plating|industries|steel|bottling|polymers?)\b", re.I)
FIT_MOD = re.compile(r"\b(auto|automotive|autobody|truckwash\w*|tires?|tyres?|concrete|ready\s?mix|print\w*|coatings|welding|collision|body\s+shop|truck\w*|motors?|stone)\b", re.I)
FIT_WEAK = re.compile(
    r"\b(office|energy|solar|software|technolog\w+|systems|space|holdings?|properties|realty|apartments?|housing|residential|multifamily|"
    r"logistics|hospitality|restaurant|hotel|consulting|capital|investments?|ventures|media|marketing|studio|clinic|dental|medical|school|"
    r"church|development|communications|oilfield|landscap\w+|distribution cent(?:er|re)|storage|data cent(?:er|re)s?|supply chain|"
    r"prime now|substation|pump station|underwriting|insurance|consult\w+|warehous\w+)\b", re.I)

# Project names on construction stormwater rows that show the work at an address is not a plant.
PROJECT_WEAK = re.compile(r"multifamily|multi-family|residential|apartments?|housing|townhomes?|\bhomes\b|school|elementary|substation|solar|"
                          r"photovoltaic|pump station|fire station|\bpark\b|data cent(?:er|re)|self storage|hotel|church", re.I)

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
