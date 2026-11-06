#!/usr/bin/env python3
"""Pull the City of Fort Lupton planning cases into the step 4 shared format, merging two
public views of the same case list on the case number:

  1. the Planning_AGOL feature service on ArcGIS Online (org 7fqvVMRB6DcB5wXC): layer 1
     (polygons, the attributes and a centroid) and layer 0 (points, the same attributes with a
     point location);
  2. the Current Development Projects page on the city website (CivicPlus), four tabs
     (Under Review, Approved, Denied, Withdrawn) with project name, case number(s), hearing
     text and a DocumentCenter folder link.

Usage:  python3 pull_fort_lupton_planning_projects.py [--since YYYY-MM-DD] [--fresh]

Both views are history-less snapshots, so every run reads the whole layer and the whole
page and APPENDS rows not seen before to the CSV. Rows already held keep their record_date,
company_name, retrieved_at and first_seen_at; the status columns (status, approved,
page_section, page_hearing_text, pc_date, cc_date, last_seen_at, in_source_last_run) are
refreshed. Nothing is deleted.

One output row per layer feature (a case number can carry two features, for example Filing 1
and Filing 2 under FPL25-002) plus one row per page case number that the layer does not hold.
record_date is the earliest of Ref_Response_Date, PC_Date and CC_Date on the layer; a
page-only row takes the earliest hearing date printed on the page, else the retrieval date
(date_type snapshot).

--since  keep only new rows whose record_date is on or after this date (default 2023-01-01,
         the QA floor; the layer's oldest referral date is 2023-10-04).
--fresh  ignore today's raw snapshot and refetch.
Raw pages are cached under ../raw/fort_lupton_planning_projects/snapshot_<UTC day>/.

The DocumentCenter folder contents (submittal PDFs) are NOT fetched: the folder index page
is a React shell that loads its file list from /Admin/DocumentCenter/..., and the site's
robots.txt disallows /admin for every user agent.
"""
import argparse, html, os, re, shutil, sys
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_common as cc

SERVICE = "https://services2.arcgis.com/7fqvVMRB6DcB5wXC/arcgis/rest/services/Planning_AGOL/FeatureServer"
POLY = SERVICE + "/1"
POINT = SERVICE + "/0"
PAGE_URL = "https://www.fortluptonco.gov/463/Current-Development-Projects"
PAGE_PAUSE = 10.0        # robots.txt Crawl-delay for the city website
SLUG = "fort_lupton_planning_projects"
SOURCE = "Fort Lupton planning projects"
OUT = os.path.join(cc.WELD_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "Project_Num", "Plan_Num", "Plan_Code", "Plan_Type", "Project_Name", "On_Website",
          "PC_Date", "CC_Date", "Year", "Approved", "Applicant", "Web_Link", "Doc_Link",
          "Ref_Response_Date", "Comments", "Status"]

EXTRA_COLS = ["industrial_use", "industrial_word", "industrial_adjacent", "industrial_adjacent_word",
              "plan_type_name", "project_name", "applicant", "status", "approved",
              "ref_response_date", "pc_date", "cc_date", "year", "comments", "doc_folder", "web_link",
              "page_section", "page_hearing_text", "latitude", "longitude", "source_detail",
              "object_id", "first_seen_at", "last_seen_at", "in_source_last_run", "parser_version"]

PLAN_TYPES = {"ADM": "Administrative site plan", "SPR": "Site plan review", "SUP": "Special use permit",
              "COZ": "Change of zone", "ANX": "Annexation", "LLA": "Lot line adjustment",
              "PPL": "Preliminary plat", "FPL": "Final plat", "CPL": "Concept plan",
              "CPA": "Comprehensive plan amendment", "APC": "Plat correction",
              "ALC": "Administrative lot consolidation", "VAR": "Variance", "LUP": "Land use permit",
              "MPL": "Minor plat", "PUD": "Planned unit development", "SPL": "Sketch plan"}
CASE_RE = re.compile(r"\b([A-Z]{3})(\d{2}|\d{4})-(\d{3,4})\b")
ADDRESS_RE = re.compile(
    r"\b(\d{2,6}\s+(?:[NSEW]\.?\s+)?[A-Za-z0-9][A-Za-z0-9' .]*?\s+"
    r"(?:St|Street|Ave|Avenue|Cir|Circle|Dr|Drive|Rd|Road|Blvd|Boulevard|Ct|Court|Ln|Lane|Way|Pl|Place|Pkwy|Parkway|Hwy|Highway))\b\.?")
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                      "august", "september", "october", "november", "december"], 1)}


