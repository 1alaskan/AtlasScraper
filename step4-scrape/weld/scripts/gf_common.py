"""Shared helpers for the greeley_fortlupton group's Weld County pulls (step 4).

Standard library only. ArcGIS REST paging with a raw cache on disk, snapshot CSV
merge (append rows never seen before, never delete), the 17 shared output columns,
the brief's industrial_use rule, and the screens that keep personal names out of
company_name and description.
"""
import csv, html, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "step4-research-pull/1.0"
PAUSE = 1.0          # seconds between ArcGIS requests
MAX_ERRORS = 3       # stop after this many consecutive failures on one request
PARSER_VERSION = "greeley_fortlupton-1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
WELD_DIR = os.path.dirname(HERE)                       # step4-scrape/weld
RAW_ROOT = os.path.join(WELD_DIR, "raw")               # git-ignored

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]
SOURCE_LEVEL = "County (Weld)"
COUNTY = "Weld"
FLAG_RULE = "all planning and development cases"

# The brief's industrial_use list: industrial, warehouse, manufacturing, distribution, flex,
# data center, processing, plant, compressor station, oil and gas facility (not a well pad).
INDUSTRIAL = re.compile(
    r"\b(ind[iu]strial|industries|industry|warehous\w*|manufactur\w*|distribution|flex|"
    r"data ?cent(?:er|re)s?|processing|plants?|compressor station|"
    r"oil and gas (?:facility|facilities|processing|plant|terminal))\b", re.I)
# Wider net, reported in its own column: words that mark an industrial-adjacent use the
# brief's list does not name (equipment yards, mining, pipelines, storage yards, business parks).
INDUSTRIAL_ADJACENT = re.compile(
    r"\b(business park|commerce park|outside storage|outdoor storage|storage yard|"
    r"equipment(?:share)?|gravel|mining|aggregate|pipeline|midstream|oil and gas|"
    r"truck\w*|fleet|renewables?|solar|battery|substation|pump ?station|"
    r"self storage|lot consolidation)\b", re.I)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http(url, params=None, max_errors=MAX_ERRORS, backoff=5, timeout=180, pause=PAUSE):
    """GET with the identifying user agent, a pause after every request, hard stop on
    repeated errors. Returns the body as text."""
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    errors = 0
    while True:
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            time.sleep(pause)
            return body
        except Exception as e:  # noqa
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
            if errors >= max_errors:
                raise SystemExit("Stopping after repeated errors on %s" % url)
            time.sleep(backoff * errors)


def http_json(url, params, **kw):
    data = json.loads(http(url, params, **kw))
    if isinstance(data, dict) and "error" in data:
        raise SystemExit("ArcGIS error on %s: %s" % (url, data["error"]))
    return data


