#!/usr/bin/env python3
"""Pull Town of Frederick development applications into the step 4 format as an append-only
snapshot archive, merging two feeds:

  * the Development_Applications/FeatureServer/0 point layer (about 22 "under review" rows,
    undated, with zoning, a Project_Type and a DocumentCenter folder), and
  * the What's Developing page https://frederickco.gov/855/Whats-Developing, three HTML
    tables: neighborhood meetings for projects not yet submitted (meeting date), applications
    under review (submittal date) and approved applications (approval date). The page is the
    dated, current feed; the layer lags it.

Usage:  python3 pull_frederick_development_applications.py [--since YYYY-MM-DD] [--fresh]

Rows merge on the project name (token overlap after dropping dates and link labels).
record_id is a slug of the project name. record_date is the page's submittal date
(date_type `submitted`); an approved-only row gets its approval date (`approved`); a
neighborhood-meeting row its meeting date (`neighborhood meeting`); a layer-only row the
retrieval date (`snapshot`). Every row is flagged Y (`all planning and development cases`);
industrial_use = Y when the use, zoning or description says industrial, warehouse,
manufacturing, distribution, flex, data center, processing, plant, compressor station or oil
and gas facility.

Snapshot semantics: rows never seen before are appended with first_seen; rows already in
the CSV keep record_date, retrieved_at and first_seen and have status, approval_date,
last_seen and in_source_last_run refreshed; rows that left both feeds stay with
in_source_last_run = N. Nothing is deleted. --since only limits which new rows are added
(rows dated before it are skipped; default 2024-01-01; undated rows are never skipped).
--fresh refetches today's snapshot. Raw copies are cached under
../raw/frederick_development_applications/snapshot_<UTC day>/.
"""
import argparse, html, os, re, shutil, sys, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frederick_common as fc
import pull_frederick_building_permits as bp

LAYER = fc.GIS + "/Development_Applications/FeatureServer/0"
PAGE = "https://frederickco.gov/855/Whats-Developing"
SLUG = "frederick_development_applications"
SOURCE = "Frederick development applications"
OUT = os.path.join(fc.WELD_DIR, "scrape_%s.csv" % SLUG)

# Contact and Email (town planner name and address) are deliberately not requested.
LAYER_FIELDS = ["OBJECTID", "Application_Type", "Project_Type", "Description", "Project_Name",
                "Zoning_Existing", "Zoning_Proposed", "Public_Hearing", "Documents"]

EXTRA_COLS = ["industrial_use", "industrial_word", "status", "page_section", "submittal_date", "approval_date",
              "meeting_date", "application_type", "project_type", "project_name", "location_text",
              "public_hearing", "zoning_existing", "zoning_proposed", "documents_link", "layer_documents_link",
              "source_feed", "layer_objectid", "latitude", "longitude", "first_seen", "last_seen",
              "in_source_last_run", "parser_version"]

INDUSTRIAL = re.compile(
    r"\b(industrial|warehous\w*|manufactur(?:ing|e|es|ed)(?! home)|distribution|logistics|flex|"
    r"data ?cent(?:er|re|ers)|cold storage|fabricat\w*|processing|production|plant|compressor station|"
    r"oil and gas facility|compressor|storage yard|outdoor storage|maintenance building|"
    r"wash bay|truck|trucks|crane|BLI|Business Light Industrial|LI-FLEX|HI-FLEX|\bI \(Industrial)\b", re.I)

STOP = {"and", "the", "of", "a", "an", "on", "pp", "pdp", "cd", "site", "plan", "plans", "rezone", "amendment",
        "amendments", "no", "to", "in", "at", "for", "with", "sp", "ppdp", "ppdprezone", "frederick"}
DATE_RE = re.compile(r"\(\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*\)")
LINK_LABEL = re.compile(r"\s*(?:\d{4}\s+)?Neighborhood Meeting\s+(?:Recording\s*(?:&|and)\s*Minutes|Documentation|Minutes)\s*$", re.I)
PERSON_ANNEX = re.compile(r"\(\s*([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+Annexation\s*\)")


