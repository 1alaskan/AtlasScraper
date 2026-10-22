#!/usr/bin/env python3
"""Colorado UCC filings (data.colorado.gov) -> scrape_ucc_filings.csv

Tables (confirmed from /api/views/<id>.json metadata):
  wffy-3uut  filing         (one row per filed document; fileid is the join key, transactionid the filing number)
  8upq-58vz  debtor
  4am6-w6u4  collateral
  ap62-sav4  secured party

Usage:  python3 pull_ucc_filings.py            # fetch (resumes from cache) then build
        python3 pull_ucc_filings.py --build    # rebuild CSV from cached raw pages only
To refresh from scratch delete raw/ucc_* first. Parser version 1.0.

Personal data rules, applied at the request:
  debtor:        $where organizationname IS NOT NULL AND lastname IS NULL AND firstname IS NULL
                 (individual debtor rows are never retrieved; name fields are not in $select)
  secured party: same $where; address fields not selected. A filing whose only secured parties are
                 individuals gets a blank secured_party.
Amendments carry no debtor/collateral/secured-party rows of their own unless they change them, so an
amendment inherits the organisation debtors, collateral and secured parties of its master initial filing
(masterdocumentid -> the filing whose transactionid equals it). That is why the whole filing table and the
whole organisation-debtor, organisation-secured-party and collateral tables are pulled, not only 2024 onward.
"""
import csv, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import soda_fetch as s

SINCE = "2024-01-01"
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "scrape_ucc_filings.csv")
SUMMARY = os.path.join(HERE, "summary_ucc_filings.md")
ORG = "organizationname IS NOT NULL AND lastname IS NULL AND firstname IS NULL"
JOBS = [
 ("ucc_filing", "wffy-3uut", "fileid",
  "fileid,transactionid,masterdocumentid,transactiontype,filingdate,lapsedate,filingtype,documenttype,continuation,terminationflag,financialstatementtype,manufacturedhometransactions", ""),
 ("ucc_debtor_org", "8upq-58vz", "debtorid",
  "debtorid,fileid,actiontype,recordstatus,debtordescription,organizationname,organizationjurisdiction,organizationtype,address1,address2,city,state,country,zipcode", ORG),
 ("ucc_secured_org", "ap62-sav4", "spid", "spid,fileid,actiontype,recordstatus,organizationname,assignor", ORG),
 ("ucc_collateral", "4am6-w6u4", "collateralid",
  "collateralid,fileid,actiontype,recordstatus,farmproductflag,collateraldescription,county,additionalcollateraldescription", ""),
]

# Filing types whose collateral free text describes a named person (patient, injury, home address).
# For these the free text is withheld; only the source's collateral category is kept.
WITHHOLD_TEXT = {"lien_hosp", "lien_othr_stat"}   # lien_hosp rows are left out altogether (see probable_individual)