def source_count(layer_url, where="1=1"):
    return http_json(layer_url + "/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]


def require_fields(layer_url, wanted):
    """Fail loudly on schema drift."""
    meta = http_json(layer_url, {"f": "json"})
    have = {f["name"] for f in meta["fields"]}
    missing = [w for w in wanted if w not in have]
    if missing:
        raise SystemExit("Schema drift on %s: missing fields %s" % (layer_url, missing))
    return meta


def fetch_all(layer_url, where, out_fields, cache_dir, page_size=1000, geometry=False,
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


def fetch_text(url, cache_path, pause=PAUSE):
    """GET a page once per cache path (HTML sources). Returns (text, fetched_at)."""
    meta = cache_path + ".meta.json"
    if os.path.exists(cache_path) and os.path.exists(meta):
        with open(meta, encoding="utf-8") as f:
            fetched = json.load(f)["fetched_at"]
        with open(cache_path, encoding="utf-8") as f:
            return f.read(), fetched
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    body = http(url, pause=pause)
    fetched = now_iso()
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(body)
    with open(meta, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": fetched, "url": url}, f)
    return body, fetched


def ms_to_date(ms):
    if ms is None or ms == "":
        return ""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\d.])(?:\+?1[-.]?)?(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-.]\d{4}\b(?![\d.])")


def clean(s, limit=None):
    """Whitespace-collapse, strip HTML entities and the dashes the brief bans, remove e-mail
    addresses and phone numbers."""
    if s is None:
        return ""
    s = html.unescape(str(s)).replace("​", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).replace("\u2014", "-").replace("\u2013", "-").strip()
    s = EMAIL_RE.sub("[email removed]", s)
    s = PHONE_RE.sub("[phone removed]", s)
    return s[:limit] if limit else s


# ---------- personal-name screens ----------

# Tokens that mark a business, institution, place or development rather than a person.
BUSINESS_HINT = re.compile(
    r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|lp|llp|lllp|pllc|pc|"
    r"plc|gmbh|dba|d/b/a|et al|etal|"
    r"construction|constructors?|contractors?|contracting|builders?|building|buildings|"
    r"group|services?|electric|electrical|mechanical|plumbing|roofing|restoration|"
    r"development|developers?|dev|enterprises?|associates|partners|partnership|solutions|systems|"
    r"homes|properties|property|industries|industrial|interiors|remodeling|renovations?|"
    r"signs?|signage|fire|steel|concrete|glass|events?|productions?|management|"
    r"engineering|engineers?|commercial|facilities|facility|installations?|"
    r"county|city|town|district|authority|university|college|school|academy|church|ministries|"
    r"hospital|clinic|bank|credit union|holdings?|investments?|capital|realty|real estate|"
    r"land|ranch|farms?|dairy|foods?|logistics|trucking|transport\w*|energy|solar|power|oil|gas|"
    r"water|sanitation|metro\w*|housing|apartments?|apts|storage|supply|equipment|"
    r"manufacturing|products|international|national|american|america|usa|united|western|"
    r"rocky mountain|rocky mtn|mountain|center|centre|park|plaza|village|estates|ventures?|"
    r"acquisitions?|fund|reit|foundation|association|assn|assoc|hoa|club|"
    r"brewing|brewery|coffee|market|motors?|auto\w*|dealership|hotel|motel|restaurant|pizza|"
    r"grill|cafe|bakery|liquor|store|shop|salon|dental|medical|health|pharmacy|veterinary|"
    r"childcare|daycare|state of|federal|bureau|department|dept|board|commission|"
    r"railroad|railway|rail|airport|airlines?|union|lodge|legion|precast|remediation|"
    r"recovery|reclamation|paving|salvage|towing|recycling|asphalt|gravel|sand|pipe|welding|"
    r"machine|tool|crane|hvac|heating|cooling|lumber|millwork|cabinet\w*|granite|stone|tile|"
    r"metal|metals|iron|aluminum|plastics?|chemical\w*|packaging|printing|labs?|technolog\w*|"
    r"tech|data|network\w*|communications?|wireless|cellular|tower|utility|utilities|pipeline|"
    r"midstream|terminal|depot|yard|works|mfg|distributing|distributors?|wholesale|express|"
    r"freight|cargo|courier|delivery|leasing|rentals?|fitness|gym|studio|theat(?:er|re)|cinema|"
    r"resort|lodging|inn|suites|golf|cemetery|mortuary|funeral|landscape|landscaping|"
    r"architecture|architects?|planning|design|collaborative|consulting|consultants?|"
    r"surveying|surveyors?|civil|redev|redevelopment|renewables?|mining|everist|"
    r"house|library|museum|justice|"
    r"walmart|target|costco|amazon|fedex|ups|usps|dhl|kroger|king soopers|safeway|walgreens|"
    r"cvs|starbucks|mcdonalds|chipotle|subway|7-eleven|circle k|quiktrip|quik trip|maverik|"
    r"loves|murphy oil|valero|xcel|psco|comcast|lumen|centurylink|verizon|vzw|t-mobile|at&t|dish|"
    r"crown castle|american tower|jbs|leprino|culver's|culvers|jiffy lube|7 brew|"
    r"equipmentshare|sphere|northland|greeley|lupton|weld|poudre|unc)\b|\d|\+",
    re.I)

PERSON_TRUST = re.compile(
    r"\b(trustee|trustees|living trust|family trust|revocable trust|irrevocable trust|"
    r"rev trust|liv trust|fam trust|estate of|est of|life estate|personal representative|"
    r"pers rep|conservator|heirs|deceased|jtwros|joint tenants|husband|wife|et ux|et vir|"
    r"a married|single person|unmarried)\b", re.I)

# Credentials and titles that ride on a person's name.
CREDENTIAL = re.compile(r"\b(nccp|aicp|pe|pls|ra|aia|asla|leed ap|jr|sr|ii|iii|iv|mr|mrs|ms|dr)\b", re.I)


def looks_like_individual(name):
    """True when a name reads as a private person: trust or estate wording, or one to four
    plain alphabetic words with no business term at all. A name joined with '&' or 'and'
    is a person if any part is. An acronym token (LG, KCP, JP) counts as a business hint
    unless the whole string is upper case. Conservative on purpose: when in doubt the name
    is blanked (brief: never write a person's name)."""
    n = clean(name)
    if not n:
        return False
    if PERSON_TRUST.search(n):
        return True
    whole = CREDENTIAL.sub(" ", n.replace(",", " "))
    if BUSINESS_HINT.search(whole):
        return False                                        # 'Ansco & Associates'
    if whole != whole.upper() and re.search(r"\b[A-Z]{2,5}\b", whole):
        return False                                        # LG Everist, KCP Northland
    for part in re.split(r"\s*(?:&|\band\b)\s*", whole, flags=re.I):
        words = part.replace(".", " ").split()
        if 1 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words):
            return True                                     # 'Joanna & Jared Welsh'
    return False