ABBREV = {"flg": "filing", "rplt": "replat", "blk": "block", "sub": "subdivision", "lt": "lot"}


def tokens(name):
    t = re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()
    return {ABBREV.get(w, w) for w in t if w not in STOP}


GENERIC_DESC = STOP | {"proposed", "proposal", "new", "building", "development", "project", "lots", "lot", "as",
                       "well", "is", "are", "be", "will", "existing", "approved", "previously", "review", "use",
                       "sq", "ft", "square", "feet", "sf", "with", "within", "into", "from", "by", "or", "this",
                       "that", "include", "including", "includes", "zone", "district", "town", "frederick"}


def desc_tokens(desc):
    t = re.sub(r"[^a-z0-9 ]", " ", (desc or "").lower()).split()
    return {w for w in t if w not in GENERIC_DESC and len(w) > 2}


def similar(a, a_desc, b, b_desc):
    """Same project when the name tokens overlap strongly, every number (lot, filing, block)
    agrees, the two do not name different companies, and the scopes share at least one
    meaningful word (two applications on the same lot are kept apart)."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return False
    na = {w for w in ta if re.search(r"\d", w)}
    nb = {w for w in tb if re.search(r"\d", w)}
    if na != nb:
        return False
    ca = bp.KNOWN_COMPANIES.search(a + " " + (a_desc or ""))
    cb = bp.KNOWN_COMPANIES.search(b + " " + (b_desc or ""))
    if ca and cb and ca.group(0).lower() != cb.group(0).lower():
        return False
    da, db = desc_tokens(a_desc), desc_tokens(b_desc)
    if da and db and not (da & db):
        return False
    inter = len(ta & tb)
    if inter == 0:
        return False
    if (ta <= tb or tb <= ta) and min(len(ta), len(tb)) >= 2:
        return True
    return inter / len(ta | tb) >= 0.6


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return "frederick-da-" + s[:80]


def to_iso(m):
    mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    return "%04d-%02d-%02d" % (y, mo, d)


def strip_tags(cell):
    return fc.clean(html.unescape(re.sub(r"<[^>]+>", " ", cell)))


def scrub_name(name):
    """Drop the date, link labels and a '(<Surname> Annexation)' aside from a project name."""
    n = DATE_RE.sub(" ", name)
    n = LINK_LABEL.sub("", n)
    n = re.sub(r"\s+", " ", n).strip(" -")
    m = PERSON_ANNEX.search(n)
    if m and not fc.BUSINESS_HINT.search(m.group(1)):
        n = n.replace(m.group(0), "(annexation)")
    return n.strip()


def parse_page(body):
    """Returns a list of dicts, one per table row, from the three What's Developing tables."""
    out = []
    for table in re.findall(r"<table.*?</table>", body, flags=re.S | re.I):
        rows = re.findall(r"<tr.*?</tr>", table, flags=re.S | re.I)
        if not rows:
            continue
        header = [strip_tags(c) for c in re.findall(r"<t[hd].*?</t[hd]>", rows[0], flags=re.S | re.I)]
        h0 = header[0].lower() if header else ""
        if "meeting" in h0:
            section, dcol, dtype = "neighborhood meeting (not yet submitted)", "meeting_date", "neighborhood meeting"
        elif "submittal" in h0:
            section, dcol, dtype = "under review", "submittal_date", "submitted"
        elif "approval" in h0:
            section, dcol, dtype = "approved", "approval_date", "approved"
        else:
            continue
        hdr = [h.lower() for h in header]
        for r in rows[1:]:
            cells = re.findall(r"<t[hd].*?</t[hd]>", r, flags=re.S | re.I)
            if len(cells) < 4:
                continue
            txt = [strip_tags(c) for c in cells]
            links = [l for l in re.findall(r'href="([^"]+)"', cells[0]) if "Neighborhood" not in l]
            raw_name = txt[0]
            dm = None
            for dm in DATE_RE.finditer(raw_name):
                pass
            rec = {"page_section": section, "date_type": dtype, "date": to_iso(dm) if dm else "",
                   "date_col": dcol, "project_name": scrub_name(raw_name),
                   "location_text": txt[1] if len(txt) > 1 else "",
                   "description": txt[2] if len(txt) > 2 else "",
                   "application_type": txt[3] if len(txt) > 3 else "",
                   "public_hearing": "", "documents_link": links[0] if links else ""}
            for i, h in enumerate(hdr):
                if "hearing" in h and i < len(txt):
                    rec["public_hearing"] = txt[i]
                if ("meeting" in h and i > 0) and i < len(txt) and section.startswith("neighborhood"):
                    pass  # the column holds the link label only
            if rec["documents_link"].startswith("/"):
                rec["documents_link"] = fc.TOWN + rec["documents_link"]
            out.append(rec)
    return out


