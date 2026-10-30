#!/usr/bin/env python3
"""Step 5 v3, part 2: resolution. Builds one account per company or per unattached address, joins address-only
records, and reaches into the full Step 4 files for supporting rows.

Join classes: "confirmed" (name and address agree, or a suite matches, or a Step 3 tie) and "possible"
(same name at another address, or a join by street address alone). Possible rows score half.
"""
import re
from collections import Counter, defaultdict, OrderedDict

from v3_lib import *
import v3_config as C
from v3_signals import sig, shared, fit_sic

ACCOUNT_GRADES = {"operator", "equipment"}


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


class Account:
    def __init__(self, kind):
        self.kind = kind                 # company | address | oedit
        self.names = OrderedDict()       # name key -> display name
        self.sites = {}                  # addr key -> dict(unit, raw, zip, city, grades, section, basis)
        self.sigs = []                   # evidence rows (dicts with cls)
        self.seen = set()
        self.section = "denver"
        self.basis = ""
        self.ak = ""                     # address accounts
        self.occupiers = []              # (display, how)
        self.other_names = []            # names that share the address (listing only)
        self.display = ""
        self.tie_note = ""
        self.step3 = None

    def add(self, s, cls, note=""):
        key = (s["src"], s["rid"], s.get("seq", ""), s["kind"])
        if key in self.seen:
            return False
        self.seen.add(key)
        e = dict(s)
        e["cls"] = cls
        if note:
            e["text"] = s["text"] + " " + note
        self.sigs.append(e)
        return True

    def has_row(self, src, rid, seq=""):
        return any(k[0] == src and k[1] == rid and (not seq or k[2] == seq) for k in self.seen)


def site_of(acct, s, grade=None):
    if not s["ak"]:
        return
    st = acct.sites.setdefault(s["ak"], dict(unit="", raw=s["addr"], zip=s["zip"], city=s["city"], grades=set(), section=s.get("section", "denver"), basis=s.get("basis", "")))
    if not st["unit"] and s["unit"]:
        st["unit"] = s["unit"]
        st["raw"] = s["addr"]
    st["grades"].add(grade or s["grade"])
    if s.get("section") == "denver":
        st["section"] = "denver"


