#!/usr/bin/env python3
"""
frs_filter.py - Filter the EPA ECHO FRS bulk download by state FIPS and NAICS prefix.

Standard library only (Python 3.8+). Streams the CSVs straight out of the zip,
so the national file never has to be extracted or loaded into memory whole.

Usage:
    python frs_filter.py --states 06,41,53 --naics 311,312,325,3261

    --states   comma-separated 2-digit state FIPS codes            (required)
    --naics    comma-separated NAICS prefixes, any length 2-6      (required)
    --match    any | primary   which NAICS codes must match        (default: any)
    --zip      path to frs_downloads.zip; downloaded if missing    (default: ./frs_downloads.zip)
    --out      output CSV path                                     (default: ./frs_filtered.csv)
    --seed     seed for the 20-row random sample                   (default: 42)

Output columns:
    frs_id, facility_name, street, city, state, zip, county, lat, lon,
    naics_primary, naics_all

Behaviour worth knowing:
  * If the download fails, is truncated, or is not a valid zip, the script
    exits non-zero and writes NO output CSV. It never invents rows.
  * If an expected column is missing from the EPA files, it stops and prints
    the headers it actually found, rather than guessing.
  * The ECHO facilities file carries the state as a postal abbreviation, so
    FIPS codes are mapped to postal codes for the state filter.
  * naics_primary: uses the file's PRIMARY_INDICATOR column when it exists.
    Otherwise it is the code reported by the most program records for that
    facility (ties -> lowest code). The script prints which method it used.
  * Dedupe keeps the first row seen for each FRS registry ID.
"""

import argparse
import csv
import io
import os
import random
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict

URL = "https://echo.epa.gov/files/echodownloads/frs_downloads.zip"

FIPS_TO_POSTAL = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI",
}

# Accepted header names per logical field (first match wins, case-insensitive).
FAC_COLS = {
    "frs_id": ["REGISTRY_ID"],
    "facility_name": ["FAC_NAME", "PRIMARY_NAME"],
    "street": ["FAC_STREET", "LOCATION_ADDRESS"],
    "city": ["FAC_CITY", "CITY_NAME"],
    "state": ["FAC_STATE", "STATE_CODE"],
    "zip": ["FAC_ZIP", "POSTAL_CODE"],
    "county": ["FAC_COUNTY", "COUNTY_NAME"],
    "lat": ["LATITUDE_MEASURE", "LATITUDE83", "FAC_LAT"],
    "lon": ["LONGITUDE_MEASURE", "LONGITUDE83", "FAC_LONG"],
}
NAICS_COLS = {
    "frs_id": ["REGISTRY_ID"],
    "naics": ["NAICS_CODE"],
}
OUT_COLS = ["frs_id", "facility_name", "street", "city", "state", "zip", "county",
            "lat", "lon", "naics_primary", "naics_all"]


def die(msg):
    print("\nERROR: " + msg, file=sys.stderr)
    print("Stopped. No output CSV was written.", file=sys.stderr)
    sys.exit(1)


