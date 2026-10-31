"""Shared helpers for the county_commercecity group's Adams County pulls (step 4).

Standard library only. Paged ArcGIS REST queries with a raw cache on disk, a
point-in-polygon lookup in plain Python, the 17 shared output columns, and the
screens that keep personal names out of company_name.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "step4-research-pull/1.0"
PAUSE = 1.0          # seconds between requests
MAX_ERRORS = 3       # stop after this many consecutive failures on one request
PARSER_VERSION = "county_commercecity-1.0"

ADAMS_HOST = "https://services3.arcgis.com/4PNQOtAivErR7nbT/arcgis/rest/services"
C3_HOST = "https://gisserver.c3gov.com/gisserver/rest/services/Central_Square"

HERE = os.path.dirname(os.path.abspath(__file__))
ADAMS_DIR = os.path.dirname(HERE)                      # step4-scrape/adams
RAW_ROOT = os.path.join(ADAMS_DIR, "raw")              # git-ignored

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]
SOURCE_LEVEL = "County (Adams)"
COUNTY = "Adams"

# Words that mark an industrial use in a description, record name, zoning or building use.
INDUSTRIAL_WORDS = re.compile(
    r"\b(industrial|industry|warehous\w*|manufactur\w*|distribution|flex|data cent\w*|"
    r"plant|process\w*|equipment|crane|tanks?|silos?|compressor\w*|dust collect\w*|"
    r"paint booth|spray booth|boiler\w*|generator\w*|fabricat\w*|machin\w*|logistics|"
    r"cold storage|freezer|refrigerat\w*|food production|brewery|brewing|distill\w*|"
    r"bottling|packaging|recycl\w*|conveyor\w*|racking|pallet rack\w*|mezzanine|"
    r"truck terminal|trucking|trucks?|truck bay|semi|trailers?|ios|outdoor storage|commerce park|business park|biogas|organics|compost\w*|xpo|fleet|batch plant|concrete plant|asphalt|aggregate|"
    r"gravel|mining|oil and gas|well pad|pipeline|substation|wastewater|treatment plant|"
    r"hangar|hanger|aerospace|laborator\w*|clean ?room|i-1|i-2|i-3|core (and|&) shell|shell building)\b",
    re.I)

# Terms that mark a business or institution rather than a person.
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
    r"owner|tenant|church|temple|foundation|association|assn|assoc|hoa|club|"
    r"dba|d/b/a|of|the|et al|etal|llc\.|inc\.|corp\.|co\.|ltd\.|lp\.|"
    r"brewing|brewery|coffee|market|motors?|auto\w*|dealership|hotel|motel|"
    r"restaurant|pizza|grill|cafe|bakery|liquor|store|shop|salon|dental|medical|"
    r"health|care|pharmacy|veterinary|animal|pet|childcare|daycare|academy|"
    r"state of|united states|usa|federal|bureau|department|dept|board|commission|"
    r"railroad|railway|rail|airport|airlines?|union|local|lodge|post|legion|"
    r"creek|precast|remediation|hatchery|canopy|substation|coors|cascade|vartega|"
    r"recovery|reclamation|paving|salvage|towing|recycling|asphalt|gravel|sand|pipe|"
    r"welding|machine|tool|crane|hvac|heating|cooling|plumb\w*|lumber|millwork|cabinet\w*|"
    r"granite|marble|stone|tile|glass|metal|metals|iron|aluminum|plastics?|chemical\w*|"
    r"packaging|printing|labs?|technolog\w*|tech|data|network\w*|communications?|wireless|"
    r"cellular|tower|utility|utilities|pipeline|terminal|depot|yard|works|mfg|distributing|"
    r"distributors?|wholesale|imports?|exports?|express|freight|cargo|courier|delivery|"
    r"leasing|rentals?|rent|fitness|gym|studio|theat(er|re)|cinema|arena|stadium|"
    r"resort|lodging|inn|suites|golf|country club|cemetery|mortuary|funeral|labeling|"
    r"stockpile|crushing|emissions|testing|dump|landfill|mud|quarry|pit|batch|wind|hardware|containers|expansion|"
    r"redevelopment|revitalization|master plan|service plan|metro district|metropolitan|"
    r"fellowship|ministry|parish|congregation|temple|mosque|synagogue|"
    r"elevator|enclosures|libraries|library|carts|automation|sortation|fiber|constructors|"
    r"toyota|honda|ford|chevrolet|chevy|nissan|subaru|kia|hyundai|dodge|jeep|ram|gmc|buick|"
    r"mazda|volkswagen|vw|bmw|mercedes|audi|lexus|acura|infiniti|tesla|rivian|volvo|"
    r"target|walmart|costco|amazon|fedex|ups|usps|dhl|xpo|kroger|king soopers|safeway|"
    r"walgreens|cvs|starbucks|mcdonalds|chipotle|subway|7-eleven|circle k|quiktrip|quik trip|"
    r"maverik|loves|pilot|flying j|kum|murphy|shell|conoco|phillips|sinclair|valero|"
    r"xcel|comcast|lumen|centurylink|verizon|t-mobile|att|dish|crown castle|american tower|"
    r"sba|vertical bridge|allo|viaero|ting|google|microsoft|meta|oracle|ntt|flexential|"
    r"cemex|martin marietta|holcim|lafarge|aggregate industries|brannan|asphalt specialties|"
    r"molson|anheuser|pepsi|coca|coke|frito|nestle|kraft|heinz|tyson|cargill|jbs|smithfield|"
    r"ardent|mills|conagra|leprino|bimbo|flowers|hostess|sara lee|sysco|shamrock|pfg|"
    r"performance food|us foods|ben e keith|reinhart|gordon|nicholas|cheney)\b|\d",
    re.I)

PERSON_TRUST = re.compile(
    r"\b(trustee|trustees|living trust|family trust|revocable trust|irrevocable trust|"
    r"rev trust|rev liv trust|liv trust|fam trust|estate of|est of|life estate|"
    r"survivors? trust|marital trust|bypass trust|trust dtd|trust dated|trust u/a|"
    r"personal representative|pers rep|conservator|heirs|deceased|decd|"
    r"jtwros|joint tenants|jt ten|husband|wife|et ux|et vir|a married|single person|"
    r"unmarried)\b", re.I)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\d.])(?:\+?1[-.]?)?(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-.]\d{4}\b(?![\d.])|"
                      r"(?i:\b(?:phone|call|tel|cell|contact|ph|mobile|text)\W{0,3})\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")


def clean(s, limit=None):
    """Whitespace-collapse, replace the dashes the brief bans, and remove e-mail addresses and
    phone numbers wherever they appear (free-text descriptions carry them now and then)."""
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", str(s)).replace("-", "-").replace("-", "-").strip()
    s = EMAIL_RE.sub("[email removed]", s)
    s = PHONE_RE.sub("[phone removed]", s)
    return s[:limit] if limit else s


def looks_like_individual(name):
    """True when a name reads as a private person: trust or estate wording, or two to four
    plain alphabetic words with no business term at all. Conservative on purpose: when in
    doubt the name is blanked (brief: never write a person's name)."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    if BUSINESS_HINT.search(n):
        return False
    words = n.replace(",", " ").replace(".", " ").split()
    return 1 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words)


