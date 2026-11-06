#!/usr/bin/env python3
"""Step 5 v3 fixed inputs that are not in the Step 4 files: the word lists for the noise cuts and fit rules, shared by every county.

County-specific values (scope, local noise cut, web checks, Step 3 ties, ground-truth projects) are in county_configs/<county>.py and are
loaded at the bottom of this file. The ground-truth list is used only by build_v3.gt_match, after ranking, for the in_ground_truth column and the report.
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


# --------------------------------------------------------------------------- county-specific values
# Everything that belongs to one county lives in county_configs/<county>.py. build_v3.py --county <name> sets V3_COUNTY before this
# module is imported. A county file must define COUNTY, COUNTY_FULL, AIRS_PREFIX, ZIP_SHARE_FILE and LOCAL_LAYERS; the rest default to empty.
import importlib, os

COUNTY_SLUG = os.environ.get("V3_COUNTY", "denver").lower()
COUNTY = COUNTY_FULL = AIRS_PREFIX = ZIP_SHARE_FILE = None
LOCAL_LAYERS = False
MAIL_CITIES = None                           # mailing cities treated as the county's own name (default: the county name, as Denver is both city and county)
SPLIT_CITIES = set()                         # mailing cities that straddle the county line; their rows are placed by zip share and the Census geocoder only
LOCAL_PERMIT_FILES = None                    # county permit files (shared 17-column format) read through v3_local; None = Denver's own layer when LOCAL_LAYERS
LOCAL_PLAN_FILES = None                      # county planning and development files read through v3_local; None = Denver's own layer when LOCAL_LAYERS
LOCAL_PERMIT_LABEL = None                    # how the permit layer is named in the sources column; None = the Denver label
LOCAL_PLAN_LABEL = None                      # how the planning layer is named in the sources column; None = the Denver label
LOCAL_INCENTIVE_FILES = []                   # county incentive agreement files (shared 17-column format, flag Y rows only); empty = no such layer (Denver, Adams)
LOCAL_DESC_USE_HOLD = False                  # hold tier A permits whose description says retail, well pad etc. at B3a (layers with no valuation or use field)
WEB_DROPS_TIER_B = False                     # let WEB_DROPS also remove tier B UCC liens (off for Denver and Adams, whose lists were built without it)
WAT_AIRPORT = re.compile(r"(?!x)x")          # never matches unless the county file sets a local airport or base cut
WAT_AIRPORT_SIC = set()
WEB_CHECKS, WEB_CHECKS_V3 = {}, {}
WEB_ADDRESS_OK = set()
WEB_DROPS = {}
PERSON_NAMED = set()                         # registered entities named after a private individual, left out of every listing (name keys); Matthew's decision per county
WEB_NOT_CONFIRMED_V3 = []
KNOWN_TIES = []
STEP3_OCCUPIERS = {}
GROUND_TRUTH = {}

_county_module = importlib.import_module("county_configs." + COUNTY_SLUG)
for _k, _v in vars(_county_module).items():
    if _k.isupper():
        globals()[_k] = _v
for _req in ("COUNTY", "COUNTY_FULL", "AIRS_PREFIX", "ZIP_SHARE_FILE"):
    if not globals()[_req]:
        raise SystemExit("county_configs/%s.py must define %s" % (COUNTY_SLUG, _req))
COUNTY_UP = COUNTY.upper()
if MAIL_CITIES is None:
    MAIL_CITIES = {COUNTY_UP}
MAIL_CITIES = {c.upper() for c in MAIL_CITIES}
SPLIT_CITIES = {c.upper() for c in SPLIT_CITIES} - MAIL_CITIES
CITY_OK = MAIL_CITIES | SPLIT_CITIES
from v3_lib import PER as _PER, SDP as _SDP
SRC_LABEL = {_PER: LOCAL_PERMIT_LABEL or _PER, _SDP: LOCAL_PLAN_LABEL or _SDP}
PERMIT_LABEL = SRC_LABEL[_PER]
PLAN_LABEL = SRC_LABEL[_SDP]
