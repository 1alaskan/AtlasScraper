#!/usr/bin/env python3
"""Step 4b add-on: run the tier B equipment words (rule B1a) on the FULL collateral text.

Step 4 cut `description` at 500 characters. This script asks the Colorado collateral table (4am6-w6u4,
data.colorado.gov, the same documented SODA API Step 4 used) for the collateral rows of the filings that
 (a) are initial UCC financing statements, (b) are not tier A, (c) have a business word in the debtor name,
 (d) have collateral text longer than 500 characters,
then applies the B1a words and guards from reflag_step4b.py to the whole text.

Usage: python3 pull_ucc_fulltext_b1a.py <step4-scrape folder> [--budget 150]
Resumable: run it again until it prints DONE. Raw text is cached under <work>/ucc_fulltext_cache/ next to this
script and is NOT copied into the scrape folder; only the hits file is:
    scrape_ucc_filings/ucc_b1a_fulltext_hits.csv   (record_id, debtor_seq, fileid, words, snippet)
reflag_step4b.py reads that file when it exists.
Polite use: 150 file ids a request, 1.2 s pause, user agent step4-research-pull/1.0. robots.txt allows /resource/.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import reflag_step4b as R
csv.field_size_limit(10 ** 9)
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
def ws(x): return re.sub(r"\s+", " ", x or "").strip()

def main():
    base = sys.argv[1]; budget = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 150
    cache = os.path.join(HERE, "ucc_fulltext_cache"); os.makedirs(cache, exist_ok=True)
    todo_p = os.path.join(cache, "todo.json"); rows_p = os.path.join(cache, "rows.json")
    src = os.path.join(base, "scrape_ucc_filings", "scrape_ucc_filings.csv")
    if not os.path.exists(todo_p):
        rows = {}
        for r in csv.DictReader(open(src, newline="", encoding="utf-8-sig")):
            if r["flag"] == "Y" or r["transaction_type"] != "Initial Filing" or "|ucc|" not in r["filing_type_raw"]: continue
            if r["debtor_name_has_entity_token"] == "N" or int(r["collateral_text_len"] or 0) <= 500: continue
            rows.setdefault(r["fileid"], []).append([r["record_id"], r["debtor_seq"], r["company_name"]])
        json.dump(sorted(rows, key=int), open(todo_p, "w")); json.dump(rows, open(rows_p, "w"))
    todo = json.load(open(todo_p)); rows = json.load(open(rows_p))
    done_p = os.path.join(cache, "text.jsonl"); done = set()
    if os.path.exists(done_p):
        for line in open(done_p, encoding="utf-8"):
            done.add(json.loads(line)["fileid"])
    left = [f for f in todo if f not in done]
    t0 = time.time(); n = 0
    with open(done_p, "a", encoding="utf-8") as out:
        while left and time.time() - t0 < budget:
            batch = left[:150]
            q = {"$select": "fileid,actiontype,collateraldescription,additionalcollateraldescription",
                 "$where": "fileid in (%s)" % ",".join("'%s'" % f for f in batch), "$limit": "50000", "$order": "collateralid"}
            url = "https://data.colorado.gov/resource/4am6-w6u4.json?" + urllib.parse.urlencode(q)
            try:
                data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "step4-research-pull/1.0"}), timeout=60))
            except Exception as e:
                print("request failed:", e); time.sleep(10); continue
            by = {f: ([], []) for f in batch}
            for d in data:
                if d.get("actiontype") == "delete only" or d["fileid"] not in by: continue
                cat, txt = ws(d.get("collateraldescription")), ws(d.get("additionalcollateraldescription"))
                if cat and cat.upper() not in ("UNKNOWN", "GENERAL DESCRIPTION") and cat not in by[d["fileid"]][0]: by[d["fileid"]][0].append(cat)
                if txt and txt not in by[d["fileid"]][1]: by[d["fileid"]][1].append(txt)
            for f in batch:
                full = SSN.sub("[redacted]", " | ".join(by[f][1])); cat = "; ".join(by[f][0])
                out.write(json.dumps({"fileid": f, "text": (cat + " " + full).strip()}) + "\n")
            out.flush(); left = left[150:]; n += 1; time.sleep(1.2)
    print("filings to check", len(todo), "fetched", len(todo) - len(left), "requests this run", n)
    if left:
        print("NOT DONE: run again"); return
    # ---- match
    hits = []; C = {}
    for line in open(done_p, encoding="utf-8"):
        j = json.loads(line); text = j["text"]
        for rid, seq, name in rows[j["fileid"]]:
            h = R.b1a_hits(text, name)
            if not h: continue
            m = next((rx.search(text) for lab, rx in R.B_RE if lab == h[0]), None)
            a = max(0, m.start() - 90) if m else 0
            hits.append([rid, seq, j["fileid"], ", ".join(h[:3]), text[a:a + 220], str(m.start() if m else -1)])
            for x in h: C[x] = C.get(x, 0) + 1
    outp = os.path.join(base, "scrape_ucc_filings", "ucc_b1a_fulltext_hits.csv")
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "debtor_seq", "fileid", "words", "snippet", "match_position"]); w.writerows(hits)
    print("DONE. rows with a hit:", len(hits), "past character 500:", sum(1 for h in hits if int(h[5]) >= 500)); print(sorted(C.items(), key=lambda x: -x[1]))

if __name__ == "__main__":
    main()