CASE_VOCAB = re.compile(
    r"\b(concept(ual)?|review|pre[- ]?app(lication)?|rezon(e|ing)|variances?|setbacks?|"
    r"subdivision|plat|final|minor|major|exemption|vacation|fireworks|inert|fill|amendment|"
    r"waivers?|lot|width|coverage|side|rear|front|fence|gazebo|garage|dwelling|adu|size|"
    r"duplex|barndominium|hangar|hanger|chile|stand|tract|parking|determination|relief|"
    r"landscape|landscaping|height|accessory|structure|shed|barn|shop|addition|home|house|"
    r"residence|residential|cup|conditional|use|permit|temporary|special|event|sign|signs|"
    r"liquor|license|renewal|rpl|rebuild|replat|replatting|exception|appeal|cdp|pud|puda|"
    r"from|to|of|the|and|for|at|on|in|a|an|new|existing|proposed|property|project|"
    r"application|request|rd|st|ave|ln|dr|ct|blvd|pkwy|way|north|south|east|west|n|s|e|w|"
    r"place|pl|street|avenue|road|drive|lane|court|circle|cir|swimming|pool|container|conex|"
    r"con[c]?ept|casa|house|lot line|adjustment|boundary|carport|patio|porch|deck|pergola|"
    r"workshop|hobby|second|unit|units|site|plan|review|replat|row|r-o-w|easement|dedication|"
    r"rezoning|rezone|combination|comprehensive|administrative|relief|appeal|boa|bocc|"
    r"requests?|preliminary|design|standards?|text|amendments?|noticing|requirements?|"
    r"corrections?|no|line|lines|lots|plots|vested|rights|extension|filing|filings|nos?|"
    r"block|tract|parcel|parcels|split|dwellings|duplexes|residences|quadplex|triplex|"
    r"acres|ranchettes|estates|gardens|conex|slaughter|hangars|access|drainage|grading|"
    r"christmas|tree|trees|sales|generation|tent|stand|booth|kiosk|cart|food|truck|trucks)\b",
    re.I)


