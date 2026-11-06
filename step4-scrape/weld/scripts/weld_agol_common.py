"""Shared helpers for the county_agol group's Weld County pulls (step 4).

Standard library only. Paged ArcGIS Online REST queries with a raw cache on disk,
key-batched lookups, the 17 shared output columns, the planner and contact scrub,
the screens that keep personal names out of company_name, Ownership-table joins,
and the first_seen / last_seen snapshot files that the undated layers need.

All four layers live on the Weld County AGOL org (ewjSqmSyHJnkfBLL). Dates come
back as epoch milliseconds in UTC (Ownership SALEDT is an ISO DateOnly string).
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "step4-research-pull/1.0"
PAUSE = 1.0          # seconds between requests
MAX_ERRORS = 3       # stop after this many consecutive failures on one request
PARSER_VERSION = "county_agol-1.0"

HOST = "https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services"
PLANNING_CASES = HOST + "/Planning_Cases_for_Development_Activity_Map_view/FeatureServer/0"
SPR = HOST + "/Site_Plan_Review_open_data/FeatureServer/0"
SALES = HOST + "/Sales_Point_open_data/FeatureServer/1"
OWNERSHIP = HOST + "/Ownership2/FeatureServer/17"

HERE = os.path.dirname(os.path.abspath(__file__))
WELD_DIR = os.path.dirname(HERE)                       # step4-scrape/weld
RAW_ROOT = os.path.join(WELD_DIR, "raw")               # git-ignored

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]
SOURCE_LEVEL = "County (Weld)"
COUNTY = "Weld"
UNINC = "Unincorporated Weld County"

OWNERSHIP_FIELDS = ["OBJECTID", "ACCOUNTNO", "NAME", "PARCELNB", "ACCTTYPE", "BUSINESSNAME",
                    "STREETNO", "STREETNAME", "STREETALP", "STREETDIR", "STREETSUF", "LOCCITY",
                    "CITY", "SUBNAME", "SALEDT", "SALEP", "DEEDTYPE", "RECEPTION_NO"]

# Words that mark an industrial use in a description, title, zoning or building use
# (the brief's list for the planning layers plus the Denver and Adams vocabulary).
INDUSTRIAL_WORDS = re.compile(
    r"\b(industrial|industry|warehous\w*|manufactur\w*|distribution|flex|data cent\w*|"
    r"plant|process\w*|equipment|crane|tanks?|silos?|compressor\w*|compressor station|"
    r"dust collect\w*|paint booth|spray booth|boiler\w*|generator\w*|fabricat\w*|machin\w*|"
    r"logistics|cold storage|freezer|refrigerat\w*|food production|brewery|brewing|distill\w*|"
    r"bottling|packaging|recycl\w*|conveyor\w*|racking|mezzanine|truck terminal|trucking|"
    r"batch plant|concrete plant|asphalt|aggregate|lumber ?yard|woodworking|roaster|roasting|"
    r"oil and gas facility|gas processing|gas plant|gathering|midstream|injection|"
    r"laborator\w*|clean ?room|seed (storage|processing|distribution)|hemp processing|"
    r"i-1|i-2|i-3|heavy industrial|light industrial|general industrial|business park|"
    r"industrial park|core (and|&) shell|shell building)\b",
    re.I)

# Terms that mark a business or institution rather than a person.
# Strong corporate tokens: a name carrying one of these is never read as a person by the given-name rule below.
STRONG_CORP = re.compile(r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|limited|lp|llp|lllp|pllc|pc|plc|gmbh|"
                         r"trust|partnership|partners|holdings?|group|enterprises?|association|assn|assoc|foundation|church|ministries|"
                         r"district|county|city|town|state|university|school|bank|credit union|properties|investments?|development|"
                         r"farms?|ranch|homes|apartments?|estates|ventures?|fund|reit|hoa|authority|commission|board|department|"
                         r"industries|international|national|systems|services|solutions|technologies|energy|resources|"
                         r"construction|builders|contractors?|logistics|trucking|manufacturing|products|dba|d/b/a)\b", re.I)
# Common given names (assessor names run SURNAME GIVEN MIDDLE), used only with the rule above.
GIVEN_NAMES = set("""JAMES JOHN ROBERT MICHAEL WILLIAM DAVID RICHARD JOSEPH THOMAS CHARLES CHRISTOPHER DANIEL MATTHEW ANTHONY MARK DONALD
STEVEN PAUL ANDREW JOSHUA KENNETH KEVIN BRIAN GEORGE TIMOTHY RONALD EDWARD JASON JEFFREY RYAN JACOB GARY NICHOLAS ERIC JONATHAN
STEPHEN LARRY JUSTIN SCOTT BRANDON BENJAMIN SAMUEL GREGORY ALEXANDER FRANK PATRICK RAYMOND JACK DENNIS JERRY TYLER AARON JOSE
ADAM NATHAN HENRY DOUGLAS ZACHARY PETER KYLE NOAH ETHAN JEREMY WALTER CHRISTIAN KEITH ROGER TERRY AUSTIN SEAN GERALD CARL
HAROLD DYLAN ARTHUR LAWRENCE JORDAN JESSE BRYAN BILLY BRUCE GABRIEL JOE LOGAN ALAN JUAN ALBERT WILLIE ELIJAH WAYNE RANDY
VINCENT MASON ROY RALPH BOBBY RUSSELL BRADLEY PHILIP EUGENE LOUIS JESUS LEE LONNIE ROCKY DELON EMRON CLAYBORNE JAY TODD DALE
DUANE DWAYNE GLEN GLENN DEAN LYLE LLOYD LEROY CLIFFORD CLYDE CURTIS MARVIN MELVIN NORMAN VERNON WARREN WESLEY ALLEN ALLAN
MARY PATRICIA JENNIFER LINDA ELIZABETH BARBARA SUSAN JESSICA SARAH KAREN LISA NANCY BETTY MARGARET SANDRA ASHLEY KIMBERLY
EMILY DONNA MICHELLE CAROL AMANDA DOROTHY MELISSA DEBORAH STEPHANIE REBECCA SHARON LAURA CYNTHIA KATHLEEN AMY ANGELA SHIRLEY
ANNA BRENDA PAMELA EMMA NICOLE HELEN SAMANTHA KATHERINE CHRISTINE DEBRA RACHEL CAROLYN JANET CATHERINE MARIA HEATHER DIANE
RUTH JULIE OLIVIA JOYCE VIRGINIA VICTORIA KELLY LAUREN CHRISTINA JOAN EVELYN JUDITH MEGAN ANDREA CHERYL HANNAH JACQUELINE
MARTHA GLORIA TERESA ANN SARA MADISON FRANCES KATHRYN JANICE JEAN ABIGAIL ALICE JULIA JUDY SOPHIA GRACE DENISE AMBER DORIS
MARILYN DANIELLE BEVERLY ISABELLA THERESA DIANA NATALIE BRITTANY CHARLOTTE MARIE KAYLA ALEXIS LORI MOLLY ELLA VICKI VICKIE
ROBERTA TAMMY TAMI TONI TONYA CONNIE BONNIE PEGGY PATTY PATTI WANDA RHONDA LORRAINE LORETTA BRANDI BRANDY KRISTI KRISTIN
KRISTEN KRISTINE KIM SHERRY SHERRI TERRI TERRY TRACY TRACI STACY STACEY WENDY LESLIE LESLEY DARLENE ARLENE CHARLENE MARLENE""".split())
# Surnames that double as business or town words, so a hint in the first token alone does not make a company.
SURNAME_COLLISION = {"BARBER", "LAW", "STONE", "PIERCE", "GROVER", "EVANS", "EATON", "AULT", "HUDSON", "FREDERICK", "WINDSOR",
                     "MEAD", "KERSEY", "GILL", "CARR", "BAKER", "COOK", "FARMER", "MASON", "MILLER", "SMITH", "TAYLOR", "WRIGHT",
                     "FISHER", "HUNTER", "GARDNER", "CARPENTER", "COOPER", "BREWER", "BUTLER", "FOSTER", "PORTER", "WALKER", "WARD",
                     "WOOD", "WOODS", "FIELDS", "HILL", "HILLS", "RIVERS", "BROOKS", "LAKE", "SNOW", "FROST", "STEEL", "GLASS",
                     "BANKS", "BELL", "BISHOP", "CHURCH", "DEAN", "KNIGHT", "LORD", "MARSHALL", "PAGE", "PARKS", "POWER",
                     "POWERS", "RICH", "ROSE", "SHARP", "SHORT", "SMALL", "STRONG", "SWIFT", "WEST", "NORTH", "SOUTH", "EAST"}
BUSINESS_HINT = re.compile(
    r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|lp|llp|lllp|pllc|pc|"
    r"plc|gmbh|sa|construction|constructors?|contractors?|contracting|builders?|building|"
    r"group|services?|electric|electrical|mechanical|plumbing|roofing|restoration|"
    r"development|developers?|enterprises?|associates|partners|partnership|solutions|systems|"
    r"homes|properties|property|industries|industrial|interiors|remodeling|"
    r"renovations?|signs?|fire|steel|concrete|glass|events?|productions?|management|"
    r"engineering|commercial|general|facilities|facility|installations?|colorado|denver|"
    r"county|city|town|district|authority|university|school|church|ministries|"
    r"hospital|clinic|bank|credit union|trust co|holdings?|investments?|capital|realty|"
    r"real estate|land|ranch|farms?|dairy|foods?|logistics|trucking|transport\w*|"
    r"energy|solar|power|oil|gas|water|sanitation|metro\w*|housing|apartments?|"
    r"storage|self storage|supply|equipment|manufacturing|products|international|"
    r"national|american|america|usa|us|united|western|rocky mountain|mountain|"
    r"center|centre|park|plaza|village|estates|ventures?|acquisitions?|fund|reit|"
    r"owner|tenant|temple|foundation|association|assn|assoc|hoa|club|"
    r"dba|d/b/a|of|the|et al|etal|llc\.|inc\.|corp\.|co\.|ltd\.|lp\.|"
    r"brewing|brewery|coffee|market|motors?|auto\w*|dealership|hotel|motel|"
    r"restaurant|pizza|grill|cafe|bakery|liquor|store|shop|salon|dental|medical|"
    r"health|care|pharmacy|veterinary|animal|pet|childcare|daycare|academy|"
    r"state of|united states|federal|bureau|department|dept|board|commission|"
    r"railroad|railway|rail|airport|airlines?|union|local|lodge|post|legion|"
    r"creek|precast|remediation|hatchery|canopy|substation|"
    r"recovery|reclamation|paving|salvage|towing|recycling|asphalt|gravel|sand|pipe|"
    r"welding|machine|tool|crane|hvac|heating|cooling|plumb\w*|lumber|millwork|cabinet\w*|"
    r"granite|marble|stone|tile|metal|metals|iron|aluminum|plastics?|chemical\w*|"
    r"packaging|printing|labs?|technolog\w*|tech|data|network\w*|communications?|wireless|"
    r"cellular|tower|utility|utilities|pipeline|terminal|depot|yard|works|mfg|distributing|"
    r"distributors?|wholesale|imports?|exports?|express|freight|cargo|courier|delivery|"
    r"leasing|leases?|rentals?|rent|fitness|gym|studio|theat(er|re)|cinema|arena|stadium|"
    r"resort|lodging|inn|suites|golf|country club|cemetery|mortuary|funeral|labeling|"
    r"stockpile|crushing|emissions|testing|dump|landfill|mud|quarry|pit|batch|wind|hardware|"
    r"containers|expansion|redevelopment|revitalization|master plan|service plan|metropolitan|"
    r"fellowship|ministry|parish|congregation|mosque|synagogue|elevator|enclosures|"
    r"libraries|library|carts|automation|sortation|fiber|"
    # Weld additions: assessor business names and planning titles seen in the sample
    r"siding|log|plant|office|offices|fuel|feed|seeds?|grain|cattle|beef|meat|pork|poultry|"
    r"eggs?|ag|agri\w*|irrigation|drilling|operating|operations|midstream|resources|petroleum|"
    r"crude|compression|compressor|processing|nursery|greenhouse|landscap\w*|excavat\w*|"
    r"trenching|ready mix|redi|fab|fabrication|machining|flooring|carpet|paint|body|collision|"
    r"tires?|trailers?|rv|trucks?|diesel|repair|car wash|laundry|cleaners|taco|cantina|bar|"
    r"tavern|saloon|pub|winery|distillery|dispensary|cannabis|hemp|vape|smoke|mart|grocery|"
    r"deli|donuts?|burgers?|chicken|bbq|kitchen|catering|floral|flowers|photography|"
    r"embroidery|insurance|agency|financial|accounting|cpa|tax|law|attorney|chiropractic|"
    r"therapy|orthodont\w*|optometry|optical|vision|eye|pediatric\w*|urgent care|wellness|"
    r"spa|nails|barber|tanning|massage|yoga|crossfit|martial|karate|dance|learning|preschool|"
    r"montessori|kids|child|gymnastics|cheer|swim|grooming|boarding|kennel|feedlot|"
    r"fertilizer|propane|oilfield|mini|casino|bowling|chapel|cellars?|vineyard|orchard|"
    r"honey|bees|apiary|hay|straw|sod|turf|tree|trees|arbor\w*|pest|exterminat\w*|"
    r"security|alarm|locksmith|glass|window\w*|doors?|garage|overhead|fence|fencing|"
    r"pool|spas|hot tub|solar|roofing|gutters?|insulation|drywall|stucco|masonry|"
    r"framing|carpentry|custom|design|designs|studios?|consulting|consultants?|"
    r"medical|hospice|dialysis|imaging|radiology|surgery|surgical|ambulance|ems|"
    r"transit|bus|limo|shuttle|charter|aviation|aircraft|helicopter|hangar|"
    r"sports|athletic|arena|rink|ranch|stables?|arena|rodeo|fairgrounds|"
    r"storage|warehouse|yard|shop|co-op|coop|cooperative|exchange|credit|"
    r"sales|service|rental|repair|supply|supplies|outlet|outfitters|gear|"
    r"toyota|honda|ford|chevrolet|chevy|nissan|subaru|kia|hyundai|dodge|jeep|ram|gmc|buick|"
    r"mazda|volkswagen|vw|bmw|mercedes|audi|lexus|acura|infiniti|tesla|rivian|volvo|"
    r"target|walmart|costco|amazon|fedex|ups|usps|dhl|xpo|kroger|king soopers|king soopes|"
    r"safeway|walgreens|cvs|starbucks|mcdonalds|chipotle|subway|7-eleven|circle k|quiktrip|"
    r"maverik|loves|pilot|flying j|kum|murphy|shell|conoco|phillips|sinclair|valero|"
    r"xcel|comcast|lumen|centurylink|verizon|t-mobile|att|dish|crown castle|american tower|"
    r"sba|vertical bridge|allo|viaero|ting|google|microsoft|meta|oracle|ntt|flexential|"
    r"cemex|martin marietta|holcim|lafarge|aggregate industries|brannan|asphalt specialties|"
    r"molson|anheuser|pepsi|coca|coke|frito|nestle|kraft|heinz|tyson|cargill|jbs|smithfield|"
    r"ardent|mills|conagra|leprino|bimbo|flowers|hostess|sara lee|sysco|shamrock|pfg|"
    r"performance food|us foods|ben e keith|reinhart|gordon|nicholas|cheney|"
    r"agilent|microvast|owens|brockway|vestas|noble|chevron|occidental|oxy|pdc|bayswater|"
    r"prairie|civitas|crestone|extraction|kerr|mcgee|anadarko|dcp|kinder|morgan|western midstream|"
    r"summit|rocky|front range|greeley|windsor|frederick|firestone|dacono|erie|evans|"
    r"fort lupton|johnstown|milliken|platteville|kersey|lasalle|la salle|keenesburg|hudson|"
    r"brighton|longmont|mead|severance|eaton|ault|pierce|nunn|grover|gilcrest|hereford)\b|\d",
    re.I)

PERSON_TRUST = re.compile(
    r"\b(trustee|trustees|living trust|family trust|revocable trust|irrevocable trust|"
    r"rev trust|rev liv trust|liv trust|fam trust|estate of|est of|life estate|"
    r"survivors? trust|marital trust|bypass trust|trust dtd|trust dated|trust u/a|"
    r"personal representative|pers rep|conservator|heirs|deceased|decd|"
    r"jtwros|joint tenants|jt ten|husband|wife|et ux|et vir|a married|single person|"
    r"unmarried)\b", re.I)

INSTITUTIONAL_TRUST = re.compile(
    r"\b(llc|inc|corp|corporation|bank|company|co|n\.?a\.?|district|association|foundation|church|"
    r"university|school|fund|reit|trust co|trust company|land trust|housing|community|national|"
    r"federal|state|county|city|investment|investors|realty|properties|holdings|partners|capital|"
    r"industrial|commercial|business|charitable|employees|pension|retirement|benefit|union|"
    r"property|opendoor|public land|conservation|hospital|college|cemetery|lodge|"
    r"cooperative|co-op|institutional|equity|mortgage|lending|securitization|certificates)\b", re.I)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return now_iso()[:10]


def http(url, params=None, post=False, max_errors=MAX_ERRORS, backoff=5, timeout=180):
    """GET (or POST) with the identifying user agent, one request a second, hard stop on
    repeated errors. Returns the body as text."""
    full = url + ("?" + urllib.parse.urlencode(params) if params and not post else "")
    errors = 0
    while True:
        try:
            if post:
                req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                             headers={"User-Agent": UA})
            else:
                req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            time.sleep(PAUSE)
            return body
        except Exception as e:  # noqa
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
            if errors >= max_errors:
                raise SystemExit("Stopping after repeated errors on %s" % url)
            time.sleep(backoff * errors)


def http_json(url, params, post=False, **kw):
    body = http(url, params, post=post, **kw)
    data = json.loads(body)
    if isinstance(data, dict) and "error" in data:
        raise SystemExit("ArcGIS error on %s: %s" % (url, data["error"]))
    return data


def source_count(layer_url, where):
    return http_json(layer_url + "/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]


def require_fields(layer_url, wanted):
    """Fail loudly on schema drift."""
    meta = http_json(layer_url, {"f": "json"})
    have = {f["name"] for f in meta["fields"]}
    missing = [w for w in wanted if w not in have]
    if missing:
        raise SystemExit("Schema drift on %s: missing fields %s" % (layer_url, missing))
    return meta


def fetch_all(layer_url, where, out_fields, cache_dir, page_size=2000, geometry=True,
              extra=None, order="OBJECTID", label=None):
    """Page through a layer with resultOffset. Each raw page is written to cache_dir before
    parsing; a page already on disk is reused, so a broken run resumes and a rerun does not
    refetch. Returns the list of features, each with _fetched_at."""
    os.makedirs(cache_dir, exist_ok=True)
    label = label or os.path.basename(cache_dir)
    feats, offset, page = [], 0, 0
    while True:
        path = os.path.join(cache_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                wrapped = json.load(f)
        else:
            params = {"where": where, "outFields": ",".join(out_fields), "orderByFields": order,
                      "resultOffset": offset, "resultRecordCount": page_size,
                      "returnGeometry": "true" if geometry else "false", "outSR": 4326, "f": "json"}
            if extra:
                params.update(extra)
            data = http_json(layer_url + "/query", params)
            wrapped = {"fetched_at": now_iso(), "layer": layer_url, "params": params, "response": data}
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(wrapped, f)
            os.replace(tmp, path)
        got = wrapped["response"].get("features", [])
        for g in got:
            g["_fetched_at"] = wrapped["fetched_at"]
        feats.extend(got)
        print("  %s page %d: %d rows (total %d)" % (label, page, len(got), len(feats)))
        if not got or not wrapped["response"].get("exceededTransferLimit"):
            break
        offset += len(got)
        page += 1
    return feats


def fetch_by_keys(layer_url, key_field, keys, out_fields, cache_dir, batch=100, extra=None):
    """Attribute lookups by key list (POST, IN clause), cached per batch. Returns
    {key: [attribute dicts]} (a key may match several rows)."""
    os.makedirs(cache_dir, exist_ok=True)
    keys = sorted({k for k in keys if k and re.fullmatch(r"[0-9A-Za-z\-]+", k)})
    out = {}
    nb = (len(keys) - 1) // batch + 1 if keys else 0
    for i in range(0, len(keys), batch):
        chunk = keys[i:i + batch]
        path = os.path.join(cache_dir, "batch_%05d.json" % (i // batch))
        wrapped = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                wrapped = json.load(f)
            if wrapped.get("keys") != chunk:
                wrapped = None
        if wrapped is None:
            params = {"where": "%s IN (%s)" % (key_field, ",".join("'%s'" % c for c in chunk)),
                      "outFields": ",".join(out_fields), "returnGeometry": "false",
                      "outSR": 4326, "f": "json"}
            if extra:
                params.update(extra)
            data = http_json(layer_url + "/query", params, post=True)
            if data.get("exceededTransferLimit"):
                raise SystemExit("Key batch exceeded the transfer limit; lower the batch size")
            wrapped = {"fetched_at": now_iso(), "keys": chunk, "response": data}
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(wrapped, f)
            os.replace(tmp, path)
        for ft in wrapped["response"].get("features", []):
            a = dict(ft["attributes"])
            if "centroid" in ft:
                a["_cx"], a["_cy"] = ft["centroid"].get("x"), ft["centroid"].get("y")
            out.setdefault(clean(a.get(key_field)), []).append(a)
        print("  %s batch %d/%d (keys matched so far %d)" % (os.path.basename(cache_dir), i // batch + 1, nb, len(out)))
    return out


def ms_to_date(ms):
    if ms is None or ms == "":
        return ""
    if isinstance(ms, str):               # DateOnly fields come back as 'YYYY-MM-DD'
        return ms[:10]
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\d.])(?:\+?1[-.]?)?(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-.]\d{4}\b(?![\d.])|"
                      r"(?i:\b(?:phone|call|tel|cell|contact|ph|mobile|text)\W{0,3})\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")
# 'Planner: Jane Doe' and 'Case Planner Jane Doe' tails in planning descriptions.
PLANNER_RE = re.compile(r"\b(case\s+)?planner\s*:?\s*[A-Z][\w'.-]*(\s+[A-Z][\w'.-]*){0,3}", re.I)
HTML_RE = re.compile(r"<[^>]+>")


def clean(s, limit=None):
    """Whitespace-collapse, replace the dashes the brief bans, and remove e-mail addresses and
    phone numbers wherever they appear."""
    if s is None:
        return ""
    s = str(s).replace("\u2014", "-").replace("\u2013", "-").replace("\xa0", " ")
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\s+", " ", s).strip()
    s = EMAIL_RE.sub("[email removed]", s)
    s = PHONE_RE.sub("[phone removed]", s)
    return s[:limit] if limit else s


def scrub_description(s, limit=500):
    """Strip HTML, planner name tails, e-mails and phones from a planning description."""
    s = HTML_RE.sub(" ", str(s or ""))
    s = PLANNER_RE.sub("[planner removed]", s)
    s = re.sub(r"\bView permit information\b.*$", "", s, flags=re.I)
    s = re.sub(r"\bE-?Permit Center\b", "", s, flags=re.I)
    return clean(s, limit)


def looks_like_individual_party(name):
    """Owner, grantor or grantee on an assessor record: 'SMITH JOHN A', 'SMITH JOHN & JANE',
    'JONES FAMILY TRUST', 'MILLER ADAM J UND 1/8 INT'. Strip ownership-share and care-of
    fragments, split on the joiners, and treat the whole name as a person if any part reads
    as one. Conservative on purpose: when in doubt the name is blanked."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    n = re.sub(r"\bUND\s+[\d/.%\s]+INT\b", " ", n, flags=re.I)
    n = re.sub(r"\([^)]*\)", " ", n)          # '(8.33% INT)', '(1/6 INT)', '(LE)', '(PR)' ownership-share and estate tags
    n = re.sub(r"\b(et\s*al\.?|etal)\b", " ", n, flags=re.I)
    n = re.sub(r"\bC/O\b.*$", " ", n, flags=re.I)
    parts = [p for p in re.split(r"\s*(?:&|\band\b|;|,)\s*", n, flags=re.I) if p.strip()]
    for p in parts:
        p_nodigit = re.sub(r"\S*\d\S*", " ", p)
        if re.search(r"\btrust\b", p_nodigit, re.I):
            if INSTITUTIONAL_TRUST.search(p_nodigit):
                continue
            return True
        # Assessor format 'SURNAME FIRST [MIDDLE] I': a trailing single-letter initial is a person whatever the
        # surname looks like (BARBER, LAW, STONE, PIERCE, GROVER and EVANS all collide with business or town words).
        # Added 2026-11-06 after the QA pass found 12 such names in the first pull.
        toks = p_nodigit.replace(".", " ").split()
        if 3 <= len(toks) <= 4 and len(toks[-1]) == 1 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in toks):
            return True
        if 2 <= len(toks) <= 3 and toks[0].upper() in SURNAME_COLLISION and not BUSINESS_HINT.search(" ".join(toks[1:])) \
                and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in toks):
            return True
        # 'SURNAME GIVEN [GIVEN] [JR]' where a given name follows the surname and no strong corporate token is present:
        # a person, even when the surname or the given name happens to be a business-hint word (FORD, STONE, ROCKY, NICHOLAS).
        plain = [w for w in toks if w.upper() not in ("JR", "SR", "II", "III", "IV")]
        if 2 <= len(plain) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in plain) \
                and not STRONG_CORP.search(p_nodigit) and any(w.upper() in GIVEN_NAMES for w in plain[1:]):
            return True
        if BUSINESS_HINT.search(p_nodigit):
            continue
        words = [w for w in p_nodigit.replace(".", " ").split() if w.upper() not in ("JR", "SR", "II", "III", "IV")]
        if 1 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words):
            return True
    return False


