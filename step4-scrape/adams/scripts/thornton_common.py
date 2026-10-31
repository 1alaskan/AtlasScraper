"""Shared helpers for the Thornton ArcGIS Enterprise pulls (Adams County step 4, group thornton).

Standard library only. Paged /query requests with every raw page cached on disk, an
identifying user agent, one request a second, a hard stop on repeated errors, and the
text-cleaning rules that keep staff stamps, contact details and personal names out of
the CSVs.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

HOST = "https://maps.thorntonco.gov/citydevweb/rest/services"
UA = "step4-research-pull/1.0"
PAUSE = 1.0
MAX_ERRORS = 3
PARSER_VERSION = "thornton-1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
ADAMS_DIR = os.path.dirname(HERE)
RAW_ROOT = os.path.join(ADAMS_DIR, "raw")

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(url, params, max_errors=MAX_ERRORS, backoff=5, post=False):
    """One request. The Thornton server answers some query shapes (ORed clauses) with an
    HTML 500 page instead of JSON; that surfaces here as a JSON decode error and counts
    as a failure, so the caller sees it quickly rather than retrying for ever."""
    full = url + "?" + urllib.parse.urlencode(params)
    errors = 0
    while True:
        try:
            if post:
                req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                             headers={"User-Agent": UA})
            else:
                req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode("utf-8")
            if body.lstrip().startswith("<"):
                raise RuntimeError("server returned HTML (HTTP 500 page) for this query shape")
            data = json.loads(body)
            if "error" in data:
                raise RuntimeError("ArcGIS error: %s" % data["error"])
            time.sleep(PAUSE)
            return data
        except Exception as e:  # noqa
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
            if errors >= max_errors:
                raise SystemExit("Stopping after repeated errors on %s" % url)
            time.sleep(backoff * errors)


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


def fetch_all(layer_url, where, out_fields, cache_dir, page_size=2000, geometry=True):
    """Page a query by resultOffset (ordered by OBJECTID). Each raw page is written to
    cache_dir before parsing and a page already on disk is reused, so a broken run
    resumes and a rerun on the same day does not refetch."""
    os.makedirs(cache_dir, exist_ok=True)
    feats, offset, page = [], 0, 0
    while True:
        path = os.path.join(cache_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                wrapped = json.load(f)
        else:
            params = {"where": where, "outFields": ",".join(out_fields), "orderByFields": "OBJECTID",
                      "resultOffset": offset, "resultRecordCount": page_size,
                      "returnGeometry": "true" if geometry else "false", "outSR": 4326, "f": "json"}
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
        print("  %s page %d: %d rows (total %d)" % (os.path.basename(cache_dir), page, len(got), len(feats)))
        if not got or not wrapped["response"].get("exceededTransferLimit"):
            break
        offset += len(got)
        page += 1
    return feats


def ms_to_date(ms):
    """Epoch milliseconds to ISO date, converted in UTC (same convention as the Denver pulls)."""
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def clean(s, limit=None):
    if s is None:
        return ""
    s = str(s).replace("\u2014", "-").replace("\u2013", "-")
    s = re.sub(r"\s+", " ", s).strip()
    if s in ("None", "None Entered"):
        return ""
    return s[:limit] if limit else s


# ---------- text scrubbing (no personal names, phones or emails in the output) ----------

STAFF_STAMP = re.compile(r"\[\s*[A-Za-z0-9._' -]{1,40}@\s*\d{1,2}/\d{1,2}/\d{2,4}[^\]]*\]")
# Unbracketed CityView stamps: "jnielsen 09/03/2025 7:39 AM" (username, date, time).
STAFF_STAMP2 = re.compile(r"[a-z][a-z0-9._-]{3,15}\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}\s*(?:[AaPp][Mm])?\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
# "Contact Justin Nielsen with questions" style phrases: the keyword is matched without
# regard to case, the name must be Capitalized words, and the rest of the sentence goes.
CONTACT_LINE = re.compile(r"\b((?i:contact|call|reach out to))\s*:?\s*[A-Z][a-z]+(\s+[A-Z][a-z]+){0,2}\b[^.\n]*")
# Titles followed by a surname: "Chief Harpring", "Inspector Smith".
TITLE_NAME = re.compile(r"\b(Chief|Inspector|Officer|Captain|Lieutenant|Lt\.?|Sgt\.?|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Marshal)\s+[A-Z][A-Za-z'\-]+")
# "Craig/DE", "Deb/Finance": a staff first name with a department after a slash.
NAME_SLASH_DEPT = re.compile(r"\b[A-Z][A-Za-z]{2,}\s*/\s*(DE|Finance|Finanance|Admin|GIS|Planning|Building|Fire|PW|Eng|Engineering)\b")

# Words that, following a first name, mean the pair is a company, place or document,
# not a person ("Lee Enterprises", "Grace Church", "Jordan Road", "Nelson Design").
NAME_SUFFIX_STOP = set("""design designs group inc llc co company corp corporation construction constructors
contracting engineering engineers homes builders building buildings electric electrical plumbing roofing
mechanical heating cooling hvac drawings drawing bank market markets enterprises industries properties
development realty partners associates church street st ave avenue blvd boulevard road rd drive dr court ct
lane ln way place pl parkway pkwy circle cir ridge park creek lake hills hill valley ranch farms farm
elementary elem school academy center centre county city controls systems services solutions technologies
tire tires auto automotive motors foods food restaurant grill cafe pizza burger burgers donuts coffee liquor
liquors dental dentistry medical clinic pharmacy fitness club sports supply store stores shop outlet mall
plaza square crossing village commons station depot wholesale express logistics distribution warehouse
manufacturing pharma tech aerospace energy power solar water gas oil fire protection alarm security signs
sign glass steel concrete paving landscaping landscape tree pool pools spa spas printing cleaners laundry
storage rentals rental leasing foundation hospital health healthcare senior living apartments townhomes
condos hoa filing subdivision amendment phase unit suite permit code section plan plans review report letter
standard standards requirements specifications specs international national american united global
brothers bros sons daughters family trust real estate investments holdings ventures capital equities
mountain mountains mesa canyon river springs heights gardens estates meadows crossing pointe point
north south east west highway hwy route""".split())
# Prepositions after which a lone first name is a person ("with Justin -", "per Kimberly").
NAME_LEAD = r"(?i:per|with|from|by|contact|call|and|to|spoke to|talked to|met with|approved by|okay with|ok with|email from|call from)"


def _is_first(w):
    return w.lower() in FIRST_NAMES


def _full_name_sub(m):
    first, second = m.group(1), m.group(2)
    if second.lower().strip(".") in NAME_SUFFIX_STOP:
        return m.group(0)
    return "[name removed]"


FULL_NAME = re.compile(r"\b([A-Z][a-z]{2,})\s+([A-Z][A-Za-z'\-]+|[A-Z]\.?)(?=[\s,.;:)\]\-/']|$)")
LEAD_NAME = re.compile(r"\b(" + NAME_LEAD + r")\s+([A-Z][a-z]{2,})(?!\s+[A-Z][a-z])(?=[\s,.;:)\]\-/]|$)")
NAME_FROM = re.compile(r"\b([A-Z][a-z]{2,})\s+(?=from\s)")
NAME_REMOVED_AND = re.compile(r"\[name removed\]\s+(and|&)\s+[A-Z][A-Za-z'\-]+(\s+[A-Z][A-Za-z'\-]+)?")


def scrub_names(s):
    s = TITLE_NAME.sub("[name removed]", s)
    s = NAME_SLASH_DEPT.sub(r"[name removed]/\1", s)
    s = FULL_NAME.sub(lambda m: _full_name_sub(m) if _is_first(m.group(1)) else m.group(0), s)
    s = LEAD_NAME.sub(lambda m: m.group(1) + " [name removed]" if _is_first(m.group(2)) else m.group(0), s)
    s = NAME_FROM.sub(lambda m: "[name removed] " if _is_first(m.group(1)) else m.group(0), s)
    s = NAME_REMOVED_AND.sub(r"[name removed] \1 [name removed]", s)
    return s


def scrub_text(s, limit=500):
    """Remove CityView staff stamps '[user @ date time]', emails, phone numbers,
    'Contact <Name> ...' phrases and first-name based person names, then trim. A surname
    used alone, or a first name not on the list, can still slip through; the notes say so."""
    s = clean(s)
    if not s:
        return ""
    s = STAFF_STAMP.sub("", s)
    s = STAFF_STAMP2.sub("", s)
    s = EMAIL.sub("[email removed]", s)
    s = PHONE.sub("[phone removed]", s)
    s = CONTACT_LINE.sub(r"\1 [name removed]", s)
    s = scrub_names(s)
    s = re.sub(r"\*{2,}", "", s)
    s = re.sub(r"\s+", " ", s).strip(" *-")
    return s[:limit]


BUSINESS_HINT = re.compile(
    r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|companies|ltd|lp|llp|lllp|pllc|pc|"
    r"properties|property|partners|partnership|holdings|group|investments?|enterprises?|associates|"
    r"association|hoa|development|developers?|construction|builders?|homes|realty|real estate|"
    r"church|ministries|diocese|school|schools|district|city|county|state|colorado|denver|thornton|"
    r"authority|university|college|hospital|health|medical|clinic|bank|credit union|foundation|"
    r"fund|trust company|owner|owners|industrial|industries|center|centre|park|plaza|square|"
    r"commons|crossing|village|ranch|farms?|management|services?|systems|solutions|logistics|"
    r"storage|energy|power|electric|gas|water|sanitation|metro|metropolitan|rtd|xcel|ventures|"
    r"capital|equities|acquisitions?|reit|trustees?|c/o|dba|aka|fka|etal|et al|and|of|the|"
    r"north|south|east|west|international|national|american|united|global|technologies|tech|"
    r"restaurant|market|markets|foods?|bakery|brewing|motors|auto|automotive|tire|church|"
    r"store|stores|shop|outlet|outlets|supply|express|academy|learning|daycare|childcare|"
    r"usa|us|america|canada|multiple|various|unknown|n/a|na|tbd|none)\b|\d|&|#",
    re.I)
PERSONAL_TRUST = re.compile(r"(?i)\b(revocable|living|family|irrevocable|marital|survivors?|trust)\b")


def looks_like_individual(name):
    """True when the name reads as a private person: no business word anywhere and two to
    five plain alphabetic tokens (assessor format is SURNAME FIRST M, often two owners
    joined by AND), or a personal trust with no company word. Conservative on purpose:
    when unsure the name is blanked, because the brief says never write a person's name."""
    n = clean(name)
    if not n:
        return False
    if n.upper() in ("HOME OWNER", "HOMEOWNER", "OWNER", "OWNER/BUILDER", "SELF", "MULTIPLE"):
        return True
    body = PERSONAL_TRUST.sub(" ", n)
    if BUSINESS_HINT.search(body):
        if PERSONAL_TRUST.search(n) and not re.search(r"(?i)\b(llc|inc|corp|company|bank|church|foundation|co)\b", n):
            # "THE SMITH FAMILY TRUST" matched only on THE/AND: a personal trust.
            words = [w for w in re.sub(r"[^A-Za-z ]", " ", body).split() if w.lower() not in ("the", "and", "of")]
            return 1 <= len(words) <= 5
        return False
    words = re.sub(r"[^A-Za-z.'\- ]", " ", body).split()
    return 1 <= len(words) <= 5


