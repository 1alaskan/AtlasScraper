"""Shared Socrata (SODA) pager for the Step 4 pulls. Parser/pager version 1.0.

Pages a dataset by a unique numeric id column (keyset paging: id > last id,
ordered by id), caches every raw CSV page to disk before anything is parsed,
and keeps a manifest (url, retrieved_at, rows) per page. Rerunning resumes
after the last cached page. Uses curl so the sandbox proxy settings apply.
"""
import csv, json, os, subprocess, sys, time, urllib.parse
from datetime import datetime, timezone

BASE = "https://data.colorado.gov/resource/"
UA = "step4-research-pull/1.0"
PAUSE = 1.2          # robots.txt Crawl-delay is 1 second
PAGE = 50000
csv.field_size_limit(10**9)


def _last_id(path, idcol):
    last = None; n = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            last = row[idcol]; n += 1
    return last, n


def fetch(dataset, idcol, select, where, outdir, page=PAGE, log=print):
    """Fetch all rows matching `where`, keyset-paged on idcol. Returns page paths."""
    os.makedirs(outdir, exist_ok=True)
    man_path = os.path.join(outdir, "manifest.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {"pages": [], "done": False}
    cursor = None
    for p in man["pages"]:
        cursor = p["last_id"]
    if man.get("done"):
        log(f"{dataset}: cached, {sum(p['rows'] for p in man['pages'])} rows")
        return [os.path.join(outdir, p["file"]) for p in man["pages"]]
    errors = 0
    while True:
        w = f"({where})" if where else None
        if cursor is not None:
            w = (w + " AND " if w else "") + f"{idcol} > {cursor}"
        params = {"$select": select, "$order": idcol, "$limit": page}
        if w:
            params["$where"] = w
        url = BASE + dataset + ".csv?" + urllib.parse.urlencode(params)
        fn = f"page_{len(man['pages']):04d}.csv"
        tmp = os.path.join(outdir, fn + ".tmp")
        time.sleep(PAUSE)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = subprocess.run(["curl", "-sS", "-m", "600", "-A", UA, "-o", tmp, "-w", "%{http_code}", url],
                           capture_output=True, text=True)
        code = r.stdout.strip()
        if r.returncode != 0 or code != "200":
            errors += 1
            log(f"{dataset}: error http={code} rc={r.returncode} {r.stderr.strip()[:200]}")
            if errors >= 3:
                raise SystemExit(f"{dataset}: stopping after 3 consecutive errors")
            time.sleep(20 * errors)
            continue
        errors = 0
        last, n = _last_id(tmp, idcol)
        if n == 0:
            os.remove(tmp)
            man["done"] = True
            json.dump(man, open(man_path, "w"), indent=1)
            break
        os.rename(tmp, os.path.join(outdir, fn))
        man["pages"].append({"file": fn, "url": url, "retrieved_at": ts, "rows": n, "last_id": last})
        json.dump(man, open(man_path, "w"), indent=1)
        log(f"{dataset}: {fn} rows={n} last_id={last}")
        cursor = last
        if n < page:
            man["done"] = True
            json.dump(man, open(man_path, "w"), indent=1)
            break
    return [os.path.join(outdir, p["file"]) for p in man["pages"]]


def rows(outdir):
    """Yield (row dict, retrieved_at) across cached pages."""
    man = json.load(open(os.path.join(outdir, "manifest.json")))
    for p in man["pages"]:
        with open(os.path.join(outdir, p["file"]), newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                yield row, p["retrieved_at"]


def count(dataset, where):
    url = BASE + dataset + ".json?" + urllib.parse.urlencode({"$select": "count(*) as n", "$where": where})
    time.sleep(PAUSE)
    r = subprocess.run(["curl", "-sS", "-m", "300", "-A", UA, url], capture_output=True, text=True)
    return int(json.loads(r.stdout)[0]["n"])