def company_from_applicant(applicant):
    """Applicant strings come as 'Firm', 'Person', 'Person, Firm, LLC' or 'Person (Firm)'.
    Returns (company or '', number of person parts dropped)."""
    a = clean(applicant)
    if not a:
        return "", 0
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", a)
    if m and looks_like_individual(m.group(1)) and not looks_like_individual(m.group(2)):
        return clean(m.group(2)), 1
    # Split on commas, but keep a trailing corporate suffix with the part before it.
    parts = [p.strip() for p in a.split(",") if p.strip()]
    merged = []
    for p in parts:
        if merged and re.fullmatch(r"(?i)(llc|l\.l\.c\.?|inc\.?|incorporated|corp\.?|co\.?|ltd\.?|lp|llp|pc|pllc|p\.c\.)", p):
            merged[-1] = merged[-1] + ", " + p
        else:
            merged.append(p)
    keep, dropped = [], 0
    for p in merged:
        if CREDENTIAL.fullmatch(p.strip(". ")):
            continue                                        # 'NCCP' after a person's name
        if looks_like_individual(p):
            dropped += 1
        else:
            keep.append(p)
    if dropped and not keep:
        return "", dropped
    company = ", ".join(keep)
    if looks_like_individual(company):
        return "", dropped + 1
    return company, dropped


def surname_tokens(individual_names):
    """Surname tokens (last word, and hyphen parts) of the individual applicants in a pull,
    used to blank project names that carry an owner's surname ('Smith Minor Sub')."""
    toks = set()
    for n in individual_names:
        for part in re.split(r"\s*(?:&|\band\b|,)\s*", clean(n), flags=re.I):
            words = [w for w in part.replace(".", " ").split() if re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w)]
            if len(words) >= 2:
                last = words[-1]
                for t in last.split("-"):
                    if len(t) >= 3:
                        toks.add(t.lower())
    return toks


