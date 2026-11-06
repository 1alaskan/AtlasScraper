#!/usr/bin/env python3
"""Pull Town of Frederick building permits (Accela mirrored to the town's ArcGIS Enterprise
server) into the step 4 shared format.

Usage:  python3 pull_frederick_building_permits.py [--since YYYY-MM-DD] [--fresh] [--no-zoning]

Layer: Building_Permits/MapServer/0 (point layer, 24,538 rows on 2026-11-06). This is the
complete mirror; the table layer Accela_Building_Permits/FeatureServer/3 that discovery and
step 2 used holds only 19,578 rows because it drops Accela-era permits whose status is Closed
(Complete, Withdrawn, Denied), so it misses 1,368 of the 2,387 permits opened since 2024.
Accela_Building_Permits_for_Notebook/FeatureServer/0 is the same 24,538-row point layer
under another name.

Scope: PermitType not starting with 'Residential', OpenedDate >= --since (default
2024-01-01), plus (default run only) 2023 non-residential permits whose Status is still
active (not Closed, Permit Expired, Finaled, Cancelled, Void). Residential types and the
'Plans Review Application' type (single-family master plan submittals) are counted and left
out.

--since  OpenedDate cursor; any value other than 2024-01-01 writes to
         scrape_<slug>_since_<date>.csv so the full file is kept, and skips the 2023 carry-in.
--fresh  ignore today's raw cache and refetch.
--no-zoning  skip the zoning polygon lookup (zoning column left blank).
Raw pages are cached under ../raw/frederick_building_permits/<since>_<UTC day>/.

Flag rules (the layer has no valuation field, so the brief's no-valuation tier A applies):
  A   : construction class (Commercial New Construction, Addition, Alteration, Foundation,
        Accessory Structure, Change of Use) AND an industrial word in the description
        or the project title (the brief's no-valuation rule).
  B3b : every other non-residential permit on industrial property (ACCTTYPE Industrial,
        zoning I, LI-FLEX, HI-FLEX or BLI, or a subdivision named Industrial), or a trade or
        accessory permit with an industrial word in its description or title.
  N   : everything else in scope.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frederick_common as fc

LAYER = fc.GIS + "/Building_Permits/MapServer/0"
TABLE_LAYER = fc.GIS + "/Accela_Building_Permits/FeatureServer/3"   # incomplete; documented only
PARCELS = fc.GIS + "/Accela_Building_Permits/FeatureServer/0"
SLUG = "frederick_building_permits"
SOURCE = "Frederick building permits"
OUT = os.path.join(fc.WELD_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "FullAddress", "PermitId", "PermitType", "Status", "Description", "UpdateDate",
          "StatusDate", "OpenedDate", "ClosedDate", "ParcelID", "Name", "CustomId"]
PARCEL_FIELDS = ["PARCEL", "ACCOUNTNO", "ACCTTYPE", "BUSINESSNA", "NAME", "SITUS", "LOCCITY", "SUBNAME",
                 "GIS_Acres", "latitude", "longitude"]

EXTRA_COLS = ["permit_type", "permit_class", "application_stage", "superseded_by", "status", "status_date",
              "issued_date", "finaled_date", "updated_date", "parcel", "valuation", "square_feet", "zoning",
              "land_use", "parcel_owner", "parcel_business", "subdivision", "parcel_acres",
              "industrial_word", "industrial_word_field", "project_title", "accela_record_id",
              "latitude", "longitude", "parser_version"]

TEST_RECORD = re.compile(r"^\s*(test\b|testest|yrdyryd|commercial fee estimator)", re.I)

# Statuses that mean a 2023 permit is finished. Anything else (including null) counts as active.
CLOSED = re.compile(r"closed|final|cancel|expired|void|denied|withdrawn", re.I)

# Permit types treated as construction permits for tier A (new building, addition, tenant
# finish or alteration, change of use, foundation, accessory structure).
CONSTRUCTION = re.compile(r"^Commercial (New Construction|Addition|Alteration|Foundation|Accessory Structure|"
                          r"Change of Use|Tenant)", re.I)

KNOWN_COMPANIES = re.compile(
    r"\b(Agilent(?: Technologies)?|Project Endeavor|Project Synergy|Clearway(?: Energy)?|Tesla|Brakes Plus|Transwest|"
    r"Stapp(?: Interstate)? Toyota|Stevinson (?:Lexus|Hyundai)|Craft Solutions|Mile High Metal Works|Full Metal Iron|Golden Triangle Construction|"
    r"Forge X(?: Workspaces)?|Flight Workspaces|Allied Auto Importers|Freedom Carwash|Mister Carwash|Carbon Valley (?:Rec|Recreation)(?: District)?|"
    r"Spindle(?: Hill)? BESS|Spindle Hill(?: Energy)?|Civitas|Chevron|Kerr[- ]McGee|Noble Energy|Extraction Oil|"
    r"Crestone|Bayswater|Bonanza Creek|Xcel(?: Energy)?|United Power|Comcast|Lumen|CenturyLink|Verizon|T-Mobile|AT&T|"
    r"Crown Castle|American Tower|King Soopers|Safeway|Walmart|Costco|Amazon|FedEx|QuikTrip|Murphy(?: USA)?|"
    r"Circle K|7-Eleven|Starbucks|McDonald'?s|Chipotle(?: Mexican Grill)?|Dutch Bros|Kum (?:&|and) Go|Maverik|Les Schwab|Discount Tire|"
    r"Big O Tires|O'?Reilly|Auto ?Zone|NAPA|Tractor Supply|Ace Hardware|Home Depot|Lowe'?s|Dollar (?:General|Tree)|"
    r"Family Dollar|Walgreens|CVS|Planet Fitness|Anytime Fitness|Orangetheory|Club Pilates|Chick-fil-A|Wendy'?s|Taco Bell|Sonic|"
    r"Arby'?s|Burger King|Popeyes|Raising Cane'?s|Culver'?s|Freddy'?s|Jimmy John'?s|Jersey Mike'?s|Domino'?s(?: Pizza)?|"
    r"Papa John'?s|Little Caesars|Pizza Hut|Dairy Queen|Dunkin(?:'? Donuts)?|Wing ?Stop|Cold ?Stone(?: Creamery)?|Great Clips|"
    r"(?:5|Five) Guys|Pacific Dental|Dentists of Frederick|Tri[- ]City Dental|Blu Sky Nails|Valvoline(?: Instant Oil Change)?|"
    r"Christian Brothers Automotive|Colorado Pavement|Quantum Canning|Trailer Source|Longs Peak Learning Center|"
    r"Wells Fargo|Chase Bank|Bank of America|Bellco|Elevations|FirstBank|UPS Store|"
    r"Frederick[- ]Firestone Fire(?: Protection District)?|St\.? Vrain Valley School(?: District)?|St\.? Vrain Sanitation District|"
    r"Town of Frederick|Frederick Public Works|Weld County|CDOT|Colorado Department of Transportation|Great Western|"
    r"4 Rivers Equipment|Traffic Signal Controls|Hirsh Precision|Meadowlark Optics|Toro Robotics|Smith Power Products|"
    r"Equipment ?Share|Guardian Storage|Centura Health|Halleck (?:&|and) Willard|Brinkmann Constructors|Dream Finder(?:s)? Homes|"
    r"Vestas|Microvast|JBS|Leprino|Pepsi|Coca[- ]Cola|Frito[- ]Lay|Sysco|US Foods|Shamrock|"
    r"Martin Marietta|Holcim|Cemex|Aggregate Industries|Brannan|Kiewit|Mortenson|Hensel Phelps|JE Dunn|Saunders|"
    r"GH Phipps|Adolfson (?:&|and) Peterson|Bryan Construction|Ryan Companies|Scannell|Prologis|Hines|Majestic|"
    r"Etkin|Confluent|Westfield|Trammell Crow|Panattoni|Lincoln Property|Schuck|McWhinney|Brinkman)\b", re.I)

# Accela convention: the business name leads the description followed by two or more hyphens
# ("Chipotle Mexican Grill--Restaurant Tenant Finish", "CHASE BANK -- Construction of ...").
PREFIX_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9&'./ ]{1,50}?)\s*-{2,}")

# "for <Company>" captures: a run of capitalised words (case-sensitive on the capture).
FOR_PATTERN = re.compile(
    r"\b(?:[Ff]or|[Tt]enant:|[Oo]ccupant:|[Oo]wner:|[Bb]usiness:|[Cc]lient:|[Dd][Bb][Aa])\s+(?:the\s+)?"
    r"((?:[A-Z][\w&'-]*\.?)(?:\s+(?:[A-Z][\w&'-]*\.?|of|and|&|de))*)")

# Capture fragments that are work descriptions rather than names.
GENERIC_WORDS = re.compile(
    r"(tenant|finish|finishes|improvement|improvements|project|phase|area|room|space|building|bldg|unit|suite|"
    r"foundation|only|canopy|canopies|irrigation|meter|sign|signs|signage|trailer|temp|temporary|"
    r"install|installation|new|existing|interior|exterior|remodel|addition|alteration|construction|"
    r"commercial|retail|office|offices|storage|warehouse|equipment|machine|machines|hvac|electrical|"
    r"mechanical|plumbing|fire|sprinkler|roof|solar|generator|pool|kitchen|bathroom|restroom|"
    r"approx|approximately|sq|sqft|sf|square|feet|ft|lot|block|future|proposed|same|this|that|all|"
    r"each|owner|customer|employees|staff|public|private|general|use|uses|work|scope|permit|"
    r"north|south|east|west|the|a|an|and|of|or|at|in|on|to|with|per|by|from|is|are|be|will|was|were|"
    r"has|have|said|see|drawings|plans|master|plan|modular|substation|control|maint|maintenance|facility)", re.I)

STRIP_SUFFIX = re.compile(r"\s+(sign|signs|signage|trailer|temp trailer|temporary trailer|foundation only|foundation|"
                          r"construction trailer|ti|tenant finish|tenant improvement|remodel|addition|canopies|canopy)\s*$", re.I)

STRICT_HINT = re.compile(fc.BUSINESS_HINT.pattern.replace("dba|d/b/a|of|the|et al|etal|", "dba|d/b/a|et al|etal|")
                         + r"|\b(nails?|dentists?|dental|orthodont\w*|chiropract\w*|pilates|yoga|crossfit|learning|preschool|"
                         r"montessori|carwash|car wash|lube|tires?|collision|detailing|cleaners|laundry|barber|tattoo|vape|smoke|"
                         r"donuts?|bagels?|creamery|wings?|burgers?|taco\w*|sushi|thai|bbq|bistro|kitchen|cantina|taproom|pub|tavern|"
                         r"saloon|lounge|winery|roasters|juice|nutrition|optics|optical|vision|robotics|offroad|golf cars|insurance|"
                         r"agency|attorneys?|law|accounting|cpa|staffing|consulting|marketing|media|design|architects?|surveying|"
                         r"mortgage|lending|financial|wealth|advisors|canning|pavement|precision|learning center|workspaces?|"
                         r"chapel|worship|christian|baptist|lutheran|methodist|catholic|episcopal|sanitation|public works|"
                         r"urgent care|emergency|pediatric\w*|hospice|senior living|assisted living|memory care|kids|kidz|"
                         r"martial arts|karate|dance|climbing|bowling|arcade|trampoline|grooming|kennel|feed|nursery|greenhouse|"
                         r"landscap\w*|fencing|garage door|overhead door|windows?|siding|gutters?|insulation|drywall|painting|"
                         r"flooring|carpet|countertops?|cabinets?|blinds|lighting|appliance\w*|mattress|furniture|decor|thrift|"
                         r"pawn|jewel\w*|boutique|apparel|clothing|shoes|sports|cycles?|bikes?|bicycles?|motorcycles?|powersports|"
                         r"marine|rv|transmission|muffler|brakes?|alignment|body shop|tint|audio|computers?|electronics|"
                         r"shipping|mail|postal|notary|tax|bookkeeping|payroll|title|bank|branch|grocery|grill|source|moments|"
                         r"image|mirror|homes|tooling|molding|mold\w*|plating|coatings?|stamping|forging|"
                         r"casting|foundry|extrusion|fabrication|machining|welding|powder|cnc)\b", re.I)


def acceptable_company(cand):
    """A candidate name is kept when it reads as a business (a business word or a known name)
    and not as a person or a work description. Returns the cleaned name or ''."""
    c = fc.clean(cand).strip(" .,;:-*")
    c = re.sub(r"^(the|a|an)\s+", "", c, flags=re.I)
    c = STRIP_SUFFIX.sub("", c).strip(" .,;:-")
    words = c.split()
    if not words or len(words) > 6:
        return ""
    if re.match(r"^\d", c) or re.search(r"\bnot buildable\b", c, re.I):
        return ""
    content = [w for w in words if not re.fullmatch(r"(of|and|&|the|de|\d+)", w, re.I)]
    if not content or all(GENERIC_WORDS.fullmatch(w.strip(".,")) for w in content):
        return ""
    if len(content) < 2 and not KNOWN_COMPANIES.search(c):
        return ""
    if not reads_as_business(c):
        return ""
    if KNOWN_COMPANIES.search(c) or STRICT_HINT.search(c):
        return c
    return ""


def reads_as_business(name):
    """A known company or a name with a business word is a business; otherwise a name of one to
    four plain words (or a personal trust) is treated as a person and dropped."""
    if KNOWN_COMPANIES.search(name) or STRICT_HINT.search(name):
        return not fc.PERSON_TRUST.search(name)
    return not (fc.looks_like_individual(name) or fc.looks_like_individual_party(name))


def extract_company(desc, title):
    """A tenant or project name read from the project title or the description. Order: a known
    company name anywhere; the Accela 'Name -- scope' prefix; the project title; a
    'for <Company>' capture. Returns (company, role)."""
    text = " ".join([title or "", desc or ""])
    m = KNOWN_COMPANIES.search(text)
    if m:
        c = re.sub(r"\s+", " ", m.group(0)).strip()
        role = "project" if c.lower().startswith("project ") else "tenant"
        return c, role
    m = PREFIX_PATTERN.match(desc or "")
    if m:
        c = acceptable_company(m.group(1))
        if c:
            return c, "tenant"
    if title:
        c = acceptable_company(title)
        if c:
            return c, "tenant"
    for seg in re.split(r"(?<!\bSt)(?<!\bMt)\.\s|\s-{1,}\s|;|\(|\)", desc or ""):
        for m in FOR_PATTERN.finditer(seg):
            c = acceptable_company(m.group(1))
            if c and (len(c.split()) >= 2 or KNOWN_COMPANIES.search(c)):
                return c, "tenant"
    return "", ""


def business_parts(value):
    """A parcel's business field is a multi-tenant list ('A/B/C') or 'Firm, Person'. Keep the
    parts that read as a business (a known chain, or not a plain personal name)."""
    out = []
    for part in value.split("/"):
        part = part.strip()
        if not part:
            continue
        if KNOWN_COMPANIES.search(part):
            out.append(part)
            continue
        # 'Firm, Person' lists: drop a comma part that is a plain personal name
        bits = [b.strip() for b in part.split(",") if b.strip()]
        keep = [b for b in bits if KNOWN_COMPANIES.search(b) or STRICT_HINT.search(b) or not fc.looks_like_individual(b)]
        if keep and all(re.fullmatch(r"(inc|llc|corp|co|ltd|lp|llp|pc)\.?", b, re.I) for b in keep):
            keep = []
        part = ", ".join(keep)
        if part and reads_as_business(part):
            out.append(part)
    return out


def permit_class(ptype):
    p = (ptype or "").lower()
    if "new construction" in p:
        return "new"
    if "addition" in p:
        return "addition"
    if "alteration" in p:
        return "alteration"
    if "foundation" in p:
        return "foundation"
    if "accessory" in p:
        return "accessory"
    if "change of use" in p:
        return "change of use"
    if "demolition" in p:
        return "demolition"
    if "grading" in p:
        return "grading"
    if re.search(r"electrical|mechanical|plumbing|roofing|solar|fire|sprinkler|sign|water tap|communication|"
                 r"temporary|plug and abandon|generator|racking|trailer", p):
        return "trade or accessory"
    return "other"


def split_name(name):
    """Name is '<address>, FREDERICK, CO <zip> : <project title>' on most rows and
    '<project title> -- <address>' on some. Returns (zip, title)."""
    n = fc.clean(name).rstrip(": ").strip()
    zip5, title = "", ""
    m = re.search(r"\b(80\d{3})\b", n)
    if m:
        zip5 = m.group(1)
    if " : " in n:
        title = n.split(" : ", 1)[1].strip()
    elif n and not re.match(r"^\d", n):
        m = re.match(r"^(.*?)\s*-{2,}\s*(.*)$", n) or re.match(r"^(.*?)\s*-+\s*\d.*$", n)
        title = m.group(1).strip() if m else n
    return zip5, title


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--no-zoning", action="store_true")
    a = ap.parse_args()
    out = OUT if a.since == "2024-01-01" else OUT.replace(".csv", "_since_%s.csv" % a.since)
    day = fc.now_iso()[:10].replace("-", "")
    cache = os.path.join(fc.RAW_ROOT, SLUG, "%s_%s" % (a.since, day))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    fc.require_fields(LAYER, FIELDS)
    nonres = "(PermitType NOT LIKE 'Residential%' OR PermitType IS NULL)"
    where_main = "OpenedDate >= DATE '%s' AND %s" % (a.since, nonres)
    n_main = fc.source_count(LAYER, where_main)
    n_res_main = fc.source_count(LAYER, "OpenedDate >= DATE '%s' AND PermitType LIKE 'Residential%%'" % a.since)
    print("source count since %s: non-residential %d, residential (left out) %d" % (a.since, n_main, n_res_main))
    feats = fc.fetch_all(LAYER, where_main, FIELDS, os.path.join(cache, "main"), page_size=2000)
    if len(feats) != n_main:
        raise SystemExit("ROW COUNT MISMATCH on the main pull: %d fetched, source says %d" % (len(feats), n_main))

    n_2023 = n_res_2023 = 0
    carry, dropped_2023 = [], Counter()
    if a.since <= "2024-01-01":
        where_2023 = "OpenedDate >= DATE '2023-01-01' AND OpenedDate < DATE '2024-01-01' AND %s" % nonres
        n_2023 = fc.source_count(LAYER, where_2023)
        n_res_2023 = fc.source_count(LAYER, "OpenedDate >= DATE '2023-01-01' AND OpenedDate < DATE '2024-01-01' "
                                            "AND PermitType LIKE 'Residential%'")
        f2023 = fc.fetch_all(LAYER, where_2023, FIELDS, os.path.join(cache, "y2023"), page_size=2000)
        if len(f2023) != n_2023:
            raise SystemExit("ROW COUNT MISMATCH on the 2023 pull: %d fetched, source says %d" % (len(f2023), n_2023))
        for f in f2023:
            st = fc.clean(f["attributes"].get("Status"))
            if st and CLOSED.search(st):
                dropped_2023[st] += 1
            else:
                carry.append(f)
        print("2023 non-residential: %d fetched, %d still active carried in, %d left out: %s"
              % (n_2023, len(carry), sum(dropped_2023.values()), dict(dropped_2023)))
    feats = feats + carry

    # Residential master plan submittals typed 'Plans Review Application' are left out too, as are
    # the town's own Accela test records (description 'test...', 'fee estimator' at town hall).
    plans_review = [f for f in feats if fc.clean(f["attributes"].get("PermitType")) == "Plans Review Application"]
    feats = [f for f in feats if fc.clean(f["attributes"].get("PermitType")) != "Plans Review Application"]
    test_rows = [f for f in feats if TEST_RECORD.search(fc.clean(f["attributes"].get("Description")))
                 and fc.clean(f["attributes"].get("FullAddress")).upper().startswith("401 LOCUST")]
    feats = [f for f in feats if f not in test_rows]

    # Parcel attributes (land use, owner, situs) for every parcel in the pull.
    parcel_ids = {fc.clean(f["attributes"].get("ParcelID")) for f in feats}
    parcel_ids = {p for p in parcel_ids if re.fullmatch(r"\d{12}", p)}
    parcels = fc.fetch_by_keys(PARCELS, "PARCEL", parcel_ids, PARCEL_FIELDS, os.path.join(cache, "parcels"), batch=200)
    print("parcels looked up: %d of %d matched" % (len(parcels), len(parcel_ids)))

    zoning = None if a.no_zoning else fc.load_zoning(cache)

    rows, seen = [], set()
    dup_ids = 0
    for f in feats:
        at = f["attributes"]
        geom = f.get("geometry") or {}
        custom = fc.clean(at.get("CustomId"))
        rid = custom or fc.clean(at.get("PermitId"))
        if rid in seen:
            dup_ids += 1
            continue
        seen.add(rid)
        ptype = fc.clean(at.get("PermitType"))
        desc = fc.clean(at.get("Description"))
        zip5, title = split_name(at.get("Name"))
        if title and not reads_as_business(title) and not GENERIC_WORDS.fullmatch(title.split()[0]):
            title = ""          # a one- to four-word plain name with no business word: possibly a person
        parcel = fc.clean(at.get("ParcelID"))
        if not re.fullmatch(r"\d{12}", parcel):
            parcel = "" if parcel.lower() in ("unknown", "none", "n/a", "") else parcel
        pa = (parcels.get(parcel) or [{}])[0]
        land_use = fc.clean(pa.get("ACCTTYPE"))
        owner = fc.clean(pa.get("NAME"))
        if owner and fc.looks_like_individual_party(owner):
            owner = ""
        pbus = fc.clean(pa.get("BUSINESSNA")).strip("* ")
        if re.search(r"\bnot buildable\b", pbus, re.I):
            pbus = ""
        pbus = "/".join(business_parts(pbus))
        x, y = geom.get("x"), geom.get("y")
        if (x is None or y is None) and pa.get("latitude"):
            x, y = pa.get("longitude"), pa.get("latitude")
        zone = ""
        if zoning is not None and x is not None and y is not None:
            z = zoning.find(x, y)
            if z:
                zone = fc.clean(z.get("ZONE_CODE"))
        addr = fc.clean(at.get("FullAddress"))
        if not addr and pa.get("SITUS"):
            addr = re.sub(r"\s+FREDERICK$", "", fc.clean(pa.get("SITUS")), flags=re.I)
        addr = re.sub(r"\s+FREDERICK$", "", addr, flags=re.I)
        company, role = extract_company(desc, title)
        if not company and pbus:
            company, role = pbus, "tenant"

        # industrial evidence, searched in order
        word, field = "", ""
        for fld, val in (("description", desc), ("project_title", title), ("land_use", land_use),
                         ("zoning", zone), ("parcel_business", pbus), ("subdivision", fc.clean(pa.get("SUBNAME")))):
            if fld == "land_use":
                if land_use.lower() == "industrial":
                    word, field = "industrial", fld
                    break
                continue
            if fld == "zoning":
                if zone in fc.INDUSTRIAL_ZONES:
                    word, field = fc.ZONE_NAMES.get(zone, zone), fld
                    break
                continue
            m = fc.INDUSTRIAL_WORDS.search(val or "")
            if m:
                word, field = m.group(0), fld
                break
        industrial_property = (land_use.lower() == "industrial" or zone in fc.INDUSTRIAL_ZONES
                               or bool(re.search(r"\bindustrial\b", fc.clean(pa.get("SUBNAME")), re.I)))
        pclass = permit_class(ptype)
        flag, rule = "N", ""
        word_in_text = bool(word) and field in ("description", "project_title")
        if CONSTRUCTION.match(ptype) and word_in_text:
            flag, rule = "Y", "A: construction permit + industrial word (no valuation in layer)"
        elif industrial_property:
            flag, rule = "Y", "B3b: no valuation, non-residential on industrial property"
        elif word_in_text:
            flag, rule = "Y", "B3b: no valuation, industrial word on trade or accessory permit"
        stage = "temporary application id (unsubmitted draft)" if re.match(r"^\d\dTMP-", rid) else "permit"

        rows.append({
            "source": SOURCE, "source_level": fc.SOURCE_LEVEL, "record_id": rid,
            "record_date": fc.ms_to_date(at.get("OpenedDate")), "date_type": "opened",
            "record_type": ptype,
            "company_name": company, "company_role": role,
            "site_address": addr, "city": fc.CITY, "county": fc.COUNTY, "zip": zip5,
            "description": fc.clean(desc, 500),
            "flag": flag, "flag_rule": rule,
            "source_url": fc.layer_query_url(LAYER, "CustomId='%s'" % rid if custom else "PermitId='%s'" % rid),
            "retrieved_at": f["_fetched_at"],
            "permit_type": ptype, "permit_class": pclass, "application_stage": stage, "superseded_by": "",
            "status": fc.clean(at.get("Status")), "status_date": fc.ms_to_date(at.get("StatusDate")),
            "issued_date": "", "finaled_date": fc.ms_to_date(at.get("ClosedDate")),
            "updated_date": fc.ms_to_date(at.get("UpdateDate")),
            "parcel": parcel, "valuation": "", "square_feet": "",
            "zoning": zone, "land_use": land_use,
            "parcel_owner": owner, "parcel_business": pbus,
            "subdivision": fc.clean(pa.get("SUBNAME")), "parcel_acres": ("%.3f" % pa["GIS_Acres"]) if pa.get("GIS_Acres") else "",
            "industrial_word": word, "industrial_word_field": field,
            "project_title": fc.clean(title, 200), "accela_record_id": fc.clean(at.get("PermitId")),
            "latitude": "%.6f" % y if y is not None else "", "longitude": "%.6f" % x if x is not None else "",
            "parser_version": fc.PARSER_VERSION})

    # square footage from the description when stated
    for r in rows:
        m = re.search(r"(\d[\d,]{2,})[\s-]*(?:sq\.?\s*ft|sf\b|square\s*f(?:ee|oo)t|sqft)", r["description"], re.I)
        if m:
            r["square_feet"] = m.group(1).replace(",", "")
    # a temporary application that became a permit: same address and same opening text
    by_key = {}
    for r in rows:
        if r["application_stage"] == "permit" and r["site_address"]:
            by_key.setdefault((r["site_address"].upper(), r["description"][:60].upper()), []).append(r["record_id"])
    for r in rows:
        if r["application_stage"] != "permit":
            hits = by_key.get((r["site_address"].upper(), r["description"][:60].upper()), [])
            r["superseded_by"] = ";".join(hits)
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    fc.write_csv(out, fc.COMMON_COLS + EXTRA_COLS, rows)

    print("rows written: %d (source: %d since %s + %d active 2023, minus %d Plans Review Application rows and %d test records)"
          % (len(rows), n_main, a.since, len(carry), len(plans_review), len(test_rows)))
    print("test records left out:", [(fc.clean(f["attributes"].get("CustomId")) or f["attributes"].get("PermitId"), f["attributes"].get("Description")) for f in test_rows])
    print("duplicate permit numbers skipped:", dup_ids)
    print("residential left out: %d since %s + %d in 2023 = %d; plus %d Plans Review Application (residential master plans)"
          % (n_res_main, a.since, n_res_2023, n_res_main + n_res_2023, len(plans_review)))
    print("flags:", Counter(r["flag_rule"] or "N" for r in rows).most_common())
    print("types:", Counter(r["record_type"] for r in rows).most_common())
    print("industrial field:", Counter(r["industrial_word_field"] for r in rows if r["industrial_word"]).most_common())
    print("zoning:", Counter(r["zoning"] for r in rows).most_common(12))
    print("land use:", Counter(r["land_use"] for r in rows).most_common())
    print("stage:", Counter(r["application_stage"] for r in rows), "superseded:", sum(1 for r in rows if r["superseded_by"]))
    for c in ("company_name", "site_address", "record_date", "zip", "parcel", "latitude", "status", "zoning", "land_use"):
        print("  null %s: %d" % (c, sum(1 for r in rows if not r[c])))
    print("company roles:", Counter(r["company_role"] for r in rows if r["company_name"]))
    print("company names:", Counter(r["company_name"] for r in rows if r["company_name"]).most_common(60))


if __name__ == "__main__":
    main()
