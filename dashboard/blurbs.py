"""Plain-English blurbs for ranked accounts.

signal_blurb(row) turns a ranked-account row (stage, top_evidence,
match_confidence) into one or two sentences a salesperson can read without
knowing the source codes: what kind of activity the records show, roughly
when, and how sure we are that the company named is really the one at the
address. It parses the fixed phrasing the analysis step writes into
top_evidence; anything it does not recognise falls back to a trimmed copy
of the raw item.
"""
from __future__ import annotations

import re
from datetime import date

MAX_ITEMS = 3

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _mon(s: str | None) -> str:
    if not s:
        return ""
    m = re.match(r"(\d{4})-(\d{2})", s)
    if not m:
        return s
    return f"{_MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


def _money(s: str | None) -> str:
    if not s or not s.startswith("$"):
        return ""
    try:
        v = float(s[1:].replace(",", ""))
    except ValueError:
        return s
    if v <= 0:
        return ""
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M".replace(".0M", "M")
    if v >= 1_000:
        return f"${v / 1_000:.0f}k"
    return f"${v:.0f}"


def _title(s: str) -> str:
    s = s.strip()
    if s.isupper():
        s = s.title()
    return s


def _trim(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1].rstrip(" ,;:") + "…"


def _is_support(item: str) -> bool:
    low = item.lower()
    return "support only" in low or "(support" in low or "cut as noise" in low


# ----------------------------------------------------------------------------
# per-source parsers: each returns a phrase or None
# ----------------------------------------------------------------------------
_PERMIT_TYPES = {
    "new building": "new-building permit",
    "phased construction": "phased-construction permit",
    "alteration/tenant finish": "tenant-finish / alteration permit",
    "addition": "building-addition permit",
    "foundation only/excavation": "foundation and excavation permit",
    "change of use only": "change-of-use permit",
    "new non-building structure": "permit for a new tank, rack or yard structure",
    "repair/replace": "repair / replace permit",
}

_PERMIT_RE = re.compile(
    r"^(?P<juris>\w+) permit (?P<id>\S+)(?: \[tier B[^\]]*\])?(?: at this address)?: "
    r"(?P<type>[^,]+), (?P<val>\$[\d,]+|no valuation), received (?P<rec>\d{4}-\d{2}-\d{2})"
    r"(?:, issued (?P<iss>\S+))?(?:, (?P<fin>not finaled|finaled \S+))?"
)


def _permit(item: str) -> str | None:
    m = _PERMIT_RE.match(item)
    if not m:
        return None
    kind = _PERMIT_TYPES.get(m.group("type").strip().lower(), m.group("type").strip().lower() + " permit")
    money = _money(m.group("val"))
    out = f"a {money + ' ' if money else ''}{kind} filed {_mon(m.group('rec'))}"
    fin = m.group("fin") or ""
    iss = m.group("iss") or ""
    if fin.startswith("finaled"):
        out += f", completed {_mon(fin.split()[-1])}"
    elif fin == "not finaled" and iss and iss != "n/a":
        out += ", issued and still open"
    elif fin == "not finaled":
        out += ", not yet issued"
    if "tied to" in item and "back-test" in item:
        out += " (tied to this company by the back-test)"
    return out


_AIR_STATUS = {
    "to be determined": "application pending",
    "final approval": "approved",
    "fa, modification": "modification approved",
    "ia, modification": "modification applied for",
    "initial application": "new application",
    "fa, transfer plant ownership": "ownership transferred",
    "permit exempt, apen only": "exempt-level, emissions notice only",
    "permit exempt, apen exempt": "exempt-level",
}

_AIR_RE = re.compile(
    r"^Air permit(?: row)? (?P<id>\S+) \((?P<status>[^)]*)\) received (?P<date>\d{4}-\d{2}-\d{2})"
    r"(?P<rest>.*)$"
)