# label -> regex body. Order = order used in flag_rule (first three matches are listed).
WORDS = [
 ("compressed air", r"compressed[\s-]air"), ("compressor", r"(?:air[\s-]?)?compressors?"),
 ("air dryer", r"air[\s-]dryers?"),
 ("atlas copco", r"atlas[\s-]?copco"), ("ingersoll rand", r"ingersoll[\s-]?rand"), ("kaeser", r"kaeser"),
 ("sullair", r"sullair"), ("quincy", r"quincy\b(?=.{0,60}\b(?:compressors?|air|qgs|qgd|qsi|qt|qr|qp)\b)"),
 ("gardner denver", r"gardner[\s-]?denver"),
 ("cnc", r"cnc"), ("lathe", r"lathes?"), ("milling machine", r"milling\s+machines?"),
 ("machining center", r"machining\s+cent(?:er|re)s?"), ("press brake", r"press[\s-]?brakes?"),
 ("stamping press", r"stamping\s+press(?:es)?"), ("hydraulic press", r"hydraulic\s+press(?:es)?"),
 ("punch press", r"punch\s+press(?:es)?"), ("extruder", r"extruders?"), ("extrusion", r"extrusions?"),
 ("injection mold", r"injection[\s-]mou?ld(?:ing|er|ers)?"), ("molding machine", r"mou?lding\s+machines?"),
 ("blow mold", r"blow[\s-]?mou?ld(?:ing|er|ers)?"), ("bottling", r"bottling"),
 ("canning line", r"canning\s+(?:line|machine|system)s?"), ("filling line", r"filling\s+(?:line|machine)s?"),
 ("packaging line", r"packaging\s+lines?"), ("packaging machine", r"packaging\s+(?:machine|machinery|equipment)s?"),
 ("boiler", r"boilers?"), ("chiller", r"chillers?"),
 ("laser cutter", r"laser\s+cutt(?:er|ers|ing)|fiber\s+laser"), ("plasma cutter", r"plasma\s+(?:cutt(?:er|ers|ing)|table)"),
 ("waterjet", r"water[\s-]?jets?"), ("welding robot", r"welding\s+robots?|robotic\s+weld(?:er|ers|ing)?"),
 ("welder", r"welders?"), ("robot", r"robots?|robotics?"), ("conveyor", r"conveyors?"),
 ("brewhouse", r"brew[\s-]?house"), ("fermenter", r"ferment[eo]rs?"), ("kiln", r"kilns?"),
 ("furnace", r"furnaces?"), ("sandblast", r"sand[\s-]?blast(?:er|ers|ing)?"),
 ("powder coat", r"powder[\s-]?coat(?:ing|er)?"), ("paint booth", r"paint\s+booths?"), ("pneumatic", r"pneumatics?"),
 ("haas", r"haas"), ("mazak", r"mazak"), ("dmg mori", r"dmg[\s-]?mori"), ("okuma", r"okuma"),
 ("trumpf", r"trumpf"), ("amada", r"amada"), ("doosan", r"doosan"), ("fanuc", r"fanuc"),
]
WORD_RE = [(lab, re.compile(r"\b(?:%s)\b" % body, re.I)) for lab, body in WORDS]
# Building-services words that also sit in real-estate fixture boilerplate ("all boilers, furnaces, plumbing,
# elevators ..."). When 2 or more boilerplate markers are present these words do not count toward the flag;
# they are listed in boilerplate_suppressed instead.
SOFT = {"boiler", "furnace", "chiller", "compressor", "conveyor", "pneumatic"}
MARKERS = [re.compile(p, re.I) for p in (
 r"\bplumbing\b", r"\bair[\s-]condition", r"\belevators?\b", r"\bawnings?\b", r"\bcarpet", r"\brefrigerators?\b",
 r"\bsinks?\b", r"\bbath\s?tubs?\b", r"\bincinerat", r"\bsprinkler", r"\bwater\s+heaters?\b", r"\bdishwashers?\b",
 r"\bwater\s+closets?\b", r"\bstoves?\b", r"\bshades\b", r"\bscreens\b", r"\bboilerplate\b", r"\bventilating\b",
 r"\breal\s+property\b", r"\breal\s+estate\b")]
ENTITY_TOKEN = re.compile(r"\b(?:llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|limited|lp|llp|lllp|pllc|pc|p\.c|"
    r"trust|bank|association|assn|assoc|foundation|church|ministr\w+|district|city|county|town|state|department|dept|"
    r"partners|partnership|group|holdings|enterprises|services|service|solutions|construction|farms?|ranch|ranches|"
    r"cattle|dairy|company|llc\.|clinic|center|centre|school|university|college|club|society|cooperative|co-op|"
    r"authority|properties|investments|management|restaurant|cafe|brewing|brewery|trucking|transport\w*|logistics|"
    r"systems|industries|manufacturing|plumbing|electric|roofing|landscap\w+|dental|medical|health|homes|builders|"
    r"contractors?|consulting|associates|ventures|capital|energy|oil|gas|mining|supply|motors|auto|automotive|"
    r"equipment|rentals?|excavat\w+|concrete|design|studio|market|store|shop|salon|fitness|pharmacy|hospital|"
    r"hoa|estate|dba|d/b/a|usa|america|american|colorado|denver|international|global|national|the|and|of|&)\b|[&0-9]", re.I)