CASE_VOCAB = re.compile(
    r"\b(concept(?:ual)?|review|pre[- ]?app(?:lication)?|rezon(?:e|ing)|variances?|setbacks?|"
    r"subdivision|sub|plat|final|minor|major|exemption|vacation|amendment|amend|waivers?|lot|lots|"
    r"width|coverage|side|rear|front|fence|gazebo|garage|dwelling|adu|size|duplex|"
    r"parking|determination|relief|landscape|landscaping|height|accessory|structure|shed|"
    r"barn|shop|addition|home|house|residence|residential|cup|conditional|use|permit|"
    r"temporary|special|event|sign|signs|license|renewal|rplt|rebuild|replat|exception|"
    r"appeal|pud|eoz|zoning|zone|establishment|from|to|of|the|and|for|at|on|in|a|an|new|"
    r"existing|proposed|property|project|application|request|rd|st|ave|ln|dr|ct|blvd|pkwy|"
    r"way|north|south|east|west|n|s|e|w|place|pl|street|avenue|road|drive|lane|court|circle|"
    r"cir|row|r-o-w|easement|dedication|administrative|preliminary|design|standards?|"
    r"text|requirements?|corrections?|no|nos|line|lines|split|dividing|merging|into|two|"
    r"three|single|filing|filings|block|tract|parcel|parcels|acres|consolidation|adjustment|"
    r"boundary|annexation|serial|offsite|onsite|off-site|on-site|improvements?|median|"
    r"phasing|units?|test|verify|verification|letter|dev|agreement|agr|"
    r"site|plan|plans|sidewalks?|pond|detention|grading|drainage|water|sewer|main|"
    r"with|after|before|per|see|attached|please|provide|our|ref|number|address|certificate|"
    r"established|irrigation|proposal|monopole|modifications?|upgrade|repairs?|replacement|"
    r"lightpole|colocation|telecom|nonsubstantial|removal|scope|kiosk|install|wall|mounted|"
    r"storefront|windows|faces|blade|panels|stucco|facade|skylights|damaged|turf|trail|"
    r"narrows|section|campus|connection|downtown|ev|wcf|row|usr|spr|sub|zon|anx)\b",
    re.I)

# Local development, street and place names that are not people (keeps the project-name
# screen from blanking them).
PLACE_HINT = re.compile(
    r"\b(greeley|weld|poudre|cache|uptown|downtown|westside|eastside|northside|southside|"
    r"centerplace|boomerang|stoneybrook|cedarwoods|balsam|willow|catalyst|cobblestone|"
    r"lowell|shortgrass|tallgrass|summer park|two rivers|lake bluff|brentwood|mcauliffe|"
    r"dayspring|ferguson|gwip|great western|osborn|mccloskey|stagecoach|la casa|"
    r"vista meadows|south platte|lancaster|high pointe|sunrise|sweetgrass|cottonwood|"
    r"wildflower|northland|north land|factory|mckinley|denver|parsnip|county road|cr)\b", re.I)


def looks_like_individual_project(name):
    """For planning record names like 'Smith Minor Sub, 1st Replat' or 'Jones EOZ': drop
    numbers and the case vocabulary, then treat one or two plain words left over, with no
    business, place or acronym hint, as a person's name."""
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
    n = re.sub(r"\b(at|on|for|@)\s+\d.*$", " ", n, flags=re.I)
    no_digits = re.sub(r"\S*\d\S*", " ", n)
    if BUSINESS_HINT.search(no_digits) or PLACE_HINT.search(no_digits):
        return False
    rest = CASE_VOCAB.sub(" ", no_digits)
    rest = re.sub(r"[^A-Za-z' \-]", " ", rest)
    words = [w for w in rest.split() if w]
    if not (1 <= len(words) <= 2 and all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]+", w) for w in words)):
        return False                                        # single letters are not names
    if n != n.upper() and all(w == w.lower() for w in words):
        return False                                        # 'verify address': not a name
    return True


