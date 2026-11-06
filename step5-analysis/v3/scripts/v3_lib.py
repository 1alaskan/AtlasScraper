#!/usr/bin/env python3
"""Step 5 v3 shared code: constants, the fixed points table, text normalisers and file readers.

Nothing here reads the earlier rankings. The points table is the one in prompt_5_analysis_v2.md and is not tuned.
Standard library only, so it runs on the Step 4 machine as it is.
"""
import csv, json, os, re

csv.field_size_limit(10 ** 9)

RUN = "2026-10-11"      # run date for recency
D12 = "2025-10-11"      # 12 months before the run date
D24 = "2024-10-11"      # 24 months before the run date
D6 = "2026-04-11"       # 6 months before the run date (fit-out window for a finaled permit)

UCC = "Colorado UCC filings"
REG = "Colorado business registrations"
PER = "Denver commercial construction permits"
SDP = "Denver concept and site plans"
WAT = "State water permits (WQCD)"
AIR = "APCD air permit status"
CRE = "Mile High CRE"
OED = "OEDIT EDC approvals"
INC = "County incentive agreements"   # named county personal-property tax incentive agreements (C.R.S. 30-11-123); added 2026-11-06, Weld first
SRC_ORDER = [UCC, AIR, PER, WAT, SDP, REG, CRE, OED, INC]
SHORT = {WAT: "State water permits"}

FILES = {
    UCC: os.path.join("scrape_ucc_filings", "scrape_ucc_filings_v2.csv"),
    REG: os.path.join("scrape_business_registrations", "scrape_business_registrations_v2.csv"),
    PER: "scrape_denver_commercial_permits_v2.csv",
    SDP: "scrape_denver_site_plans.csv",
    WAT: "scrape_state_water_permits.csv",
    AIR: "scrape_apcd_permit_status.csv",
    CRE: "scrape_mile_high_cre.csv",
    OED: "scrape_oedit_approvals.csv",
}
B1A_HITS = os.path.join("scrape_ucc_filings", "ucc_b1a_fulltext_hits.csv")

SHARED = ["source", "source_level", "record_id", "record_date", "date_type", "record_type", "company_name", "company_role",
          "site_address", "city", "county", "zip", "description", "flag", "flag_rule", "source_url", "retrieved_at"]

# --------------------------------------------------------------------------- points table (fixed; do not retune)
PTS = {
    "ucc_compressor": 30,        # UCC filing naming an air compressor or compressed-air system (tier A)
    "ucc_b1a": 30,               # UCC filing with a tier B process-equipment word (B1a)
    "ucc_machinery": 25,         # UCC filing naming production machinery (tier A)
    "air_process": 25,           # air permit application, modification or approval for process units
    "permit_new": 22,            # Denver permit, new building or addition, industrial property, $250k or more
    "water_construction": 20,    # construction stormwater permit with a manufacturing SIC or company-named facility
    "incentive_named": 20,       # county tax incentive agreement naming the company and the facility address (approved before the equipment goes into service); added 2026-11-06
    "permit_alt": 18,            # Denver permit, alteration or tenant finish, industrial property, $250k or more
    "permit_b3a": 12,            # Denver permit, $50k to $250k, industrial property (B3a)
    "air_apen": 12,              # air permit APEN-only or exempt
    "water_new": 12,             # new industrial stormwater or no-exposure certification
    "sdp_heavy": 12,             # concept or site plan on I-A or I-B zoning
    "ucc_weak": 8,               # UCC flagged word without production machinery; towable compressor
    "press_name": 8,             # press story naming the company
    "ucc_b1b": 8,                # vague lien held by an equipment lender (B1b)
    "ucc_b1c": 8,                # blanket lien on a maker (B1c)
    "reg_a": 6,                  # flagged tier A registration
    "sdp_imx": 6,                # concept or site plan on industrial mixed-use zoning
    "permit_b3b": 6,             # Denver permit under $50k on industrial property (B3b)
    "permit_unflagged": 6,       # unflagged permit at the company's address
    "press_addr": 5,             # press story naming only the address
    "oedit": 5,                  # OEDIT code-name approval
    "ucc_generic": 4,            # generic or blanket UCC lien (support)
    "sdp_other": 4,              # other site plan at the address (support)
    "reg_b": 3,                  # tier B registration (B2a)
    "reg_unflagged": 3,          # unflagged registration (support)
    "noise": 2,                  # air or water row cut as noise (support)
}
MILLION_BONUS = 3                # +3 on a flagged tier A permit of $1M or more
REPEAT_PTS, REPEAT_MAX, REPEAT_MIN = 3, 9, 12
SRC_SIGNAL_MIN = 5               # a source counts as an independent signal source at 5 points or more
SRC_BONUS, SRC_BONUS_MAX = 8, 24
SUP_BONUS, SUP_BONUS_MAX = 3, 6
REC_MIN = 4                      # recency looks at the latest row worth 4 points or more
REC_12, REC_24 = 15, 8
STAGE_PTS = {"buying equipment": 12, "fit-out": 12, "under construction": 8, "operating and expanding": 8, "planned": 4, "unknown": 0}
STAGE_ORDER = ["buying equipment", "fit-out", "under construction", "operating and expanding", "planned", "unknown"]
SMALL_PERMIT_STAGE_CAP = 4       # a permit under $50k adds at most 4 stage points, whatever its status
FIT_PTS = {"strong": 15, "moderate": 6, "unknown": 0, "weak": -15}
TIER_B_KINDS = {"ucc_b1a", "ucc_b1b", "ucc_b1c", "reg_b", "permit_b3a", "permit_b3b"}

