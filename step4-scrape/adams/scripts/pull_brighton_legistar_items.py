#!/usr/bin/env python3
"""Pull Brighton Legistar matters and agenda items (Granicus Legistar Web API, client brightonco).

Usage:  python3 pull_brighton_legistar_items.py [--since YYYY-MM-DD] [--fresh]

Pulls Matters with MatterIntroDate >= 2024-01-01, Events with EventDate >= 2024-01-01 and
each event's EventItems (one request per meeting). Matters are the primary rows; agenda
items that carry no matter and are not procedural boilerplate are added as rows of their
own. No attachments are opened. MatterRequester, MatterText2 (a staff email) and
MatterNotes are not requested into the CSV.
--since  refetch matter pages and meetings dated from this day on; earlier cache is reused.
--fresh  drop the raw cache. Raw JSON: raw/brighton_legistar_items/.

Bodies on this Legistar client: City Council and South Brighton General Improvement District
only. Planning Commission and the Brighton Urban Renewal Authority have no body here (checked
with BodyActiveFlag eq 0 and by matter and event body id), so they cannot be pulled from
this source.
"""
import argparse, json, os, re, shutil, sys, urllib.parse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aurora_brighton_common as c

API = "https://webapi.legistar.com/v1/brightonco"
WEB = "https://brightonco.legistar.com"
SOURCE = "Brighton Legistar meeting items"
SLUG = "brighton_legistar_items"
OUT = os.path.join(c.ADAMS_DIR, "scrape_%s.csv" % SLUG)
CACHE = os.path.join(c.RAW_ROOT, SLUG)
START = "2024-01-01"
PAGE = 1000

RULES = [
    ("incentive", re.compile(r"\b(incentives?|business assistance|economic development agreement|tax rebate|"
                             r"fee waiver|sales tax (rebate|reimbursement|refund)|use tax (rebate|reimbursement|refund)|"
                             r"enterprise zone|urban renewal plan|tax increment)\b", re.I)),
    ("rezoning", re.compile(r"\b(rezon\w*|zone change|zoning map amendment|zoning change|zoning of)\b", re.I)),
    ("planned development", re.compile(r"\b(planned (unit )?development|PUD|planned development)\b", re.I)),
    ("use by special review", re.compile(r"\b(use by special review|special use|conditional use)\b", re.I)),
    ("site plan", re.compile(r"\bsite plan\b", re.I)),
    ("plat", re.compile(r"\b(plat|replat|subdivision|minor subdivision)\b", re.I)),
    ("annexation", re.compile(r"\bannex\w*\b", re.I)),
    ("agreement", re.compile(r"\b(development agreement|annexation agreement|improvement agreement|"
                             r"reimbursement agreement|infrastructure agreement|lease agreement|purchase agreement|"
                             r"purchase and sale|disposition and development|cost[- ]sharing agreement|"
                             r"water (resources|rights) (dedication|agreement)|will[- ]serve)\b", re.I)),
]
RESIDENTIAL = re.compile(r"\b(residential|apartments?|single[- ]family|townhomes?|townhouses?|housing|homes|"
                         r"dwelling|multi[- ]?family|duplex|senior living|subdivision filing|to r-?[1-4])\b", re.I)
NONRES = re.compile(r"\b(industrial|commercial|warehouse|manufactur\w*|logistics|business|employment|"
                    r"data center|retail|office|mixed[- ]use|distribution|cold storage|energy|solar|battery|"
                    r"plant|facility|center)\b", re.I)
BOILERPLATE = re.compile(r"^\s*(by\b|consolidated items|.*\bitems?\s*$|approval of regular agenda|roll call|pledge|call to order|approval of( the)? agenda|agenda approval|adjourn\w*|"
                         r"public (invited|comment)|consent agenda|reports?( by| from)?|executive session|ceremonies|"
                         r"approval of minutes|mayor|council|city manager|city attorney|study session|presentations?|"
                         r"business|general business|public hearings?|ordinances? for (initial|final)|resolutions?|"
                         r"informational|staff reports?|closing remarks|upcoming|announcements|other business|"
                         r"consent|motion|recess|work session|item[s]? for)\b", re.I)
SUFFIX = re.compile(r"^(LLC|L\.L\.C\.?|INC\.?|INCORPORATED|CORP\.?|CORPORATION|COMPANY|CO\.|LTD\.?|LIMITED|LP|L\.P\.|LLP|"
                    r"PLC|GMBH|LLLP|N\.A\.|P\.C\.)[,.;)]*$", re.I)