# Probable individuals typed into the organisation-name field. The debtor table has no reliable person/organisation
# marker beyond which name field is filled, and some filers put a person's name in organizationname.
# Those rows are left out. The rules need no personal fields from the API.
FIRSTNAMES = set('james john robert michael william david richard joseph thomas charles christopher daniel matthew anthony mark donald steven steve paul andrew joshua kenneth kevin brian george edward ronald timothy jason jeffrey jeff ryan jacob gary nicholas eric jonathan stephen larry justin scott brandon benjamin samuel gregory greg frank alexander raymond patrick jack dennis jerry tyler aaron jose adam henry nathan douglas doug zachary peter kyle walter ethan jeremy harold keith christian roger noah gerald carl terry sean austin arthur lawrence jesse dylan bryan joe jordan billy bruce albert willie gabriel logan alan juan wayne roy ralph randy eugene vincent russell elijah louis bobby philip phillip johnny bradley brad shawn travis todd craig chad derek dustin marcus luis carlos jared troy curtis corey cory cody clint clinton darrell darren dale dean glenn glen gordon harvey herbert howard ivan jay jim jimmy joel jon karl kirk kurt lance lee leonard leroy lloyd luke marvin melvin mike mitchell neil norman oscar perry randall ricky rick rodney ron ross shane stanley stuart ted theodore tim tom tommy tony trevor victor wade warren wesley herschel aden jerold miguel jesus manuel pedro francisco javier ricardo jorge mario antonio alejandro fernando roberto eduardo sergio raul hector rafael ruben armando alberto arturo enrique ramon salvador guillermo mary patricia jennifer linda elizabeth barbara susan jessica sarah karen lisa nancy betty margaret sandra ashley kimberly emily donna michelle carol amanda dorothy melissa deborah debra stephanie rebecca sharon laura cynthia kathleen amy angela shirley anna brenda pamela emma nicole helen samantha katherine christine debbie rachel carolyn janet catherine maria heather diane ruth julie olivia joyce virginia victoria kelly lauren christina joan evelyn judith megan andrea cheryl hannah jacqueline martha gloria teresa ann sara madison frances kathryn janice jean abigail alice judy sophia grace denise amber doris marilyn danielle beverly isabella theresa diana natalie brittany charlotte marie kayla alexis lori tammy tina tracy wendy cindy dawn kim kristin kristen kristina crystal erin erica jamie jill joanne kathy katie kay leslie lindsay lindsey lynn monica peggy renee rhonda robin rose sally sheila sherry stacy stacey sue suzanne tara terri valerie vanessa veronica vicki wanda yvonne valeda cristina maggie connie bonnie paula gail carla becky rita ana rosa guadalupe juana leticia claudia adriana gabriela'.split())
_STRIP = re.compile(r"\b(?:the|estate|of|trust|revocable|irrevocable|living|family|dated|dtd|jr|sr|ii|iii|iv|dds|dmd|md|do|dc|cpa|dvm|od|phd|esq)\b\.?", re.I)
_COMMA = re.compile(r"^[A-Za-z' -]+,\s*[A-Za-z'-]+(?:\s+[A-Za-z]\.?|\s+[A-Za-z'-]+)?$")
_PERSONAL_DESC = re.compile(r"trust|decedent|estate", re.I)


