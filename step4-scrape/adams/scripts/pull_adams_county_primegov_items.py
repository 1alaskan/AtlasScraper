#!/usr/bin/env python3
"""Pull Adams County PrimeGov agenda items (Board of County Commissioners public hearings and study
sessions, Planning Commission) into the step 4 shared format.

Usage:  python3 pull_adams_county_primegov_items.py [--since YYYY-MM-DD] [--fresh]

--since  meeting-date cursor (default 2024-01-01).
--fresh  ignore today's raw cache and refetch.

ROBOTS GATE. On 2026-10-31 https://adamscounty.primegov.com/robots.txt (last-modified
2026-10-08) read "User-agent: * / Disallow: /". The brief says to respect robots.txt, so this
script checks the file first and exits without fetching anything when the API and portal paths
are disallowed; it then writes a header-only CSV so the file set stays complete. The item parser
below has therefore NOT been exercised against a live agenda; verify it on the first run that the
robots file permits (check raw/adams_county_primegov_items/<day>/agenda_<id>.html against the
items it yields).

Route when permitted: JSON index /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY (one call a
year), then the "HTML Agenda" document of each in-scope meeting
(/Portal/Meeting?compiledMeetingDocumentFileId=<id>). Attachments and packets are never opened.
"""
import argparse, html, json, os, re, shutil, sys, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_common as cc