# --------------------------------------------------------------------------- normalisers
STATUS_TAIL = re.compile(r",\s*(?:Dissolved|Delinquent|Noncompliant|Withdrawn|Converted|Merged)\b.*$", re.I)


def clean_name(s):
    """Display form: drop a status note that the filer typed into the name (", Dissolved April 24, 2025")."""
    return STATUS_TAIL.sub("", s or "").strip()


_ENT_ANY = {"INC", "INCORPORATED", "LLC", "CORP", "CORPORATION", "LTD", "LIMITED", "LP", "LLP", "LLLP", "PC", "PLLC", "DBA"}
_ENT_TAIL = {"CO", "COMPANY"}


def nk(s):
    """Name key: upper case, no punctuation, no leading 'The', no entity words, single letters joined (R B MACHINE -> RB MACHINE).
    'Co' and 'Company' are dropped only at the end of the name, so 'CB CO Manufacturing' does not collapse into 'CB Manufacturing'."""
    s = STATUS_TAIL.sub("", s or "").upper()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("&", " AND ").replace("'", "").replace("\u2019", "")
    s = re.sub(r"\bL L C\b", " LLC ", re.sub(r"[^A-Z0-9 ]", " ", s))
    t = [w for w in s.split() if w not in _ENT_ANY]
    if t and t[0] == "THE":
        t = t[1:]
    while t and t[-1] in _ENT_TAIL:
        t = t[:-1]
    out = []
    run = False
    for w in t:
        single = len(w) == 1 and w.isalpha()
        if single and run and out:
            out[-1] += w
        else:
            out.append(w)
        run = single
    return " ".join(out)


GENERIC_LEAD = {"DENVER", "COLORADO", "ROCKY", "MOUNTAIN", "MILE", "HIGH", "FRONT", "RANGE", "WESTERN", "WEST", "EAST", "NORTH",
                "SOUTH", "AMERICAN", "AMERICA", "UNITED", "NATIONAL", "FIRST", "NEW", "BLUE", "RED", "GREEN", "BIG", "ALL",
                "CITY", "METRO", "SUMMIT", "PEAK", "ELEVATION", "ELEVATED", "ALPINE", "CENTENNIAL", "A", "AND", "PROJECT"}


def lead_word(key):
    t = key.split()
    if not t:
        return ""
    w = re.sub(r"S$", "", t[0]) if len(t[0]) > 4 else t[0]
    return w


def same_company_by_lead(k1, k2):
    """Two names at one address are one company when they share a distinctive leading word, or their first two words."""
    t1, t2 = k1.split(), k2.split()
    if not t1 or not t2:
        return False
    if len(t1) >= 2 and len(t2) >= 2 and t1[:2] == t2[:2]:
        return True
    l1, l2 = lead_word(k1), lead_word(k2)
    return l1 == l2 and len(l1) >= 4 and l1 not in GENERIC_LEAD and not l1.isdigit()


HAS_UNIT = re.compile(r"(?:\b(?:ste|suite|unit|apt|bldg|building|bay|spc|space|fl|floor|rm|room|dock)\b\.?\s*#?\s*[A-Za-z0-9-]+|#\s*[A-Za-z0-9-]+)", re.I)
_TYPES = {"ST", "STREET", "AVE", "AVENUE", "AV", "BLVD", "BOULEVARD", "RD", "ROAD", "DR", "DRIVE", "LN", "LANE", "CT", "COURT",
          "PL", "PLACE", "WAY", "PKWY", "PARKWAY", "CIR", "CIRCLE", "HWY", "HIGHWAY", "TER", "TERRACE", "TRL", "TRAIL"}
_DIRS = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "N": "N", "S": "S", "E": "E", "W": "W"}