def probable_individual(name, debtor_desc, ftype):
    """Return the rule name if the organisation-field value looks like a private individual, else ''."""
    if ftype == "lien_hosp":
        return "hospital lien (record about a patient)"
    if re.search(r"\bsole\s+prop(?:rietor)?\b|\bin (?:his|her) official capacity\b|\ban individual\b", name, re.I):
        return "sole proprietor / named person wording"
    core = ws(_STRIP.sub(" ", re.sub(r"\b(?:d\.d\.s|m\.d|d\.o|d\.m\.d|ph\.d|dr)\b\.?", " ", name, flags=re.I))).strip(" ,.")
    if not core or ENTITY_TOKEN.search(core):
        return ""
    if re.fullmatch(r"[A-Za-z'-]+ [A-Za-z]\.? [A-Za-z'-]+", core):
        return "given name, middle initial, surname pattern"
    if _COMMA.match(core):
        return "SURNAME, GIVEN pattern"
    toks = re.findall(r"[A-Za-z'-]+", core)
    alpha = len(toks) >= 2 and len(toks) <= 4 and re.fullmatch(r"[A-Za-z' .:;-]+", core) is not None
    if alpha and toks[0].lower().strip("-':") in FIRSTNAMES:
        return "given name first, no entity word"
    if alpha and _PERSONAL_DESC.search(debtor_desc or ""):
        return "trust/estate debtor description, no entity word"
    return ""

SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

COLS = ["source", "source_level", "record_id", "record_date", "date_type", "record_type", "company_name",
        "company_role", "site_address", "city", "county", "zip", "description", "flag", "flag_rule",
        "source_url", "retrieved_at",
        "secured_party", "debtor_state", "filing_type_raw", "debtor_seq",
        "transaction_type", "master_document_id", "lapse_date", "financial_statement_type", "fileid",
        "debtor_country", "debtor_org_type", "debtor_jurisdiction", "debtor_description", "debtor_record_status",
        "debtor_source", "collateral_source", "secured_party_source", "collateral_category", "collateral_county",
        "collateral_text_len", "boilerplate_suppressed", "debtor_name_has_entity_token"]


def ws(x):
    return re.sub(r"\s+", " ", x or "").strip()


def match(text):
    hits = [lab for lab, rx in WORD_RE if rx.search(text)]
    # drop generic labels subsumed by a more specific one
    if "welding robot" in hits:
        hits = [h for h in hits if h not in ("welder", "robot") or
                re.search(r"\b(?:robots?|robotics?|welders?)\b", re.sub(r"welding\s+robots?|robotic\s+weld\w*", " ", text, flags=re.I), re.I)]
    supp = []
    if any(h in SOFT for h in hits) and sum(1 for m in MARKERS if m.search(text)) >= 2:
        supp = [h for h in hits if h in SOFT]
        hits = [h for h in hits if h not in SOFT]
    return hits, supp


def keep_org(rows, ftype, stats):
    out = []
    for d in rows or []:
        why = probable_individual(ws(d["organizationname"]), d["debtordescription"], ftype)
        if why:
            stats["debtor_rows_left_out_probable_individual: " + why] += 1
        else:
            out.append(d)
    return out


