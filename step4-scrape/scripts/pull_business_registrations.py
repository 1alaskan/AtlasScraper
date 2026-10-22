#!/usr/bin/env python3
"""Colorado business registrations (data.colorado.gov dataset 4ykn-tg5h) -> scrape_business_registrations.csv

Usage:  python3 pull_business_registrations.py            # fetch (resumes from cache) then build
        python3 pull_business_registrations.py --build    # rebuild CSV from cached raw pages only
To refresh from scratch delete raw/biz/ first. Parser version 1.0.

Personal data: the $select never asks for agent first/middle/last name, suffix, or any agent address.
"""
import csv, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import soda_fetch as s

DATASET = "4ykn-tg5h"
SINCE = "2024-01-01"
SELECT = ("entityid,entityname,principaladdress1,principaladdress2,principalcity,principalstate,"
          "principalzipcode,principalcountry,entitystatus,jurisdictonofformation,entitytype,"
          "agentorganizationname,entityformdate")
WHERE = f"entityformdate >= '{SINCE}'"
RAW = os.path.join(HERE, "raw", "biz")
OUT = os.path.join(HERE, "scrape_business_registrations.csv")
SUMMARY = os.path.join(HERE, "summary_business_registrations.md")

# label -> regex body (word boundaries are added). Order = order used in flag_rule.
WIDE = [
 ("manufacturing", r"manufacturing"), ("manufacturer", r"manufacturers?"), ("mfg", r"mfg"),
 ("industries", r"industries"), ("industrial", r"industrial"), ("technologies", r"technologies"),
 ("technology", r"technology"), ("energy", r"energy"), ("foods", r"foods"), ("food", r"food"),
 ("brewing", r"brewing"), ("brewery", r"brewery|breweries"), ("distilling", r"distilling"),
 ("distillery", r"distillery|distilleries"), ("beverage", r"beverages?"), ("bottling", r"bottling"),
 ("aerospace", r"aerospace"), ("space", r"space"), ("systems", r"systems"), ("machine", r"machines?"),
 ("machining", r"machining"), ("fabrication", r"fabrication"), ("fabricators", r"fabricators?"),
 ("metal", r"metals?"), ("steel", r"steel"), ("plastics", r"plastics?"), ("polymer", r"polymers?"),
 ("chemical", r"chemicals?"), ("materials", r"materials?"), ("composites", r"composites?"),
 ("semiconductor", r"semiconductors?"), ("electronics", r"electronics"), ("battery", r"battery|batteries"),
 ("solar", r"solar"), ("pharma", r"pharma|pharmaceuticals?"), ("biotech", r"biotech|biotechnology"),
 ("bioscience", r"biosciences?"), ("packaging", r"packaging"), ("precision", r"precision"),
 ("tool", r"tools?|tooling"), ("forge", r"forge|forging"), ("foundry", r"foundry|foundries"),
 ("casting", r"castings?"), ("coatings", r"coatings?"), ("cement", r"cement"), ("concrete", r"concrete"),
 ("lumber", r"lumber"), ("mill", r"mills?|milling"), ("processing", r"processing"),
 ("automation", r"automation"), ("robotics", r"robotics"),
]
NARROW = {"manufacturing", "industries", "technologies", "energy", "foods", "brewing", "aerospace", "systems"}
WIDE_RE = [(lab, re.compile(r"\b(?:%s)\b" % body, re.I)) for lab, body in WIDE]

COLS = ["source", "source_level", "record_id", "record_date", "date_type", "record_type", "company_name",
        "company_role", "site_address", "city", "county", "zip", "description", "flag", "flag_rule",
        "source_url", "retrieved_at",
        "entity_status", "entity_type", "jurisdiction_of_formation", "principal_state", "principal_country",
        "is_foreign", "flag_narrow", "agent_organization_name"]


def ws(x):
    return re.sub(r"\s+", " ", x or "").strip()


def build():
    n = 0; seen = set(); dups = 0
    monthly = defaultdict(Counter); perword = Counter(); perword_narrow = Counter()
    mismatch = Counter()
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(COLS)
        for r, ts in s.rows(RAW):
            eid = r["entityid"]
            if eid in seen:
                dups += 1; continue
            seen.add(eid)
            date = r["entityformdate"][:10]
            if not date or date < SINCE:
                raise SystemExit(f"schema/filter drift: entity {eid} has form date {date!r}")
            etype = ws(r["entitytype"]); juris = ws(r["jurisdictonofformation"]); name = ws(r["entityname"])
            foreign = etype.upper().startswith("F")
            mismatch[(foreign, juris == "CO")] += 1
            hits = [lab for lab, rx in WIDE_RE if rx.search(name)]
            flag = "Y" if (foreign and hits) else "N"
            rule = "foreign entity + name match: " + ", ".join(hits[:3]) if flag == "Y" else ""
            narrow = "Y" if (foreign and any(h in NARROW for h in hits)) else "N"
            addr = ", ".join(x for x in (ws(r["principaladdress1"]), ws(r["principaladdress2"])) if x)
            desc = f"{etype} formed {date}; status {ws(r['entitystatus'])}; jurisdiction {juris}"
            w.writerow(["Colorado business registrations", "State (Colorado)", eid, date, "filed", etype, name,
                        "registrant", addr, ws(r["principalcity"]), "", ws(r["principalzipcode"]), desc[:500],
                        flag, rule, f"https://data.colorado.gov/resource/{DATASET}.json?entityid={eid}", ts,
                        ws(r["entitystatus"]), etype, juris, ws(r["principalstate"]), ws(r["principalcountry"]),
                        "Y" if foreign else "N", narrow, ws(r["agentorganizationname"])])
            n += 1
            m = monthly[date[:7]]; m["rows"] += 1; m["foreign"] += foreign
            m["flag"] += flag == "Y"; m["narrow"] += narrow == "Y"
            if flag == "Y":
                for h in hits: perword[h] += 1
                for h in hits:
                    if h in NARROW: perword_narrow[h] += 1
    with open(SUMMARY, "w") as f:
        f.write("# Colorado business registrations: monthly summary\n\n")
        f.write(f"Rows written: {n}. Duplicate entity ids skipped: {dups}.\n\n")
        f.write("| month | rows | foreign | flag Y (wide list) | flag_narrow Y |\n|---|---|---|---|---|\n")
        for k in sorted(monthly):
            m = monthly[k]; f.write(f"| {k} | {m['rows']} | {m['foreign']} | {m['flag']} | {m['narrow']} |\n")
        t = Counter()
        for m in monthly.values(): t.update(m)
        f.write(f"| total | {t['rows']} | {t['foreign']} | {t['flag']} | {t['narrow']} |\n\n")
        f.write("## Flagged rows per matched word (a row with several matches counts under each)\n\n| word | rows | in narrow list |\n|---|---|---|\n")
        for k, v in perword.most_common():
            f.write(f"| {k} | {v} | {'yes' if k in NARROW else ''} |\n")
        f.write("\n## Entity type prefix F against jurisdiction of formation\n\n| type starts with F | jurisdiction is CO | rows |\n|---|---|---|\n")
        for k, v in sorted(mismatch.items()): f.write(f"| {k[0]} | {k[1]} | {v} |\n")
    print("rows", n, "dups", dups)


if __name__ == "__main__":
    if "--build" not in sys.argv:
        s.fetch(DATASET, "entityid", SELECT, WHERE, RAW)
    build()