PRO_TITLE = re.compile(r"(?i)(^|\s)(dr|dds|dmd|md|do|dvm|od|phd|esq|cpa|dc|pa-c|np|rn|lcsw|cfp|ea|pllc)\.?(\s|$)")
FIRST_NAMES = set("""james john robert michael william david richard joseph thomas charles christopher daniel
matthew anthony mark donald steven paul andrew joshua kenneth kevin brian george timothy ronald edward jason
jeffrey ryan jacob gary nicholas eric jonathan stephen larry justin scott brandon benjamin samuel gregory
alexander frank patrick raymond jack dennis jerry tyler aaron jose adam nathan henry douglas zachary peter
kyle noah ethan jeremy walter christian keith roger terry  sean gerald carl harold dylan arthur lawrence
 jesse bryan billy bruce gabriel joe  alan juan albert willie elijah wayne randy vincent mason roy
ralph bobby russell bradley philip eugene louis mary patricia jennifer linda elizabeth barbara susan jessica
sarah karen lisa nancy betty sandra margaret ashley kimberly emily donna michelle carol amanda melissa deborah
stephanie dorothy rebecca sharon laura cynthia amy kathleen angela shirley brenda emma anna pamela nicole
samantha katherine christine helen debra rachel carolyn janet maria catherine heather diane olivia julie
joyce victoria ruth virginia lauren kelly christina joan evelyn judith andrea hannah megan cheryl jacqueline
martha  teresa gloria sara janice ann kathryn abigail sophia frances jean alice judy isabella julia
grace amber denise danielle marilyn beverly charlotte natalie theresa diana brittany doris kayla alexis lori
morgan taylor casey jamie  drew cameron riley peyton skyler  chris mike dave steve tom bill bob
jim joe tony rick dan matt jeff greg doug tim ken ron ed jon ben sam nick alex max leo ray lee jay
luke craig deb kim jen jenn kate katie rob don al ted pat sue liz beth becky jess josh zach nate andy hank
jose luis carlos miguel maria ana rosa jorge pedro manuel roberto ricardo javier diego fernando alejandro
sofia isabel lucia marco antonio angel victor hector raul ruben sergio oscar mario cesar pablo eduardo arturo
rafael alberto armando enrique ignacio ismael omar rene salvador tomas ivan adrian andres jesus jaime julio
leonardo lorenzo mauricio moises orlando ramiro rodrigo rolando santiago saul leni julia chad brett
travis trevor cody corey dustin shane shawn wade blake chase colin derek devin eli evan garrett  ian
jared jesse kirk kurt lance marcus mitchell neil owen reid seth spencer todd troy tyler wesley abby
alyssa amanda ashley brooke caitlin carla carrie cassie chelsea courtney  dana  erica erin
gina heidi  jackie  jenna jill jodi kara kari kelsey kristen kristin krista leah lindsay lindsey
lynn mandy meghan misty molly monica paige   shannon shelly stacy tara tina tracy tracey
vanessa wendy whitney""".split())


