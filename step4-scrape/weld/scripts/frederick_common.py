"""Shared helpers for the `frederick` group's Weld County pulls (step 4).

Standard library only. Paged ArcGIS REST queries against the Town of Frederick's ArcGIS
Enterprise server with a raw cache on disk, a point-in-polygon lookup in plain Python, the
17 shared output columns, and the screens that keep personal names out of company_name.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "step4-research-pull/1.0"
PAUSE = 1.0          # seconds between requests
MAX_ERRORS = 3       # stop after this many consecutive failures on one request
PARSER_VERSION = "frederick-1.0"

GIS = "https://gis.frederickco.gov/arcgis/rest/services"
TOWN = "https://www.frederickco.gov"

HERE = os.path.dirname(os.path.abspath(__file__))
WELD_DIR = os.path.dirname(HERE)                       # step4-scrape/weld
RAW_ROOT = os.path.join(WELD_DIR, "raw")               # git-ignored

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]
SOURCE_LEVEL = "County (Weld)"
COUNTY = "Weld"
CITY = "Frederick"

# Words that mark an industrial use in a description, record name, zoning or land use.
# `process` and `equipment` only count in industrial phrasings; `manufactured home` does not count.
INDUSTRIAL_WORDS = re.compile(
    r"\b(industrial|industry|warehous\w*|manufactur(?:ing|e|es|ed)(?! home)|distribution|flex|data ?cent\w*|"
    r"plant|process(?:ing|\s+(?:piping|equipment|line|area|water|building|facility|room))|"
    r"(?:process|manufacturing|production|owner[- ]furnished|new|existing)\s+equipment|"
    r"crane|tanks?|tank farm|silos?|compressor\w*|compressed air|dust collect\w*|"
    r"paint booth|spray booth|boiler\w*|generator\w*|fabricat\w*|machin(?:e|ing|ery) shop|machinery|cnc|logistics|"
    r"cold storage|freezer|refrigeration|walk[- ]in cooler|food production|brewery|brewing|distill\w*|"
    r"bottling|canning|packaging|recycl\w*|conveyor\w*|racking|pallet rack\w*|high[- ]piled|mezzanine|"
    r"truck terminal|trucking|truck bay|outdoor storage|storage yard|business park|batch plant|concrete plant|asphalt|aggregate|"
    r"gravel|mining|oil and gas|pipeline|substation|bess|battery (?:energy )?storage|wastewater|treatment plant|"
    r"hangar|aerospace|laborator\w*|labs?|lab (?:renovation|space|spaces)|clean ?room|core (and|&) shell|shell building|"
    r"li-flex|hi-flex|light industrial|heavy industrial|piping|welding|maintenance (?:building|facility|shop))\b",
    re.I)

# Zoning codes on the Frederick Zoning_Designation layer that count as industrial.
INDUSTRIAL_ZONES = {"I", "LI-FL", "HI-FL", "BLI"}
ZONE_NAMES = {"I": "Industrial", "LI-FL": "LI-FLEX", "HI-FL": "HI-FLEX", "BLI": "Business Light Industrial"}

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
    r"leasing|rentals?|rent|fitness|gym|studio|theat(er|re)|cinema|arena|stadium|"
    r"resort|lodging|inn|suites|golf|country club|cemetery|mortuary|funeral|"
    r"stockpile|crushing|emissions|testing|dump|landfill|quarry|pit|batch|wind|hardware|containers|"
    r"redevelopment|master plan|service plan|metro district|metropolitan|"
    r"fellowship|ministry|parish|congregation|mosque|synagogue|"
    r"elevator|libraries|library|automation|fiber|workspaces?|"
    r"toyota|honda|ford|chevrolet|chevy|nissan|subaru|kia|hyundai|dodge|jeep|ram|gmc|buick|"
    r"mazda|volkswagen|vw|bmw|mercedes|audi|lexus|acura|infiniti|tesla|rivian|volvo|"
    r"target|walmart|costco|amazon|fedex|ups|usps|dhl|xpo|kroger|king soopers|safeway|"
    r"walgreens|cvs|starbucks|mcdonalds|chipotle|subway|7-eleven|circle k|quiktrip|quik trip|"
    r"maverik|loves|pilot|flying j|kum|murphy|shell|conoco|phillips|sinclair|valero|"
    r"xcel|comcast|lumen|centurylink|verizon|t-mobile|att|dish|crown castle|american tower|"
    r"sba|vertical bridge|google|microsoft|meta|oracle|agilent|clearway|civitas|oxy|occidental|"
    r"chevron|noble|pdc|kerr|bayswater|crestone|extraction|bonanza|kinder morgan|dcp|williams|"
    r"brakes plus|transwest|stapp|stevinson|craft solutions|mile high|forge x|flight|"
    r"molson|anheuser|pepsi|coca|coke|frito|nestle|kraft|heinz|tyson|cargill|jbs|smithfield|"
    r"leprino|sysco|us foods)\b|\d",
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
    r"federal|state|county|city|town|investment|investors|realty|properties|holdings|partners|capital|"
    r"industrial|commercial|business|charitable|employees|pension|retirement|benefit|union)\b", re.I)


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
    if body.lstrip().startswith("<"):
        raise SystemExit("HTML instead of JSON from %s (first 200 chars): %s" % (url, body[:200]))
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
    phone numbers wherever they appear."""
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", str(s)).replace("\u2014", "-").replace("\u2013", "-").strip()
    s = EMAIL_RE.sub("[email removed]", s)
    s = PHONE_RE.sub("[phone removed]", s)
    return s[:limit] if limit else s