HOST = "https://adamscounty.primegov.com"
SLUG = "adams_county_primegov_items"
SOURCE = "Adams County PrimeGov agenda items"
OUT = os.path.join(cc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

EXTRA_COLS = ["meeting_title", "meeting_id", "meeting_datetime", "agenda_section", "item_number",
              "case_numbers", "parser_version"]

MEETING_TITLES = re.compile(r"board of county commissioners|planning commission", re.I)
MEETING_EXCLUDE = re.compile(r"liquor|marijuana|board of adjustment|equalization|health|housing authority", re.I)

# Meeting-item rule from the brief: incentive, agreement, rezoning, planned development, use by
# special review, site plan or plat for a non-residential project. The rule names the word.
RULE_WORDS = [
    ("incentive", re.compile(r"\bincentive", re.I)),
    ("agreement", re.compile(r"\b(development|incentive|economic development|intergovernmental|improvement|"
                             r"subdivision improvement|annexation|lease|tax|rebate|performance) agreement\b|\bIGA\b", re.I)),
    ("rezoning", re.compile(r"\brezon|\bzone change|\bRCU\d{4}", re.I)),
    ("planned development", re.compile(r"\bplanned (unit )?development\b|\bPUD\b", re.I)),
    ("use by special review", re.compile(r"\buse by special review\b|\bconditional use\b|\bspecial use\b", re.I)),
    ("site plan", re.compile(r"\bsite (development )?plan\b|\bdevelopment plan\b|\bPLN\d{4}|\bPRC\d{4}", re.I)),
    ("plat", re.compile(r"\bplat\b|\bsubdivision\b|\bPLT\d{4}", re.I)),
]
RESIDENTIAL = re.compile(r"\b(single[- ]family|residential|townhome|duplex|apartments?|housing|homes?|"
                         r"subdivision exemption|dwelling|ADU|mobile home)\b", re.I)
CASE_RE = re.compile(r"\b(PRE|RCU|PRC|PLN|PLT|PUD|VSP|TVM|EXG|VAC|PRA)\d{4}-\d{5}\b")
# "... agreement with <Company>" / "between Adams County and <Company>" / "for <Company>"
WITH_RE = re.compile(r"\b(?:with|between adams county and|and|for|to|by)\s+((?:[A-Z][\w&'\.\-]*|of|and|&|de|the)(?:\s+(?:[A-Z][\w&'\.\-]*|of|and|&|de|the)){0,6})")
ENTITY_SUFFIX = re.compile(r"\b(LLC|L\.L\.C\.?|Inc\.?|Corp\.?|Corporation|Co\.?|Company|Ltd\.?|LP|LLP|LLLP|"
                           r"Partners(hip)?|Holdings|Group|Trust|District|Authority|Foundation|Association|"
                           r"Industries|Foods|Mills|Energy|Logistics|Enterprises|Properties|Development|"
                           r"Investments|Ventures|Capital|Realty|Americas?|International|USA)\b")


def robots_allows(paths):
    """Minimal robots.txt reader: rules for our UA group first, else the * group. Returns
    (allowed, text)."""
    try:
        txt = cc.http(HOST + "/robots.txt", timeout=60)
    except SystemExit:
        return True, "(robots.txt could not be read; treated as no rules)"
    groups, cur = {}, None
    for line in txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = [p.strip() for p in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            cur = v.lower()
            groups.setdefault(cur, [])
        elif k in ("allow", "disallow") and cur is not None:
            groups[cur].append((k, v))
    rules = groups.get(cc.UA.lower()) or groups.get(cc.UA.split("/")[0].lower()) or groups.get("*") or []
    for path in paths:
        best = None
        for k, v in rules:
            if v and path.startswith(v) and (best is None or len(v) > len(best[1])):
                best = (k, v)
        if best and best[0] == "disallow":
            return False, txt
    return True, txt


def strip_tags(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return s


def parse_items(agenda_html):
    """First-cut item parser (untested, see the module docstring): take the agenda text line by
    line, track the current section heading (an all-caps line), and treat a line that starts with
    an item number or letter followed by text of 15+ characters as an item title."""
    items, section = [], ""
    for raw in strip_tags(agenda_html).splitlines():
        line = cc.clean(raw)
        if not line:
            continue
        if len(line) < 80 and line.upper() == line and re.search(r"[A-Z]{4,}", line) and not re.match(r"^\d", line):
            section = line
            continue
        m = re.match(r"^(\d{1,2}(?:\.\d+)?[.)]?|[A-Z][.)]|[ivx]+[.)])\s+(.{15,})$", line)
        if m:
            items.append({"number": m.group(1).rstrip(".)"), "title": m.group(2), "section": section})
    return items


def company_from_title(title):
    for m in WITH_RE.finditer(title):
        cand = cc.clean(m.group(1)).strip(" ,.;:")
        cand = re.sub(r"\s+(?:of|and|&|de|the)$", "", cand)
        if ENTITY_SUFFIX.search(cand) and not cc.looks_like_individual(cand):
            return cand[:120]
    m = re.search(r"\bdba\s+([A-Z][^,;:]{2,60})", title)
    if m:
        return cc.clean(m.group(1))[:120]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = cc.now_iso()[:10].replace("-", "")
    cache = os.path.join(cc.RAW_ROOT, SLUG, day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
    os.makedirs(cache, exist_ok=True)

    allowed, robots_txt = robots_allows(["/api/v2/PublicPortal/ListArchivedMeetings", "/Portal/Meeting"])
    with open(os.path.join(cache, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_txt)
    if not allowed:
        cc.write_csv(OUT, cc.COMMON_COLS + EXTRA_COLS, [])
        print("robots.txt disallows the PrimeGov API and portal paths for this agent; nothing fetched.")
        print("header-only CSV written:", OUT)
        return

    years = range(int(a.since[:4]), datetime.now(timezone.utc).year + 1)
    meetings = []
    for y in years:
        path = os.path.join(cache, "meetings_%d.json" % y)
        if os.path.exists(path):
            data = json.load(open(path, encoding="utf-8"))
        else:
            data = cc.http_json(HOST + "/api/v2/PublicPortal/ListArchivedMeetings", {"year": y})
            json.dump(data, open(path, "w", encoding="utf-8"))
        meetings.extend(data)
    rows, rules = [], Counter()
    for m in meetings:
        title = cc.clean(m.get("title"))
        when = cc.clean(m.get("dateTime"))[:10]
        if not when or when < a.since or not MEETING_TITLES.search(title) or MEETING_EXCLUDE.search(title):
            continue
        doc = next((d for d in m.get("documentList", []) if d.get("templateName") == "HTML Agenda"), None)
        if not doc:
            continue
        path = os.path.join(cache, "agenda_%s.html" % doc["id"])
        if os.path.exists(path):
            body = open(path, encoding="utf-8").read()
        else:
            body = cc.http(HOST + "/Portal/Meeting", {"compiledMeetingDocumentFileId": doc["id"]})
            open(path, "w", encoding="utf-8").write(body)
        fetched = cc.now_iso()
        for it in parse_items(body):
            t = it["title"]
            flag, rule = "N", ""
            if not RESIDENTIAL.search(t):
                for word, rx in RULE_WORDS:
                    if rx.search(t):
                        flag, rule = "Y", word
                        break
            rules[rule] += 1
            name = company_from_title(t)
            rows.append({
                "source": SOURCE, "source_level": cc.SOURCE_LEVEL,
                "record_id": "%s/%s" % (m.get("id"), it["number"]), "record_date": when, "date_type": "agenda",
                "record_type": "agenda item", "company_name": name, "company_role": "applicant" if name else "unknown",
                "site_address": "", "city": "Unincorporated Adams County", "county": cc.COUNTY, "zip": "",
                "description": cc.clean(t, 500), "flag": flag, "flag_rule": rule,
                "source_url": HOST + "/Portal/Meeting?" + urllib.parse.urlencode({"compiledMeetingDocumentFileId": doc["id"]}),
                "retrieved_at": fetched, "meeting_title": title, "meeting_id": str(m.get("id")),
                "meeting_datetime": cc.clean(m.get("dateTime")), "agenda_section": it["section"],
                "item_number": it["number"], "case_numbers": "; ".join(sorted(set(CASE_RE.findall(t)))),
                "parser_version": cc.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written:", len(rows), "flag rules:", rules.most_common())


if __name__ == "__main__":
    main()
