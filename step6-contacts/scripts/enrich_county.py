"""Step 6: contact enrichment for one county's ranked list, by rule.
Usage (repo root): python3 -I step6-contacts/scripts/enrich_county.py <County> <ranked.csv> <evidence.csv> <wq_cache.json> <out.csv> [N] [overrides.json]
Permit contact role and organisation come from the WQCD sheet cache (wq_cache.py, no personal fields).
Contractors come from construction stormwater permits (permittee and property owner organisation).
Phones are never looked up here: they come from overrides.json, typed in after a check of the company's own website."""
import csv, json, re, sys
csv.field_size_limit(10**9)
county, ranked_f, ev_f, wq_f, out_f = sys.argv[1:6]
N = int(sys.argv[6]) if len(sys.argv) > 6 else 25
OV = json.load(open(sys.argv[7])) if len(sys.argv) > 7 else {}
COLS = ["rank","company_name","site_address","zip","match_confidence","site_phone","phone_type","phone_source_url","phone_checked_date","permit_contact_role","permit_contact_org","permit_contact_relation","permit_contact_source","contractors","contractor_roles","contractor_sources","coverage_note","zoominfo_name","zoominfo_title","zoominfo_phone","zoominfo_email","call_notes"]
ENT = {"INC","LLC","CORP","CORPORATION","CO","COMPANY","LTD","LP","LLP","THE","OF","US","USA"}
BIZ = re.compile(r"\b(inc|llc|l\.l\.c|corp|corporation|co|company|ltd|lp|llp|district|city|county|town|group|partners|construction|constructors|contracting|contractors|builders|properties|holdings|development|developers|industries|services|civil|excavating|homes|foods|mills|technologies|international|authority|trust|ventures|capital|enterprises|associates|logistics|realty|investments|materials|paving|concrete|energy|electric|utilities|school|university|airport|railroad|railway|bank)\b", re.I)
def nkey(s, n=2):
    w = [x for x in re.sub(r"[^A-Z0-9 ]", " ", s.upper().replace("&", " ")).split() if x not in ENT]
    return " ".join(w[:n])
def akey(s):
    m = re.match(r"\s*(\d+)\s+(?:[NSEW]\.?\s+)?(?:(?:NORTH|SOUTH|EAST|WEST)\s+)?(?:(?:COUNTY ROAD|COUNTY RD|HIGHWAY|HWY|WCR|CR)\s+)?([A-Z0-9]+)", s.upper())
    if not m: return None
    return (m.group(1), re.sub(r"(ST|ND|RD|TH)$", "", m.group(2)) if m.group(2)[0].isdigit() else m.group(2))
ranked = list(csv.DictReader(open(ranked_f, encoding="utf-8-sig")))[:N]
ev = [e for e in csv.DictReader(open(ev_f, encoding="utf-8-sig")) if e["rank"].isdigit() and int(e["rank"]) <= N]
wq = json.load(open(wq_f))
apcd = {r["record_id"]: r for r in csv.DictReader(open("step4-scrape/scrape_apcd_permit_status.csv", encoding="utf-8-sig"))}
wq_addr = {}
for w in wq:
    k = akey(w["FacilityAddress1"])
    if k: wq_addr.setdefault(k, []).append(w)
CONSTR = ("COR400", "COG080", "COG317", "COG318", "COG604", "COG608")
def is_constr(w): return w["GeneralPermitType"].upper().startswith(CONSTR) or w["PermitID"].upper().startswith(CONSTR)
def in_county(w): return w["FacilityCounty"].strip().upper() == county.upper()
def title(c): return c[2].strip()
GENERIC = {"PLANT","DENVER","AURORA","THORNTON","COLORADO","MANUFACTURING","CAMPUS","PRODUCTS","INDUSTRIES","SERVICES","INTERNATIONAL","TECHNOLOGIES","FOODS","NORTH","AMERICAN","WELD","COUNTY","FREDERICK","GREELEY","OCCUPIER","NAMED","STEP","RECORD","PRECISION","MATERIALS","STEEL","ENTERPRISES","EAST","WEST"}
def toks(s): return {x for x in re.sub(r"[^A-Z0-9 ]", " ", s.upper()).split() if len(x) >= 4 and x not in ENT and x not in GENERIC}
def same_city(a, b):
    a, b = re.sub(r"[^A-Z]", "", a.upper()), re.sub(r"[^A-Z]", "", b.upper())
    return bool(a) and (a == b or (len(a) > 5 and a[:4] == b[:4] and abs(len(a) - len(b)) <= 1))
PREF = ("COR9", "CONOX", "CO00", "COPB", "COG5")
def pref(w): return next((i for i, x in enumerate(PREF) if w["PermitID"].upper().startswith(x)), len(PREF))
def fmt(c, fac_city, label):
    loc = "" if same_city(c[3], fac_city) or not c[3].strip() else f", {c[3].strip().title()} {c[4].strip()}"
    return f"{title(c)} ({label}{loc})"
