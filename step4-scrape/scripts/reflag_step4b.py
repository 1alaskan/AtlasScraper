#!/usr/bin/env python3
"""Step 4b: add a second, wider flag tier (tier B) to three Step 4 scrape files.

Usage:
    python3 reflag_step4b.py <step4-scrape folder> [--out <folder>]

Reads   scrape_ucc_filings/scrape_ucc_filings.csv
        scrape_business_registrations/scrape_business_registrations.csv
        scrape_denver_commercial_permits.csv
        scrape_flagged.csv                      (tier A rows of all eight sources)
Writes  the three source files with _v2 on the end (same rows, same order, three new columns),
        scrape_flagged_v2.csv and reflag_counts.json.

Nothing is scraped. `flag` and `flag_rule` are never changed. New columns:
    flag_v2       Y / N
    flag_tier     A = flagged in Step 4, B = newly flagged here, blank = not flagged
    flag_rule_v2  tier A: the Step 4 rule, copied.  tier B: every tier B rule that fired, "; " separated.

Rule ids: B1a B1b B1c (UCC), B2a (registrations), B3a B3b (Denver permits).
Rules are generic: no company name or address from the ground-truth test set appears below.
Version 1.2, 2026-10-11 (B1a now uses the full collateral text where pull_ucc_fulltext_b1a.py has fetched it). Version 1.1, 2026-10-10 (decisions after the first run applied: trimmed B2a words, B3b on zoning or parcel, funder liens dropped).
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict

csv.field_size_limit(10 ** 9)

# --------------------------------------------------------------------------- shared
def norm_party(s):
    s = re.sub(r"[^A-Z0-9& ]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()

HAS_UNIT = re.compile(r"(?:\b(?:ste|suite|unit|apt|bldg|building|bay|spc|space|fl|floor|rm|room|dock)\b\.?\s*#?\s*[A-Za-z0-9-]+|#\s*[A-Za-z0-9-]+)", re.I)

def addr_key(a):
    """House number + S/W/E prefix + street name. N prefixes, street types and units are dropped (Step 5 method)."""
    a = a.upper().replace(".", " ").replace(",", " ")
    a = re.sub(r"\b(?:STE|SUITE|UNIT|APT|BLDG|BUILDING|BAY|SPC|SPACE|FL|FLOOR|RM|ROOM)\b\.?\s*#?\s*[A-Z0-9-]+.*$", "", a)
    a = re.sub(r"#\s*[A-Z0-9-]+.*$", "", a)
    t = a.split()
    if len(t) < 2 or not re.match(r"^\d+[A-Z]?$", t[0]):
        return ""
    num = re.sub(r"[A-Z]$", "", t[0]); rest = t[1:]
    pre = ""
    D = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "N": "N", "S": "S", "E": "E", "W": "W"}
    if rest and rest[0] in D and len(rest) > 1:
        pre = D[rest[0]]; rest = rest[1:]
    TYPES = {"ST", "STREET", "AVE", "AVENUE", "AV", "BLVD", "BOULEVARD", "RD", "ROAD", "DR", "DRIVE", "LN", "LANE", "CT", "COURT",
             "PL", "PLACE", "WAY", "PKWY", "PARKWAY", "CIR", "CIRCLE", "HWY", "HIGHWAY", "TER", "TERRACE", "TRL", "TRAIL"}
    out = []
    for w in rest:
        if w in TYPES and out:
            break
        out.append(w)
    name = " ".join(out)
    name = re.sub(r"^(\d+)(?:ST|ND|RD|TH)$", r"\1", name)
    if pre == "N":
        pre = ""
    return (num + " " + (pre + " " if pre else "") + name).strip()

# --------------------------------------------------------------------------- UCC
# B1a. Process-equipment words. Matched on `description`, which Step 4 cut at 500 characters
# (the full collateral text is not on disk; see reflag_notes.md).
B_WORDS = [
    ("granulator", r"granulators?"), ("pelletizer", r"pelleti[sz]ers?"), ("shredder", r"shredders?"),
    ("grinder", r"grinders?"), ("mixer", r"mixers?"),
    ("blender", r"(?:ribbon|paddle|tumble|drum|powder|batch|gravimetric|vacuum|industrial|v|\d+[\s-]?(?:cu|gal|gallon|lb|l|liter)\S*)[\s-]+blenders?"),
    ("filler", r"(?:can|bottle|keg|piston|vacuum|rotary|liquid|volumetric|auger|cup|pouch|bag|cart|cartridge|lotion|balm|tube|drum|gravity|pressure|inline|in-line|net[\s-]weight|\d+[\s-]?head(?:\s+\w+){0,2})(?:\s+and\s+\w+)?[\s-]+fillers?"),
    ("capper", r"cappers?"), ("labeler", r"labell?ers?"), ("palletizer", r"palleti[sz]ers?"),
    ("oven", r"ovens?"), ("kiln", r"kilns?"), ("dryer", r"dryers?|driers?"), ("extruder", r"extruders?"),
    ("thermoformer", r"thermoform(?:er|ers|ing)"), ("blow molder", r"blow[\s-]?mou?ld(?:er|ers|ing)?"),
    ("die caster", r"die[\s-]?cast(?:er|ers|ing)"), ("sandblast", r"sand[\s-]?blast(?:er|ers|ing)?"),
    ("powder coat", r"powder[\s-]?coat(?:ing|er)?"), ("spray booth", r"spray\s+booths?"),
    ("dust collector", r"dust\s+collect(?:or|ors|ion)"), ("vacuum pump", r"vacuum\s+pumps?"),
    ("air dryer", r"air[\s-]dryers?"), ("nitrogen generator", r"nitrogen\s+generat(?:or|ors|ion)"),
    ("fermenter", r"ferment[eo]rs?|fermentation\s+(?:tank|vessel)s?"), ("brewhouse", r"brew[\s-]?house"),
    ("canning line", r"canning\s+(?:line|machine|system)s?"),
    ("still", r"(?:pot|column|reflux|copper|spirit|whiske?y|vodka|gin|stripping)\s+stills?|stills?\s+(?:and|with)\s+(?:column|condenser|mash)|distill(?:ation|ing)\s+(?:equipment|system|column|still)s?|\d+[\s-]?(?:gal|gallon|l|liter|litre)s?\s+stills?"),
    ("roaster", r"roasters?"),
    # bare "mill" hits surnames, place names and asphalt milling, so only typed mills or a model code followed by "mill" count
    ("mill", r"(?:roller|hammer|ball|bead|grain|flour|malt|pellet|pin|colloid|jet|attrition|vertical|horizontal|knee|bridgeport|turret|bed|gantry|boring|tube|rolling|timber|lumber|grist|hemp|three[\s-]roll|3[\s-]roll)\s+mills?|(?=[A-Z-]*\d)[A-Z0-9-]{2,}\s+mills?"),
    # compressor brands not in the Step 4 list (Kaeser, Sullair, Gardner Denver, Quincy were; kept for re-runs)
    ("kaeser", r"kaeser"), ("sullair", r"sullair"), ("gardner denver", r"gardner[\s-]?denver"),
    ("quincy", r"quincy\b(?=.{0,60}\b(?:compressors?|air|qgs|qgd|qsi|qt|qr|qp)\b)"),
    ("chicago pneumatic", r"chicago[\s-]?pneumatic"), ("elgi", r"elgi"), ("boge", r"boge(?=.{0,60}\b(?:compressors?|air|screw)\b)"),
    ("compair", r"compair"), ("fs-curtis", r"fs[\s-]?curtis"), ("sullivan-palatek", r"sullivan[\s-]?palatek|palatek"),
]
B_RE = [(lab, re.compile(r"\b(?:%s)\b" % body, re.I)) for lab, body in B_WORDS]
BRANDS = {"kaeser", "sullair", "gardner denver", "quincy", "chicago pneumatic", "elgi", "boge", "compair", "fs-curtis", "sullivan-palatek"}
# Step 4 fixture-boilerplate guard, unchanged: 2 or more markers = real-estate fixture language.
MARKERS = [re.compile(p, re.I) for p in (
    r"\bplumbing\b", r"\bair[\s-]condition", r"\belevators?\b", r"\bawnings?\b", r"\bcarpet", r"\brefrigerators?\b",
    r"\bsinks?\b", r"\bbath\s?tubs?\b", r"\bincinerat", r"\bsprinkler", r"\bwater\s+heaters?\b", r"\bdishwashers?\b",
    r"\bwater\s+closets?\b", r"\bstoves?\b", r"\bshades\b", r"\bscreens\b", r"\bboilerplate\b", r"\bventilating\b",
    r"\breal\s+property\b", r"\breal\s+estate\b")]
# Guards for obvious false hits.
G_FOODSERVICE_NAME = re.compile(r"\b(?:restaurants?|cafe|café|coffee(?!\s+roast)|pizza|pizzeria|grill|grille|kitchen|bar|tavern|catering|taco|tacos|taqueria|burger|burgers|bbq|barbecue|diner|sushi|bistro|cantina|deli|donuts?|doughnuts?|eatery|steakhouse|pub|saloon|wings|ramen|pho|thai|cuisine|food\s+truck|ice\s+cream|juice|smoothie|subs?|sandwich(?:es)?|market|grocery|liquors?|hotel|lodge|school|church|hospital|senior|assisted)\b", re.I)
G_FOODSERVICE_TEXT = re.compile(r"\b(?:fryers?|griddles?|dishwashers?|walk[\s-]?in|reach[\s-]?in|ice\s+(?:machine|maker)|espresso|hood\s+system|exhaust\s+hood|point\s+of\s+sale|pos\s+system|soft\s+serve|steam\s+table|salamander|charbroiler|pizza\s+oven|microwave|convection\s+oven|combi\s+oven|range)\b", re.I)
G_MAKER_NAME = re.compile(r"\b(?:bakery|bakeries|baking|bread|foods?|tortill\w+|manufactur\w+|mfg|brew\w+|distill\w+|roast\w+|commissary|processing|packing|meats?|creamery|dairy|confection\w*|chocolat\w+|candy|snacks?)\b", re.I)
G_LAUNDRY = re.compile(r"\b(?:washers?|laundr\w+|tumbl\w+|speed\s*queen|huebsch|dexter|unimac|wascomat|girbau|maytag|whirlpool|clothes|coin[\s-]?op\w*|hair|salon|hand\s+dryers?|blow\s+dryers?|grain|corn|car\s*wash|tunnel|stackable|stack\s+dryers?)\b", re.I)
G_LAUNDRY_NAME = re.compile(r"\b(?:laundr\w+|cleaners|dry\s+clean\w*|wash|salon|farms?|ranch|grain)\b", re.I)
G_MIXER = re.compile(r"\b(?:vermeer|directional|hdd|drills?|grout|bridgeking|pull[\s-]type|trailers?|harsh|supreme|augers?|hoppers?|pumps?|zim[\s-]?mixer|imer|semi|mixer\s+trucks?|truck\s+mixers?|concrete\s+mixers?|cement\s+mixers?|mixer\s+bod(?:y|ies)|ready[\s-]?mix|trucks?|vin|mack|kenworth|peterbilt|freightliner|feed|tmr|vertical\s+mixers?|wagons?|audio|sound|dj|digital\s+mixers?|console|yamaha|behringer|mortar\s+mixers?|mud\s+mixers?|skid\s+steer)\b", re.I)
G_GRINDER = re.compile(r"\b(?:stump|tub|horizontal|coffee|espresso|angle|bench|concrete|floor|feed|rock)\s+grinders?\b|\bgrinders?\s+pumps?\b|\b(?:lavina|husqvarna|wolfpack|tomahawk|planetary|dust\s+extractor|shot\s*blast|surface\s+prep|floors?|epoxy)\b", re.I)
G_TRADE_NAME = re.compile(r"\b(?:farms?|ranch|ranches|cattle|livestock|feeders|feedyard|dairy|construction|contracting|contractors?|excavat\w+|drilling|concrete|ready\s*mix|trucking|locating|communications|broadband|telecom|builders|rentals?|flooring|floors?|epoxy|tile|surfaces|gutters?|barricade|roll[\s-]?off|septic|sanitation|towing|county|city\s+of|town\s+of|school|district|trust|estate)\b", re.I)
G_OVEN = re.compile(r"\b(?:warmers?|ventless|rapid\s+cook|cooking\s+surface|pizza|toaster|microwave)\b", re.I)
G_LAB = re.compile(r"\b(?:agilent|peak|genius|chromatograph\w*|lc[\s/-]?ms|mass\s+spec\w*|sciex|waters)\b", re.I)
G_VACTANK = re.compile(r"\b(?:vac\s+tanks?|septic|trucks?|trailers?)\b", re.I)
G_SHREDDER = re.compile(r"\b(?:paper|document|stalk|flail|brush|mulch|chipper)[\s/-]+shredders?\b|\bshredders?[\s/-]+(?:chipper)\b", re.I)
G_VACPUMP_NAME = re.compile(r"\b(?:dental|dentist\w*|dds|dmd|orthodont\w*|endodont\w*|periodont\w*|oral|smiles?|medical|clinic|surgery|surgical|veterinar\w*|animal|dairy|farms?|ranch|septic|plumbing|hvac|heating)\b", re.I)
G_FILLER = re.compile(r"\b(?:crack|joint|seam|wood|body|dermal)\s+fillers?\b", re.I)
G_ROASTER_NAME = G_FOODSERVICE_NAME

def b1a_hits(desc, name):
    hits = [lab for lab, rx in B_RE if rx.search(desc)]
    if not hits:
        return []
    boiler = sum(1 for m in MARKERS if m.search(desc)) >= 2
    kitchen_ctx = (G_FOODSERVICE_NAME.search(name) or G_FOODSERVICE_TEXT.search(desc)) and not G_MAKER_NAME.search(name)
    out = []
    for h in hits:
        if h in BRANDS:
            out.append(h); continue
        if boiler:
            continue
        if h in ("oven", "mixer", "blender", "grinder", "filler", "roaster", "dryer") and kitchen_ctx:
            continue
        if h in ("mixer", "grinder", "mill", "shredder", "dryer", "vacuum pump", "dust collector") and G_TRADE_NAME.search(name):
            continue
        if h == "oven" and G_OVEN.search(desc):
            continue
        if h == "nitrogen generator" and G_LAB.search(desc):
            continue
        if h == "vacuum pump" and G_VACTANK.search(desc):
            continue
        if h == "dust collector" and G_GRINDER.search(desc):
            continue
        if h == "dryer" and (G_LAUNDRY.search(desc) or G_LAUNDRY_NAME.search(name)):
            continue
        if h == "mixer" and G_MIXER.search(desc):
            continue
        if h == "grinder" and G_GRINDER.search(desc):
            continue
        if h == "shredder" and (G_SHREDDER.search(desc) or re.search(r"shred", name, re.I)):
            continue
        if h == "vacuum pump" and G_VACPUMP_NAME.search(name):
            continue
        if h == "filler" and G_FILLER.search(desc):
            continue
        out.append(h)
    return out

# B1b. Vague collateral + equipment lender.
BLANKET = re.compile(
    r"\ball\s+(?:of\s+)?(?:the\s+)?(?:debtor'?s?'?\s+|borrower'?s?'?\s+|grantor'?s?'?\s+)?(?:(?:business|personal|present\s+and\s+future|existing\s+and\s+future|tangible\s+and\s+intangible|right,?\s+title\s+and\s+interest\s+in(?:\s+and\s+to)?(?:\s+all)?)\s+)*(?:assets|personal\s+property|property\s+and\s+assets)\b"
    r"|\ball\s+(?:of\s+)?(?:the\s+)?(?:debtor'?s?'?\s+)?(?:inventory|equipment|accounts|goods|fixtures|furniture)\b[^.;]{0,160}\b(?:accounts|general\s+intangibles|chattel\s+paper|instruments|inventory)\b"
    r"|\bblanket\s+lien\b", re.I)
NOT_BLANKET = re.compile(r"\b(?:not\s+an?\s+all[\s-]asset|purchase[\s-]money|financed\s+by|leased\s+(?:by|from|to)|sold\s+by|supplied\s+by|purchased\s+from|purchased\s+with|described\s+(?:below|herein|on|in)|listed\s+(?:below|on|in)|pursuant\s+to|in\s+reference\s+to|the\s+following\s+(?:equipment|goods|items?|property|collateral|described|specific))\b", re.I)
POINTER = re.compile(
    r"\bsee\s+(?:the\s+)?(?:attached|attachment|exhibit|schedule|addendum|annex|appendix)\b"
    r"|\b(?:described|set\s+forth|listed|identified|shown|detailed)\s+(?:herein\s+and/?or\s+)?(?:on|in)\s+(?:the\s+)?(?:attached\s+)?(?:exhibit|schedule|attachment|addendum|annex|appendix)\b"
    r"|\b(?:exhibit|schedule|appendix|attachment)\s+[\"'“]?[A-Z1-9][\"'”]?\s+(?:attached|hereto|annexed)\b"
    r"|\b(?:on|in|per)\s+(?:the\s+)?(?:attached\s+)?(?:exhibit|schedule)\s+[\"'“]?[A-Z1-9]\b", re.I)
ITEMISED = re.compile(r"\b(?:s/n|sn|serial|vin|model|mdl)\b\s*[:#]?\s*[A-Z0-9-]{3,}|\b(?:19|20)\d{2}\s+[A-Z][A-Za-z]+\s+[A-Z0-9-]{2,}", re.I)

def vague_kind(desc, textlen):
    """'' if the collateral is described; else blank / blanket / pointer."""
    d = desc.strip()
    if not d:
        return "blank"
    head = d[:260]
    m = BLANKET.search(head)
    if m and m.start() <= 90 and not NOT_BLANKET.search(head) and not ITEMISED.search(head):
        return "blanket"
    if POINTER.search(d) and textlen <= 600 and not ITEMISED.search(d):
        return "pointer"
    return ""

# Lender list, built from the secured parties on tier A rows, ranked by count. A lender is kept when it has
# 2 or more tier A rows AND is equipment-specific. Two versions:
# NARROW (default, delivered): machinery makers and dealers and their captive finance arms, plus finance
#   companies where 20% or more of the lender's own initial filings in the file are tier A.
# BROAD (--broad-lenders): adds general equipment lessors and bank equipment-finance divisions, whose tier A
#   share is under 20% (they also finance copiers, vehicles, dental and restaurant equipment).
# Left out of both: banks, the SBA, filing agents (CSC, CT Corporation, CHTD, Financial Agent Services, Secured
# Lender Solutions), community loan funds, construction, farm and truck lenders and dealers (Wagner, John Deere,
# Faris, Power Equipment, CNH, Commercial Credit Group, Keystone, Trans Lease, North Mill), laundry, pharmacy,
# medical and office-equipment vendors (Alliance Laundry, Cardinal Health, Zimmer, Canon), and individuals.
# Matching is a substring test on the normalised secured party name.
LENDERS_NARROW = [
    "CNC ASSOCIATES", "STAR CNC MACHINE TOOL", "TRUMPF", "METHODS MACHINE TOOLS", "PRODUCTIVITY INC", "HARTWIG INC",
    "MULTIVAC", "ROBERT REISER", "YAMAZEN", "MITSUI SEIKI", "MARUKA USA", "ABSOLUTE HAITIAN", "GROB SYSTEMS", "MAZAK",
    "FANUC AMERICA", "YASKAWA AMERICA", "SMT FINANCE", "AMERICAN PACKAGING CAPITAL", "HANSEN METALLURGICAL",
    "SUMITOMO MITSUI FINANCE & LEASING", "MACHINERY FINANCE RESOURCES", "MANUFACTURERS CAPITAL", "WILDCAT FUNDING",
    "VERDANT COMMERCIAL CAPITAL", "UNIFI EQUIPMENT FINANCE", "M2 EQUIPMENT FINANCE", "FIVE LAKES FINANCIAL",
    "NOREAST CAPITAL", "LANDMARK FINANCIAL CORP",
]
LENDERS_BROAD_EXTRA = [
    "U S BANK EQUIPMENT FINANCE", "KEY EQUIPMENT FINANCE", "WELLS FARGO EQUIPMENT FINANCE", "WELLS FARGO VENDOR FINANCIAL",
    "SIEMENS FINANCIAL SERVICES", "KLC FINANCIAL", "AILCO EQUIPMENT FINANCE", "CUSTOMERS COMMERCIAL FINANCE",
    "ALLEGIANT PARTNERS", "STEARNS BANK EQUIPMENT FINANCE", "NORTHLAND CAPITAL", "NAVITAS CREDIT", "OAKMONT CAPITAL",
    "BLUE BRIDGE FINANCIAL", "WESTERN EQUIPMENT FINANCE", "MARLIN LEASING", "HIGHLAND CAPITAL CORP", "GENEVA CAPITAL",
    "DE LAGE LANDEN", "DLL FINANCE", "GREATAMERICA FINANCIAL", "NORTH STAR LEASING", "LEAF CAPITAL FUNDING",
    "TARGETED LENDING", "COMMERCIAL CAPITAL COMPANY",
]
SBA = re.compile(r"SMALL BUSINES+ ADMIN|\bSBA\b")
# Sales of future receivables (merchant cash advances) read like blanket liens but signal cash strain, not capacity.
RECEIVABLES_SALE = re.compile(r"sale\s+of\s+accounts|purchase\s+of\s+(?:rights|receivables|future)|future\s+(?:receivables|receipts|sales)|purchased\s+(?:receivables|receipts|amount)|merchant\s+(?:cash|agreement)", re.I)

# Decision 2026-10-10: blanket liens held by known receivables and merchant-cash funders do not count for B1c.
# Name test on the secured party. Equipment lessors with "Funding" in the name are excepted.
FUNDER = re.compile(r"\bLCF GROUP\b|\bFUNDINGS?\b|\bADVANCE\b|\bMERCHANT\b|\bFACTOR(?:S|ING)?\b|QFS CAPITAL|KATAN CAPITAL|KAPITUS|"
                    r"ON ?DECK|FUNDBOX|BLUEVINE|RAPID FINANCE|CREDIBLY|LIBERTAS|FORWARD FINANCING|WEBBANK|PARAFIN|INKIND|MAXITRANSFERS")
FUNDER_EXCEPT = re.compile(r"EQUIPMENT|LEAF CAPITAL")

def is_funder(sp_norm):
    return bool(FUNDER.search(sp_norm)) and not FUNDER_EXCEPT.search(sp_norm)

def lender_hit(sp_norm, lenders):
    for l in lenders:
        if l in sp_norm:
            return l
    return ""

# B1c. Maker word in the debtor name, on a blanket lien.
MAKER_UCC = re.compile(
    r"\b(?:brewing|brewery|breweries|brewers|distilling|distillery|distillers|bakery|bakeries|baking|foods|roasters|roastery|roasting|"
    r"manufacturing|manufacturers?|mfg|machine|machines|machining|fabrication|fabricators?|fabricating|plastics|metal|metals|"
    r"precision|tool|tooling|coatings|packaging|printing|printers|woodworks|woodworking|millwork|cabinets|cabinetry|foundry|"
    r"castings?|molding|moulding|bottling|composites|welding|winery|cidery|meadery|creamery|tortilleria|confections|chocolates?|"
    r"candy|extrusions?|stamping|plating|anodizing|galvanizing|forge|forging)\b", re.I)
# Words that turn a maker word into a trade, a shop or a service. Guard for B1c only.
NOT_MAKER_UCC = re.compile(
    r"\b(?:roofing|roofs?|construction|contracting|contractors?|builders?|landscap\w+|restaurant|cafe|pizza|grill|bar|realty|properties|"
    r"holdings?|rentals?|rental|consulting|supply|supplies|store|sales|recycling|franchise|security|timber|felling|directional|trucking|transport\w*|logistics|plumbing|heating|electric|cleaning|detailing|auto|automotive|"
    r"dental|medical|salon|fitness|farms?|ranch|buildings?|siding|gutters?|fencing|flooring|painting|drywall|concrete|excavat\w+|"
    r"tool\s+rental|machine\s+learning|precision\s+(?:ag|agriculture|landscap\w+|lawn|plumbing|roofing|auto|automotive|collision|eye|dental|chiropractic|medicine|health|fitness|contracting|construction|excavat\w+|painting|drywall|concrete|electric|heating|cleaning|homes?|builders?|tree|pest|drilling|fence|floors?|flooring|tile|glass|air|hvac|mechanical|turf|pavement|paving|sealcoat\w*|grading|irrigation|sprinklers?))\b", re.I)

def maker_word(name):
    m = MAKER_UCC.search(name)
    if not m or NOT_MAKER_UCC.search(name):
        return ""
    return m.group(0).lower()

FULLHITS = {}     # (record_id, debtor_seq) -> words; filled in main() from scrape_ucc_filings/ucc_b1a_fulltext_hits.csv when present

def flag_ucc(r, lenders):
    """Return list of rule strings for one UCC row (empty = no tier B flag)."""
    if r["flag"] == "Y" or r["transaction_type"] != "Initial Filing" or "|ucc|" not in r["filing_type_raw"]:
        return []
    if r["debtor_name_has_entity_token"] == "N":
        return []                      # may be an individual: never tier B
    name = r["company_name"]; desc = r["description"]
    try:
        tl = int(r["collateral_text_len"] or 0)
    except ValueError:
        tl = len(desc)
    rules = []
    fh = FULLHITS.get((r["record_id"], r["debtor_seq"])) if tl > 500 else None
    if FULLHITS and tl > 500:
        # the full collateral text was checked by pull_ucc_fulltext_b1a.py; its result replaces the 500-character match
        if fh:
            rules.append("B1a initial filing + process-equipment word (full collateral text): " + fh)
    else:
        h = b1a_hits(desc, name)
        if h:
            rules.append("B1a initial filing + process-equipment word (%s): " % ("whole text" if tl <= 500 else "first 500 characters") + ", ".join(h[:3]))
    vk = vague_kind(desc, tl)
    sp = norm_party(r["secured_party"])
    if vk:
        l = lender_hit(sp, lenders)
        if l:
            rules.append("B1b initial filing + %s collateral + equipment lender: %s" % (vk, l.title()))
    if vk == "blanket" and not SBA.search(sp) and not RECEIVABLES_SALE.search(desc) and not is_funder(sp):
        w = maker_word(name)
        if w:
            rules.append("B1c initial filing + blanket lien + maker word in debtor name: " + w)
    return rules

# --------------------------------------------------------------------------- registrations
# Decision 2026-10-10: bakery, coatings, foods, foundry, machine and machines were dropped from the brief's list
# after the sample read (home bakeries, floor-coating contractors, vending and gaming "machines").
NARROW = re.compile(r"\b(manufacturing|mfg|machining|fabrications?|plastics|brewing|brewery|distilling|distillery|"
                    r"roasters|bottling|packaging|composites|aerospace|robotics|semiconductors?)\b", re.I)
DEAD_STATUS = re.compile(r"withdrawn|dissolved|converted|merged", re.I)
AGENT_MIN = 10

def reg_addr_key(r):
    a = re.sub(r"[^A-Z0-9 ]", " ", r["site_address"].upper())
    a = re.sub(r"\b(?:SUITE|STE|UNIT|APT|NO|NUMBER)\b", "#", a)
    a = re.sub(r"\s+", " ", a).strip()
    return a + "|" + r["zip"][:5] if a else ""

def flag_reg(r, addr_count):
    if r["flag"] == "Y" or r["is_foreign"] != "N":
        return [], ""
    m = NARROW.search(r["company_name"])
    if not m:
        return [], ""
    if DEAD_STATUS.search(r["entity_status"]):
        return [], "status"
    k = reg_addr_key(r)
    if k and addr_count.get(k, 0) >= AGENT_MIN:
        return [], "agent"
    return ["B2a domestic entity + narrow maker word: " + m.group(1).lower()], ""

# --------------------------------------------------------------------------- Denver permits
IND_ZONE = re.compile(r"^(?:I-A|I-B|I-MX|M-IMX)")
# Assessor classes that carry the INDUSTRIAL- prefix but are not production or service-bay property.
NOT_PRODUCTION_PARCEL = re.compile(r"CHURCH|SCHOOL|PRESCHOOL|MEETING HALL|MISC RECREATION|HEALTH CLUB|MORTUARY|CEMETERY|CONV STORE|AUTO DEALER|VETERINARY|SERVICE STATION")
B3B_CLASSES = {"New Building", "Addition", "Alteration/Tenant Finish"}
SKIP_CLASSES = {"Special Event", "Change of Contractor"}

def ind_parcel(pc, strict):
    if not pc.startswith("INDUSTRIAL"):
        return False
    return True if strict else not NOT_PRODUCTION_PARCEL.search(pc)

def flag_permit(r, strict=False):
    if r["flag"] == "Y":
        return []
    if r["zone_district"] == "DIA" or re.search(r"\bpe[nñ]a\b", r["site_address"], re.I):
        return []                      # Step 5 airport rule
    if r["class"] in SKIP_CLASSES:
        return []
    try:
        v = float(r["valuation"])
    except ValueError:
        return []                      # blank valuation: not flagged
    ip = ind_parcel(r["parcel_class"], strict); iz = bool(IND_ZONE.match(r["zone_district"]))
    if v >= 50000 and (ip or iz):
        why = []
        if ip: why.append("parcel " + r["parcel_class"].title())
        if iz: why.append("zoning " + r["zone_district"])
        return ["B3a valuation >= 50k + industrial property: " + ", ".join(why)]
    # Decision 2026-10-10: B3b fires on industrial zoning OR industrial parcel class (the brief required the parcel class).
    if v < 50000 and (ip or iz) and r["class"] in B3B_CLASSES:
        why = []
        if ip: why.append("parcel " + r["parcel_class"].title())
        if iz: why.append("zoning " + r["zone_district"])
        return ["B3b valuation < 50k (%s) + industrial property + %s: %s" % ("zero" if v == 0 else "nominal", r["class"].lower(), ", ".join(why))]
    return []

# --------------------------------------------------------------------------- run
SHARED = ["source", "source_level", "record_id", "record_date", "date_type", "record_type", "company_name", "company_role",
          "site_address", "city", "county", "zip", "description", "flag", "flag_rule", "source_url", "retrieved_at"]
NEW = ["flag_v2", "flag_tier", "flag_rule_v2"]

def rule_id(s):
    return s.split(" ", 1)[0]

def process(src, dst, fn, counts, key, is_denver):
    tierB = []
    with open(src, newline="", encoding="utf-8-sig") as fi, open(dst, "w", newline="", encoding="utf-8") as fo:
        rd = csv.DictReader(fi); cols = rd.fieldnames
        w = csv.writer(fo); w.writerow(cols + NEW)
        for r in rd:
            counts[key]["rows"] += 1
            if r["flag"] == "Y":
                counts[key]["tierA"] += 1
                extra = ["Y", "A", r["flag_rule"]]
            else:
                rules = fn(r)
                if rules:
                    counts[key]["tierB"] += 1
                    den = is_denver(r)
                    if den: counts[key]["tierB_denver"] += 1
                    ids = sorted(set(rule_id(x) for x in rules))
                    for i in ids:
                        counts[key][i] += 1
                        if den: counts[key][i + "_denver"] += 1
                    if len(ids) == 1:
                        counts[key][ids[0] + "_only"] += 1
                    extra = ["Y", "B", "; ".join(rules)]
                    tierB.append({**{c: r[c] for c in SHARED}, "flag_tier": "B", "flag_rule_v2": extra[2],
                                  "_secured_party": r.get("secured_party", "")})
                else:
                    extra = ["N", "", ""]
            w.writerow([r[c] for c in cols] + extra)
    return tierB

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = args[0]
    out = base
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    lender_version = "broad" if "--broad-lenders" in sys.argv else "narrow"
    strict_parcel = "--strict-parcel" in sys.argv
    lenders = LENDERS_NARROW + (LENDERS_BROAD_EXTRA if lender_version == "broad" else [])
    counts = defaultdict(Counter)
    os.makedirs(os.path.join(out, "scrape_ucc_filings"), exist_ok=True)
    os.makedirs(os.path.join(out, "scrape_business_registrations"), exist_ok=True)

    hp = os.path.join(base, "scrape_ucc_filings", "ucc_b1a_fulltext_hits.csv")
    if os.path.exists(hp):
        with open(hp, newline="", encoding="utf-8") as f:
            for h in csv.DictReader(f):
                FULLHITS[(h["record_id"], h["debtor_seq"])] = h["words"]
        counts["settings"]["fulltext_hits_file_rows"] = len(FULLHITS)
    den_city = lambda r: r["city"].strip().upper() == "DENVER" and r.get("debtor_state", r.get("principal_state", "CO")) == "CO"
    # UCC
    ucc_b = process(os.path.join(base, "scrape_ucc_filings", "scrape_ucc_filings.csv"),
                    os.path.join(out, "scrape_ucc_filings", "scrape_ucc_filings_v2.csv"),
                    lambda r: flag_ucc(r, lenders), counts, "ucc", den_city)
    # registrations: first pass counts registrations per address and suite
    reg_src = os.path.join(base, "scrape_business_registrations", "scrape_business_registrations.csv")
    addr_count = Counter()
    with open(reg_src, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            k = reg_addr_key(r)
            if k: addr_count[k] += 1
    left = Counter()
    def reg_fn(r):
        rules, why = flag_reg(r, addr_count)
        if why: left[why] += 1
        return rules
    reg_b = process(reg_src, os.path.join(out, "scrape_business_registrations", "scrape_business_registrations_v2.csv"),
                    reg_fn, counts, "reg", den_city)
    counts["reg"]["left_out_status"] = left["status"]; counts["reg"]["left_out_agent_address"] = left["agent"]
    # permits
    per_b = process(os.path.join(base, "scrape_denver_commercial_permits.csv"),
                    os.path.join(out, "scrape_denver_commercial_permits_v2.csv"),
                    lambda r: flag_permit(r, strict_parcel), counts, "permits", lambda r: True)

    # ---- combined flagged file. Home-address rule for tier B UCC and registration rows:
    # a street address is shown only if it has a suite or unit, appears in a site-based source, or is
    # shared by two or more business names. Otherwise "withheld" (zip kept).
    site_keys = set()
    tierA_rows = []
    with open(os.path.join(base, "scrape_flagged.csv"), newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            tierA_rows.append(r)
    for fn_ in ("scrape_denver_commercial_permits.csv", "scrape_denver_site_plans.csv", "scrape_state_water_permits.csv",
                "scrape_apcd_permit_status.csv", "scrape_mile_high_cre.csv"):
        with open(os.path.join(base, fn_), newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                k = addr_key(r["site_address"])
                if k: site_keys.add(k)
    names_at = defaultdict(set)
    for path in (os.path.join(base, "scrape_ucc_filings", "scrape_ucc_filings.csv"), reg_src):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                k = addr_key(r["site_address"])
                if k and len(names_at[(k, r["zip"][:5])]) < 3:
                    names_at[(k, r["zip"][:5])].add(re.sub(r"[^A-Z0-9]", "", r["company_name"].upper())[:25])
    withheld = 0
    with open(os.path.join(out, "scrape_flagged_v2.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(SHARED + ["flag_tier", "flag_rule_v2"])
        for r in tierA_rows:
            w.writerow([r[c] for c in SHARED] + ["A", r["flag_rule"]])
        for src_rows, personal in ((ucc_b, True), (reg_b, True), (per_b, False)):
            for r in src_rows:
                row = dict(r); row["flag"] = "Y"
                if personal and row["site_address"]:
                    k = addr_key(row["site_address"])
                    ok = bool(HAS_UNIT.search(row["site_address"])) or (k in site_keys and row["city"].strip().upper() == "DENVER") \
                        or len(names_at.get((k, row["zip"][:5]), ())) >= 2
                    if not ok:
                        row["site_address"] = "withheld (home-address rule; see source record)"; withheld += 1
                w.writerow([row[c] for c in SHARED] + [row["flag_tier"], row["flag_rule_v2"]])
    counts["flagged_v2"]["tierA"] = len(tierA_rows)
    counts["flagged_v2"]["tierB"] = len(ucc_b) + len(reg_b) + len(per_b)
    counts["flagged_v2"]["tierB_addresses_withheld"] = withheld
    counts["settings"]["lender_version_" + lender_version] = 1
    counts["settings"]["strict_parcel"] = int(strict_parcel)
    # lender breakdown for B1b
    lb = Counter()
    for r in ucc_b:
        for part in r["flag_rule_v2"].split("; "):
            if part.startswith("B1b"):
                lb[part.rsplit(": ", 1)[1]] += 1
    counts["b1b_by_lender"] = lb
    wb = Counter()
    for r in ucc_b:
        for part in r["flag_rule_v2"].split("; "):
            if part.startswith("B1a"):
                for x in part.rsplit(": ", 1)[1].split(", "): wb[x] += 1
            if part.startswith("B1c"): wb["c:" + part.rsplit(": ", 1)[1]] += 1
    counts["b1a_b1c_by_word"] = wb
    rw = Counter(r["flag_rule_v2"].rsplit(": ", 1)[1] for r in reg_b)
    counts["b2a_by_word"] = rw
    with open(os.path.join(out, "reflag_counts.json"), "w") as f:
        json.dump({k: dict(v) for k, v in counts.items()}, f, indent=1, sort_keys=True)
    for k in counts:
        print(k, dict(sorted(counts[k].items(), key=lambda x: (-x[1] if isinstance(x[1], int) else 0, x[0]))))

if __name__ == "__main__":
    main()