def looks_like_person_business(name):
    """Narrow test for a business-name field, where most values are storefronts: a professional
    title (DDS, MD, DR) or two plain words with a common first name first ("BILLY BIRCH")."""
    n = clean(name)
    if not n:
        return False
    if PRO_TITLE.search(n):
        return True
    words = re.sub(r"[^A-Za-z' ]", " ", n).split()
    if 2 <= len(words) <= 3 and words[0].lower() in FIRST_NAMES and not BUSINESS_HINT.search(n):
        return True
    return False


def entity_or_blank(name, business_field=False):
    """Return (name, blanked_flag). business_field=True uses the narrow storefront test."""
    n = clean(name)
    if not n:
        return "", False
    test = looks_like_person_business if business_field else looks_like_individual
    if test(n):
        return "", True
    return n, False


def write_csv(path, cols, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    os.replace(tmp, path)


def read_csv(path):
    if not os.path.exists(path):
        return [], None
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return list(rd), rd.fieldnames


def fmt_num(v):
    if v is None or v == "":
        return ""
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return clean(v)
    return "%d" % fv if fv.is_integer() else "%.2f" % fv


def layer_record_url(layer_url, where):
    return layer_url + "/query?" + urllib.parse.urlencode({"where": where, "outFields": "*", "f": "html"})
