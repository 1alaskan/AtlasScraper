#!/usr/bin/env python3
"""Pull Weld County BOCC Tax Incentive Agreements (C.R.S. 30-11-123) from the Laserfiche WebLink
portal into the step 4 shared format.

Usage:  python3 pull_weld_incentive_agreements.py [--since YYYY-MM-DD] [--fresh]

--since  Hearing Date cursor for the field search (default 2022-01-01; the brief pulls every
         agreement from 2022 on because the 2022 and 2023 agreements are still inside their
         equipment phase windows).
--fresh  ignore the raw cache (search listing, document info and OCR pages) and refetch.

Route (the one step 2 validated): the WebLink JSON services, read-only, with a session cookie
from one GET of Welcome9.aspx.
  POST SearchService.aspx/GetSearchListing   field search on the Commissioner Records template
  POST FolderListingService.aspx/GetDocumentInfo   true page count (thumbnailPageCount caps at 5)
  POST DocumentService.aspx/GetTextHtmlForPage     OCR text, one request per page
One request a second, user agent step4-research-pull/1.0. No PDF download exists on this
portal, so OCR per page is the only text route.

Search: {[Commissioner Records]:[Notes]="*TAX INCENTIVE*"} & {[Commissioner Records]:[Hearing Date]>="M/D/YYYY"}
The hits are the 30-11-123 agreements plus a few Section 179D energy-deduction allocation forms
for county buildings (same words in Notes). Both are written; the 179D rows carry their own
record_type and are flagged N.

Cache: raw/weld_incentive_agreements/ (git-ignored). Step 2's OCR text at
step3-validation/weld/raw/lf_<docid>.txt is reused when it holds every page of the document,
so a rerun refetches only what is missing. The CSV is always rebuilt from the cache.

Every page of each agreement is OCR'd (the agreement sits on page 2 to 8 of the later packets).
For the 179D rows only page 1 (the resolution) is OCR'd; nothing in the rest of those packets is
needed. Small Business Incentive Program applications are not pulled (see notes_laserfiche.md).

Parsing rules: dollar caps, percentages and years come only from regexes anchored on the
agreement's own phrases; when the OCR does not give a clean number the field stays blank.
"""
import argparse, csv, http.cookiejar, json, os, re, sys, time, urllib.request
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WELD_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(WELD_DIR))
SLUG = "weld_incentive_agreements"
SOURCE = "Weld County incentive agreements"
RAW = os.path.join(WELD_DIR, "raw", SLUG)
STEP3_RAW = os.path.join(REPO, "step3-validation", "weld", "raw")
OUT = os.path.join(WELD_DIR, "scrape_%s.csv" % SLUG)

BASE = "https://minutes.weld.gov/WebLink/"
REPO_NAME = "CTBIMAGES"
UA = "step4-research-pull/1.0"
DELAY = 1.0
PARSER_VERSION = "1.0"

SHARED_COLS = ["source", "source_level", "record_id", "record_date", "date_type", "record_type",
               "company_name", "company_role", "site_address", "city", "county", "zip", "description",
               "flag", "flag_rule", "source_url", "retrieved_at"]
EXTRA_COLS = ["doc_code", "names_field", "notes_field", "page_count", "project_codename", "phase_1_cap",
              "phase_2_cap", "phase_3_cap", "rebate_pct", "term_years", "term_tax_years",
              "equipment_in_service_years", "other_parties", "facility_parcel",
              "est_phase_1_equipment_investment", "est_phase_2_equipment_investment",
              "est_phase_1_total_investment", "finance_sheet_new_equipment", "est_10yr_pp_tax_due", "laserfiche_entry_id", "ocr_source", "ocr_confidence_note",
              "parser_version"]