def company_for(name, desc):
    """Company or project name when a company: a known name in the project name or scope, a
    parenthetical applicant in the name, or the project name itself when it reads as a firm."""
    m = bp.KNOWN_COMPANIES.search(name)
    if m:
        return m.group(0), "project"
    for par in re.findall(r"\(([^()]+)\)", name):
        if DATE_RE.match("(" + par + ")") or par.strip().upper() in ("CD", "ANNEXATION"):
            continue
        for part in re.split(r"\s*/\s*", par):
            c = bp.acceptable_company(part)
            if c:
                return c, "applicant"
    m = bp.KNOWN_COMPANIES.search(desc or "")
    if m:
        return m.group(0), "project"
    m = re.search(r"\bProposed\s+((?:[A-Z][\w&'-]*\.?)(?:\s+(?:[A-Z][\w&'-]*\.?|of|and|&))*)", desc or "")
    if m:
        c = bp.acceptable_company(m.group(1))
        if c and len(c.split()) >= 2:
            return c, "project"
    base = re.sub(r"\(.*?\)", " ", name)
    base = re.split(r"\b(?:Filing|Flg|Replat|Rplt|Lot|Lots|Block|Blk|Amendment|Subdivision|Minor|Site Plan)\b", base, maxsplit=1)[0]
    c = bp.acceptable_company(base)
    if c and not re.search(r"\b(business park|business center|subdivision|annexation|park|place|heights|creek|"
                           r"villages?|farms|meadows|commons|marketplace|town centre|shores|hill|hills|greens|"
                           r"construction plans|plans|filing|estates|ridge|crossing|station|square)\b", c, re.I):
        return c, "project"
    return "", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    now = fc.now_iso()
    day = now[:10].replace("-", "")
    cache = os.path.join(fc.RAW_ROOT, SLUG, "snapshot_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
    os.makedirs(cache, exist_ok=True)

    # 1. the layer
    fc.require_fields(LAYER, LAYER_FIELDS)
    n_layer = fc.source_count(LAYER, "1=1")
    feats = fc.fetch_all(LAYER, "1=1", LAYER_FIELDS, os.path.join(cache, "layer"), page_size=1000)
    if len(feats) != n_layer:
        raise SystemExit("ROW COUNT MISMATCH on the layer: %d fetched, source says %d" % (len(feats), n_layer))

    # 2. the page
    page_path = os.path.join(cache, "whats_developing.html")
    if os.path.exists(page_path):
        with open(page_path, encoding="utf-8") as f:
            body = f.read()
        page_fetched = json.load(open(page_path + ".meta.json"))["fetched_at"]
    else:
        body = fc.http(PAGE)
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(body)
        page_fetched = fc.now_iso()
        json.dump({"fetched_at": page_fetched, "url": PAGE}, open(page_path + ".meta.json", "w"))
    page_rows = parse_page(body)
    if len(page_rows) < 10:
        raise SystemExit("Page parse found only %d rows; the HTML layout has probably changed" % len(page_rows))
    print("layer rows %d, page rows %d (%s)" % (len(feats), len(page_rows), Counter(r["page_section"] for r in page_rows)))

    # 3. merge page rows and layer rows on project name
    merged = []
    for pr in page_rows:
        merged.append({"page": pr, "layer": None})
    unmatched_layer = 0
    for f in feats:
        at = f["attributes"]
        lname = scrub_name(fc.clean(at.get("Project_Name")))
        hit = None
        for m in merged:
            if m["page"] is not None and similar(m["page"]["project_name"], m["page"]["description"],
                                                 lname, fc.clean(at.get("Description"))):
                hit = m
                break
        if hit is None or hit["layer"] is not None:
            merged.append({"page": None, "layer": f})
            if hit is None:
                unmatched_layer += 1
        else:
            hit["layer"] = f
    print("layer rows matched to a page row: %d of %d" % (len(feats) - unmatched_layer, len(feats)))

    # 4. build output rows
    fresh_rows = {}
    for m in merged:
        pr, f = m["page"], m["layer"]
        at = (f or {}).get("attributes", {}) if f else {}
        geom = (f or {}).get("geometry") or {}
        name = pr["project_name"] if pr else scrub_name(fc.clean(at.get("Project_Name")))
        desc = pr["description"] if pr else fc.clean(at.get("Description"))
        ldesc = fc.clean(at.get("Description")) if f else ""
        if f and pr and ldesc and ldesc.lower() not in desc.lower():
            desc = (desc + " | Layer: " + ldesc).strip(" |")
        tier = fc.clean(re.sub(r"<[^>]+>", "", at.get("Application_Type") or "")) if f else ""
        app_type = pr["application_type"] if pr else (fc.clean(at.get("Project_Type")) or tier)
        rtype = app_type
        if f and fc.clean(at.get("Project_Type")) and fc.clean(at.get("Project_Type")).lower() not in app_type.lower():
            rtype = app_type + "; " + fc.clean(at.get("Project_Type"))
        if pr:
            rdate, dtype = pr["date"], pr["date_type"]
            if not rdate:
                rdate, dtype = page_fetched[:10], "snapshot"
        else:
            rdate, dtype = f["_fetched_at"][:10], "snapshot"
        company, role = company_for(name, desc)
        zoning_ex = fc.clean(at.get("Zoning_Existing")) if f else ""
        zoning_pr = fc.clean(at.get("Zoning_Proposed")) if f else ""
        text = " ".join([name, desc, rtype, zoning_ex, zoning_pr])
        im = INDUSTRIAL.search(text)
        rid = slug(name)
        feed = "both" if (pr and f) else ("page" if pr else "layer")
        x, y = geom.get("x"), geom.get("y")
        row = {
            "source": SOURCE, "source_level": fc.SOURCE_LEVEL, "record_id": rid,
            "record_date": rdate, "date_type": dtype, "record_type": rtype,
            "company_name": company, "company_role": role,
            "site_address": pr["location_text"] if pr else "", "city": fc.CITY, "county": fc.COUNTY, "zip": "",
            "description": fc.clean(desc, 500),
            "flag": "Y", "flag_rule": "all planning and development cases",
            "source_url": PAGE if pr else fc.layer_query_url(LAYER, "OBJECTID=%s" % at.get("OBJECTID")),
            "retrieved_at": page_fetched if pr else f["_fetched_at"],
            "industrial_use": "Y" if im else "N", "industrial_word": im.group(0) if im else "",
            "status": pr["page_section"] if pr else "under review (layer only)",
            "page_section": pr["page_section"] if pr else "",
            "submittal_date": pr["date"] if pr and pr["date_col"] == "submittal_date" else "",
            "approval_date": pr["date"] if pr and pr["date_col"] == "approval_date" else "",
            "meeting_date": pr["date"] if pr and pr["date_col"] == "meeting_date" else "",
            "application_type": app_type + ((" (" + tier + " review)") if tier else ""),
            "project_type": fc.clean(at.get("Project_Type")) if f else "",
            "project_name": name, "location_text": pr["location_text"] if pr else "",
            "public_hearing": pr["public_hearing"] if pr else fc.clean(at.get("Public_Hearing")),
            "zoning_existing": zoning_ex, "zoning_proposed": zoning_pr,
            "documents_link": pr["documents_link"] if pr else "",
            "layer_documents_link": fc.clean(at.get("Documents")) if f else "",
            "source_feed": feed, "layer_objectid": str(at.get("OBJECTID")) if f else "",
            "latitude": "%.6f" % y if y is not None else "", "longitude": "%.6f" % x if x is not None else "",
            "first_seen": now, "last_seen": now, "in_source_last_run": "Y", "parser_version": fc.PARSER_VERSION}
        if rid in fresh_rows:   # same project in two page sections (for example under review and approved)
            old = fresh_rows[rid]
            for k in ("submittal_date", "approval_date", "meeting_date", "documents_link", "layer_documents_link",
                      "zoning_existing", "zoning_proposed", "latitude", "longitude", "layer_objectid"):
                old[k] = old[k] or row[k]
            old["status"] = old["status"] if "approved" in old["status"] else row["status"]
            old["source_feed"] = "both" if (old["source_feed"] != row["source_feed"] or feed == "both") else feed
            if old["date_type"] in ("snapshot", "neighborhood meeting", "approved") and dtype == "submitted":
                old["record_date"], old["date_type"] = rdate, dtype
            continue
        fresh_rows[rid] = row

    # 5. append-only merge with the existing CSV
    cols = fc.COMMON_COLS + EXTRA_COLS
    old_cols, old_rows = fc.read_csv(OUT)
    if old_cols and old_cols != cols:
        raise SystemExit("Existing CSV columns differ from the parser's; delete the file to rebuild")
    by_id = {r["record_id"]: r for r in old_rows}
    added = updated = skipped = 0
    for rid, row in fresh_rows.items():
        if rid in by_id:
            old = by_id[rid]
            for k in ("status", "page_section", "approval_date", "meeting_date", "submittal_date", "documents_link",
                      "layer_documents_link", "source_feed", "public_hearing", "zoning_existing", "zoning_proposed",
                      "application_type", "project_type", "record_type", "description", "industrial_use",
                      "industrial_word", "layer_objectid", "latitude", "longitude", "site_address", "location_text"):
                if row[k]:
                    old[k] = row[k]
            if old["date_type"] in ("snapshot", "neighborhood meeting", "approved") and row["date_type"] == "submitted":
                old["record_date"], old["date_type"] = row["record_date"], row["date_type"]
            if not old["company_name"] and row["company_name"]:
                old["company_name"], old["company_role"] = row["company_name"], row["company_role"]
            old["last_seen"], old["in_source_last_run"] = now, "Y"
            updated += 1
        else:
            if row["date_type"] != "snapshot" and row["record_date"] < a.since:
                skipped += 1
                continue
            by_id[rid] = row
            added += 1
    for rid, old in by_id.items():
        if rid not in fresh_rows:
            old["in_source_last_run"] = "N"
    rows = sorted(by_id.values(), key=lambda r: (r["record_date"], r["record_id"]))
    fc.write_csv(OUT, cols, rows)

    print("rows in CSV: %d (added %d, refreshed %d, skipped as before --since %d, gone from both feeds %d)"
          % (len(rows), added, updated, skipped, sum(1 for r in rows if r["in_source_last_run"] == "N")))
    print("source feed:", Counter(r["source_feed"] for r in rows))
    print("status:", Counter(r["status"] for r in rows))
    print("date types:", Counter(r["date_type"] for r in rows))
    print("industrial_use:", Counter(r["industrial_use"] for r in rows))
    for c in ("company_name", "site_address", "record_date", "latitude"):
        print("  null %s: %d" % (c, sum(1 for r in rows if not r[c])))
    print("companies:", sorted({(r["company_name"], r["company_role"]) for r in rows if r["company_name"]}))
    print("dates:", min(r["record_date"] for r in rows), "to", max(r["record_date"] for r in rows))


if __name__ == "__main__":
    main()