def _air(item: str) -> str | None:
    m = _AIR_RE.match(item)
    if not m:
        return None
    status = _AIR_STATUS.get(m.group("status").strip().lower(), m.group("status").strip().lower())
    rest = m.group("rest")
    desc = ""
    if ":" in rest:
        desc = rest.split(":", 1)[1]
        desc = re.sub(r";\s*AIRS.*$", "", desc)
        desc = re.sub(r"\(ID:[^)]*\)", "", desc)
        desc = re.sub(r"\(cut as noise.*$", "", desc)
        desc = re.sub(r"\(support.*$", "", desc)
        desc = desc.strip(" ;")
    out = f"a state air-emissions permit ({status}) received {_mon(m.group('date'))}"
    if "support only" in item.lower() and "applicant" in item.lower():
        appl = re.search(r"applicant ([^(\[]+)", item)
        if appl:
            out += f" in the name of {_title(appl.group(1))}"
        return out + " at this address"
    if desc:
        out += f" for '{_trim(_title(desc), 70)}'"
    return out


_UCC_KW_RE = re.compile(r"^UCC (?P<date>\d{4}-\d{2}-\d{2}): (?P<kw>[^|]+)\|(?P<desc>.*)$")
_UCC_INIT_RE = re.compile(
    r"^UCC (?P<date>\d{4}-\d{2}-\d{2}) initial filing(?: \[tier B[^\]]*\])?, secured party (?P<sp>[^:]+): (?P<desc>.*)$"
)


def _ucc(item: str) -> str | None:
    m = _UCC_KW_RE.match(item)
    if m:
        kws = [k.strip() for k in m.group("kw").split(",") if k.strip()]
        return f"financed production equipment ({', '.join(kws[:4])}) in {_mon(m.group('date'))}"
    m = re.match(r"^UCC (?P<date>\d{4}-\d{2}-\d{2}) initial filing by a debtor at this address", item)
    if m:
        occ = re.search(r"possible occupier ([^)\]]+)", item)
        who = f" by {_title(occ.group(1).strip())}" if occ else ""
        return f"a UCC financing statement filed{who} at this address in {_mon(m.group('date'))} (collateral not described)"
    m = _UCC_INIT_RE.match(item)
    if not m:
        return None
    sp = _title(re.sub(r"\s*\[.*$", "", m.group("sp")))
    sp = "" if sp.lower().startswith("not given") else sp
    lender = f" from {sp}" if sp else ""
    desc = m.group("desc")
    if "blanket lien" in desc.lower():
        return f"a blanket all-assets lien{lender} in {_mon(m.group('date'))} (what was bought is not described)"
    desc = re.sub(r"\(support.*$", "", desc)
    desc = re.sub(r"\[.*$", "", desc).strip(" :;,")
    return f"an equipment lien{lender} in {_mon(m.group('date'))} covering '{_trim(desc, 60)}'"


_WATER_PROG = {
    "COR400000": "a construction-stormwater permit (site work under way)",
    "COR900000": "an industrial-stormwater permit",
    "CONOX000": "an industrial no-exposure stormwater certification",
    "COG500000": "a sand-and-gravel process-water permit",
    "COG080000": "a construction-dewatering permit",
    "COE": "a reclaimed-water reuse permit",
}

_WATER_RE = re.compile(
    r"^Water permit(?: row)? (?P<id>\S+) \((?P<prog>[^)]+)\) received (?P<date>\d{4}-\d{2}-\d{2}): "
    r"facility (?P<fac>.+?), permittee (?P<perm>.+?), SIC (?P<sic>\S+)(?: (?P<sicdesc>[^,]+))?, status (?P<status>[^(\[]+)"
)


def _water_kind(prog: str) -> str:
    kind = _WATER_PROG.get(prog)
    if kind is None:
        kind = next((v for k, v in _WATER_PROG.items() if prog.startswith(k)), None)
    if kind is None:
        kind = "a construction-dewatering / groundwater permit" if prog.startswith("COG31") else "a state water permit"
    return kind


_WATER_LOOSE_RE = re.compile(
    r"^Water permit(?: row)? (?P<id>\S+) \((?P<prog>[^)]+)\) received (?P<date>\d{4}-\d{2}-\d{2})(?: at this address)?: "
    r"(?:project or facility )?'?(?P<fac>[^'(\[]+)'?"
)