def company_or_blank(name):
    """The company parts of an assessor name, else '' (and True when anything was blanked).
    'NINE TEN HOLDINGS LLC; DEKOWZAN THEODORE' keeps the LLC and drops the person; a
    name that is one person, or a personal trust, is blanked entirely."""
    n = clean(name)
    if not n or n in ("0", "NA", "N/A", "NONE"):
        return "", False
    if PERSON_TRUST.search(n):
        return "", True
    # The assessor separates parties with ';' ('&' and 'and' sit inside company names too).
    parts = [p.strip(" ,") for p in n.split(";") if p.strip(" ,")]
    if len(parts) <= 1:
        if looks_like_individual_party(n):
            return "", True
        return n, False
    kept = [p for p in parts if not looks_like_individual_party(p)]
    return "; ".join(kept), len(kept) < len(parts)


CASE_VOCAB = re.compile(
    r"\b(site plan review|use by special review|special review|zoning permit|change of zone|"
    r"rezon(e|ing)|amendment|amended|permit|solar|energy|facility|facilities|storage|"
    r"warehouse|office|shop|contractor|kennel|event center|events?|center|rv|vehicle|"
    r"repair|service|truck|parking|outdoor|indoor|gravel|mining|pit|well|injection|"
    r"compressor|station|substation|battery|wind|water|treatment|plant|for|and|the|of|"
    r"a|an|in|at|on|to|new|existing|proposed|addition|expansion|building|buildings|"
    r"sf|sq|ft|acre|acres|lot|lots|tract|parcel|phase|filing|no|usr|spr|zpag|coz|sif)\b", re.I)