LABEL = {"Legal": "legal contact", "FacilityContact": "facility contact", "Compliance": "compliance contact", "Environmental": "environmental contact", "Stormwater": "stormwater contact", "Consultant": "consultant", "DMR": "reporting contact", "Operator": "operator contact", "PropertyOwner": "property owner contact", "Pretreatment": "pretreatment contact", "Inspection": "inspection contact", "Engineering": "engineering contact", "Other": "other contact"}
out, review = [], []
for r in ranked:
    k = int(r["rank"]); name = r["company_name"]; unatt = name.startswith("Unattached address")
    evs = [e for e in ev if int(e["rank"]) == k]
    keys = {akey(r["site_address"])} | {akey(e["site_address"]) for e in evs if not e["source"].startswith(("Colorado UCC", "Colorado business", "Mile High"))}
    keys.discard(None)
    names = set() if unatt else {nkey(x) for x in [re.sub(r"\(.*", "", name).split(",")[0]] + r.get("name_variants", "").split("|") if len(nkey(x)) >= 6}
    ev_ids = {e["record_id"] for e in evs if e["source"].startswith("State water")}
    ntok = toks(name + " " + r.get("name_variants", ""))
    def same_biz(w, how="addr", extra=""): return how == "evidence" or bool(ntok & toks(w["Permittee"] + " " + w["FacilityName"] + " " + extra))
    hits = {}
    for a in keys:
        for w in wq_addr.get(a, []):
            if in_county(w) or (r["zip"] and w["FacilityZip"][:5] == r["zip"]): hits[w["PermitID"]] = (w, "addr")
    for w in wq:
        if w["PermitID"] in ev_ids: hits.setdefault(w["PermitID"], (w, "evidence"))
    hl = sorted(hits.values(), key=lambda x: x[0]["ApplicationReceivedDate"], reverse=True)
    oper = [h for h in hl if not is_constr(h[0])]; con = [h for h in hl if is_constr(h[0])]
    live = [h for h in oper if h[0]["PermitStatus"] in ("Effective", "Admin continued", "Pending")]
    role = org = rel = src = ""; notes = []
    pool = sorted(live or oper, key=lambda h: pref(h[0]))
    pick = pool[0] if pool else None
    if pick and not unatt and not OV.get(str(k), {}).get("accept_permit") and not same_biz(pick[0], pick[1], " ".join(c[1] for c in pick[0]["c"])):
        notes.append(f"A water permit at this address ({pick[0]['PermitID']}) is held by {pick[0]['Permittee'].strip()}, which does not match this company by name, so its contact was not used.")
        pick = None; other_holder = True
    else: other_holder = False
    if pick:
        w = pick[0]; cs = w["c"]; seen = []; parts = []
        for b in ("FacilityContact", "Legal", "Compliance", "Environmental", "Stormwater", "Operator", "Consultant"):
            for c in cs:
                if c[0] == b and title(c) and title(c).upper() not in seen:
                    seen.append(title(c).upper()); parts.append(fmt(c, w["FacilityCity"], LABEL[b]))
        fc = [c for c in cs if c[0] in ("FacilityContact", "Legal", "Compliance", "Environmental") and title(c)]
        role = "; ".join(parts[:3]); org = next((c[1] for c in cs if c[0] == "FacilityContact" and c[1]), w["Permittee"]); src = "wqcd_sheet:" + w["PermitID"]
        if role:
            local = any(same_city(c[3], w["FacilityCity"]) or re.search(r"plant|site|facility", title(c), re.I) for c in fc)
            cons_only = all(c[0] == "Consultant" for c in cs if title(c))
            rel = "third_party" if cons_only else ("on_site" if local else "unknown")
            if w["PermitStatus"] not in ("Effective", "Admin continued", "Pending"): notes.append(f"Permit contact comes from a permit that is {w['PermitStatus'].lower()} (received {w['ApplicationReceivedDate'][:4]}), so treat the role as a guide, not as current.")
            elif w["ApplicationReceivedDate"][:4] < "2023": notes.append(f"Permit contact dates from a {w['ApplicationReceivedDate'][:4]} application; the role may have changed hands.")
            if rel == "unknown": notes.append("Contact is a company employee listed at another city, so not marked on-site.")
        else: org = src = ""
    cl = []
    for w, how in con[:4]:
        p = w["Permittee"].strip(); own = next((c[1].strip() for c in w["c"] if c[0] == "PropertyOwner" and c[1].strip()), "")
        st = f"{w['PermitStatus'].lower()}, received {w['ApplicationReceivedDate'][:7]}"
        proj = w["FacilityName"].strip().replace(";", ",")
        if p and not unatt and ntok & toks(p):
            notes.append(f"The company holds its own construction stormwater permit {w['PermitID']} for '{proj}' ({st}): a sign of site work, but it names no contractor.")
        elif p and BIZ.search(p) and p.upper() not in [x[0].upper() for x in cl]:
            cl.append((p.replace(";", ","), f"construction stormwater permittee for '{proj}' ({st})", "wqcd_sheet:" + w["PermitID"]))
        if own and BIZ.search(own) and nkey(own) != nkey(p) and not (ntok & toks(own)) and own.upper() not in [x[0].upper() for x in cl]:
            cl.append((own.replace(";", ","), f"property owner on the construction stormwater permit for '{proj}'", "wqcd_sheet:" + w["PermitID"]))
    if not role and con:
        w = con[0][0]; c = next((c for c in w["c"] if c[0] == "FacilityContact" and title(c)), None)
        if c and not unatt and ntok & toks(c[1] or w["Permittee"]):
            role = fmt(c, w["FacilityCity"], "facility contact on the company's own construction permit"); org = c[1] or w["Permittee"]; src = "wqcd_sheet:" + w["PermitID"]
            rel = "on_site" if same_city(c[3], w["FacilityCity"]) else "unknown"
            if rel == "unknown": notes.append("Contact is a company employee listed at another city, so not marked on-site.")
            c = None
        if c and BIZ.search(c[1] or w["Permittee"]) and (unatt or not (ntok & toks(c[1] or w["Permittee"]))):
            role = fmt(c, w["FacilityCity"], "facility contact on the construction permit"); org = c[1] or w["Permittee"]; rel = "third_party"; src = "wqcd_sheet:" + w["PermitID"]
            notes.append("Only a construction permit exists here, so the permit contact is the contractor's, not the plant's.")
    ap = sorted({f"{apcd[e['record_id']]['permit_number']} (AIRS {apcd[e['record_id']]['airs_id']})" for e in evs if e["source"].startswith("APCD") and e["record_id"] in apcd})
    if ap: notes.append("APCD documents not reached (the records viewer needs a real browser); look up by hand: " + ", ".join(ap[:4]) + ".")
    if not role and not other_holder: notes.append("No state water permit record matched this " + ("address" if unatt else "company and address") + ", so no permit contact.")
    if not cl: notes.append("No contractor found: no construction stormwater permit matched, and the county permit files carry no contractor.")
    o = OV.get(str(k), {})
    if unatt: pn = "Phone lookup skipped: address with no attached company."
    elif o.get("phone"): pn = o.get("phone_note", "Phone from the company's own website.")
    else: pn = o.get("phone_note", "Phone not checked: the company website could not be opened (page fetches needed an approval that was not answered).")
    mc = "" if unatt and "possible occupier" not in name else ("confirmed" if r["match_confidence"].startswith(("confirmed", "address confirmed; occ")) or pick and not unatt else "possible")
    if unatt and "possible occupier" in name: mc = "possible"
    row = dict.fromkeys(COLS, ""); row.update(rank=k, company_name=name, site_address=o.get("addr", r["site_address"]), zip=r["zip"], match_confidence=mc,
        site_phone=o.get("phone", ""), phone_type=o.get("ptype", ""), phone_source_url=o.get("purl", ""), phone_checked_date=o.get("checked", ""),
        permit_contact_role=role, permit_contact_org=org, permit_contact_relation=rel, permit_contact_source=src,
        contractors="; ".join(c[0] for c in cl), contractor_roles="; ".join(c[1] for c in cl), contractor_sources="; ".join(c[2] for c in cl),
        coverage_note=" ".join([pn] + notes + ([o["note"]] if o.get("note") else [])))
    for f in o.get("blank", []): row[f] = ""
    out.append(row)
    review.append(f"{k} {name[:34]} | {rel or '-'} | {role[:95]} | {org[:30]} | {src} | con: {'; '.join(c[0][:28] for c in cl)} | hits: {' '.join(h[0]['PermitID'] + ':' + h[1][0] for h in hl[:7])}")
with open(out_f, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(out)
print("\n".join(review))
c = lambda fn: sum(1 for o in out if fn(o))
print("COUNTS rows", len(out), "| site", c(lambda o: o["phone_type"] == "site"), "hq_only", c(lambda o: o["phone_type"] == "hq_only"), "none_found", c(lambda o: o["phone_type"] == "none_found"), "skipped", c(lambda o: o["coverage_note"].startswith("Phone lookup skipped")), "not checked", c(lambda o: o["coverage_note"].startswith("Phone not checked")),
      "| permit contact", c(lambda o: o["permit_contact_role"]), "on_site", c(lambda o: o["permit_contact_relation"] == "on_site"), "third_party", c(lambda o: o["permit_contact_relation"] == "third_party"), "unknown", c(lambda o: o["permit_contact_relation"] == "unknown"), "| contractor", c(lambda o: o["contractors"]))