def _water(item: str) -> str | None:
    m = _WATER_RE.match(item)
    if not m:
        m2 = _WATER_LOOSE_RE.match(item)
        if not m2:
            return None
        fac = m2.group("fac").strip(" ,")
        return f"{_water_kind(m2.group('prog').strip())} received {_mon(m2.group('date'))} for '{_trim(fac, 45)}'"
    prog = m.group("prog").strip()
    kind = _water_kind(prog)
    out = f"{kind} received {_mon(m.group('date'))}"
    sic = m.group("sic").strip(" ,")
    sicdesc = (m.group("sicdesc") or "").strip()
    if sic and sic.lower() != "none":
        if sicdesc:
            out += f", listing the site as SIC {sic} ({sicdesc.lower()})"
        elif sic[0] in "23":
            out += f", listing a manufacturing SIC code ({sic})"
        else:
            out += f", listing SIC {sic}"
    fac = m.group("fac").strip()
    if fac and fac.lower() not in item.split(":")[0].lower():
        out += f" for the facility '{_trim(fac, 40)}'"
    return out


_ENTITY = {"DLLC": "Colorado LLC", "FLLC": "out-of-state LLC", "DPC": "Colorado corporation",
           "FPC": "out-of-state corporation", "DLP": "Colorado limited partnership",
           "DLLP": "Colorado limited liability partnership", "DNC": "Colorado nonprofit",
           "FNC": "out-of-state nonprofit", "DPC-PBC": "Colorado public-benefit corporation"}
_REG_RE = re.compile(
    r"^Registered in Colorado (?P<date>\d{4}-\d{2}-\d{2}) \((?P<ent>[\w-]+)(?:, (?P<home>\w+))?\)(?: \[tier B[^\]]*\])? ?; "
    r"status (?P<status>[^;]+)(?:; office (?P<office>[^(\[;]+))?(?:; name word: (?P<word>\w+))?"
)


def _registration(item: str) -> str | None:
    m = _REG_RE.match(item)
    if not m:
        return None
    ent = _ENTITY.get(m.group("ent"), "business")
    if m.group("home"):
        ent = ent.replace("out-of-state", f"{m.group('home')}-based")
    office = (m.group("office") or "").strip()
    if office.startswith("at this address"):
        where = " at this address"
    elif office:
        where = f" with its office in {office}"
    else:
        where = ""
    out = f"a new {ent} registered {_mon(m.group('date'))}{where} (status {m.group('status').strip().lower()})"
    if m.group("word"):
        out += f"; the name contains '{m.group('word')}'"
    occ = re.search(r"possible occupier ([^)\]]+)", item) or re.search(r"\[([^\]]+) has this address", item)
    if occ:
        out += f", possibly {_title(occ.group(1).strip())}"
    return out


_PLAN_TYPES = [
    (r"concept review", "a concept-review planning case"),
    (r"conceptual review", "a conceptual-review planning case"),
    (r"standard sdp|site development plan", "a site-development-plan application"),
    (r"sdp modification|sdp amendment", "a site-plan modification"),
    (r"site plan minor amendment", "a minor site-plan amendment"),
    (r"site plan new", "a new site-plan application"),
    (r"site plan review", "a site-plan review"),
    (r"rezone", "a rezoning / conditional-use case"),
    (r"variance", "a zoning variance request"),
    (r"subdivision", "a subdivision plat"),
    (r"bocc project", "a county-commissioner project case"),
    (r"temporary use", "a temporary-use permit"),
    (r"development plan", "a development-plan application"),
    (r"development permits", "a development permit application"),
    (r"mining", "a mining / construction-debris case"),
    (r"liquor", "a liquor licence"),
    (r"marijuana", "a marijuana establishment licence"),
    (r"commercial addition", "a commercial-addition plan review"),
    (r"commercial new construction", "a commercial new-construction plan review"),
    (r"conditional use", "a conditional-use case"),
    (r"pud|planned unit", "a planned-unit-development case"),
    (r"plat|replat", "a subdivision plat"),
    (r"boa project", "a board-of-adjustment case"),
    (r"use-by", "a use-by-right permit"),
    (r"zoning", "a zoning case"),
    (r"vacation|right of way", "a right-of-way / vacation case"),
    (r"planning (case|project)|^other$", "a planning case"),
]