def scrub_project_name(name, surnames):
    """Returns (scrubbed name, reason) where reason is '' when the name was kept."""
    n = clean(name).strip('"').strip()
    if not n:
        return "", ""
    n = re.sub(r"\b[Aa]sk \w+ to\b", "Ask staff to", n)          # staff first names in notes
    toks = {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z'\-]+", n)}
    if surnames and (toks & surnames) and not re.search(r"\b(llc|inc|corp|company|church|academy|school)\b", n, re.I):
        return "", "applicant surname in project name"
    if looks_like_individual_project(n):
        return "", "reads as a person's name"
    return n, ""


# ---------- company names from project names ----------

# Business-name phrases inside a free-text project name: a known brand, or a capitalised
# phrase ending in a corporate or business word.
BRAND = re.compile(
    r"\b(Walmart|Culver's|7 Brew Coffee|7 Brew|Jiffy Lube|Crabtree Brewing|Loveland Industries|"
    r"Murphy Oil USA|Club Car Wash|Club Carwash|Salt Church|West Ridge Academy|Boomerang Self Storage|"
    r"T-Mobile|Verizon|VZW|AT&T|Great Western Industrial Park|Weld County Justice Center|"
    r"Weld County|UNC|Edison's Ice Cream|Brentwood Middle School|McAuliffe STEM Academy|"
    r"Two Rivers Solar|The Garage Automotive Solutions|Stagecoach Apartments|Tallgrass Apartments|"
    r"Element II Apts|Short Grass Apartments|West Greeley Commons Metropolitan District|"
    r"EquipmentShare|Northland Business Park|North Land PUD|LG Everist|L\. ?G\. Everist|"
    r"Sphere Renewables|Western Midstream|Xcel Energy|City of Fort Lupton|Fort Lupton City Hall|"
    r"South Platte Valley Historical Society|City of Brighton)\b", re.I)
SUFFIX_PHRASE = re.compile(
    r"\b((?:[A-Z][\w'&.-]*\s+){0,4}[A-Z][\w'&.-]*\s+"
    r"(?:LLC|L\.L\.C\.|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?|LP|Brewing|Brewery|Industries|"
    r"Church|Academy|Apartments|Apts|Storage|Solar|School|District|Authority|Enterprises|"
    r"Holdings|Partners|Group|Services|Systems|Energy|Renewables|Midstream|Pipeline|Business Park|"
    r"Historical Society|Metropolitan District|Justice Center|Hospital|Clinic|Bank|Foundation|"
    r"Association|Market|Motors|Automotive|Coffee|Pizza|Restaurant|Store))\b")


def company_from_project_name(name):
    """A company or named-project string from a project name, or ''."""
    n = clean(name).strip('"')
    if not n:
        return ""
    m = BRAND.search(n)
    if m:
        return m.group(1)
    m = SUFFIX_PHRASE.search(n)
    if m:
        cand = m.group(1).strip()
        if GENERIC_LEAD.match(cand) or looks_like_individual(cand):
            return ""
        return cand
    return ""


# A capitalised phrase that starts with one of these is a description, not a business name.
GENERIC_LEAD = re.compile(
    r"^(New|Existing|Proposed|Outside|Outdoor|Gravel|Drive|Thru|Drive Thru|Baptist|Catholic|"
    r"Methodist|Lutheran|Community|Public|Private|Commercial|Residential|Mobile|Self|Minor|"
    r"Major|Final|Preliminary|Administrative|Zoning|Site|Multi|Mixed|Water|Sewer|Storm)\b", re.I)


def industrial_flags(text):
    m = INDUSTRIAL.search(text or "")
    a = INDUSTRIAL_ADJACENT.search(text or "")
    return ("Y" if m else "N", m.group(0).lower() if m else "",
            "Y" if a else "N", a.group(0).lower() if a else "")


# ---------- CSV ----------

def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def read_csv(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return list(rd), rd.fieldnames or []


def layer_query_url(layer_url, where):
    return layer_url + "/query?" + urllib.parse.urlencode({"where": where, "outFields": "*", "f": "html"})