# Names-field lines that are not the taxpayer (economic development partners).
PARTNER_WORDS = re.compile(r"UPSTATE COLORADO|ECONOMIC DEVELOPMENT", re.I)
# A Names line is treated as a business when it carries one of these or a digit. Lines without
# one would be a person and are never written (none occur in the agreement hits).
BUSINESS_WORDS = re.compile(
    r"\b(LLC|L\.L\.C|INC|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLP|LLLP|PRODUCTS|TECHNOLOGIES|FOODS|"
    r"NUTRITION|SIDING|RENEWABLES|SYSTEMS|METAL|MACHINES|INDUSTRIAL|GLASS|ENERGY|PRECISION|"
    r"METALWORKS|PACKING|SPACE|MISSION|HEATING|CONTAINER|FARM|ENGINEERING|ARCHITECTURE|CONSULTING|"
    r"ENGINEERS|DEVELOPMENT|COLORADO|GROUP|HOLDINGS|PARTNERS|ENTERPRISES|SERVICES|SOLUTIONS|"
    r"MANUFACTURING|LOGISTICS|STUD|MACHINING|KENNELS|RANCH|TRUCKING|ACADEMY|CAMPGROUND|TUTORING|"
    r"PROPERTIES|EQUESTRIAN|MEATS|LOCKERS)\b", re.I)

# OCR fixes that are certain (documented in notes_laserfiche.md).
ADDRESS_FIXES = [
    (re.compile(r"\b1-(25|76|70)\b"), r"I-\1"),          # "1-76 Frontage Road" is I-76
]
CITY_FIXES = {"FREDRICK": "Frederick", "LASALLE": "LaSalle"}
# Per-document reading corrections taken from the step 2 notes (notes_county.md, rank 1 table),
# applied only where the OCR string is unreadable as an address.
ADDRESS_OVERRIDES = {
    "20231862": ("2400 W 29th Street", "OCR gives '2400 29`1 Street'; street read as W 29th Street per step 2 notes"),
}


# ----------------------------------------------------------------------------- HTTP
class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.op.addheaders = [("User-Agent", UA)]
        self.last = 0.0
        self.errors = 0
        self.requests = 0

    def _wait(self):
        dt = time.time() - self.last
        if dt < DELAY:
            time.sleep(DELAY - dt)
        self.last = time.time()

    def open_session(self):
        self._wait()
        r = self.op.open(BASE + "Welcome9.aspx?repo=" + REPO_NAME, timeout=60)
        r.read()
        self.requests += 1
        names = [c.name for c in self.cj]
        if "WebLinkSession" not in names:
            sys.exit("no WebLinkSession cookie from Welcome9.aspx; stopping")

    def post(self, path, payload):
        self._wait()
        req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": UA})
        try:
            r = self.op.open(req, timeout=120)
            body = r.read().decode("utf-8", "replace")
            self.requests += 1
        except Exception as e:  # noqa: BLE001
            self.errors += 1
            print("ERROR %s: %s" % (path, e), file=sys.stderr)
            if self.errors >= 3:
                sys.exit("three request errors; stopping (a block is an answer)")
            return None
        try:
            return json.loads(body)
        except ValueError:
            self.errors += 1
            print("ERROR %s: non-JSON body (%d bytes)" % (path, len(body)), file=sys.stderr)
            if self.errors >= 3:
                sys.exit("three request errors; stopping")
            return None


# ----------------------------------------------------------------------------- fetch with cache
def cache_path(name):
    return os.path.join(RAW, name)


