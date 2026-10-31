#!/usr/bin/env python3
"""Pull the Thornton Development Projects layer (CityView planning cases mirrored to ArcGIS
Enterprise) into the step 4 format, as an append-only archive.

Usage:  python3 pull_thornton_development_projects.py [--since YYYY-MM-DD] [--fresh]

The layer is small (about 300 rows, one request) and rows leave the public map when a case
closes (OnMap flips to N and OffMapDate is set). They have been retained so far but there is
no guarantee, so every run snapshots the whole layer and APPENDS rows not seen before to the
CSV (keyed on the layer GlobalID) without deleting old ones. Rows already in the CSV keep
their original record_date, retrieved_at and first_seen_at; only the status columns
(on_map, off_map_date, phase, status_alt, last_edited, last_seen_at, in_layer_last_run) are
refreshed. A row that has disappeared from the layer stays in the CSV with
in_layer_last_run = N.

Scope: every row whose record date (OnMapDate, else created_date, else last_edited_date) is
on or after --since (default 2024-01-01), including rows with OnMap = N.
Every row is flagged Y ("all planning and development cases"); industrial_use = Y when the
name, scope text, planning-area name or development type says industrial, warehouse,
manufacturing, distribution, logistics, flex or data center.

--fresh  ignore today's raw snapshot and refetch.
Raw snapshots are cached under ../raw/thornton_development_projects/snapshot_<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thornton_common as tc

LAYER = tc.HOST + "/DevelopmentProjects/MapServer/0"
SOURCE = "Thornton development projects"
SLUG = "thornton_development_projects"
OUT = os.path.join(tc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

# Planner, Engineer, created_user, last_edited_user (staff names) and V_Drive_Link (internal
# path) are deliberately not requested.
FIELDS = ["OBJECTID", "GlobalID", "PermitNumber", "created_date", "last_edited_date", "PermitType",
          "PermitStatus", "PermitAddress", "Comments", "ADDRKEY", "DevelopmentType", "Description",
          "PAName", "ParcelNumber", "Acres", "Website", "ProjectLocation", "TypeOfHousingAtAddress",
          "SFNo", "MFNo", "ApprovalTrack", "OnMap", "Applicant", "OnMapDate", "OffMapDate", "CaseNos",
          "Name", "Type", "Phase", "Status", "StatusAlt"]

EXTRA_COLS = ["industrial_use", "industrial_word", "global_id", "object_id", "project_name", "applicant",
              "permit_type", "permit_status", "development_type", "phase", "status", "status_alt",
              "approval_track", "on_map", "on_map_date", "off_map_date", "created_date", "last_edited",
              "case_numbers", "planning_area", "parcel_number", "acres", "project_location", "housing_type",
              "sf_units", "mf_units", "website", "address_key", "latitude", "longitude",
              "first_seen_at", "last_seen_at", "in_layer_last_run", "parser_version"]

INDUSTRIAL = re.compile(r"\b(industrial|warehous\w*|manufactur\w*|distribution|logistics|flex|"
                        r"data ?cent(er|re|ers)|cold storage|fabricat\w*|processing|production)\b", re.I)

# Words that mark an applicant value as a firm rather than a person (beyond the shared list).
FIRM_HINT = re.compile(r"(?i)\b(architect\w*|engineer\w*|civil|design\w*|consult\w*|planning|surveying|"
                       r"residential|housing|home|homes|library|infrastructure|neighborhoods?|brothers|"
                       r"studio|builders?|partners|realty|advisors|capital|crow|hines|greystar|lennar|"
                       r"walmart|quiktrip|costco|target|amazon|kroger|safeway|cot|seafood|meats?|produce|beverage|brewing|"
                       r"bakery|pharma\w*|aerospace|thermal|electric\w*|mechanical|plumbing|roofing|wireless|mobility|"
                       r"tower|towers|church|schools?|district|academy|library|pickle|fitness|dental|medical|clinic)\b")


CORP_SUFFIX = re.compile(r"(?i)^(inc|llc|l\.l\.c|co|corp|corporation|ltd|lp|llp|lllp|pc|pllc|company)\.?$")
GLUE = re.compile(r"(?i)\b(and|of|the|c/o|obo|dba)\b")


def clean_applicant(raw):
    """Keep only the firm parts of an applicant string. The string is split on ' - ', ', ',
    ' for ', ' c/o ', ' obo ' and ' / '; a bare corporate suffix part
    ("Inc.", "LLC") is glued back onto the part before it. A part survives when it carries a
    business or firm word (glue words such as 'and' and 'of' do not count), or is a single
    token (a firm name such as Hines or Kentro). A part whose first word is a common first
    name, a personal trust, two or three plain Capitalized words with no firm word, or a
    professional title is dropped as a person. Returns (cleaned, person_dropped)."""
    s = tc.clean(raw)
    if not s or s.lower() in ("multiple", "various", "n/a", "na", "unknown", "tbd", "none", "property owner", "owner"):
        return "", False
    # "<Person> of <Firm>": drop the person; otherwise 'of' stays inside the name (City of Thornton).
    m = re.match(r"^([A-Z][a-z]+)(\s+[A-Z]\.?)?\s+[A-Z][A-Za-z'\-]+\s+of\s+(?=[A-Z])", s)
    if m and m.group(1).lower() in tc.FIRST_NAMES:
        s = s[m.end():]
    # "<Personal trust> & <Firm>": drop the trust side.
    if tc.PERSONAL_TRUST.search(s) and re.search(r"\s(&|and)\s", s):
        sides = re.split(r"\s(?:&|and)\s", s, maxsplit=1)
        s = " & ".join(x for x in sides if not tc.PERSONAL_TRUST.search(x))
    raw_parts = [p.strip(" -,/") for p in re.split(r"\s+-\s+|,\s+|\s+for\s+|\s+c/o\s+|\s+obo\s+|\s+/\s+", s) if p.strip(" -,/")]
    parts = []
    for p in raw_parts:
        if CORP_SUFFIX.match(p) and parts:
            parts[-1] = parts[-1] + ", " + p
        elif CORP_SUFFIX.match(p):
            continue
        else:
            parts.append(p)
    keep, dropped = [], False
    for p in parts:
        body = GLUE.sub(" ", p)
        words = re.sub(r"[^A-Za-z.'\- ]", " ", body).split()
        hinted = bool(tc.BUSINESS_HINT.search(body) or FIRM_HINT.search(body))
        first_is_name = bool(words) and words[0].lower().strip(".") in tc.FIRST_NAMES
        personal_trust = bool(tc.PERSONAL_TRUST.search(p)) and not re.search(r"(?i)\b(llc|inc|corp|company|bank|co)\b", p)
        if tc.looks_like_person_business(p) or personal_trust or (first_is_name and not re.search(r"(?i)\b(llc|inc|corp|company|co|group|homes|properties|partners|associates|architect\w*|engineer\w*|design\w*|development|construction|builders|realty|church|school|district|city)\b", body)):
            dropped = True
            continue
        if not hinted and 2 <= len(words) <= 3 and all(re.fullmatch(r"[A-Z][a-z'\-]+|[A-Z]{1,2}\.?", w) for w in words):
            dropped = True
            continue
        keep.append(p)
    return " - ".join(keep), dropped


def parse_permit_address(s):
    """'13802 COLORADO  BLVD, THORNTON, CO 80602' -> (street, city, zip)."""
    s = tc.clean(s)
    if not s:
        return "", "", ""
    m = re.match(r"^(.*?),\s*([A-Za-z .]+),\s*CO\s*(\d{5})?", s)
    if m:
        return tc.clean(m.group(1)), tc.clean(m.group(2)).title(), m.group(3) or ""
    return s, "", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    cache = os.path.join(tc.RAW_ROOT, SLUG, "snapshot_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
    tc.require_fields(LAYER, FIELDS)
    n_source = tc.source_count(LAYER, "1=1")
    feats = tc.fetch_all(LAYER, "1=1", FIELDS, cache)
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH: fetched %d, source says %d" % (len(feats), n_source))
    print("source count (whole layer): %d" % n_source)

    existing, _ = tc.read_csv(OUT)
    by_gid = {r["global_id"]: r for r in existing}
    cols = tc.COMMON_COLS + EXTRA_COLS
    new_rows, updated, out_of_window, dropped_people, date_types = [], 0, 0, 0, Counter()
    seen_gids = set()
    for f in feats:
        at = f["attributes"]
        gid = tc.clean(at.get("GlobalID")).strip("{}").lower()
        seen_gids.add(gid)
        fetched = f["_fetched_at"]
        if at.get("OnMapDate"):
            rdate, dtype = tc.ms_to_date(at["OnMapDate"]), "on map"
        elif at.get("created_date"):
            rdate, dtype = tc.ms_to_date(at["created_date"]), "created"
        else:
            rdate, dtype = tc.ms_to_date(at.get("last_edited_date")), "last edited"
        status_cols = {
            "on_map": tc.clean(at.get("OnMap")), "off_map_date": tc.ms_to_date(at.get("OffMapDate")),
            "phase": tc.clean(at.get("Phase")), "status": tc.clean(at.get("Status")),
            "status_alt": tc.clean(at.get("StatusAlt")), "permit_status": tc.clean(at.get("PermitStatus")),
            "last_edited": tc.ms_to_date(at.get("last_edited_date")), "last_seen_at": fetched,
            "in_layer_last_run": "Y"}
        if gid in by_gid:
            by_gid[gid].update(status_cols)
            updated += 1
            continue
        if rdate < a.since:
            out_of_window += 1
            continue
        date_types[dtype] += 1
        g = f.get("geometry") or {}
        x, y = g.get("x"), g.get("y")
        has_pt = isinstance(x, (int, float)) and isinstance(y, (int, float)) and -106 < x < -104 and 39 < y < 41
        applicant, dropped = clean_applicant(at.get("Applicant"))
        dropped_people += dropped
        name = tc.scrub_text(at.get("Name"), 255)
        if applicant:
            company, role = applicant, "applicant"
        elif name:
            company, role = name, "project"
        else:
            company, role = "", "unknown"
        street, city, zip5 = parse_permit_address(at.get("PermitAddress"))
        if not street:
            street = tc.scrub_text(at.get("ProjectLocation"), 200)
        comments = tc.scrub_text(at.get("Comments"), 500)
        desc = comments or tc.scrub_text(at.get("Description"), 500)
        text = " ".join([tc.clean(at.get("Name")), tc.clean(at.get("Comments")), tc.clean(at.get("Description")),
                         tc.clean(at.get("PAName")), tc.clean(at.get("DevelopmentType")), tc.clean(at.get("PermitType"))])
        m = INDUSTRIAL.search(text)
        pn = tc.clean(at.get("PermitNumber"))
        oid = at.get("OBJECTID")
        row = {
            "source": SOURCE, "source_level": "County (Adams)",
            "record_id": pn or ("GID-" + gid), "record_date": rdate, "date_type": dtype,
            "record_type": tc.clean(at.get("PermitType")) or ("Pre-application" if tc.clean(at.get("StatusAlt")) == "Presubmittal" else "Planning case"),
            "company_name": company, "company_role": role,
            "site_address": street, "city": city or "Thornton", "county": "Adams", "zip": zip5,
            "description": desc, "flag": "Y", "flag_rule": "all planning and development cases",
            "source_url": tc.layer_record_url(LAYER, "OBJECTID=%s" % oid), "retrieved_at": fetched,
            "industrial_use": "Y" if m else "N", "industrial_word": m.group(0).lower() if m else "",
            "global_id": gid, "object_id": str(oid), "project_name": name, "applicant": applicant,
            "permit_type": tc.clean(at.get("PermitType")), "development_type": tc.clean(at.get("DevelopmentType")),
            "approval_track": tc.clean(at.get("ApprovalTrack")),
            "on_map_date": tc.ms_to_date(at.get("OnMapDate")), "created_date": tc.ms_to_date(at.get("created_date")),
            "case_numbers": tc.clean(at.get("CaseNos")), "planning_area": tc.clean(at.get("PAName")),
            "parcel_number": tc.clean(at.get("ParcelNumber")), "acres": tc.fmt_num(at.get("Acres")),
            "project_location": tc.scrub_text(at.get("ProjectLocation"), 200),
            "housing_type": tc.clean(at.get("TypeOfHousingAtAddress")),
            "sf_units": tc.fmt_num(at.get("SFNo")), "mf_units": tc.fmt_num(at.get("MFNo")),
            "website": tc.clean(at.get("Website")), "address_key": tc.fmt_num(at.get("ADDRKEY")),
            "latitude": "%.6f" % y if has_pt else "", "longitude": "%.6f" % x if has_pt else "",
            "first_seen_at": fetched, "parser_version": tc.PARSER_VERSION}
        row.update(status_cols)
        new_rows.append(row)
    for gid, r in by_gid.items():
        if gid not in seen_gids:
            r["in_layer_last_run"] = "N"
    rows = existing + new_rows
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    tc.write_csv(OUT, cols, rows)
    print("rows in CSV: %d (new this run %d, already held and refreshed %d, no longer in layer %d, before --since %d)"
          % (len(rows), len(new_rows), updated, sum(1 for r in by_gid.values() if r["in_layer_last_run"] == "N"), out_of_window))
    print("date types of new rows:", dict(date_types))
    print("applicant strings with a person part dropped:", dropped_people)
    print("industrial_use Y:", sum(1 for r in rows if r["industrial_use"] == "Y"))
    print("flag rules:", Counter(r["flag_rule"] for r in rows if r["flag"] == "Y"))


if __name__ == "__main__":
    main()