_PLAN_RE = re.compile(
    r"^(?P<juris>Denver|Adams|Weld) (?P<type>.+?) (?P<id>\S+)(?: at this address,?)? opened (?P<date>\d{4}-\d{2}-\d{2}), status (?P<status>.*?), zone ?(?P<zone>[^\[(]*)"
)


def _planning(item: str) -> str | None:
    m = _PLAN_RE.match(item)
    if not m:
        return None
    t = m.group("type").lower()
    kind = next((v for pat, v in _PLAN_TYPES if re.search(pat, t)), f"a {t.lower()} planning case")
    status = m.group("status").strip()
    out = f"{kind} opened {_mon(m.group('date'))}"
    if status:
        out += f" ({status.lower()})"
    if "industrial" in item.lower() or re.match(r"\s*I-", m.group("zone") or ""):
        out += " on industrially zoned land"
    return out


_CRE_RE = re.compile(r"^Mile High CRE (?P<date>\d{4}-\d{2}-\d{2}) (?:names|mentions) (?:this address|the company): (?P<title>.+?)(?: \[.*)?$")


def _cre(item: str) -> str | None:
    m = _CRE_RE.match(item)
    if not m:
        return None
    return f"a commercial real-estate news story ({_mon(m.group('date'))}): '{_trim(m.group('title'), 80)}'"


_OEDIT_RE = re.compile(r"^OEDIT (?P<date>\d{4}-\d{2}-\d{2}) (?P<prog>[^:]+): (?P<desc>.+?)(?:; jobs (?P<jobs>\d+))?(?: \[.*)?$")


def _oedit(item: str) -> str | None:
    m = _OEDIT_RE.match(item)
    if not m:
        return None
    jobs = f", {m.group('jobs')} jobs" if m.group("jobs") else ""
    return f"a state job-growth tax-credit approval ({_mon(m.group('date'))}{jobs}): '{_trim(m.group('desc'), 90)}'"


_INCENT_RE = re.compile(r"^(?P<juris>\w+) County tax incentive agreement (?P<date>\d{4}-\d{2}-\d{2})[^:]*: (?P<desc>.+)$")


def _incentive(item: str) -> str | None:
    m = _INCENT_RE.match(item)
    if not m:
        return None
    fac = re.search(r"facility at ([^;]+)", m.group("desc"))
    where = f" for the facility at {fac.group(1).strip()}" if fac else ""
    return f"a {m.group('juris')} County tax-incentive agreement ({_mon(m.group('date'))}){where}"


# California (added 2026-11-10): SMARTS stormwater enrolments and state incentive awards
_CA_WATER_RE = re.compile(r"^Water permit(?: row)? (?P<id>.+?) \((?P<prog>CA (?:IGP|NEC|CGP))\) processed (?P<date>\d{4}-\d{2}-\d{2}): facility (?P<fac>.+?), permittee ,? ?SIC (?P<sic>\S+) ?(?P<desc>.*?), status (?P<status>[^|(]*)")
_CA_KIND = {"CA IGP": "a new industrial stormwater enrolment with the state", "CA NEC": "a new no-exposure stormwater certification (indoor industrial site)",
            "CA CGP": "a construction stormwater enrolment marked industrial"}
_CA_AWARD_RE = re.compile(r"^California state incentive award (?P<date>\d{4}-\d{2}-\d{2}) \((?P<prog>[^)]+) award\): (?:\[[^\]]*\] )?(?P<desc>.*)")


def _ca_water(item: str) -> str | None:
    m = _CA_WATER_RE.match(item)
    if not m:
        return None
    out = f"{_CA_KIND[m.group('prog')]} ({_mon(m.group('date'))})"
    sic, desc = m.group("sic").strip(), m.group("desc").strip(" ,")
    if sic.lower() != "none" and desc:
        out += f", listing the site as SIC {sic} ({desc.lower()})"
    return out


