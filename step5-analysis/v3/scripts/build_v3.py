#!/usr/bin/env python3
"""Step 5 v3: rebuild a county ranking in one pass from the Step 4 files. Default county: denver.

Usage:  python3 build_v3.py <step4-scrape folder> <step5-analysis folder> [--county denver] [--out <folder>] [--offline] [--budget 150]
        --county picks county_configs/<county>.py (scope, local noise cuts, web checks, ground truth). The points table is the same for every county.

Reads   step4-scrape: the three _v2 files, the five unchanged source files, ucc_b1a_fulltext_hits.csv
        this folder:  denver_zip_share.json, geocode_cache.json
        step5-analysis: denver_ranked_accounts.csv and denver_ranked_accounts_v2.csv, ONLY to fill the two comparison
        columns (rank_step5, rank_step5b) and the rank-change report after the ranking is final.
Writes  <out>/<county>_ranked_accounts_v3.csv, <out>/<county>_evidence_v3.csv, <out>/v3_report.json
Web use: the Census geocoder only, for addresses not yet in geocode_cache.json (see v3_geocode.py).
"""
import csv, os, re, sys, time
from collections import Counter, defaultdict

if "--county" in sys.argv:                      # must be set before v3_config is imported
    os.environ["V3_COUNTY"] = sys.argv[sys.argv.index("--county") + 1].lower()

from v3_lib import *
import v3_config as C
import v3_signals, v3_resolve, v3_geocode
from v3_score import score, points_text, eff_pts, base_pts, BASE

STREET = re.compile(r"\b\d{2,6}\s+(?:[NSEW]\.?\s+)?(?:[A-Za-z0-9]+\.?\s+){1,3}(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Pkwy|Parkway|Cir|Circle)\b\.?", re.I)
CONTACT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")
SUPPORT_CAP = 5          # unflagged support rows listed per source per account in the evidence file (the best ones; the rest add no points)
WITHHELD = "withheld (not confirmed as a business premises; see source record)"
SECTION_ORDER = {"denver": 0, "unconfirmed": 1, "oedit": 2}
RANK_COLS = ["rank", "company_name", "name_variants", "site_address", "zip", "county_basis", "stage", "score", "sources_count", "sources",
             "first_signal_date", "latest_signal_date", "top_evidence", "compressed_air_fit", "match_confidence", "in_ground_truth", "next_step",
             "tier", "rank_step5", "rank_step5b"]