def looks_like_individual_project(name):
    """For planning titles like 'Smith Kennel' or 'Garcia Contractor Shop': drop the case
    vocabulary and treat one or two plain words left over, with no business term, as a
    person's name. Loses a few two-word project names, which is the safe side."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    if re.match(r"^\d", n):
        return False
    if n != n.upper() and re.search(r"\b[A-Z]{3,}\b", n):
        return False
    n = re.sub(r"\([^)]*\)", " ", n)
    no_digits = re.sub(r"\S*\d\S*", " ", n)
    if BUSINESS_HINT.search(no_digits):
        return False
    rest = CASE_VOCAB.sub(" ", no_digits)
    rest = re.sub(r"[^A-Za-z' \-]", " ", rest)
    words = [w for w in rest.split() if w]
    return 1 <= len(words) <= 2 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words)


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def layer_query_url(layer_url, where):
    return layer_url + "/query?" + urllib.parse.urlencode({"where": where, "outFields": "*", "f": "html"})


# ---------- Weld-specific helpers ----------

def pad_parcel(v):
    """Weld assessor parcel numbers are 12 digits; the SPR layer stores them as doubles with
    the leading zero lost. Returns '' for 0 / None."""
    if v is None or v == "":
        return ""
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return re.sub(r"\D", "", str(v)).zfill(12)
    if n <= 0:
        return ""
    return "%012d" % n


def weld_city(v):
    """PROPERTYCITY / LOCCITY: 'WELD' is the assessor's code for unincorporated county."""
    c = clean(v)
    if not c or c.upper() in ("WELD", "WELD COUNTY", "UNINCORPORATED"):
        return UNINC
    return c.title().replace("Of ", "of ")