def _ca_award(item: str) -> str | None:
    m = _CA_AWARD_RE.match(item)
    if not m:
        return None
    d = m.group("desc")
    what = re.search(r"(?:Use of proceeds|Industry): ([^;]+)", d)
    amt = re.search(r"qualified property approved \$([\d.]+)|investment (\$[\d,]+)", d)
    money = ""
    if amt:
        money = (", $%.1fM of equipment approved tax-free" % (float(amt.group(1)) / 1e6)) if amt.group(1) else (", %s committed investment" % amt.group(2))
    return f"a {m.group('prog')} state award ({_mon(m.group('date'))})" + (f" for {what.group(1).strip().lower()}" if what else "") + money


_PARSERS = (_ca_water, _ca_award, _permit, _air, _ucc, _water, _registration, _planning, _cre, _oedit, _incentive)


def describe_item(item: str) -> str:
    """One plain-English phrase for a single top_evidence item."""
    item = item.strip()
    for p in _PARSERS:
        try:
            out = p(item)
        except Exception:  # a parser should never take the page down
            out = None
        if out:
            return out
    return _trim(re.sub(r"\[.*?\]", "", item), 110)


# ----------------------------------------------------------------------------
# stage and confidence wording
# ----------------------------------------------------------------------------
def _lead(stage: str) -> str:
    s = (stage or "").lower()
    small = "permit under $50k" in s
    if s.startswith("buying equipment"):
        return "Repeat equipment buyer at an existing plant" if "repeat" in s else "Financing new production equipment"
    if s.startswith("fit-out"):
        return "Small fit-out work (permit under $50k)" if small else "Fit-out work under way (interior build-out permits)"
    if s.startswith("under construction"):
        return "Minor work at a site under construction (permit under $50k)" if small else "Construction under way at the site"
    if s.startswith("operating and expanding"):
        return "Existing operation with small recent work (permit under $50k)" if small else "Existing operation adding to the site"
    if s.startswith("planned"):
        return "Planned project, not yet built"
    if "registration or press" in s:
        return "Weak signal: only a business registration or a press mention"
    if "blanket or vague lien" in s:
        return "Weak signal: only a blanket lien with no equipment described"
    if "not production-specific" in s:
        return "Weak signal: an equipment lien that is not production-specific"
    return "Signal of unknown stage"


def _caveat(conf: str) -> str:
    c = (conf or "").lower()
    if c == "confirmed":
        return ""
    if "company not attached" in c:
        return "No company is attached yet; this is an address-level signal."
    if "company possible" in c:
        return "The company named is a probable but unconfirmed match for the address."
    if c.startswith("address rows are possible"):
        return "The name comes from a state permit at this street address; the other records are possible matches."
    if c.startswith("possible for some rows"):
        return "Some of the records are possible rather than confirmed matches."
    if "code name" in c:
        return "The project is known only by a code name; the company is not identified."
    if "occupier from" in c:
        return "The occupier is inferred from permit descriptions, not from a named field."
    return ""


def signal_blurb(stage: str, top_evidence: str, match_confidence: str) -> str:
    items = [s.strip() for s in (top_evidence or "").split("||") if s.strip() and not s.strip().startswith("Points:")]
    primary = [i for i in items if not _is_support(i)]
    support = [i for i in items if _is_support(i)]
    ordered = primary + support
    phrases: list[str] = []
    seen: set[str] = set()
    for it in ordered:
        ph = describe_item(it)
        if ph not in seen:
            phrases.append(ph)
            seen.add(ph)
        if len(phrases) >= MAX_ITEMS:
            break
    extra = len(ordered) - len(phrases)

    lead = _lead(stage)
    if phrases:
        body = "; ".join(phrases)
        if extra > 0:
            body += f" (+{extra} more record{'s' if extra > 1 else ''})"
        text = f"{lead}: {body}."
    else:
        text = f"{lead}."
    cav = _caveat(match_confidence)
    return f"{text} {cav}".strip()


if __name__ == "__main__":  # quick manual check: python3 dashboard/blurbs.py path/to/ranked.csv
    import csv
    import sys

    for path in sys.argv[1:]:
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.DictReader(fh)):
                if i >= 12:
                    break
                print(f"#{row['rank']} {row['company_name']}\n   {signal_blurb(row['stage'], row['top_evidence'], row['match_confidence'])}\n")