def download(url, dest):
    part = dest + ".part"
    print("Downloading %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (frs_filter.py)"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(part, "wb") as fh:
            expected = resp.headers.get("Content-Length")
            expected = int(expected) if expected and expected.isdigit() else None
            got, next_report = 0, 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                got += len(chunk)
                if got >= next_report:
                    total = (" / %.0f MB" % (expected / 1e6)) if expected else ""
                    print("  %.0f MB%s" % (got / 1e6, total), flush=True)
                    next_report += 50 * 1024 * 1024
    except Exception as exc:  # network, HTTP, disk
        if os.path.exists(part):
            os.remove(part)
        die("download failed: %r" % (exc,))
    if expected is not None and got != expected:
        os.remove(part)
        die("download truncated: got %d bytes, server said %d" % (got, expected))
    if not zipfile.is_zipfile(part):
        os.remove(part)
        die("downloaded file is not a valid zip (got %d bytes)" % got)
    os.replace(part, dest)
    print("Download complete: %s (%.0f MB)" % (dest, got / 1e6))


def find_member(zf, token):
    hits = [n for n in zf.namelist()
            if token in os.path.basename(n).upper() and n.lower().endswith(".csv")]
    if len(hits) != 1:
        die("expected exactly one CSV containing %r in the zip, found %r.\nZip contents: %r"
            % (token, hits, zf.namelist()))
    return hits[0]


def open_csv(zf, member):
    raw = zf.open(member)
    text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
    reader = csv.reader(text)
    try:
        header = next(reader)
    except StopIteration:
        die("%s is empty" % member)
    header = [h.strip().lstrip("﻿").upper() for h in header]
    return reader, header


def resolve(header, spec, member, optional=()):
    idx = {}
    for field, candidates in spec.items():
        for cand in candidates:
            if cand in header:
                idx[field] = header.index(cand)
                break
        else:
            if field not in optional:
                die("%s has no column for %r (looked for %r).\nHeaders found: %r"
                    % (member, field, candidates, header))
    return idx


def cell(row, i):
    return row[i].strip() if i < len(row) else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--states", required=True)
    ap.add_argument("--naics", required=True)
    ap.add_argument("--match", choices=["any", "primary"], default="any")
    ap.add_argument("--zip", default="frs_downloads.zip")
    ap.add_argument("--out", default="frs_filtered.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    fips = [s.strip().zfill(2) for s in args.states.split(",") if s.strip()]
    bad = [f for f in fips if f not in FIPS_TO_POSTAL]
    if bad:
        die("unknown state FIPS code(s): %r" % bad)
    postal = {FIPS_TO_POSTAL[f] for f in fips}
    prefixes = tuple(p.strip() for p in args.naics.split(",") if p.strip())
    if not prefixes or not all(p.isdigit() and 2 <= len(p) <= 6 for p in prefixes):
        die("NAICS prefixes must be 2-6 digit numbers, got %r" % (prefixes,))

    print("State FIPS : %s -> %s" % (",".join(fips), ",".join(sorted(postal))))
    print("NAICS      : %s (match on %s codes)" % (",".join(prefixes), args.match))

    if not os.path.exists(args.zip):
        download(URL, args.zip)
    elif not zipfile.is_zipfile(args.zip):
        die("%s exists but is not a valid zip. Delete it and rerun." % args.zip)
    else:
        print("Using existing %s" % args.zip)

    csv.field_size_limit(10 ** 9)
    with zipfile.ZipFile(args.zip) as zf:
        fac_member = find_member(zf, "FRS_FACILITIES")
        naics_member = find_member(zf, "FRS_NAICS")

        # Pass 1: facilities -> registry IDs inside the chosen states
        reader, header = open_csv(zf, fac_member)
        fi = resolve(header, FAC_COLS, fac_member)
        fac_raw = 0
        fac_state_rows = 0
        state_ids = set()
        for row in reader:
            fac_raw += 1
            if cell(row, fi["state"]).upper() in postal:
                fac_state_rows += 1
                state_ids.add(cell(row, fi["frs_id"]))

        # Pass 2: NAICS codes for those IDs
        reader, header = open_csv(zf, naics_member)
        ni = resolve(header, NAICS_COLS, naics_member)
        prim_idx = header.index("PRIMARY_INDICATOR") if "PRIMARY_INDICATOR" in header else None
        naics_raw = 0
        naics_in_state = 0
        codes = defaultdict(Counter)
        flagged = defaultdict(Counter)
        for row in reader:
            naics_raw += 1
            rid = cell(row, ni["frs_id"])
            if rid not in state_ids:
                continue
            code = "".join(ch for ch in cell(row, ni["naics"]) if ch.isdigit())
            if not code:
                continue
            naics_in_state += 1
            codes[rid][code] += 1
            if prim_idx is not None and cell(row, prim_idx).upper() in ("PRIMARY", "P", "Y", "YES", "1"):
                flagged[rid][code] += 1

        def primary_of(rid):
            pool = flagged.get(rid) or codes[rid]
            return sorted(pool.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

        keep = {}
        for rid, counter in codes.items():
            prim = primary_of(rid)
            pool = [prim] if args.match == "primary" else list(counter)
            if any(c.startswith(prefixes) for c in pool):
                keep[rid] = (prim, ";".join(sorted(counter)))

        # Pass 3: write matching facilities, dedupe on registry ID
        rows_after_naics = 0
        written = 0
        seen = set()
        sample = []
        rng = random.Random(args.seed)
        tmp_out = args.out + ".part"
        reader, header = open_csv(zf, fac_member)
        with open(tmp_out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(OUT_COLS)
            for row in reader:
                if cell(row, fi["state"]).upper() not in postal:
                    continue
                rid = cell(row, fi["frs_id"])
                if rid not in keep:
                    continue
                rows_after_naics += 1
                if rid in seen:
                    continue
                seen.add(rid)
                out = [rid] + [cell(row, fi[c]) for c in OUT_COLS[1:9]] + list(keep[rid])
                w.writerow(out)
                written += 1
                if len(sample) < 20:          # reservoir sample of 20
                    sample.append(out)
                else:
                    j = rng.randrange(written)
                    if j < 20:
                        sample[j] = out
        os.replace(tmp_out, args.out)

    no_coords = "n/a"
    print("\n=== ROW COUNTS ===")
    print("NAICS file, raw rows                        : %10d" % naics_raw)
    print("NAICS file, rows for in-state facilities    : %10d" % naics_in_state)
    print("Facilities, raw rows                        : %10d" % fac_raw)
    print("Facilities, after state filter              : %10d  (%d distinct FRS IDs)" % (fac_state_rows, len(state_ids)))
    print("  ...of which have at least one NAICS code  : %10d" % len(codes))
    print("Facilities, after NAICS filter              : %10d" % rows_after_naics)
    print("Facilities, after dedupe on FRS ID          : %10d  (%d duplicates dropped)" % (written, rows_after_naics - written))
    print("naics_primary method: %s" % ("PRIMARY_INDICATOR column, falling back to most-reported code"
                                        if prim_idx is not None else
                                        "most-reported code per facility (file has no PRIMARY_INDICATOR column)"))
    print("Wrote %d rows to %s" % (written, args.out))

    print("\n=== %d RANDOM ROWS (seed %d) ===" % (len(sample), args.seed))
    w = csv.writer(sys.stdout)
    w.writerow(OUT_COLS)
    for r in sample:
        w.writerow(r)


if __name__ == "__main__":
    main()