STOP = {"WITH", "BETWEEN", "FOR", "TO", "OF", "BY", "FROM", "THE", "A", "AN", "APPROVING", "AUTHORIZING",
        "APPROVE", "AUTHORIZE", "INTO", "ON", "IN", "AT", "AS", "KNOWN", "ENTITLED", "RESOLUTION", "ORDINANCE",
        "AGREEMENT", "CONTRACT", "AMENDMENT", "AMENDING", "ACCEPTING", "AMONG", "GRANTING", "APPLICANT", "OWNER",
        "DEVELOPER", "COLORADO,", "BRIGHTON,", "BRIGHTON", "COLORADO", "CITY", "COUNCIL", "SUBMITTED", "FILED",
        "REQUEST", "REQUESTED", "-", ";", "APPLICATION", "BE", "IS", "ARE", "WAS", "WERE", "ALSO", "HEREIN", "SHALL"}
PERSON_ITEM = re.compile(r"\b(appoint\w*|re-?appoint\w*|recogni\w*|honor\w*|proclaim\w*|in memory|retire\w*|"
                         r"condolence\w*|congratulat\w*|employee of|oath|swearing|elect\w* |mayor pro tem|"
                         r"resignation|farewell|welcom\w*|citizen of|volunteer of|birthday|anniversary|"
                         r"scholarship|student|eagle scout|award\w*)\b", re.I)
CONTRACT = re.compile(r"\b(contract|construction|professional services|services agreement|purchase|bid|"
                      r"change order|task order|design|engineering|consult\w*)\b", re.I)


def scrub_person_items(title):
    """Appointments, proclamations and recognitions name individuals; cut the title at the
    keyword so no personal name is written."""
    m = PERSON_ITEM.search(title)
    if m:
        return title[:m.end()].rstrip() + " [name withheld]"
    return title

EXTRA_COLS = ["matter_id", "body", "matter_status", "intro_date", "agenda_date", "passed_date", "enactment_number",
              "event_dates", "last_action", "last_action_date", "event_id", "residential", "parser_version"]


def fetch_pages(path, filt, cache_tag):
    out, skip, page = [], 0, 0
    while True:
        p = os.path.join(CACHE, "%s_p%04d.json" % (cache_tag, page))
        w = c.cached(p, lambda: http(path, {"$filter": filt, "$top": PAGE, "$skip": skip}))
        got = w["response"]
        for g in got:
            g["_fetched_at"] = w["fetched_at"]
        out.extend(got)
        print("  %s page %d: %d" % (cache_tag, page, len(got)))
        if len(got) < PAGE:
            return out
        skip += PAGE
        page += 1


def http(path, params=None):
    return c.http_json(API + path, params)


def company_from_title(title):
    toks = title.split()
    for i, t in enumerate(toks):
        if SUFFIX.match(t):
            j = i
            while j > 0 and toks[j - 1].strip(",").upper() not in STOP and not toks[j - 1].endswith(";") and i - j < 10:
                j -= 1
            if j == i:
                continue
            name = " ".join(toks[j:i + 1]).strip(" ,.;")
            name = re.sub(r"^(D/B/A|DBA)\s+", "", name, flags=re.I)
            if re.search(r"\b(CITY|BRIGHTON|COUNTY|DISTRICT|AUTHORITY|BOARD)\b.*\bAND\b", name, re.I):
                name = name[name.upper().rfind(" AND ") + 5:]
            name = re.sub(r"^AND\s+", "", name, flags=re.I)
            if 2 <= len(name.split()) <= 11 and not c.looks_like_person(name):
                return name
    return ""


def role_for(title, rule, company):
    if not company:
        return "unknown"
    if rule == "incentive":
        return "grantee"
    if rule in ("rezoning", "planned development", "use by special review", "site plan", "plat", "annexation"):
        return "applicant"
    if CONTRACT.search(title):
        return "contractor"
    return "unknown"