def case_key(code, yy, seq):
    return "%s%s-%s" % (code, yy, seq)


def cases_in(text):
    return [case_key(*m) for m in CASE_RE.findall(text or "")]


def parse_hearing_dates(text):
    """'Planning Commission: 08/28/25 - 6:00 PM City Council: 09/16/25' -> [(date, label)]."""
    out = []
    t = cc.clean(text)
    labels = [(m.start(), m.group(1)) for m in re.finditer(r"(Planning Commission|City Council|Board of Adjustment)", t, re.I)]
    for m in re.finditer(r"(\d{1,2})/(\d{1,2})/(\d{2,4})|([A-Z][a-z]+) (\d{1,2}), (\d{4})", t):
        if m.group(1):
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
        else:
            mo, d, y = MONTHS.get(m.group(4).lower()), int(m.group(5)), int(m.group(6))
            if not mo:
                continue
        label = "hearing"
        for pos, lab in labels:
            if pos < m.start():
                label = lab.lower()
        try:
            out.append((datetime(y, mo, d).strftime("%Y-%m-%d"), label))
        except ValueError:
            continue
    return out


def parse_page(body):
    """The four tab tables -> list of dicts (section, name, cases, hearing, link)."""
    rows = []
    for tm in re.finditer(r"<table.*?</table>", body, re.S | re.I):
        pre = re.sub(r"<[^>]+>", " ", body[max(0, tm.start() - 800):tm.start()])
        pre = cc.clean(html.unescape(pre))
        sm = re.search(r"(Under Review|Approved|Denied|Withdrawn|On Hold)\s*$", pre, re.I)
        section = sm.group(1).title() if sm else ""
        for tr in re.findall(r"<tr.*?</tr>", tm.group(0), re.S | re.I):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
            if len(cells) < 3:
                continue
            txt = [cc.clean(html.unescape(re.sub(r"<[^>]+>", " ", c))) for c in cells]
            if txt[0].lower().startswith("project name"):
                continue
            link = re.search(r'href="([^"]*DocumentCenter[^"]*)"', tr)
            url = link.group(1) if link else ""
            if url.startswith("/"):
                url = "https://www.fortluptonco.gov" + url
            rows.append({"section": section, "name": txt[0], "cases": cases_in(txt[1]), "case_text": txt[1],
                         "hearing": txt[2], "link": url})
    if not rows:
        raise SystemExit("Current Development Projects page: no table rows parsed (layout changed?)")
    return rows