def situs_address(o):
    """Assemble the situs street address from an Ownership row."""
    parts = [clean(o.get("STREETNO")), clean(o.get("STREETDIR")), clean(o.get("STREETNAME")),
             clean(o.get("STREETSUF")), clean(o.get("STREETALP"))]
    return " ".join(p for p in parts if p)


def money(v):
    if v is None or v == "":
        return ""
    return "%d" % v if float(v).is_integer() else "%.2f" % v


def num(v, fmt="%g"):
    if v is None or v == "":
        return ""
    return fmt % v


ZONE_PATTERNS = [
    re.compile(r"\b((?:I|C|R|E|MH)-\d|A|PUD)\b\s*\([^)]*\)", re.I),                 # I-3 (Heavy Industrial)
    re.compile(r"\(((?:I|C|R|E|MH)-\d|A|PUD)\)\s*\w*\s*\w*\s*zone district", re.I),   # (A) Agricultural Zone District
    re.compile(r"\b((?:I|C|R|E|MH)-\d|A|PUD)\b(?:\s+\w+){0,3}\s+zone district", re.I),  # I-1 Light Industrial Zone District
]


ZONE_NAMES = {"agricultural": "A", "light industrial": "I-1", "medium industrial": "I-2",
              "heavy industrial": "I-3", "business commercial": "C-3", "general commercial": "C-2",
              "neighborhood commercial": "C-1", "planned unit development": "PUD", "estate": "E"}