def looks_like_individual_party(name):
    """Grantor or grantee on a deed: 'SMITH JOHN A', 'SMITH JOHN & JANE', 'JONES FAMILY TRUST',
    'MILLER ADAM J UND 1/8 INT'. Strip ownership-share and care-of fragments, split on the
    joiners, and treat the whole name as a person if any part reads as one."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    n = re.sub(r"\bUND\s+[\d/.%\s]+INT\b", " ", n, flags=re.I)     # undivided interest shares
    n = re.sub(r"\b(et\s*al\.?|etal)\b", " ", n, flags=re.I)
    n = re.sub(r"\bC/O\b.*$", " ", n, flags=re.I)                   # care-of address line
    parts = [p for p in re.split(r"\s*(?:&|\band\b|;|,)\s*", n, flags=re.I) if p.strip()]
    for p in parts:
        p_nodigit = re.sub(r"\S*\d\S*", " ", p)
        if re.search(r"\btrust\b", p_nodigit, re.I):
            if INSTITUTIONAL_TRUST.search(p_nodigit):     # 'WILMINGTON TRUST NA'
                continue
            return True                                   # 'THE RENEE A CASTILLO TRUST'
        if BUSINESS_HINT.search(p_nodigit):
            continue
        words = [w for w in p_nodigit.replace(".", " ").split() if w.upper() not in ("JR", "SR", "II", "III", "IV")]
        if 1 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words):
            return True
    return False


INSTITUTIONAL_TRUST = re.compile(
    r"\b(llc|inc|corp|corporation|bank|company|co|n\.?a\.?|district|association|foundation|church|"
    r"university|school|fund|reit|trust co|trust company|land trust|housing|community|national|"
    r"federal|state|county|city|investment|investors|realty|properties|holdings|partners|capital|"
    r"industrial|commercial|business|charitable|employees|pension|retirement|benefit|union)\b", re.I)


def looks_like_individual_project(name):
    """For planning record and project names like 'Garcia Gazebo Setback Variance', 'Smith
    Subdivision Final Plat' or 'Martinez Casa 6850': drop numbers and the case vocabulary, then
    treat one or two plain words left over, with no business term, as a person's name. Loses a
    few two-word development names, which is the safe side of the brief's rule."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    if re.match(r"^\d", n):                           # address-led names carry no person
        return False
    if n != n.upper() and re.search(r"\b[A-Z]{3,}\b", n):   # an acronym in a mixed-case name (EVRAZ, TCVMD)
        return False
    n = re.sub(r"\([^)]*\)", " ", n)                                # '(Todd Creek Farms, Filing 5)' asides
    n = re.sub(r"\b(at|on|for|@)\s+\d.*$", " ", n, flags=re.I)   # '... at 5200 Sheridan' tails
    n = re.sub(r"\b(on|along|near|off)\s+[A-Z][\w\s.]*?\b(street|st|avenue|ave|road|rd|drive|dr|lane|ln|"
               r"court|ct|place|pl|blvd|boulevard|way|pkwy|parkway|circle|cir|hwy|highway)\b.*$", " ", n, flags=re.I)
    no_digits = re.sub(r"\S*\d\S*", " ", n)          # addresses and case numbers are not hints
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


def layer_query_url(layer_url, where):
    return layer_url + "/query?" + urllib.parse.urlencode({"where": where, "outFields": "*", "f": "html"})


# ---------- point in polygon (ESRI rings, even-odd rule) ----------

class PolyIndex:
    def __init__(self, features):
        self.items = []
        for f in features:
            rings = (f.get("geometry") or {}).get("rings") or []
            if not rings:
                continue
            xs = [p[0] for r in rings for p in r]
            ys = [p[1] for r in rings for p in r]
            self.items.append((min(xs), min(ys), max(xs), max(ys), rings, f["attributes"]))

    @staticmethod
    def _in_rings(x, y, rings):
        inside = False
        for ring in rings:
            n = len(ring)
            j = n - 1
            for i in range(n):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
        return inside

    def find(self, x, y):
        if x is None or y is None:
            return None
        for (x0, y0, x1, y1, rings, attrs) in self.items:
            if x0 <= x <= x1 and y0 <= y <= y1 and self._in_rings(x, y, rings):
                return attrs
        return None


ZONING_LAYER = ADAMS_HOST + "/Zoning/FeatureServer/0"


def load_county_zoning(cache_root):
    """Adams County zoning polygons: unincorporated districts (A-1, I-1, C-3, P-U-D and so on)
    plus one polygon per city carrying the city name as ZONE_. Used for both zoning and city."""
    feats = fetch_all(ZONING_LAYER, "1=1", ["OBJECTID", "ZONE_", "CITY_NAME"],
                      os.path.join(cache_root, "zoning"), page_size=200,
                      extra={"geometryPrecision": 6})
    n = source_count(ZONING_LAYER, "1=1")
    if len(feats) != n:
        raise SystemExit("Zoning layer: got %d polygons, source says %d" % (len(feats), n))
    return PolyIndex(feats)


def county_zone_class(zone):
    """Adams County unincorporated districts: I-1/I-2/I-3 industrial, C-0..C-5 commercial."""
    z = (zone or "").upper().strip()
    if re.match(r"^I-[123]$", z):
        return "industrial"
    if re.match(r"^C-[0-5]$", z) or z == "CO":
        return "commercial"
    return ""