def build():
    # 1. filings: every row kept in a light map for master lookup; in-scope rows kept in full
    tx2file = {}; scope = []
    for r, ts in s.rows(os.path.join(RAW, "ucc_filing")):
        if r["transactionid"] == r["masterdocumentid"] or r["transactiontype"] == "Initial Filing":
            tx2file[r["transactionid"]] = r["fileid"]
        if r["filingdate"][:10] >= SINCE:
            scope.append((r, ts))
    need = set(); master_of = {}
    for r, _ in scope:
        need.add(r["fileid"])
        if r["transactionid"] != r["masterdocumentid"]:
            m = tx2file.get(r["masterdocumentid"])
            if m:
                master_of[r["fileid"]] = m; need.add(m)
    print("in-scope filings", len(scope), "fileids needed", len(need), flush=True)
    # 2. organisation debtors
    debt = defaultdict(list)
    for r, _ in s.rows(os.path.join(RAW, "ucc_debtor_org")):
        if r["fileid"] in need and r["actiontype"] != "delete only":
            debt[r["fileid"]].append(r)
    # 3. organisation secured parties
    sp = defaultdict(list)
    for r, _ in s.rows(os.path.join(RAW, "ucc_secured_org")):
        if r["fileid"] in need and r["actiontype"] != "delete only":
            nm = ws(r["organizationname"])
            if nm and nm not in sp[r["fileid"]]:
                sp[r["fileid"]].append(nm)
    # 4. collateral
    coll = defaultdict(list)
    for r, _ in s.rows(os.path.join(RAW, "ucc_collateral")):
        if r["fileid"] in need and r["actiontype"] != "delete only":
            coll[r["fileid"]].append((ws(r["collateraldescription"]), ws(r["additionalcollateraldescription"]), ws(r["county"])))
    print("debtor fileids", len(debt), "sp fileids", len(sp), "collateral fileids", len(coll), flush=True)

    stats = Counter(); monthly = defaultdict(Counter); perword = Counter(); firstword = Counter()
    bytype = Counter(); flag_bytype = Counter(); supp_count = Counter(); ids = Counter()
    scope.sort(key=lambda x: (x[0]["filingdate"], int(x[0]["fileid"])))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(COLS)
        done_tx = set()
        for r, ts in scope:
            fid = r["fileid"]; mid = master_of.get(fid)
            if r["transactionid"] in done_tx:      # the source filing table repeats a handful of filing numbers
                stats["source_duplicate_filing_rows_skipped"] += 1
                continue
            done_tx.add(r["transactionid"])
            is_amend = r["transactionid"] != r["masterdocumentid"]
            if is_amend and not mid:
                stats["amendment_master_not_in_table"] += 1
            ftype = r["filingtype"]
            own = keep_org(debt.get(fid), ftype, stats)
            mas = keep_org(debt.get(mid), ftype, stats) if (mid and not own) else []
            if own:
                ds, dsrc = own, "own"
            elif mas:
                ds, dsrc = mas, "master"
            else:
                stats["left_out_no_org_debtor"] += 1
                stats["left_out_no_org_debtor:" + r["transactiontype"]] += 1
                continue
            if sp.get(fid): spn, spsrc = sp[fid], "own"
            elif mid and sp.get(mid): spn, spsrc = sp[mid], "master"
            else: spn, spsrc = [], ""
            if coll.get(fid): cl, csrc = coll[fid], "own"
            elif mid and coll.get(mid): cl, csrc = coll[mid], "master"
            else: cl, csrc = [], ""
            cats = []; texts = []; counties = []
            for cat, txt, cty in cl:
                if cat and cat not in cats: cats.append(cat)
                if txt and txt not in texts: texts.append(txt)
                if cty and cty not in counties: counties.append(cty)
            withheld = ftype in WITHHOLD_TEXT
            real_cats = [c for c in cats if c.upper() not in ("UNKNOWN", "GENERAL DESCRIPTION")]
            full = "" if withheld else SSN.sub("[redacted]", " | ".join(texts))
            cattext = "; ".join(real_cats)
            if withheld:
                desc = (cattext or ftype) + " [free text withheld: names a private individual]"
            else:
                desc = (cattext + ": " + full) if (cattext and full) else (full or cattext)
            initial = r["transactiontype"] == "Initial Filing"
            hits, supp = match(cattext + " " + full) if not withheld else ([], [])
            flag = "Y" if (initial and hits) else "N"
            rule = "initial filing + collateral match: " + ", ".join(hits[:3]) if flag == "Y" else ""
            seen_names = set(); seq = 0
            for d in ds:
                name = ws(d["organizationname"])
                key = (name.upper(), ws(d["address1"]).upper())
                if not name or key in seen_names:
                    continue
                seen_names.add(key); seq += 1
                addr = ", ".join(x for x in (ws(d["address1"]), ws(d["address2"])) if x)
                w.writerow(["Colorado UCC filings", "State (Colorado)", r["transactionid"], r["filingdate"][:10], "filed",
                            ws(r["documenttype"]), name, "debtor", addr, ws(d["city"]), "", ws(d["zipcode"]), desc[:500],
                            flag, rule, f"https://data.colorado.gov/resource/wffy-3uut.json?transactionid={r['transactionid']}", ts,
                            "; ".join(spn)[:300], ws(d["state"]), f"{r['transactiontype']}|{ftype}|{ws(r['documenttype'])}", seq,
                            r["transactiontype"], r["masterdocumentid"], r["lapsedate"][:10], ws(r["financialstatementtype"]), fid,
                            ws(d["country"]), ws(d["organizationtype"]), ws(d["organizationjurisdiction"]), ws(d["debtordescription"]),
                            d["recordstatus"], dsrc, csrc, spsrc, "; ".join(cats)[:200], "; ".join(counties)[:200],
                            len(full), ", ".join(supp) if initial else "", "Y" if ENTITY_TOKEN.search(name) else "N"])
                stats["rows"] += 1; ids[r["transactionid"]] += 1
                mo = monthly[r["filingdate"][:7]]
                mo["rows"] += 1; mo["initial"] += initial; mo["flag"] += flag == "Y"
                mo["ucc_initial"] += (initial and ftype == "ucc")
                bytype[(r["transactiontype"], ftype, ws(r["documenttype"]))] += 1
                if not name: stats["null_name"] += 1
                if not addr: stats["null_addr"] += 1
                if not spn: stats["null_sp"] += 1
                if not desc: stats["null_desc"] += 1
                if flag == "Y":
                    flag_bytype[ftype] += 1; firstword[hits[0]] += 1
                    for h in hits: perword[h] += 1
                    if len(hits) == 1: perword["__only__" + hits[0]] += 1
                if initial and supp:
                    for h in supp: supp_count[h] += 1
            stats["filings_written"] += 1
            mo = monthly[r["filingdate"][:7]]; mo["filings"] += 1
    stats["record_ids_with_more_than_one_row"] = sum(1 for v in ids.values() if v > 1)
    stats["extra_rows_from_multi_debtor"] = sum(v - 1 for v in ids.values() if v > 1)
    stats["in_scope_filings_in_source"] = len(scope)
    with open(SUMMARY, "w") as f:
        f.write("# Colorado UCC filings: monthly summary\n\n")
        for k in sorted(stats): f.write(f"- {k}: {stats[k]}\n")
        f.write("\n| month | filings written | rows (filing x org debtor) | rows on initial filings | rows on initial UCC financing statements | flag Y |\n|---|---|---|---|---|---|\n")
        t = Counter()
        for k in sorted(monthly):
            m = monthly[k]; t.update(m)
            f.write(f"| {k} | {m['filings']} | {m['rows']} | {m['initial']} | {m['ucc_initial']} | {m['flag']} |\n")
        f.write(f"| total | {t['filings']} | {t['rows']} | {t['initial']} | {t['ucc_initial']} | {t['flag']} |\n")
        f.write("\n## Flagged rows per matched word\n\nA row with several matches counts under each word. `first` = rows where the word is the first one named in flag_rule. `only` = rows flagged by that word alone.\n\n| word | rows | first | only |\n|---|---|---|---|\n")
        for k, v in sorted(((k, v) for k, v in perword.items() if not k.startswith("__")), key=lambda x: -x[1]):
            f.write(f"| {k} | {v} | {firstword[k]} | {perword['__only__' + k]} |\n")
        f.write("\n## Flagged rows by filing type\n\n")
        for k, v in flag_bytype.most_common(): f.write(f"- {k}: {v}\n")
        f.write("\n## Soft words suppressed as real-estate fixture boilerplate (rows on initial filings)\n\n")
        for k, v in supp_count.most_common(): f.write(f"- {k}: {v}\n")
        f.write("\n## Rows by filing type\n\n| transaction type | filing type | document type | rows |\n|---|---|---|---|\n")
        for k, v in bytype.most_common(): f.write(f"| {k[0]} | {k[1]} | {k[2]} | {v} |\n")
    for k in sorted(stats): print(k, stats[k])


if __name__ == "__main__":
    if "--build" not in sys.argv:
        for name, ds, idc, sel, wh in JOBS:
            s.fetch(ds, idc, sel, wh, os.path.join(RAW, name))
    build()