def load_json(name):
    p = cache_path(name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(name, obj):
    with open(cache_path(name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def search_listing(client, since, fresh):
    """Run the field search, paging 100 at a time; cache the merged result list."""
    d = datetime.strptime(since, "%Y-%m-%d")
    syn = ('{[Commissioner Records]:[Notes]="*TAX INCENTIVE*"} & '
           '{[Commissioner Records]:[Hearing Date]>="%d/%d/%d"}' % (d.month, d.day, d.year))
    name = "search_%s.json" % since
    if not fresh:
        cached = load_json(name)
        if cached and cached.get("fetched_on") == datetime.now(timezone.utc).strftime("%Y-%m-%d"):
            return cached["results"], cached["hitCount"], syn
    results, start, page = [], 0, 100
    hit_count = None
    uuid = ""
    while True:
        res = client.post("SearchService.aspx/GetSearchListing",
                          {"repoName": REPO_NAME, "searchSyn": syn, "startIdx": start, "endIdx": start + page,
                           "getNewListing": start == 0, "searchUuid": uuid})
        if res is None:
            sys.exit("search failed; stopping")
        data = res["data"]
        if data.get("failed"):
            sys.exit("search reported failure: %s" % data.get("errMsg"))
        hit_count = data.get("hitCount")
        uuid = data.get("searchUuid") or uuid
        batch = data.get("results") or []
        results.extend(batch)
        if len(batch) < page or len(results) >= (hit_count or 0):
            break
        start += page
    save_json(name, {"fetched_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "searchSyn": syn,
                     "hitCount": hit_count, "results": results})
    return results, hit_count, syn


def document_info(client, entry_id, fresh):
    name = "info_%d.json" % entry_id
    if not fresh:
        c = load_json(name)
        if c:
            return c
    res = client.post("FolderListingService.aspx/GetDocumentInfo", {"repoName": REPO_NAME, "dId": entry_id})
    if res is None:
        return None
    save_json(name, res["data"])
    return res["data"]


def step3_pages(doc_id):
    """Pages from the step 2 OCR cache, as {page_no: text}, or {} when the file is missing."""
    p = os.path.join(STEP3_RAW, "lf_%s.txt" % doc_id)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    parts = re.split(r"=== PAGE (\d+) ===\n?", txt)
    pages = {}
    for i in range(1, len(parts) - 1, 2):
        pages[int(parts[i])] = parts[i + 1]
    return pages


def ocr_pages(client, doc_id, entry_id, page_count, pages_wanted, fresh):
    """Return ({page_no: text}, source_label). Order: raw cache, step 2 cache, live fetch."""
    out, sources = {}, set()
    s3 = {} if fresh else step3_pages(doc_id)
    for n in pages_wanted:
        name = "ocr_%s_p%d.txt" % (doc_id, n)
        p = cache_path(name)
        if not fresh and os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out[n] = f.read()
            sources.add("raw cache")
            continue
        if n in s3 and s3[n].strip():
            out[n] = s3[n]
            with open(p, "w", encoding="utf-8") as f:
                f.write(s3[n])
            sources.add("step 2 cache")
            continue
        res = client.post("DocumentService.aspx/GetTextHtmlForPage",
                          {"repoName": REPO_NAME, "documentId": entry_id, "pageNum": n, "showAnn": False,
                           "searchUuid": ""})
        if res is None:
            out[n] = ""
            continue
        text = (res.get("data") or {}).get("text") or ""
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        out[n] = text
        sources.add("live")
    return out, ", ".join(sorted(sources))


# ----------------------------------------------------------------------------- parsing
def meta(result):
    m = {}
    for f in result.get("metadata") or []:
        m[f["name"]] = [v for v in (f.get("values") or []) if v is not None]
    return m


def iso_date(s):
    try:
        return datetime.strptime(s.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def squash(text):
    for ch in (chr(0x2014), chr(0x2013)):      # em and en dash
        text = text.replace(ch, "-")
    for ch in (chr(0x201C), chr(0x201D)):      # curly quotes
        text = text.replace(ch, '"')
    return re.sub(r"\s+", " ", text)


def money(s):
    """'13,765,102' or '4,750,000' or '59.5 Million' -> integer dollars; None when unclear."""
    s = s.strip()
    m = re.match(r"^\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|m|b|mm)?\b\.?$", s, re.I)
    if not m:
        return None
    num = m.group(1)
    unit = (m.group(2) or "").lower()
    if "," in num and not re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", num):
        return None
    try:
        val = float(num.replace(",", ""))
    except ValueError:
        return None
    if unit in ("million", "m", "mm"):
        val *= 1_000_000
    elif unit in ("billion", "b"):
        val *= 1_000_000_000
    elif val < 10_000:
        return None  # a bare "$ 90" with no unit is not a usable amount
    return int(round(val))


def split_address(addr):
    """'4300 Godding Hollow Pkwy, Frederick, CO 80504' -> (street, city, zip).
    The OCR sometimes ends with ', CO 80642, Colorado' or ', Weld County, Colorado', so the
    state, zip and county tails are stripped repeatedly before the city is split off."""
    a = addr.strip().strip(",. ")
    for rx, rep in ADDRESS_FIXES:
        a = rx.sub(rep, a)
    a = re.sub(r"\s+", " ", a)
    zip_ = ""
    for _ in range(4):
        m = re.search(r"[,.]?\s*\b(\d{5})\s*$", a)
        if m:
            zip_ = zip_ or m.group(1)
            a = a[:m.start()].strip().strip(",. ")
            continue
        m = re.search(r"[,.]?\s*\b(Colorado|CO|Weld County)\s*$", a, flags=re.I)
        if m:
            a = a[:m.start()].strip().strip(",. ")
            continue
        break
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) >= 2:
        city = parts[-1].strip(". ")
        street = ", ".join(parts[:-1])
    else:
        city, street = "", a
    city = CITY_FIXES.get(city.upper(), city)
    return street, city, zip_


def parse_agreement(doc_id, text):
    """Pull the agreement facts out of the squashed OCR text of the whole packet."""
    f = {}
    notes = []
    # Facility
    addr = ""
    m = re.search(r"Facilit(?:y|ies) at (.{5,160}?)\s*\(\s*\"?\s*the Facility", text)
    if m:
        addr = m.group(1)
    else:
        m = re.search(r"\(\s*\"?the Business Facility\"?\s*\),?\s*at (.{5,160}?),\s*Colorado", text)
        if m:
            addr = m.group(1)
    if doc_id in ADDRESS_OVERRIDES:
        street_fix, note = ADDRESS_OVERRIDES[doc_id]
        _s, city, zip_ = split_address(addr) if addr else ("", "", "")
        f["site_address"], f["city"], f["zip"] = street_fix, city, zip_
        notes.append(note)
    elif addr:
        f["site_address"], f["city"], f["zip"] = split_address(addr)
    else:
        f["site_address"] = f["city"] = f["zip"] = ""
        notes.append("no 'Facility at' phrase found in OCR")
    # Rebate percentage: the clause "fifty-percent (50%) of the amount of ... taxes"
    m = re.search(r"percent\s*\(\s*(\d{1,3})\s*%\s*\)\s*of the amount of (?:personal property )?taxes", text, re.I)
    f["rebate_pct"] = m.group(1) if m else ""
    # Term: an explicit Term clause (BAE, 2026) wins over the standard "ten (10) tax years" wording
    term = ""
    m = re.search(r"term of this Agreement shall be from (\w+ \d{1,2}, \d{4}),? to and until (\w+ \d{1,2}, \d{4})", text)
    if m:
        try:
            d1 = datetime.strptime(m.group(1), "%B %d, %Y")
            d2 = datetime.strptime(m.group(2), "%B %d, %Y")
            term = str(round((d2 - d1).days / 365.25))
        except ValueError:
            pass
    if not term:
        m = re.search(r"\b(?:ten|five|fifteen|twenty)\s*\(\s*(\d{1,2})\s*\)\s*tax years", text, re.I)
        if m:
            term = m.group(1)
    f["term_years"] = term
    m = re.search(r"tax years beginning (?:in )?(\d{4}) and ending (?:in )?(\d{4})", text)
    f["term_tax_years"] = "%s-%s" % (m.group(1), m.group(2)) if m else ""
    # Equipment in-service window: text between "placed into service in Weld County in:" and "and appearing"
    m = re.search(r"placed into service in Weld County in:\s*(?:[a-d]\.\s*)?(.{4,60}?),?\s+and appearing", text)
    window = ""
    if m:
        w = m.group(1).strip(" ,.")
        if re.search(r"\b20\d\d\b", w) and re.match(r"^[A-Za-z0-9 ,\-]+$", w):
            window = re.sub(r"\s*-\s*", "-", re.sub(r"^(?:Between|between)\s+", "", w))
    if not window:
        m = re.search(r"in service between the years of (\d{4})\s*-\s*(\d{4})", text)
        if m:
            window = "%s-%s" % (m.group(1), m.group(2))
    f["equipment_in_service_years"] = window
    # Phase caps (only the word "cap" counts)
    caps = {1: "", 2: "", 3: ""}
    for m in re.finditer(r"Phase\s+(I{1,3}|[123])\b(.{0,400}?)cap of \$\s*([\d,]{5,})", text):
        n = {"I": 1, "II": 2, "III": 3, "1": 1, "2": 2, "3": 3}[m.group(1)]
        v = money(m.group(3))
        if v and not caps[n]:
            caps[n] = str(v)
    f["phase_1_cap"], f["phase_2_cap"], f["phase_3_cap"] = caps[1], caps[2], caps[3]
    # Codename
    cands = [c for c in re.findall(r"\bProject\s+([A-Z][a-z]{2,})\b", text)
             if c not in ("Information", "Description", "Assumptions", "Name", "Manager", "Summary", "Type",
                          "Details", "Location", "Address", "Overview", "Title", "Start", "Status", "Investment",
                          "Due", "Date", "Cost", "Costs", "Budget", "Timeline", "Scope", "Team", "Lead",
                          "Contact", "Phase", "Site", "Size", "Total", "Period", "Plan", "Form", "Mercury0")]
    f["project_codename"] = ("Project " + Counter(cands).most_common(1)[0][0]) if cands else ""
    # Project Information Form estimates (never guessed: strict money())
    def pif(rx):
        m = re.search(rx, text, re.I)
        if not m:
            return ""
        v = money(m.group(1))
        return str(v) if v else ""
    f["est_phase_1_equipment_investment"] = pif(r"Est\.?\s*Phase 1 New Equipment\s*\(depreciable personal property\)\s*Investment:?\s*\$?\s*([\d][\d,.]*\s*(?:Million|Billion|M|B)?)\b")
    f["est_phase_2_equipment_investment"] = pif(r"Est\.?\s*Phase 2 New Equipment\s*\(depreciable personal property\)\s*Investment:?\s*\$?\s*([\d][\d,.]*\s*(?:Million|Billion|M|B)?)\b")
    f["est_phase_1_total_investment"] = pif(r"Total Est\.?\s*Investment\s*\([^)]{0,60}\)\s*:?\s*\$?\s*([\d][\d,.]*\s*(?:Million|Billion|M|B)?)\b")
    f["finance_sheet_new_equipment"] = pif(r"\bNew Equipment:\s*\$\s*([\d][\d,.]*\s*(?:Million|Billion|M|B)?)\b")
    f["est_10yr_pp_tax_due"] = pif(r"10 YR TOTAL ESTIMATED PP TAX DUE:\s*\$\s*([\d][\d,.]*)\b")
    # Parcel number if the agreement states one (Weld parcels are 12 digits, often with no separators)
    m = re.search(r"\b(?:Parcel|PIN|Parcel No\.?|Parcel Number)[:#\s]*(\d{12}|\d{4}-\d{2}-\d{1}-\d{2}-\d{3})\b", text)
    f["facility_parcel"] = m.group(1) if m else ""
    f["_notes"] = notes
    return f


def company_from_names(names):
    """(taxpayer string, other parties string). Lines are upper case; one party per line."""
    taxpayers, partners = [], []
    for line in names:
        for part in line.split("\n"):
            p = part.strip()
            if not p:
                continue
            if PARTNER_WORDS.search(p):
                partners.append(p)
            elif BUSINESS_WORDS.search(p) or re.search(r"\d", p):
                taxpayers.append(p)
            else:
                # would be a person: never written
                continue
    return " / ".join(taxpayers), "; ".join(partners)


SMALL = {"and", "of", "the", "for", "at"}
KEEP_UPPER = {"LLC", "INC", "LP", "LLP", "LLLP", "II", "III", "IV", "US", "USA", "BAE", "TFP", "K2D", "GG", "CO"}


def title_case(s):
    out = []
    for w in s.split():
        wu = w.strip(".,").upper()
        if wu in KEEP_UPPER:
            out.append(w.upper())
        elif wu in SMALL and out:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def classify(m):
    notes = " ".join(m.get("Notes") or [])
    code = (m.get("DocCode") or [""])[0]
    if re.search(r"179D", notes, re.I):
        return "179D deduction allocation"
    if re.search(r"amend", notes, re.I):
        return "amendment"
    if code.startswith("RESO"):
        return "resolution"
    if code.startswith("AGRMT"):
        return "tax incentive agreement"
    return "other commissioner record"


def fmt_money(v):
    return "${:,.0f}".format(int(v)) if v else ""


def describe(rtype, company, f, notes_field):
    bits = []
    if rtype == "tax incentive agreement":
        bits.append("Tax incentive agreement (C.R.S. 30-11-123) with %s" % (company or "taxpayer"))
        if f.get("project_codename"):
            bits.append(f["project_codename"])
        if f.get("site_address"):
            bits.append("facility at %s%s" % (f["site_address"], (", " + f["city"]) if f.get("city") else ""))
        if f.get("rebate_pct"):
            bits.append("%s percent of personal property taxes on qualifying equipment" % f["rebate_pct"])
        if f.get("equipment_in_service_years"):
            bits.append("equipment placed in service %s" % f["equipment_in_service_years"])
        if f.get("term_years"):
            t = "%s-year term" % f["term_years"]
            if f.get("term_tax_years"):
                t += " (tax years %s)" % f["term_tax_years"]
            bits.append(t)
        caps = [(n, f.get("phase_%d_cap" % n)) for n in (1, 2, 3)]
        caps = ["Phase %s cap %s" % ("I II III".split()[n - 1], fmt_money(v)) for n, v in caps if v]
        if caps:
            bits.append("; ".join(caps))
        if f.get("est_phase_1_equipment_investment"):
            bits.append("est. phase 1 equipment investment %s" % fmt_money(f["est_phase_1_equipment_investment"]))
        if f.get("est_phase_2_equipment_investment"):
            bits.append("est. phase 2 equipment %s" % fmt_money(f["est_phase_2_equipment_investment"]))
        if f.get("est_phase_1_total_investment"):
            bits.append("est. phase 1 total investment (building, land, equipment) %s" % fmt_money(f["est_phase_1_total_investment"]))
        if not f.get("est_phase_1_equipment_investment") and f.get("finance_sheet_new_equipment"):
            bits.append("new equipment per Finance sheet %s" % fmt_money(f["finance_sheet_new_equipment"]))
        if f.get("est_10yr_pp_tax_due"):
            bits.append("county's 10-year personal property tax estimate %s" % fmt_money(f["est_10yr_pp_tax_due"]))
    elif rtype == "179D deduction allocation":
        bits.append("Section 179D energy efficient commercial building deduction allocation for a county "
                    "building project (not a 30-11-123 incentive); allocated to %s" % (company or "designer"))
        bits.append("Notes: " + notes_field)
    else:
        bits.append("%s; Notes: %s" % (rtype, notes_field))
    d = "; ".join(bits)
    for ch in (chr(0x2014), chr(0x2013)):
        d = d.replace(ch, "-")
    if len(d) > 500:
        cut = d.rfind("; ", 0, 500)
        d = d[:cut] if cut > 200 else d[:500]
    return d


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2022-01-01")
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)

    client = Client()
    client.open_session()
    results, hit_count, syn = search_listing(client, args.since, args.fresh)
    print("search hits: %s (listed %d) for %s" % (hit_count, len(results), syn))
    # An incremental --since run must not drop the older rows: merge every cached listing by entryId.
    merged = {}
    for fn in sorted(os.listdir(RAW)):
        if fn.startswith("search_") and fn.endswith(".json"):
            for r in (load_json(fn) or {}).get("results", []):
                merged[r["entryId"]] = r
    for r in results:
        merged[r["entryId"]] = r
    results = list(merged.values())
    print("documents to process (all cached listings merged): %d" % len(results))

    rows = []
    for r in results:
        m = meta(r)
        doc_id = r["name"]
        entry_id = r["entryId"]
        rtype = classify(m)
        info = document_info(client, entry_id, args.fresh) or {}
        page_count = int(info.get("pageCount") or r.get("thumbnailPageCount") or 0)
        wanted = list(range(1, page_count + 1)) if rtype in ("tax incentive agreement", "resolution", "amendment") else [1]
        pages, ocr_source = ocr_pages(client, doc_id, entry_id, page_count, wanted, args.fresh)
        text = squash(" ".join(pages.get(n, "") for n in wanted))
        empty = [n for n in wanted if not pages.get(n, "").strip()]

        names = m.get("Names") or []
        notes_vals = m.get("Notes") or []
        company, partners = company_from_names(names)
        names_field = " | ".join(" | ".join(x.split("\n")) for x in names)
        notes_field = " | ".join(" | ".join(x.strip() for x in x.split("\n") if x.strip()) for x in notes_vals)
        hearing = iso_date((m.get("Hearing Date") or [""])[0])
        retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        f = {}
        conf = []
        if rtype in ("tax incentive agreement", "amendment", "resolution"):
            f = parse_agreement(doc_id, text)
            conf.extend(f.pop("_notes"))
            if re.search(r"Upstate Colorado", text, re.I) and "UPSTATE COLORADO" not in partners.upper():
                partners = "; ".join([p for p in [partners, "UPSTATE COLORADO ECONOMIC DEVELOPMENT"] if p])
            role = "taxpayer"
            flag = "Y" if company else "N"
            rule = "county tax incentive agreement" if flag == "Y" else ""
        else:
            role = "grantee"
            flag, rule = "N", ""
            f = {"site_address": "", "city": "", "zip": ""}
            mm = re.search(r"\b(\d{2,5} [A-Z0-9][\w ]{2,40}?(?:ST|STREET|AVE|AVENUE|RD|ROAD|DR|DRIVE|BLVD|WAY|PL|PKWY))\b,?\s*([A-Z]+)", notes_field)
            if mm:
                f["site_address"], f["city"] = title_case(mm.group(1)), title_case(mm.group(2))
                f["city"] = CITY_FIXES.get(f["city"].upper(), f["city"])
        if empty:
            conf.append("OCR empty on page(s) %s" % ",".join(map(str, empty)))
        if ocr_source and ocr_source != "live":
            conf.append("text from %s" % ocr_source)
        city = f.get("city") or ""
        row = {
            "source": SOURCE, "source_level": "County (Weld)", "record_id": doc_id, "record_date": hearing,
            "date_type": "hearing", "record_type": rtype, "company_name": company, "company_role": role,
            "site_address": f.get("site_address", ""), "city": city or ("Unincorporated Weld County" if rtype == "tax incentive agreement" else "Weld County"),
            "county": "Weld", "zip": f.get("zip", ""),
            "description": describe(rtype, company, f, notes_field), "flag": flag, "flag_rule": rule,
            "source_url": "https://minutes.weld.gov/WebLink/DocView.aspx?id=%d&dbid=0&repo=%s" % (entry_id, REPO_NAME),
            "retrieved_at": retrieved,
            "doc_code": (m.get("DocCode") or [""])[0], "names_field": names_field, "notes_field": notes_field,
            "page_count": str(page_count), "project_codename": f.get("project_codename", ""),
            "phase_1_cap": f.get("phase_1_cap", ""), "phase_2_cap": f.get("phase_2_cap", ""),
            "phase_3_cap": f.get("phase_3_cap", ""), "rebate_pct": f.get("rebate_pct", ""),
            "term_years": f.get("term_years", ""), "term_tax_years": f.get("term_tax_years", ""),
            "equipment_in_service_years": f.get("equipment_in_service_years", ""), "other_parties": partners,
            "facility_parcel": f.get("facility_parcel", ""),
            "est_phase_1_equipment_investment": f.get("est_phase_1_equipment_investment", ""),
            "est_phase_2_equipment_investment": f.get("est_phase_2_equipment_investment", ""),
            "est_phase_1_total_investment": f.get("est_phase_1_total_investment", ""),
            "finance_sheet_new_equipment": f.get("finance_sheet_new_equipment", ""),
            "est_10yr_pp_tax_due": f.get("est_10yr_pp_tax_due", ""),
            "laserfiche_entry_id": str(entry_id), "ocr_source": ocr_source or "none",
            "ocr_confidence_note": "; ".join(conf), "parser_version": PARSER_VERSION,
        }
        rows.append(row)

    rows.sort(key=lambda x: (x["record_date"], x["record_id"]))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SHARED_COLS + EXTRA_COLS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    by_type = Counter(r["record_type"] for r in rows)
    by_rule = Counter(r["flag_rule"] or "(none)" for r in rows)
    print("rows written: %d -> %s" % (len(rows), OUT))
    print("by record_type:", dict(by_type))
    print("by flag_rule:", dict(by_rule))
    print("requests this run: %d, errors: %d" % (client.requests, client.errors))


if __name__ == "__main__":
    main()