ZONE_NAME_RE = re.compile(r"\b(%s)\s+zone district" % "|".join(ZONE_NAMES), re.I)


def zoning_from_text(text):
    """'... in the I-3 (Heavy Industrial) Zone District' -> 'I-3'. Returns the districts named
    in the text, comma separated, in the order found. Pass the untruncated description."""
    found = []
    for pat in ZONE_PATTERNS:
        for m in pat.finditer(text or ""):
            z = m.group(1).upper()
            if z not in found:
                found.append(z)
    for m in ZONE_NAME_RE.finditer(text or ""):
        z = ZONE_NAMES[m.group(1).lower()]
        if z not in found:
            found.append(z)
    return ", ".join(found)


def industrial_zoning(z):
    return bool(re.search(r"\bI-[123]\b", z or "", re.I))


# ---------- snapshot files (undated layers) ----------

def load_snapshot(path):
    """{record_id: row} from snapshot_<slug>.csv (record_id, first_seen, last_seen, ...)."""
    return {r["record_id"]: r for r in read_csv(path)}


def update_snapshot(snap, record_id, seen_day, **extra):
    """Mark record_id seen today; first_seen is kept from the first run that saw it."""
    row = snap.get(record_id)
    if row is None:
        row = {"record_id": record_id, "first_seen": seen_day, "last_seen": seen_day}
        snap[record_id] = row
    else:
        if seen_day > row.get("last_seen", ""):
            row["last_seen"] = seen_day
    row.update({k: v for k, v in extra.items() if v is not None})
    return row


def write_snapshot(path, snap, extra_cols=()):
    cols = ["record_id", "first_seen", "last_seen"] + [c for c in extra_cols if c not in ("record_id", "first_seen", "last_seen")]
    rows = sorted(snap.values(), key=lambda r: (r["first_seen"], r["record_id"]))
    write_csv(path, cols, [{c: r.get(c, "") for c in cols} for r in rows])