def address_from(*texts):
    for t in texts:
        m = ADDRESS_RE.search(cc.clean(t))
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip(" .")
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    cache = os.path.join(cc.RAW_ROOT, SLUG, "snapshot_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    cc.require_fields(POLY, FIELDS)
    cc.require_fields(POINT, FIELDS)
    n_poly = cc.source_count(POLY)
    n_point = cc.source_count(POINT)
    polys = cc.fetch_all(POLY, "1=1", FIELDS, os.path.join(cache, "polygons"), page_size=2000,
                         extra={"returnCentroid": "true"}, label="polygons")
    points = cc.fetch_all(POINT, "1=1", FIELDS, os.path.join(cache, "points"), page_size=2000,
                          geometry=True, label="points")
    if len(polys) != n_poly or len(points) != n_point:
        raise SystemExit("ROW COUNT MISMATCH: polygons %d/%d, points %d/%d" % (len(polys), n_poly, len(points), n_point))
    print("source counts: polygons %d, points %d" % (n_poly, n_point))
    page_body, page_fetched = cc.fetch_text(PAGE_URL, os.path.join(cache, "current_development_projects.html"),
                                            pause=PAGE_PAUSE)
    page_rows = parse_page(page_body)
    print("page rows parsed: %d (%s)" % (len(page_rows), dict(Counter(r["section"] for r in page_rows))))

    def feat_key(at):
        rid = cc.clean(at.get("Plan_Num"))
        if not rid:
            found = cases_in(at.get("Doc_Link")) or cases_in(at.get("Project_Num"))
            rid = found[0] if found else ""
        return rid, (rid + "|" + cc.clean(at.get("Project_Name")).lower())

    # point location by key
    pt_by_key = {}
    for f in points:
        rid, key = feat_key(f["attributes"])
        g = f.get("geometry") or {}
        x, y = g.get("x"), g.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and -106 < x < -104 and 39 < y < 41:
            pt_by_key[key] = (x, y)

    page_by_case = {}
    for pr in page_rows:
        for c in pr["cases"]:
            page_by_case.setdefault(c, pr)

    existing, _ = cc.read_csv(OUT)
    by_key = {}
    for r in existing:
        # layer rows key on case number plus name (a case can carry two features); page-only rows
        # key on the case number alone, because staff edit the page's project names in place
        if r["source_detail"] == "page":
            by_key[r["record_id"] + "|page"] = r
        else:
            by_key[r["record_id"] + "|" + r["project_name"].lower()] = r
    layer_cases = set()
    for f in polys:
        layer_cases.add(feat_key(f["attributes"])[0])
        layer_cases.update(cases_in(f["attributes"].get("Project_Num")))     # LUP2022-0022 aliases
    cols = cc.COMMON_COLS + EXTRA_COLS
    new_rows, updated, out_of_window, applicants_blanked, names_blanked, upgraded = [], 0, 0, 0, 0, 0
    seen = set()

    individuals = []
    for f in polys:
        comp, dropped = cc.company_from_applicant(f["attributes"].get("Applicant"))
        if dropped and not comp:
            individuals.append(f["attributes"].get("Applicant"))
    surnames = cc.surname_tokens(individuals)

    def build_row(rid, raw_name, code, rdate, dtype, applicant_raw, comments, doc_link, web_link, status,
                  approved, ref, pc, ccd, year, pr, latlon, source_detail, oid, fetched):
        nonlocal applicants_blanked, names_blanked
        applicant, dropped = cc.company_from_applicant(applicant_raw)
        if dropped:
            applicants_blanked += 1
        name, why = cc.scrub_project_name(raw_name, surnames)
        if why:
            names_blanked += 1
        if applicant:
            company, role = applicant, "applicant"
        else:
            company = cc.company_from_project_name(name)
            role = "project" if company else "unknown"
        doc_folder = cc.clean((doc_link or "").replace("/", "\\").split("\\")[-1])
        comments_c = cc.clean(comments, 300)
        desc = name
        if comments_c and comments_c.lower() not in ("staff review", "staff review."):
            desc = (desc + ". " + comments_c) if desc else comments_c
        text = " ".join([raw_name or "", comments or "", doc_folder, PLAN_TYPES.get(code, "")])
        ind, ind_word, adj, adj_word = cc.industrial_flags(text)
        row = {
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": rid,
            "record_date": rdate, "date_type": dtype, "record_type": code,
            "company_name": company, "company_role": role,
            "site_address": address_from(raw_name, doc_folder), "city": "Fort Lupton", "county": cc.COUNTY, "zip": "",
            "description": cc.clean(desc, 500), "flag": "Y", "flag_rule": cc.FLAG_RULE,
            "source_url": cc.layer_query_url(POLY, "Plan_Num='%s'" % rid) if "layer" in source_detail else PAGE_URL,
            "retrieved_at": fetched,
            "industrial_use": ind, "industrial_word": ind_word,
            "industrial_adjacent": adj, "industrial_adjacent_word": adj_word,
            "plan_type_name": PLAN_TYPES.get(code, ""), "project_name": name, "applicant": applicant,
            "ref_response_date": ref, "year": year, "comments": comments_c, "doc_folder": doc_folder,
            "web_link": web_link or (pr["link"] if pr else ""),
            "latitude": "%.6f" % latlon[1] if latlon else "", "longitude": "%.6f" % latlon[0] if latlon else "",
            "source_detail": source_detail, "object_id": oid,
            "first_seen_at": fetched, "parser_version": cc.PARSER_VERSION}
        row.update(status_cols(status, approved, pc, ccd, pr, fetched))
        return row

    def status_cols(status, approved, pc, ccd, pr, fetched):
        return {"status": status or (pr["section"] if pr else ""), "approved": approved,
                "pc_date": pc, "cc_date": ccd,
                "page_section": pr["section"] if pr else "", "page_hearing_text": cc.clean(pr["hearing"], 200) if pr else "",
                "last_seen_at": fetched, "in_source_last_run": "Y"}

    # 1. layer features
    for f in polys:
        at = f["attributes"]
        rid, key = feat_key(at)
        if not rid:
            raise SystemExit("no case number on OBJECTID %s" % at.get("OBJECTID"))
        seen.add(key)
        fetched = f["_fetched_at"]
        pr = page_by_case.get(rid)
        ref, pc, ccd = cc.ms_to_date(at.get("Ref_Response_Date")), cc.ms_to_date(at.get("PC_Date")), cc.ms_to_date(at.get("CC_Date"))
        status, approved = cc.clean(at.get("Status")), cc.clean(at.get("Approved"))
        if key in by_key:
            by_key[key].update(status_cols(status, approved, pc, ccd, pr, fetched))
            updated += 1
            continue
        dated = [(d, t) for d, t in ((ref, "referral"), (pc, "planning commission"), (ccd, "city council")) if d]
        if dated:
            rdate, dtype = min(dated)
        else:
            rdate, dtype = fetched[:10], "snapshot"
        if rdate < a.since:
            out_of_window += 1
            continue
        code = cc.clean(at.get("Plan_Code")) or rid[:3]
        latlon = pt_by_key.get(key)
        if not latlon and f.get("centroid"):
            latlon = (f["centroid"].get("x"), f["centroid"].get("y"))
        row = build_row(rid, at.get("Project_Name"), code, rdate, dtype, at.get("Applicant"),
                        at.get("Comments"), at.get("Doc_Link"), cc.clean(at.get("Web_Link")), status, approved,
                        ref, pc, ccd, cc.clean(at.get("Year")), pr, latlon,
                        "both" if pr else "layer", str(at.get("OBJECTID")), fetched)
        page_row = by_key.pop(rid + "|page", None)
        if page_row is not None:
            # a case first seen on the page now has a layer feature: upgrade that row in place
            row["first_seen_at"] = page_row["first_seen_at"]
            existing.remove(page_row)
            upgraded += 1
        new_rows.append(row)

    # 2. page-only cases
    for pr in page_rows:
        for rid in pr["cases"]:
            if rid in layer_cases:
                continue
            key = rid + "|page"
            if key in seen:
                continue                                    # the same case number on two page rows
            seen.add(key)
            if key in by_key:
                r = by_key[key]
                r.update(status_cols("", "", "", "", pr, page_fetched))
                r["project_name"] = cc.scrub_project_name(pr["name"], surnames)[0]
                updated += 1
                continue
            hd = parse_hearing_dates(pr["hearing"])
            if hd:
                rdate, dtype = min(hd)
            else:
                rdate, dtype = page_fetched[:10], "snapshot"
            if rdate < a.since:
                out_of_window += 1
                continue
            new_rows.append(build_row(rid, pr["name"], rid[:3], rdate, dtype, "", "", "", pr["link"], "", "",
                                      "", "", "", "", pr, None, "page", "", page_fetched))

    for key, r in by_key.items():
        if key not in seen:
            r["in_source_last_run"] = "N"
    rows = existing + new_rows
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cols, rows)
    print("rows in CSV: %d (new this run %d, already held and refreshed %d, page rows upgraded to layer rows %d, "
          "no longer in source %d, before --since %d)"
          % (len(rows), len(new_rows) - upgraded, updated, upgraded,
             sum(1 for r in by_key.values() if r["in_source_last_run"] == "N"), out_of_window))
    print("source_detail of new rows:", dict(Counter(r["source_detail"] for r in new_rows)))
    print("date types of new rows:", dict(Counter(r["date_type"] for r in new_rows)))
    print("applicant strings with a person part dropped: %d; project names blanked: %d" % (applicants_blanked, names_blanked))
    print("industrial_use Y: %d; industrial_adjacent Y: %d" % (sum(1 for r in rows if r["industrial_use"] == "Y"),
                                                              sum(1 for r in rows if r["industrial_adjacent"] == "Y")))
    print("flag rules:", Counter(r["flag_rule"] for r in rows if r["flag"] == "Y"))
    print("types:", Counter(r["record_type"] for r in rows).most_common())


if __name__ == "__main__":
    main()