def addr_key(a):
    """House number + S/W/E prefix + street name. N prefixes, street types and units are dropped (the Step 5 method)."""
    a = (a or "").upper().replace(".", " ").replace(",", " ")
    a = re.sub(r"\b(?:STE|SUITE|UNIT|APT|BLDG|BUILDING|BAY|SPC|SPACE|FL|FLOOR|RM|ROOM)\b\.?\s*#?\s*[A-Z0-9-]+.*$", "", a)
    a = re.sub(r"#\s*[A-Z0-9-]+.*$", "", a)
    t = a.split()
    if len(t) < 2 or not re.match(r"^\d+[A-Z]?$", t[0]):
        return ""
    num = re.sub(r"[A-Z]$", "", t[0])
    rest = t[1:]
    pre = ""
    if rest and rest[0] in _DIRS and len(rest) > 1:
        pre = _DIRS[rest[0]]
        rest = rest[1:]
    out = []
    for w in rest:
        if w in _TYPES and out:
            break
        out.append(w)
    if out and re.match(r"^\d+(?:ST|ND|RD|TH)$", out[0]):
        out = out[:1]          # a numbered street is one word; anything after it with no street type is a unit ("9400 E 46th 101")
    name = " ".join(out)
    name = re.sub(r"^(\d+)(?:ST|ND|RD|TH)$", r"\1", name)
    if pre == "N":
        pre = ""
    return (num + " " + (pre + " " if pre else "") + name).strip()


def unit_of(a):
    a = (a or "").upper().replace(",", " ").replace(".", " ")
    m = re.search(r"(?:\b(?:STE|SUITE|UNIT|APT|BLDG|BUILDING|BAY|SPC|SPACE|RM|ROOM)\b\s*#?\s*|#\s*)([A-Z0-9-]+)", a)
    if m and m.group(1) not in ("UNIT", "SUITE"):
        return m.group(1).lstrip("0") or m.group(1)
    m = re.search(r"\b(?:ST|AVE|BLVD|RD|DR|LN|CT|PL|WAY|PKWY|CIR|HWY)\s+([A-Z]?\d+[A-Z]?|[A-Z])(?:\s|$)", a)
    if not m:
        m = re.search(r"^\d+[A-Z]?\s+(?:[NSEW]\s+)?\d+(?:ST|ND|RD|TH)\s+([A-Z]?\d+[A-Z]?)(?:\s|$)", a.strip())
    return (m.group(1).lstrip("0") or m.group(1)) if m else ""


def units_conflict(u1, u2):
    return bool(u1 and u2 and u1 != u2)


def norm_party(s):
    s = re.sub(r"[^A-Z0-9& ]", " ", (s or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def reg_addr_key(r):
    """Address and suite key for the registered-agent test (10 or more 2024-26 registrations at one address and suite)."""
    a = re.sub(r"[^A-Z0-9 ]", " ", r["site_address"].upper())
    a = re.sub(r"\b(?:SUITE|STE|UNIT|APT|NO|NUMBER)\b", "#", a)
    a = re.sub(r"\s+", " ", a).strip()
    return a + "|" + r["zip"][:5] if a else ""


AGENT_MIN = 10


NOT_A_SITE = re.compile(r"\b(?:apt|apartment|pmb)\b", re.I)     # an apartment or private mailbox never qualifies an address for display
BUILDING_MIN = 200       # registrations at one street address and zip, any suite: a mailbox or agent building


def building_key(r):
    ak = addr_key(r["site_address"])
    return ("B|" + ak + "|" + r["zip"][:5]) if ak else ""


def agent_keys(r):
    """Two keys for the registered-agent test: the Step 4b text key, and a normalised (street, suite, zip) key that also
    catches 'Ste 700' against 'Suite 700' and private-mailbox numbers."""
    ak = addr_key(r["site_address"])
    return reg_addr_key(r), ((ak + "|" + unit_of(r["site_address"]) + "|" + r["zip"][:5]) if ak else "")


def is_agent_address(r, agent_count):
    k1, k2 = agent_keys(r)
    if (k1 and agent_count.get(k1, 0) >= AGENT_MIN) or (k2 and agent_count.get(k2, 0) >= AGENT_MIN):
        return True
    b = building_key(r)
    return bool(b and agent_count.get(b, 0) >= BUILDING_MIN)


def money(v):
    try:
        return "${:,.0f}".format(float(v or 0))
    except ValueError:
        return "$?"


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def g(x):
    return ("%g" % x)


def no_emdash(s):
    return (s or "").replace(chr(8212), "-").replace(chr(8211), "-")


# --------------------------------------------------------------------------- IO
def reader(folder, source):
    f = open(os.path.join(folder, FILES[source]), newline="", encoding="utf-8-sig")
    return csv.DictReader(f)


def read_all(folder, source):
    with open(os.path.join(folder, FILES[source]), newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def find_files(out):
    """-> (ranked file, evidence file) in a v3 output folder, whatever the county prefix is."""
    import glob
    rk = sorted(glob.glob(os.path.join(out, "*_ranked_accounts_v3.csv")))
    ev = sorted(glob.glob(os.path.join(out, "*_evidence_v3.csv")))
    if len(rk) != 1 or len(ev) != 1:
        raise SystemExit("Expected exactly one *_ranked_accounts_v3.csv and one *_evidence_v3.csv in %s" % out)
    return rk[0], ev[0]


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


HERE = os.path.dirname(os.path.abspath(__file__))