def resolve(sg, S4, log=print):
    named, naming, address, oedit = sg["named"], sg["naming"], sg["address"], sg["oedit"]
    counts = Counter()

    # ------------------------------------------------------------------ entities from named rows
    uf = UF()
    by_ak_names = defaultdict(dict)      # ak -> name key -> unit
    by_filing = defaultdict(list)
    for s in named + naming:
        keys = [k for k in (nk(n) for n in s["names"]) if len(k) >= 3]
        s["keys"] = keys
        for k in keys:
            uf.find(k)
        for k in keys[1:]:
            uf.union(keys[0], k)
        if s["src"] == UCC and keys:
            by_filing[s["rid"]].append(keys[0])
        if s["ak"] and s["grade"] != "project":
            for k in keys[:1]:
                by_ak_names[s["ak"]].setdefault(k, s["unit"])
    for rid, ks in by_filing.items():
        for k in ks[1:]:
            uf.union(ks[0], k)
            counts["merge_co_debtors"] += 1
    for ak, nm in by_ak_names.items():
        ks = sorted(nm)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                if uf.find(ks[i]) != uf.find(ks[j]) and same_company_by_lead(ks[i], ks[j]) and not units_conflict(nm[ks[i]], nm[ks[j]]):
                    uf.union(ks[i], ks[j])
                    counts["merge_same_address_leading_word"] += 1

    ents = {}                             # root -> Account
    for s in named:
        if not s["keys"]:
            continue
        a = ents.setdefault(uf.find(s["keys"][0]), Account("company"))
        for n in s["names"]:
            k = nk(n)
            if len(k) >= 3:
                a.names.setdefault(k, clean_name(n))
        a.add(s, "confirmed")
        site_of(a, s)
    shadow = {}                           # naming-only entities: become accounts only if an address row attaches
    for s in naming:
        if not s["keys"] or s["grade"] == "project":
            continue
        root = uf.find(s["keys"][0])
        a = ents.get(root)
        if a is None:
            a = shadow.setdefault(root, Account("company"))
        for n in s["names"]:
            k = nk(n)
            if len(k) >= 3:
                a.names.setdefault(k, clean_name(n))
        a.add(s, "confirmed")
        site_of(a, s)
    counts["company_entities_with_a_flagged_signal"] = len(ents)

    # a company's rows at an address other than its main site are "possible" (same name, different address)
    for a in ents.values():
        own = [e for e in a.sigs if e["flagged"]]
        best = max(own, key=lambda e: (e["grade"] == "operator", PTS[e["kind"]], e["date"]))
        a.main_ak = best["ak"]
        op_sites = set(e["ak"] for e in a.sigs if e["grade"] == "operator")
        for e in a.sigs:
            if e["ak"] and e["ak"] != a.main_ak and e["src"] in (UCC, REG):
                if e["ak"] not in op_sites:
                    e["cls"] = "possible"
                    e["text"] += " [same name, different address: possible match]"
    for a in shadow.values():
        a.main_ak = a.sigs[0]["ak"]

    # ------------------------------------------------------------------ address-only rows
    site_ix = defaultdict(list)           # ak -> [(account, site)]
    for a in list(ents.values()) + list(shadow.values()):
        for ak, st in a.sites.items():
            if st["grades"] & ACCOUNT_GRADES and st["section"] == "denver":
                site_ix[ak].append((a, st))
    ties = {}
    for t in C.KNOWN_TIES:
        for a in ents.values():
            if t["name_key"] in a.names:
                a.display = t["display"]
                for ak in t["addr_keys"]:
                    ties[ak] = (a, t["note"])
    addr_accts = {}
    promoted = set()
    for s in address:
        ak, u = s["ak"], s["unit"]
        if ak in ties:
            a, note = ties[ak]
            a.add(s, "confirmed", "[%s]" % note)
            site_of(a, s, "tie")
            counts["address_row_to_company_step3_tie"] += 1
            continue
        cands = [(a, st) for a, st in site_ix.get(ak, []) if not units_conflict(u, st["unit"])]
        exact = [(a, st) for a, st in cands if u and st["unit"] == u]
        pick = None
        if len(exact) == 1:
            pick = (exact[0][0], "confirmed")
        elif len(cands) == 1:
            pick = (cands[0][0], "possible")
        if pick and s.get("section", "denver") == "denver":
            a, cls = pick
            a.add(s, cls, "" if cls == "confirmed" else "[joined by street address only] [possible match]")
            counts["address_row_to_company_%s" % cls] += 1
            if id(a) not in promoted and a in shadow.values():
                promoted.add(id(a))
            continue
        a = addr_accts.get(ak)
        if a is None:
            a = addr_accts[ak] = Account("address")
            a.ak = ak
            a.section, a.basis = s.get("section", "denver"), ""
        a.add(s, "confirmed")
        site_of(a, s, "address")
        counts["address_row_to_unattached_address"] += 1
    for root, a in list(shadow.items()):
        if id(a) in promoted:
            ents[root] = a
            a.named_by_state_permit = True
            counts["address_rows_named_by_a_state_permit_operator"] += 1

    # ------------------------------------------------------------------ weak flagged companies at an unattached address: possible occupier, half points
    for root, a in list(ents.items()):
        grades = set(g for st in a.sites.values() for g in st["grades"])
        if grades & ACCOUNT_GRADES or "tie" in grades:
            continue
        if any(e["src"] in (PER, SDP, CRE) for e in a.sigs):
            continue
        if not a.main_ak or a.main_ak not in a.sites:
            continue
        t = addr_accts.get(a.main_ak)
        if t is None or (a.sites[a.main_ak]["section"] != "denver" and t.section == "denver"):
            continue
        cu = a.sites[a.main_ak]["unit"]
        if all(units_conflict(cu, e["unit"]) for e in t.sigs):
            continue
        name = next(iter(a.names.values()))
        for e in a.sigs:
            e2 = dict(e)
            t.add(e2, "possible", "[%s has this address: possible occupier]" % name)
        t.occupiers.append((name, "flagged %s at this address; possible, not confirmed" % ("lien" if any(e["src"] == UCC for e in a.sigs) else "registration")))
        for k, v in a.names.items():
            t.names.setdefault(k, v)
        del ents[root]
        counts["weak_flagged_company_folded_into_address_as_possible_occupier"] += 1

    accounts = list(ents.values()) + list(addr_accts.values())

    # ------------------------------------------------------------------ OEDIT code names
    for s in oedit:
        a = Account("oedit")
        a.names[nk(s["names"][0])] = s["names"][0]
        a.section, a.basis = "oedit", s["basis"]
        a.add(s, "confirmed")
        accounts.append(a)

    # ------------------------------------------------------------------ reach into the full files
    name_ix = {}
    for a in accounts:
        if a.kind == "company":
            for k in a.names:
                if len(k) >= 4:
                    name_ix.setdefault(k, a)
    addr_ix = defaultdict(list)
    for a in accounts:
        if a.kind == "company":
            for ak, st in a.sites.items():
                addr_ix[ak].append(a)
        elif a.kind == "address":
            addr_ix[a.ak].append(a)
    at_addr = defaultdict(dict)           # (ak, zip5) -> name key -> (display, src, row, pts kind)
    kept_ids = set((s["src"], s["rid"]) for s in named + address)

    def note_name(ak, zp, name, src, row):
        k = nk(name)
        if len(k) < 3:
            return
        d = at_addr[(ak, zp)]
        if k not in d or (src == REG and d[k][1] == UCC):
            d[k] = (clean_name(name), src, row)

    # UCC
    for r in reader(S4, UCC):
        if r["transaction_type"] != "Initial Filing" or r["debtor_name_has_entity_token"] != "Y" or "|ucc|" not in r["filing_type_raw"]:
            continue
        k = nk(r["company_name"])
        a = name_ix.get(k)
        ak = None
        if a is not None and not a.has_row(UCC, r["record_id"]):
            ak = addr_key(r["site_address"])
            here = ak in a.sites
            if True:
                sp = r["secured_party"][:50] or "not given"
                hidden = " [lender not named: filed through an agent]" if C.AGENT_LENDER.search(r["secured_party"]) else ""
                tag = "support: generic or blanket lien" if r["flag_v2"] != "Y" else "support: flagged filing that was cut as noise or sits outside the " + C.COUNTY + " test"
                text = "UCC %s initial filing, secured party %s%s: %s (%s)" % (r["record_date"], sp, hidden, r["description"][:80] or "no collateral text", tag)
                s = sig(UCC, r, "ucc_generic", "", text, flagged=False, seq=r["debtor_seq"])
                s["rule"] = ""
                a.add(s, "confirmed" if here else "possible", "" if here else "[same name, different address: possible match]")
        if r["debtor_state"] == "CO":
            if ak is None:
                ak = addr_key(r["site_address"])
            if ak in addr_ix:
                note_name(ak, r["zip"][:5], r["company_name"], UCC, r)
    # registrations
    agent_count = sg["agent_count"]
    for r in reader(S4, REG):
        k = nk(r["company_name"])
        a = name_ix.get(k)
        ak = None
        if a is not None and not a.has_row(REG, r["record_id"]):
            ak = addr_key(r["site_address"])
            here = ak in a.sites
            text = "Registered in Colorado %s (%s); status %s; office %s %s (support: registration under the same name)" % (
                r["record_date"], r["record_type"], r["entity_status"], r["city"].strip(), r["principal_state"])
            s = sig(REG, r, "reg_unflagged", "", text, flagged=False, seq="")
            s["rule"] = ""
            a.add(s, "confirmed" if here else "possible", "" if here else "[same name, different address: possible match]")
        if r["principal_state"] == "CO":
            if ak is None:
                ak = addr_key(r["site_address"])
            if ak in addr_ix and not re.search(r"withdrawn|dissolved|converted|merged", r["entity_status"], re.I):
                if not is_agent_address(r, agent_count):
                    note_name(ak, r["zip"][:5], r["company_name"], REG, r)
    # permits (unflagged, or flagged and cut)
    for r in sg["permits"]:
        if (PER, r["record_id"]) in kept_ids or r["cancel_date"] or r["class"] in C.SKIP_CLASSES:
            continue
        if r["zone_district"] == "DIA" or re.search(r"\bpe[nñ]a\b", r["site_address"], re.I):
            continue
        ak = addr_key(r["site_address"])
        u = unit_of(r["site_address"])
        for a in addr_ix.get(ak, []):
            if a.kind == "company":
                st = a.sites[ak]
                if units_conflict(u, st["unit"]) or st["section"] != "denver":
                    continue
                cls = "confirmed" if (u and st["unit"] == u) else "possible"
                if cls == "possible" and not (st["grades"] & (ACCOUNT_GRADES | {"tie"})):
                    continue      # a registration or lien alone does not put the company at the street address; no suite match, no support
            else:
                cls = "possible"
            text = "Denver permit %s at this address: %s, %s, received %s, parcel class %s (unflagged, or flagged and cut; support)" % (
                r["record_id"], r["class"], money(r["valuation"]), r["record_date"], r["parcel_class"] or "blank")
            s = sig(PER, r, "permit_unflagged", r.get("flag_tier", ""), text, flagged=False)
            a.add(s, cls, "" if cls == "confirmed" else "[possible match]")
    # site plans that are not signals
    for r in sg["sdp"]:
        if (SDP, r["record_id"]) in kept_ids:
            continue
        ak = addr_key(r["site_address"])
        for a in addr_ix.get(ak, []):
            if a.kind == "company" and a.sites[ak]["section"] != "denver":
                continue
            text = "Denver %s %s at this address, opened %s, status %s, zone %s (support: not industrially zoned)" % (
                r["record_type"], r["record_id"], r["record_date"], r.get("status", ""), r.get("zone_district", "") or "blank")
            a.add(sig(SDP, r, "sdp_other", "A", text, flagged=False), "possible", "[possible match]")
    # industrial site plans and flagged permits already used as signals elsewhere are not repeated.
    # water and air rows by name (statewide) or by address (Denver County)
    for src, rows in ((WAT, sg["water"]), (AIR, sg["air"])):
        for r in rows:
            keys = [nk(r["company_name"])]
            if src == WAT and r.get("permittee") and not r["record_type"].startswith(C.CONSTRUCTION_WATER):
                keys.append(nk(r["permittee"]))
            ak = addr_key(r["site_address"])
            done = set()
            in_denver = (r["county"].strip().upper() == C.COUNTY_UP) if src == WAT else r.get("airs_id", "").startswith(C.AIRS_PREFIX)
            for k in keys:
                a = name_ix.get(k) if len(k) >= 4 else None
                if a is not None and id(a) not in done and not a.has_row(src, r["record_id"]):
                    done.add(id(a))
                    here = ak in a.sites and in_denver
                    text = "%s row %s (%s) received %s: %s (not a scoring signal; support only)" % (
                        "Water permit" if src == WAT else "Air permit", r.get("permit_number") or r["record_id"], r["record_type"].split("-")[0].strip()[:28], r["record_date"],
                        (r["company_name"] + ", " + r["city"]).strip(", ")[:70] if src == WAT else r["description"][:70])
                    s = sig(src, r, "noise", "A" if r["flag"] == "Y" else "", text, flagged=False)
                    if src == WAT and here and not r["record_type"].startswith(C.CONSTRUCTION_WATER) and fit_sic(r):
                        s["info"] = dict(sic=fit_sic(r), sic_desc=r.get("sic_description", ""))
                    a.add(s, "confirmed" if here else "possible", "" if here else "[same name, different address: possible match]")
            if in_denver and ak:
                for a in addr_ix.get(ak, []):
                    if id(a) in done or a.has_row(src, r["record_id"]):
                        continue
                    if a.kind == "company" and a.sites[ak]["section"] != "denver":
                        continue
                    what = "project or facility '%s'" % r["company_name"][:60] if src == WAT else "applicant %s" % r["company_name"][:50]
                    text = "%s row %s (%s) received %s at this address: %s (support only)" % (
                        "Water permit" if src == WAT else "Air permit", r.get("permit_number") or r["record_id"], r["record_type"].split("-")[0].strip()[:28], r["record_date"], what)
                    s = sig(src, r, "noise", "A" if r["flag"] == "Y" else "", text, flagged=False)
                    if src == WAT:
                        s["info"] = dict(project=r["company_name"], activity=r.get("construction_activity", ""))
                    a.add(s, "possible", "[joined by street address only] [possible match]")
    # press: address mentions and name mentions
    name_keys = [(k, a) for k, a in name_ix.items() if (len(k.split()) >= 2 or len(k) >= 8) and a.kind == "company"]
    for r in sg["cre"]:
        city = r["city"].strip().upper()
        head = r["description"].split(" | ")[0]
        addrs = [(r["site_address"], city == "" or city in C.CITY_OK)]
        for part in (r.get("addresses_all") or "").split(";"):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"^(.*?),\s*([A-Za-z .]+)$", part)
            if m:
                addrs.append((m.group(1), m.group(2).strip().upper() in C.CITY_OK))
            else:
                addrs.append((part, city == "" or city in C.CITY_OK))
        hit = set()
        for adr, ok in addrs:
            ak = addr_key(adr)
            if not ak or not ok:
                continue
            for a in addr_ix.get(ak, []):
                if id(a) in hit or a.has_row(CRE, r["record_id"]):
                    continue
                if a.kind == "company" and a.sites[ak]["section"] != "denver":
                    continue
                hit.add(id(a))
                text = "Mile High CRE %s mentions this address: %s" % (r["record_date"], head[:100])
                a.add(sig(CRE, r, "press_addr", "A" if r["flag"] == "Y" else "", text, flagged=False), "possible", "[possible match]")
        if city == "" or city in C.CITY_OK:
            hn = " " + nk(head + " " + r["company_name"]) + " "
            for k, a in name_keys:
                if (" " + k + " ") in hn and id(a) not in hit and not a.has_row(CRE, r["record_id"]):
                    hit.add(id(a))
                    text = "Mile High CRE %s names the company: %s" % (r["record_date"], head[:100])
                    a.add(sig(CRE, r, "press_name", "A" if r["flag"] == "Y" else "", text, flagged=False), "possible", "[name match only] [possible match]")

    # ------------------------------------------------------------------ names that share an address (listing; one name alone is a possible occupier)
    site_keys = set(sg["layer_keys"])
    for rows in (sg["water"], sg["air"]):
        for r in rows:
            k = addr_key(r["site_address"])
            if k:
                site_keys.add(k)
    for r in sg["cre"]:
        for adr in [r["site_address"]] + (r.get("addresses_all") or "").split(";"):
            k = addr_key(adr.split(",")[0])
            if k:
                site_keys.add(k)
    for a in accounts:
        if a.kind != "address":
            continue
        zips = set(e["zip"] for e in a.sigs if e["zip"])
        pool = {}
        for (ak, zp), d in at_addr.items():
            if ak == a.ak and (not zips or not zp or zp in zips):
                for k, v in d.items():
                    pool.setdefault(k, v)
        for k in list(pool):
            if k in a.names:
                del pool[k]
        a.other_names = sorted(v[0] for v in pool.values())
        if len(pool) == 1 and not a.occupiers:
            k, (disp, src, row) = next(iter(pool.items()))
            if src == REG:
                text = "Registered in Colorado %s (%s); status %s; office at this address (support: one registration at the address; possible occupier %s)" % (row["record_date"], row["record_type"], row["entity_status"], disp)
                s = sig(REG, row, "reg_unflagged", row.get("flag_tier", ""), text, flagged=False, seq="")
            else:
                text = "UCC %s initial filing by a debtor at this address (support: possible occupier %s)" % (row["record_date"], disp)
                s = sig(UCC, row, "ucc_generic", row.get("flag_tier", ""), text, flagged=False, seq=row["debtor_seq"])
            a.add(s, "possible", "[possible match]")
            a.occupiers.append((disp, "%s at this address; possible, not confirmed" % ("business registration" if src == REG else "UCC debtor")))
            a.other_names = []
            counts["address_with_one_unflagged_name_as_possible_occupier"] += 1

    # ------------------------------------------------------------------ section and county basis
    for a in accounts:
        if a.kind == "company":
            srcs = set(e["src"] for e in a.sigs if e["cls"] == "confirmed" or e["src"] in (PER, SDP))
            air = [e for e in a.sigs if e["src"] == AIR and e.get("basis", "").startswith("AIRS")]
            wat = [e for e in a.sigs if e["src"] == WAT and e.get("basis", "").startswith("county field")]
            own = [e for e in a.sigs if e["src"] in (UCC, REG) and e["flagged"]]
            den = [e for e in own if e["section"] == "denver"]
            clash = [e for e in own if e["section"] == "unconfirmed" and "geocoder places it in" in e["basis"] and any(w["ak"] == e["ak"] for w in wat)]
            if air:
                a.section, a.basis = "denver", air[0]["basis"]
            elif wat and clash and not den:
                county = re.search(r"places it in ([A-Za-z ]+ County)", clash[0]["basis"]).group(1)
                a.section = "unconfirmed"
                a.basis = "%s mailing address, county unconfirmed (sources disagree: the water permit county field says %s, the Census geocoder places the address in %s)" % (C.COUNTY, C.COUNTY, county)
            elif wat:
                a.section, a.basis = "denver", wat[0]["basis"]
            elif den:
                best = max(den, key=lambda e: (e["ak"] == a.main_ak, e["date"]))
                a.section, a.basis = "denver", best["basis"]
            elif own:
                best = max(own, key=lambda e: (e["ak"] == a.main_ak, e["date"]))
                a.section, a.basis = best["section"], best["basis"]
            else:
                a.section, a.basis = "denver", "Denver permit layer (Denver only)"
        elif a.kind == "address":
            layer = [e for e in a.sigs if e["src"] in (PER, SDP) and e["flagged"]]
            if layer:
                a.section = "denver"
                a.basis = "Denver permit layer (Denver only)" if any(e["src"] == PER for e in layer) else "Denver site plan layer (Denver only)"
            else:
                e = [e for e in a.sigs if e["src"] == CRE and e["flagged"]][0]
                a.section, a.basis = e["section"], e["basis"]
        if a.kind == "address" and a.ak in C.STEP3_OCCUPIERS:
            a.step3 = C.STEP3_OCCUPIERS[a.ak]

    counts["accounts_company"] = sum(1 for a in accounts if a.kind == "company")
    counts["accounts_address"] = sum(1 for a in accounts if a.kind == "address")
    counts["accounts_oedit"] = sum(1 for a in accounts if a.kind == "oedit")
    return accounts, dict(counts), dict(site_keys=site_keys, at_addr=at_addr)