EVID_COLS = SHARED + ["rank", "company_key", "match_class", "flag_tier", "flag_rule_v2", "points"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def show_address(raw, zp, extra, names=()):
    """Home-address rule: a UCC or registration street address is shown only when it has a suite or unit, appears in a site-based
    source (permits, site plans, air, water, press), carries two or more business names among the flagged rows of the ranking,
    or was shown in the first run on the strength of its web check. Otherwise the ranking shows "withheld" and keeps the zip."""
    k = addr_key(raw)
    if not k:
        return False
    if NOT_A_SITE.search(raw):
        return False
    if HAS_UNIT.search(raw) or k in extra["site_keys"]:
        return True
    if extra["shared"].get(k, 0) >= 2:
        return True
    return any(n in C.WEB_ADDRESS_OK for n in names)


def display(a, sc, extra):
    """-> dict of the descriptive columns for one account."""
    d = {}
    own = [e for e in a.sigs if e["flagged"]]
    if a.kind == "company":
        named = [e for e in a.sigs if e["cls"] == "confirmed" and e.get("names")]
        pref = {UCC: 3, AIR: 2, WAT: 1, REG: 0}
        best = max(named, key=lambda e: (e["flagged"], e["_eff"], pref.get(e["src"], 0), e["date"]))
        name = a.display or clean_name(best["names"][0])
        variants = [v for v in a.names.values() if nk(v) != nk(name)]
        d["company_name"] = name
        d["name_variants"] = " | ".join(sorted(set(variants)))
        st = a.sites.get(a.main_ak)
        ops = [x for x in a.sites.values() if "operator" in x["grades"]]
        if ops and (st is None or "operator" not in st["grades"]):
            st = ops[0]
        if st is None:
            d["site_address"], d["zip"] = "not given in the source", ""
        else:
            d["site_address"] = st["raw"] if show_address(st["raw"], st["zip"], extra, a.names) else WITHHELD
            d["zip"] = st["zip"]
        poss = any(e["cls"] == "possible" for e in own)
        d["match_confidence"] = "possible for some rows (see evidence file)" if poss else "confirmed"
        if getattr(a, "named_by_state_permit", False):
            d["match_confidence"] = "address rows are possible: the name comes from a state permit at the same street address"
    elif a.kind == "address":
        best = max(own, key=lambda e: (e["cls"] == "confirmed", e["_eff"], e["date"]))
        if a.step3:
            d["company_name"] = a.step3["display"]
            d["match_confidence"] = a.step3["confidence"]
            d["name_variants"] = ""
        elif a.occupiers:
            d["company_name"] = "Unattached address (possible occupier: %s)" % a.occupiers[0][0]
            d["match_confidence"] = "address confirmed; company possible"
            more = [o[0] for o in a.occupiers[1:]]
            d["name_variants"] = "basis: %s" % a.occupiers[0][1] + ((" | other possible occupiers: " + "; ".join(more)) if more else "")
        else:
            d["company_name"] = "Unattached address (no company attached)"
            d["match_confidence"] = "address confirmed; company not attached"
            d["name_variants"] = ""
        if a.other_names:
            n = len(a.other_names)
            extra_txt = "%d other business name%s at this address in the UCC or registration files (not attached; not listed here)" % (n, "" if n == 1 else "s")
            d["name_variants"] = (d["name_variants"] + " | " if d["name_variants"] else "") + extra_txt
        d["site_address"], d["zip"] = best["addr"], best["zip"]
    else:
        d["company_name"] = next(iter(a.names.values()))
        d["name_variants"] = ""
        d["site_address"], d["zip"] = "not given in the source (code name only)", ""
        d["match_confidence"] = "code name; company not identified"
    return d


def next_step(a, sc):
    stage, fit = sc["stage"][0], sc["fit"][0]
    if a.kind == "oedit":
        return "Watch for the state press release that names the company; do not treat as a %s account until it does" % C.COUNTY
    if a.kind == "address" and a.section == "unconfirmed":
        return "Tenant not identified; county not confirmed"
    if a.section == "unconfirmed":
        return "Confirm the county with the assessor before treating this as a %s account; if it is yours, qualify by phone" % C.COUNTY
    if a.kind == "address":
        if a.step3:
            return "Find the mechanical contractor and timing; air is specified during mechanical design"
        if a.occupiers:
            return "Tenant not identified; the possible occupier is not confirmed"
        return "Tenant not identified"
    if fit == "weak":
        return "Low priority: use looks like office, retail, storage or data centre"
    if stage.startswith("buying equipment"):
        return "Call now: financing production equipment in the last 12 months; ask what air the new machines need"
    if stage.startswith("fit-out") and "under $50k" not in stage:
        return "Call now: build-out permit open; ask who is specifying compressed air"
    if stage.startswith("under construction") and "under $50k" not in stage:
        return "Find the mechanical contractor and timing; air is specified during mechanical design"
    if stage.startswith("planned"):
        return "Early: watch for a building permit at this address"
    if sc["signal"] < 12:
        return "Qualify first: one weak signal only"
    return "Existing plant with a recent permit or equipment signal: ask about capacity additions and compressor age"


def gt_match(a, d):
    """-> list of (project, how)"""
    names = " ".join([nk(d["company_name"])] + list(a.names.keys()) + [nk(o[0]) for o in a.occupiers])
    keys = set(a.sites.keys()) | ({a.ak} if a.ak else set()) | set(e["ak"] for e in a.sigs if e["src"] in (PER, SDP, CRE) and e["ak"])
    out = []
    for p, (aliases, addrs) in C.GROUND_TRUTH.items():
        how = None
        if a.kind != "oedit" and any(al in names for al in aliases):
            how = "name (as a possible occupier)" if (a.kind == "address") else "name"
        if any(k in addrs for k in keys):
            how = (how + " and address") if how else "address only"
        if how:
            out.append((p, how))
    return out


def old_ranks(path):
    """-> (name key -> rank, address key -> rank, row list) for an earlier ranked file; comparison only."""
    by_name, by_addr = {}, {}
    if not os.path.exists(path):
        return by_name, by_addr, []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for x in rows:
        r = int(x["rank"])
        nm = x["company_name"]
        if nm.startswith("Unattached address") or nm.startswith("Safeway milk plant"):
            k = addr_key(x["site_address"])
            if k:
                by_addr.setdefault(k, r)
            continue
        for n in [nm] + [v for v in x["name_variants"].split(" | ") if v]:
            k = nk(n)
            if len(k) >= 3:
                by_name.setdefault(k, r)
        k = addr_key(x["site_address"])
        if k:
            by_addr.setdefault("C:" + k, r)
    return by_name, by_addr, rows


def find_old(a, d, by_name, by_addr):
    if a.kind in ("company", "oedit"):
        for k in [nk(d["company_name"])] + list(a.names.keys()):
            if k in by_name:
                return by_name[k]
        for k in a.sites:
            if k in by_addr:
                return by_addr[k]
        return ""
    if a.ak in by_addr:
        return by_addr[a.ak]
    for o in a.occupiers:
        if nk(o[0]) in by_name:
            return by_name[nk(o[0])]
    if "C:" + a.ak in by_addr:
        return by_addr["C:" + a.ak]
    return ""


def rank_accounts(accounts, P):
    scored = [(a, score(a, P)) for a in accounts]
    scored.sort(key=lambda t: (SECTION_ORDER[t[0].section], -round(t[1]["total"], 4), t[1]["latest"] and -int(t[1]["latest"].replace("-", "")) or 0,
                               next(iter(t[0].names.values()), t[0].ak)))
    return scored


def label_of(a, d):
    return "%s @ %s" % (d["company_name"][:60], d["site_address"][:30])


def main():
    pos = [x for i, x in enumerate(sys.argv[1:], 1) if not x.startswith("--") and not sys.argv[i - 1] in ("--out", "--budget", "--county")]
    if len(pos) < 2:
        print(__doc__)
        sys.exit(2)
    S4, S5 = pos[0], pos[1]
    OUT = arg("--out", os.path.join(S5, "v3"))
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    zshare = load_json(os.path.join(HERE, C.ZIP_SHARE_FILE))
    if zshare is None:
        print("Missing %s: build the zip share file for %s first (see county_configs/README.md)." % (C.ZIP_SHARE_FILE, C.COUNTY_FULL))
        sys.exit(2)
    gpath = os.path.join(HERE, "geocode_cache.json")

    def geocoder(queries):
        return v3_geocode.geocode_all(queries, gpath, budget_seconds=float(arg("--budget", "150")), offline="--offline" in sys.argv)

    try:
        sg = v3_signals.build_signals(S4, zshare, geocoder)
    except v3_geocode.Incomplete as e:
        print(str(e))
        sys.exit(3)
    print("signals: %d named, %d address-only, %d OEDIT (%.0fs)" % (len(sg["named"]), len(sg["address"]), len(sg["oedit"]), time.time() - t0))
    accounts, rcounts, extra = v3_resolve.resolve(sg, S4)
    shared_names = defaultdict(set)      # address key -> business names of ranked companies with a flagged row there
    for a in accounts:
        for e in a.sigs:
            if e["flagged"] and e["src"] in (UCC, REG, WAT, AIR) and e["ak"]:
                for n in e.get("names", [])[:1]:
                    shared_names[e["ak"]].add(nk(n))
    shared_n = Counter({k: len(v) for k, v in shared_names.items()})
    extra["shared"] = shared_n

    scored = rank_accounts(accounts, BASE)
    n1, a1, rows1 = old_ranks(os.path.join(S5, C.COUNTY_SLUG + "_ranked_accounts.csv"))
    n2, a2, rows2 = old_ranks(os.path.join(S5, C.COUNTY_SLUG + "_ranked_accounts_v2.csv"))

    out_rows, evid_rows, meta = [], [], []
    capped = 0
    for i, (a, sc) in enumerate(scored, 1):
        a.rank = i
        d = display(a, sc, extra)
        tiers = set(e["tier"] for e in a.sigs if e["flagged"] and e["tier"])
        srcs = sorted(set(e["src"] for e in a.sigs), key=SRC_ORDER.index)
        top = sorted(a.sigs, key=lambda e: (-e["_eff"], e["date"] and -int(e["date"].replace("-", "")) or 0))[:3]
        hide_text = d["site_address"] == WITHHELD
        if hide_text:
            for e in top:
                if e["src"] in (UCC, REG):
                    e["text"] = STREET.sub("[address removed]", e["text"])
        gt = gt_match(a, d)
        r5, r5b = find_old(a, d, n1, a1), find_old(a, d, n2, a2)
        row = dict(rank=i, score="%.1f" % sc["total"], county_basis=a.basis, stage=sc["stage"][0], sources_count=len(srcs), sources="; ".join(C.SRC_LABEL.get(x, x) for x in srcs),
                   first_signal_date=sc["first"], latest_signal_date=sc["latest"],
                   top_evidence=no_emdash(CONTACT.sub("[contact detail removed]", " || ".join(e["text"] for e in top)) + " || " + points_text(sc)),
                   compressed_air_fit="%s: %s" % sc["fit"], in_ground_truth=("yes: " + "; ".join("%s (%s)" % (p.split(" ")[0], h) for p, h in gt)) if gt else "no",
                   next_step=next_step(a, sc), tier="+".join(sorted(tiers)) if tiers else "", rank_step5=r5, rank_step5b=r5b)
        row.update({k: no_emdash(v) for k, v in d.items()})
        out_rows.append(row)
        key = ("N:" + next(iter(a.names))) if a.kind == "company" else ("A:" + a.ak) if a.kind == "address" else ("O:" + next(iter(a.names)))
        shown = Counter()
        keep_latest = {}
        for e in a.sigs:
            if e["_eff"] >= REC_MIN and e["date"] > keep_latest.get(e["src"], ("", None))[0]:
                keep_latest[e["src"]] = (e["date"], id(e))
        for e in sorted(a.sigs, key=lambda e: (SRC_ORDER.index(e["src"]), -e["_eff"], e["date"] and -int(e["date"].replace("-", "")) or 0)):
            if not e["flagged"] and e["_eff"] < REPEAT_MIN and keep_latest.get(e["src"], ("", None))[1] != id(e):
                shown[e["src"]] += 1
                if shown[e["src"]] > SUPPORT_CAP:
                    capped += 1
                    continue
            x = dict(e["row"])
            if e["src"] in (UCC, REG) and (not show_address(x["site_address"], x["zip"][:5], extra, a.names if a.kind == "company" else ()) or hide_text):
                if not show_address(x["site_address"], x["zip"][:5], extra, a.names if a.kind == "company" else ()):
                    x["site_address"] = "withheld (see source record)"
                x["description"] = STREET.sub("[address removed]", x["description"])
            if e["src"] == UCC and e["info"].get("hidden"):
                e["rule"] = e["rule"] + " [lender not named: filed through an agent]"
            if e["src"] == CRE:
                x["description"] = x["description"].split(" | ")[0]
            x["description"] = CONTACT.sub("[contact detail removed]", x["description"])
            x.update(rank=i, company_key=key, match_class=e["cls"], flag_tier=e["tier"] if e["flagged"] or e["row"].get("flag") == "Y" else "",
                     flag_rule_v2=e["rule"], points=g(e["_eff"]))
            evid_rows.append(x)
        meta.append(dict(rank=i, label=label_of(a, d), kind=a.kind, section=a.section, total=sc["total"], per={SHORT.get(k, k): list(v) for k, v in sc["per"].items()},
                         sources=sc["sources"], recency=sc["recency"], stage=sc["stage"][1], fit=FIT_PTS[sc["fit"][0]], stage_label=sc["stage"][0], fit_label=sc["fit"][0],
                         tier=row["tier"], r5=r5, r5b=r5b, gt=gt, name=d["company_name"], addr=d["site_address"], key=key,
                         web=("web check" in sc["fit"][1]), n_sources=len(srcs)))

    with open(os.path.join(OUT, C.COUNTY_SLUG + "_ranked_accounts_v3.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RANK_COLS)
        w.writeheader()
        w.writerows(out_rows)
    with open(os.path.join(OUT, C.COUNTY_SLUG + "_evidence_v3.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EVID_COLS)
        w.writeheader()
        w.writerows(evid_rows)

    # ------------------------------------------------------------------ report (counts, ground truth, sensitivity, rank changes)
    rep = dict(run_date=RUN, cuts=sg["cuts"], resolve_counts=rcounts, web_drops=sg["drops"])
    den = [m for m in meta if m["section"] == "denver"]
    rep["rows"] = dict(total=len(meta), denver=len(den), unconfirmed=sum(1 for m in meta if m["section"] == "unconfirmed"), oedit=sum(1 for m in meta if m["section"] == "oedit"),
                       denver_companies=sum(1 for m in den if m["kind"] == "company"), denver_addresses=sum(1 for m in den if m["kind"] == "address"),
                       denver_50_plus=sum(1 for m in den if m["total"] >= 50), tier=dict(Counter(m["tier"] for m in meta)),
                       denver_sources=dict(Counter(min(m["n_sources"], 4) for m in den)), denver_fit=dict(Counter(m["fit_label"] for m in den)),
                       denver_stage=dict(Counter(m["stage_label"].split(" (")[0] for m in den)), evidence_rows=len(evid_rows), support_rows_not_listed=capped,
                       withheld=sum(1 for r in out_rows if r["site_address"] == WITHHELD),
                       top100_tier=dict(Counter(m["tier"] for m in meta[:100])))
    gc = sg["gcache"]
    need = sg["geocode_needed"]
    rep["geocoder"] = dict(addresses=len(need), results=dict(Counter(gc.get(q, "error") for q in need)))
    gt = {}
    for p in C.GROUND_TRUTH:
        hits = [(m["rank"], h, m["name"][:60], m["addr"][:30], "%.1f" % m["total"]) for m in meta for (pp, h) in m["gt"] if pp == p]
        gt[p] = hits
    rep["ground_truth"] = gt
    rep["top"] = [dict(rank=m["rank"], name=m["name"], addr=m["addr"], score=m["total"], stage=m["stage_label"], tier=m["tier"], r5=m["r5"], r5b=m["r5b"],
                       evidence=out_rows[m["rank"] - 1]["top_evidence"], fit=out_rows[m["rank"] - 1]["compressed_air_fit"], sources=m["n_sources"]) for m in meta[:60]]
    # sensitivity of the Denver top 25
    base25 = [m["label"] for m in den[:25]]
    sens = {}
    for name, P in (("recency doubled", dict(rec=2, src=1, b=1)), ("recency removed", dict(rec=0, src=1, b=1)),
                    ("source bonus doubled", dict(rec=1, src=2, b=1)), ("source bonus removed", dict(rec=1, src=0, b=1)),
                    ("tier B points halved", dict(rec=1, src=1, b=0.5)), ("tier B points doubled", dict(rec=1, src=1, b=2))):
        alt = [(a, sc) for a, sc in rank_accounts(accounts, P) if a.section == "denver"][:25]
        labs = [label_of(a, display(a, sc, extra)) for a, sc in alt]
        sens[name] = dict(changed=len([x for x in labs if x not in base25]), enter=[x for x in labs if x not in base25], leave=[x for x in base25 if x not in labs],
                          top10_same=set(labs[:10]) == set(base25[:10]))
    for a in accounts:
        score(a, BASE)
    rep["sensitivity"] = sens
    # rank changes against the tier B run, with the old and new points lines side by side
    pat = re.compile(r"Points: signal ([\d.]+) \((.*?)\); sources ([\d.]+); recency ([\d.]+); stage ([\d.]+); fit (-?[\d.]+)\s*$")
    old2 = {int(x["rank"]): x for x in rows2}
    moves = []
    for m, row in zip(meta, out_rows):
        if m["r5b"] == "":
            continue
        o = old2[m["r5b"]]
        mm = pat.search(o["top_evidence"])
        oldp = dict(signal=float(mm.group(1)), per=mm.group(2), sources=float(mm.group(3)), recency=float(mm.group(4)), stage=float(mm.group(5)), fit=float(mm.group(6))) if mm else {}
        moves.append(dict(rank=m["rank"], was=m["r5b"], delta=m["r5b"] - m["rank"], name=m["name"], addr=m["addr"], score=m["total"], score_was=float(o["score"]),
                          old_name=o["company_name"], old=oldp, new=dict(signal=sum(b + r for b, r in m["per"].values()), per=row["top_evidence"].rsplit("Points: ", 1)[1],
                                                                         sources=m["sources"], recency=m["recency"], stage=m["stage"], fit=m["fit"]),
                          old_stage=o["stage"], new_stage=m["stage_label"], old_fit=o["compressed_air_fit"][:60], new_fit=row["compressed_air_fit"][:60], section=m["section"]))
    def parse_per(txt):
        d = {}
        for part in (txt or "").split("; "):
            if ": " in part:
                k, v = part.rsplit(": ", 1)
                mm_ = re.match(r"([\d.]+)(?:\+([\d.]+) repeat)?", v)
                if mm_:
                    d[k] = (float(mm_.group(1)), float(mm_.group(2) or 0))
        return d

    for mv in moves:
        o, n = mv["old"], mv["new"]
        if not o:
            mv["what"], mv["cause"] = "", "old points line could not be read"
            continue
        op = parse_per(o["per"])
        np_ = parse_per(n["per"].split("(", 1)[1].split(")", 1)[0] if "(" in n["per"] else "")
        bits, causes = [], []
        for k in sorted(set(op) | set(np_)):
            ob, orp = op.get(k, (0, 0))
            nb, nr = np_.get(k, (0, 0))
            if abs(ob - nb) > 0.01:
                bits.append("%s %s to %s" % (k, g(ob), g(nb)))
            if abs(orp - nr) > 0.01:
                bits.append("%s repeat points %s to %s" % (k, g(orp), g(nr)))
                causes.append("repeat-month points")
        for lab in ("sources", "recency", "stage", "fit"):
            if abs(o[lab] - n[lab]) > 0.01:
                bits.append("%s %s to %s" % (lab, g(o[lab]), g(n[lab])))
        was_addr = mv["old_name"].startswith("Unattached") or mv["old_name"].startswith("Safeway milk")
        is_addr = mv["name"].startswith("Unattached") or mv["name"].startswith("Safeway milk")
        ds = mv["score"] - mv["score_was"]
        if abs(ds) < 0.05:
            cause = "score unchanged; other rows moved around it"
        elif not was_addr and is_addr:
            cause = "was named after a project or possible occupier and scored at half; now an address row at full points"
        elif was_addr and not is_addr:
            cause = "now named from a state permit or equipment filing at the address; address rows score half"
        else:
            diffs = dict(fit=abs(o["fit"] - n["fit"]), stage=abs(o["stage"] - n["stage"]), recency=abs(o["recency"] - n["recency"]), sources=abs(o["sources"] - n["sources"]),
                         signal=abs(o["signal"] - n["signal"]))
            top = max(diffs, key=diffs.get)
            cause = {"fit": "fit rule gives a different class", "stage": "stage rule gives a different stage", "recency": "recency points differ",
                     "sources": "source bonus differs (support rows found or lost)", "signal": "signal points differ"}[top]
            if top == "signal" and "repeat-month points" in causes:
                cause = "repeat-month points (now counted for every row of 12 or more)"
        mv["what"] = "; ".join(bits)
        mv["cause"] = cause
    old_section = {}
    for x in rows2:
        cb = x["county_basis"]
        old_section[int(x["rank"])] = "oedit" if cb.startswith("OEDIT") else "unconfirmed" if cb.startswith(C.COUNTY + " mailing address") else "denver"
    for mv in moves:
        if old_section.get(mv["was"]) != mv["section"]:
            mv["cause"] = "moved between the %s section and the county-unconfirmed section (%s to %s)" % (C.COUNTY, old_section.get(mv["was"]), mv["section"])
    rep["moves"] = moves
    big = [mv for mv in moves if abs(mv["delta"]) > 10]
    rep["moves_over_10"] = dict(count=len(big), by_cause=dict(Counter(mv["cause"] for mv in big)))
    with open(os.path.join(OUT, "rank_changes_v3.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank_v3", "rank_step5b", "places_moved_up", "company_name", "site_address", "score_v3", "score_step5b", "main_cause", "what_changed"])
        for mv in sorted(big, key=lambda m: m["rank"]):
            w.writerow([mv["rank"], mv["was"], mv["delta"], no_emdash(mv["name"]), mv["addr"], "%.1f" % mv["score"], "%.1f" % mv["score_was"], mv["cause"], mv["what"]])
    matched2 = set(m["r5b"] for m in meta if m["r5b"] != "")
    rep["v2_rows_not_in_v3"] = [dict(rank=int(x["rank"]), name=x["company_name"], addr=x["site_address"], score=x["score"], basis=x["county_basis"][:70]) for x in rows2 if int(x["rank"]) not in matched2]
    rep["v3_rows_not_in_v2"] = [dict(rank=m["rank"], name=m["name"], addr=m["addr"], score=m["total"], tier=m["tier"]) for m in meta if m["r5b"] == ""]
    rep["top50_named_without_web_check"] = [dict(rank=m["rank"], name=m["name"]) for m in meta[:50] if m["kind"] == "company" and not m["web"]]
    save_json(os.path.join(OUT, "v3_report.json"), rep)
    print(("ranked %d rows: %d " + C.COUNTY.replace("%", "%%") + " (%d companies, %d addresses), %d county unconfirmed, %d OEDIT; %d evidence rows (%.0fs)") % (
        len(meta), len(den), rep["rows"]["denver_companies"], rep["rows"]["denver_addresses"], rep["rows"]["unconfirmed"], rep["rows"]["oedit"], len(evid_rows), time.time() - t0))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