def flag_title(title, mtype):
    if mtype in ("Proclamation", "Minutes"):
        return "N", "", ""
    res = "Y" if RESIDENTIAL.search(title) and not NONRES.search(title) else ""
    for rule, rx in RULES:
        if rx.search(title):
            return ("N", "", res) if res else ("Y", rule, res)
    return "N", "", res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    if a.fresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    os.makedirs(CACHE, exist_ok=True)
    if a.since:
        for fn in os.listdir(CACHE):
            if fn.startswith("matters_") or fn.startswith("events_"):
                os.remove(os.path.join(CACHE, fn))

    matters = fetch_pages("/Matters", "MatterIntroDate ge datetime'%s'" % START, "matters")
    events = fetch_pages("/Events", "EventDate ge datetime'%s'" % START, "events")
    print("matters %d, events %d" % (len(matters), len(events)))

    items_by_matter, unlinked = {}, []
    for ev in sorted(events, key=lambda e: e["EventDate"]):
        eid = ev["EventId"]
        p = os.path.join(CACHE, "eventitems_%d.json" % eid)
        if a.since and ev["EventDate"][:10] >= a.since and os.path.exists(p):
            os.remove(p)
        w = c.cached(p, lambda: http("/Events/%d/EventItems" % eid))
        for it in w["response"]:
            it["_event"] = ev
            it["_fetched_at"] = w["fetched_at"]
            if it.get("EventItemMatterId"):
                items_by_matter.setdefault(it["EventItemMatterId"], []).append(it)
            else:
                unlinked.append(it)
    print("event items linked to matters: %d, unlinked: %d" % (sum(len(v) for v in items_by_matter.values()), len(unlinked)))

    rows, counts = [], Counter()
    for m in matters:
        title = c.clean(m.get("MatterTitle"))
        mtype = c.clean(m.get("MatterTypeName"))
        if PERSON_ITEM.search(title):
            title = scrub_person_items(title)
            counts["titles cut at a person-item keyword"] += 1
        flag, rule, res = flag_title(title, mtype)
        its = sorted(items_by_matter.get(m["MatterId"], []), key=lambda i: i["_event"]["EventDate"])
        ev_dates = sorted({i["_event"]["EventDate"][:10] for i in its})
        last = its[-1] if its else None
        company = company_from_title(title)
        url = WEB + "/LegislationDetail.aspx?" + urllib.parse.urlencode({"ID": m["MatterId"], "GUID": m["MatterGuid"]})
        rows.append({
            "source": SOURCE, "source_level": "County (Adams)", "record_id": c.clean(m.get("MatterFile")),
            "record_date": (m.get("MatterIntroDate") or "")[:10], "date_type": "introduced",
            "record_type": mtype, "company_name": company, "company_role": role_for(title, rule, company),
            "site_address": "", "city": "Brighton", "county": "Adams", "zip": "",
            "description": c.clean(title, 500), "flag": flag, "flag_rule": rule,
            "source_url": url, "retrieved_at": m["_fetched_at"],
            "matter_id": str(m["MatterId"]), "body": c.clean(m.get("MatterBodyName")),
            "matter_status": c.clean(m.get("MatterStatusName")), "intro_date": (m.get("MatterIntroDate") or "")[:10],
            "agenda_date": (m.get("MatterAgendaDate") or "")[:10], "passed_date": (m.get("MatterPassedDate") or "")[:10],
            "enactment_number": c.clean(m.get("MatterEnactmentNumber")), "event_dates": "; ".join(ev_dates),
            "last_action": c.clean(last.get("EventItemActionName") or last.get("EventItemPassedFlagName")) if last else "",
            "last_action_date": last["_event"]["EventDate"][:10] if last else "",
            "event_id": str(last["_event"]["EventId"]) if last else "", "residential": res,
            "parser_version": c.PARSER_VERSION,
        })
        counts["matters"] += 1
    for it in unlinked:
        title = c.clean(it.get("EventItemTitle"))
        if not title or BOILERPLATE.match(title) or len(title) < 12:
            counts["unlinked agenda items left out as boilerplate"] += 1
            continue
        ev = it["_event"]
        if PERSON_ITEM.search(title):
            title = scrub_person_items(title)
            counts["titles cut at a person-item keyword"] += 1
        flag, rule, res = flag_title(title, "")
        company = company_from_title(title)
        url = WEB + "/MeetingDetail.aspx?" + urllib.parse.urlencode({"ID": ev["EventId"], "GUID": ev["EventGuid"]})
        rows.append({
            "source": SOURCE, "source_level": "County (Adams)", "record_id": "EI-%d" % it["EventItemId"],
            "record_date": ev["EventDate"][:10], "date_type": "agenda", "record_type": "agenda item",
            "company_name": company, "company_role": role_for(title, rule, company),
            "site_address": "", "city": "Brighton", "county": "Adams", "zip": "",
            "description": c.clean(title, 500), "flag": flag, "flag_rule": rule,
            "source_url": url, "retrieved_at": it["_fetched_at"],
            "matter_id": "", "body": c.clean(ev.get("EventBodyName")), "matter_status": "",
            "intro_date": "", "agenda_date": ev["EventDate"][:10], "passed_date": "", "enactment_number": "",
            "event_dates": ev["EventDate"][:10],
            "last_action": c.clean(it.get("EventItemActionName") or it.get("EventItemPassedFlagName")),
            "last_action_date": ev["EventDate"][:10], "event_id": str(ev["EventId"]), "residential": res,
            "parser_version": c.PARSER_VERSION,
        })
        counts["unlinked agenda items kept"] += 1
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    c.write_csv(OUT, c.COMMON_COLS + EXTRA_COLS, rows)
    s = c.summarize(rows)
    s["counts"] = dict(counts)
    s["bodies"] = dict(Counter(r["body"] for r in rows))
    s["types"] = dict(Counter(r["record_type"] for r in rows))
    s["residential_only_N"] = sum(1 for r in rows if r["residential"] == "Y")
    s["events"] = len(events)
    with open(os.path.join(CACHE, "summary.json"), "w") as fh:
        json.dump(s, fh, indent=1)
    print(json.dumps(s, indent=1))
    print("wrote", OUT, len(rows), "rows")


if __name__ == "__main__":
    main()