def looks_like_individual(name):
    """True when a name reads as a private person: trust or estate wording, or one to four
    plain alphabetic words with no business term at all. Conservative on purpose."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    if BUSINESS_HINT.search(n):
        return False
    words = n.replace(",", " ").replace(".", " ").split()
    return 1 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words)


def looks_like_individual_party(name):
    """Assessor owner names: 'SMITH JOHN A', 'SMITH JOHN & JANE', 'JONES FAMILY TRUST'."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    n = re.sub(r"\([^)]*\)", " ", n)                                # '(JT 45%)', '(16% INT)' shares
    n = re.sub(r"\bUND\s+[\d/.%\s]+INT\b", " ", n, flags=re.I)
    n = re.sub(r"\b(et\s*al\.?|etal)\b", " ", n, flags=re.I)
    n = re.sub(r"\bC/O\b.*$", " ", n, flags=re.I)
    parts = [p for p in re.split(r"\s*(?:&|\band\b|;|,)\s*", n, flags=re.I) if p.strip()]
    for p in parts:
        p_nodigit = re.sub(r"\S*\d\S*", " ", p)
        if re.search(r"\btrust\b", p_nodigit, re.I):
            if INSTITUTIONAL_TRUST.search(p_nodigit):
                continue
            return True
        if BUSINESS_HINT.search(p_nodigit):
            continue
        words = [w for w in p_nodigit.replace(".", " ").split() if w.upper() not in ("JR", "SR", "II", "III", "IV")]
        if 1 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words):
            return True
    return False


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


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


ZONING_LAYER = GIS + "/Zoning_Designation/MapServer/0"


def load_zoning(cache_root):
    """Frederick zoning polygons (one per platted lot or parcel, about 9,000). ZONE_CODE is the
    district (I, BLI, LI-FL, HI-FL, C-C, R-1 and so on); the overlay rows have ZONE_CODE null."""
    feats = fetch_all(ZONING_LAYER, "ZONE_CODE IS NOT NULL", ["OBJECTID", "ZONE_CODE", "ZONING", "SUBDIVISION"],
                      os.path.join(cache_root, "zoning"), page_size=1000,
                      extra={"geometryPrecision": 6})
    n = source_count(ZONING_LAYER, "ZONE_CODE IS NOT NULL")
    if len(feats) != n:
        raise SystemExit("Zoning layer: got %d polygons, source says %d" % (len(feats), n))
    return PolyIndex(feats)
