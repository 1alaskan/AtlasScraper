"""Step 6: build denver_top25_contacts.csv from the v3b ranking plus the looked-up values below.
Run from the repo root: python3 -I step6-contacts/scripts/build_contacts.py
Every looked-up value is typed here with its source tag, so the file is the audit trail. No people's names."""
import csv, sys
csv.field_size_limit(10**9)
RANKED = "step5-analysis/v3/denver_ranked_accounts_v3b.csv"
OUT = "step6-contacts/denver_top25_contacts.csv"
N = 32
COLS = ["rank","company_name","site_address","zip","match_confidence","site_phone","phone_type","phone_source_url","phone_checked_date","permit_contact_role","permit_contact_org","permit_contact_relation","permit_contact_source","contractors","contractor_roles","contractor_sources","coverage_note","zoominfo_name","zoominfo_title","zoominfo_phone","zoominfo_email","call_notes"]
CHECKED = "2026-11-16"
BLOCKED = "Phone not checked: the company website could not be opened (page fetches needed an approval that was not answered)."
NOADDR = "Phone lookup skipped: address with no attached company."
APCD = "APCD documents for permit {p} (AIRS {a}) not reached: the records viewer needs a real browser; look up by AIRS ID by hand."
BP = "contractor of record on building permit"
# rank: dict of overrides. match: confirmed / possible / "" (no company).
D = {
1: dict(match="confirmed", role="EHS Mgr (facility contact); Sr Plant Dir (legal contact)", org="CB Manufacturing Company, Inc (PepsiCo)", rel="on_site", src="wqcd_sheet:COR901708",
   con=[("Gray Construction","construction stormwater permittee and "+BP+" (general contractor likely)","wqcd_sheet:COR418089 + denver_permits:2024-COMMCON-0000760"),
        ("ARCO/Murray National Construction Company LLC",BP+" ($9.3M new building, $7.1M phased construction)","denver_permits:2025-COMMCON-0000506 + 2025-COMMCON-0001156"),
        ("Gracon LLC",BP,"denver_permits:2024-COMMCON-0001928 + 2025-COMMCON-0000721"),
        ("HEI Civil","construction stormwater permittee, Project Mustang - E 69th Avenue (civil contractor likely, property owner on the permit is PepsiCo)","wqcd_sheet:COR427808")],
   note=BLOCKED+" "+APCD.format(p="22DE0598",a="031-2567")+" Owner-side roles on the construction permits: Sr Director Manufacturing and Director of Facilities and Infrastructure, both PepsiCo, Denver."),
2: dict(match="confirmed", role="Plant Manager (facility contact); Sr. Environmental Risk Compliance Manager (legal contact, Boise ID)", org="Safeway, Inc., Denver Milk; Albertsons, LLC", rel="on_site", src="wqcd_sheet:COPB90721",
   con=[("Rhinotrax Construction Inc",BP+" ($2.15M new building)","denver_permits:2025-COMMCON-0002159 + 2025-COMMCON-0002650"),
        ("Traverse Builders LLC",BP+" ($806,745 addition)","denver_permits:2025-COMMCON-0000089"),
        ("D & E Steel Services Inc",BP+" ($103,920 alteration)","denver_permits:2025-COMMCON-0000782")],
   note=BLOCKED+" Occupier now confirmed from a state record: pretreatment permit COPB90721 names 'Safeway, Inc., Denver Milk' at 4301 Forest St. That permit dates from 2017, so the role may have changed hands. No APCD row for this address."),
3: dict(match="confirmed", role="Plant Mgr (facility and legal contact); EHS Mgr (compliance contact)", org="ConAgra Foods Packaged Foods LLC", rel="on_site", src="wqcd_sheet:COR901555",
   con=[("Encompass Contracting Services Corp",BP+" ($300,000 alteration, joined by street address)","denver_permits:2024-COMMCON-0001455")],
   note=BLOCKED+" "+APCD.format(p="13DE1362",a="031-2169")),
4: dict(match="confirmed", role="Safety/Regulatory Compliance Leader (facility contact); Site Leader (legal contact)", org="King Soopers Inc (King Soopers Bakery Plant)", rel="on_site", src="wqcd_sheet:CONOX0088",
   con=[("Frost Line Mechanical LLC",BP+" ($150,000 alteration, mechanical contractor by name, joined by street address)","denver_permits:2024-COMMCON-0000781")],
   note=BLOCKED+" "+APCD.format(p="95DE314",a="031-1662")+" An older permit (COPB90772) lists an Env Compliance Dir at Kroger Co, Cincinnati."),
5: dict(match="confirmed", role="Safety Mgr (facility contact); Pres (legal contact); Controller (billing contact)", org="Quality Linings Co Inc", rel="on_site", src="wqcd_sheet:COR900679",
   note=BLOCKED+" A number appears on listing sites; not recorded because those are not allowed sources. "+APCD.format(p="04DE1382",a="031-1968")+" No contractor found: the site plan records carry no applicant."),
6: dict(match="confirmed", role="Env Specialist (facility contact); Plant Mgr (legal contact)", org="Nestle Purina PetCare Co", rel="on_site", src="wqcd_sheet:COR900463",
   con=[("PCL Construction Services Inc",BP+" ($617,595 and $179,607 alterations, joined by street address)","denver_permits:2025-COMMCON-0001586 + 2025-COMMCON-0002297")],
   note=BLOCKED+" "+APCD.format(p="93DE1121",a="031-0042")),
7: dict(match="possible",
   con=[("RM Construction LLC",BP+" ($470,000 new non-building structure)","denver_permits:2025-COMMCON-0001930"),
        ("Seven Point Construction Inc",BP+" ($191,333 alteration)","denver_permits:2026-COMMCON-0001010")],
   note=NOADDR+" Possible occupier Adams McClure comes from an undated EPA registry row. No air or water permit record at this address, so no permit contact."),
8: dict(match="confirmed", role="EHS Mgr (facility and legal contact); Plant Dir (billing contact)", org="Dawn Food Products Inc", rel="on_site", src="wqcd_sheet:COR901688",
   note=BLOCKED+" "+APCD.format(p="10DE1562",a="031-2067")+" No contractor found: no building permit or press row at this address."),
9: dict(match="confirmed", role="General Manager (facility contact, Denver); Regional Vice President (legal contact, Santa Fe Springs CA)", org="Lakin Tire West LLC - Denver", rel="on_site", src="wqcd_sheet:CONOX0954",
   con=[("CMC Group Inc",BP+" ($220,000 alteration, finaled 2026-04-16, joined by street address)","denver_permits:2025-COMMCON-0001683 + 2025-COMMCON-0002413"),
        ("Industrial Outdoor Ventures","property owner and landlord (bought and leased 3750 Nome Street, per press)","mile_high_cre:52994 + 53304")],
   note=BLOCKED+" No APCD row."),
10: dict(match="confirmed",
   note=BLOCKED+" No air or water permit record at this address, so no permit contact. No contractor found: the 2026 concept review carries no applicant. Earlier steps note SRM Concrete bought this site for a batch plant, so the concept review may be SRM's."),
11: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record under this name. No contractor found."),
12: dict(match="confirmed", phone="855-396-7836", ptype="site", purl="https://titanfittings.com/about-us",
   note="Phone is the one number the company's own site shows; the site footer gives the 11795 E 45th Ave address and hours Mon-Fri 8AM-5PM MST. It is toll-free and may ring sales, not the shop floor. No air or water permit record, so no permit contact. No contractor found."),
13: dict(match="confirmed",
   con=[("Harris Dewart LLC",BP+" ($75,000 alteration, issued 2026-08-06, joined by street address)","denver_permits:2026-COMMCON-0001370"),
        ("Jabez Construction Services Inc",BP+" ($10,000 alteration, joined by street address)","denver_permits:2026-COMMCON-0000535")],
   note=BLOCKED+" No current permit record: the only water permit at 10660 E 51 Ave belonged to an earlier occupier and ended in 2021."),
14: dict(match="confirmed", role="Plant Mgr (facility contact); Regional Operations Manager (legal contact)", org="Cargill Animal Nutrition", rel="on_site", src="wqcd_sheet:COR900462",
   note=BLOCKED+" Water permit gives the site as 4450 Madison St; the air permits say 4545 Madison St. "+APCD.format(p="26DE0441, 26DE0060 and 13DE035-4",a="031-0052")+" No contractor found."),
15: dict(match="confirmed", role="Manager (facility and legal contact)", org="2401 W 6th Ave LLC", rel="unknown", src="wqcd_sheet:CONOX0981",
   con=[("Precision Homes LLC",BP+" ($165,000 alteration, unit A, finaled 2025-05-06, joined by street address)","denver_permits:2024-COMMCON-0000857")],
   note="Phone lookup skipped: the named entity is an LLC named after the address and registered at an office suite elsewhere; the operating business on site (stone products, SIC 3281 on the permit) is not named in any record. Relation left unknown for the same reason."),
16: dict(match="confirmed", note=BLOCKED+" No air or water permit record, so no permit contact. No contractor found."),
17: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record. No contractor found."),
18: dict(match="confirmed", role="EHS Coord (facility contact, Denver); West Region Supply Chain VP (legal contact, CA); Region VP (reporting contact, TX)", org="Frito Lay Inc", rel="on_site", src="wqcd_sheet:COR900229",
   con=[("Burns & McDonnell Engineering Company Inc",BP+" on six permits 2024 to 2026, largest $4.9M (engineer and design-build firm, joined by street address)","denver_permits:2025-COMMCON-0001774 + 2024-COMMCON-0001014 + 2025-COMMCON-0002384 + 2026-COMMCON-0001005")],
   note=BLOCKED+" No APCD row in the feed."),
19: dict(match="",
   con=[("Burns & McDonnell Engineering Company Inc",BP+" ($1,468,528 alteration, not finaled)","denver_permits:2026-COMMCON-0000192 + 2026-COMMCON-0001412")],
   note=NOADDR+" No air or water permit record, so no permit contact. The contractor of record is the same firm as on the Frito-Lay plant permits; that does not name the occupier."),
20: dict(match="confirmed", role="EHS Manager (facility contact); Plant Manager (legal contact)", org="Amcor Rigid Packaging", rel="on_site", src="wqcd_sheet:CONOX1012 + CONOX0386",
   con=[("Summit Partners, Ltd.",BP+" ($2,000,000 new non-building structure, joined by street address)","denver_permits:2025-COMMCON-0002615")],
   note=BLOCKED+" No APCD row in the feed."),
21: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record. No contractor found."),
22: dict(match="",
   con=[("SMA LLC",BP+" ($9,265,000 addition, issued 2026-07-30)","denver_permits:2026-COMMCON-0000593")],
   note=NOADDR+" No air or water permit record at 4460 N Madison St, so no permit contact. Cargill's water permit is at 4450 Madison St, next door by number; no record ties the two."),
23: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record. No contractor found."),
24: dict(match="possible", role="Superintendent (facility contact); VP (legal contact); Project Manager (billing contact)", org="GE Johnson Construction Company", rel="third_party", src="wqcd_sheet:COR418857",
   con=[("Rand Construction Corporation",BP+" ($1,631,240 tenant finish, suite 1200, not finaled)","denver_permits:2026-COMMCON-0000441 + 2026-COMMCON-0001398"),
        ("GE Johnson Construction Company (DPR Construction)","general contractor for the base building (construction stormwater permittee and "+BP+" in 2024)","wqcd_sheet:COR418857 + denver_permits:2024-COMMCON-0002248"),
        ("Elevation Development Group LLC","developer (property owner on the construction stormwater permit)","wqcd_sheet:COR418857")],
   note=NOADDR+" This is Steel House, a 12-storey office building. Press reports a software company leasing 32,930 sq ft there (mile_high_cre:58932), so the suite 1200 fit-out is probably office space: weak compressed-air fit. The permit contact is the base-building contractor on a permit that ended 2026-02-01, not the tenant."),
25: dict(match="confirmed", note=BLOCKED+" No air or water permit record, so no permit contact. No contractor found."),
26: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record. No contractor found."),
27: dict(match="confirmed", note=BLOCKED+" No permit record under this name at this address. No contractor found."),
28: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking; a business address shows on third-party listings of its federal contractor registration but was not recorded from those. No permit record. No contractor found."),
29: dict(match="confirmed", note=BLOCKED+" No air or water permit record, so no permit contact. No contractor found."),
30: dict(match="confirmed", role="VP GM (facility contact); Pres (legal contact)", org="Intertech Plastics Inc", rel="on_site", src="wqcd_sheet:COR900614",
   note=BLOCKED+" The permit contact comes from an old permit at this address (received 2012, ended 2017), so treat the roles as a guide to who signs, not as current. No contractor found."),
31: dict(match="confirmed", addr="3838 Eudora Way", phone="303-320-1813", ptype="site", purl="https://neversummer.com/blogs/snowboarding/tour-the-never-summer-snowboards-factory-in-denver-co",
   note="Address was withheld in the ranking; shown here because the company's own website prints it in its footer with this phone. No air or water permit record, so no permit contact. No contractor found."),
32: dict(match="confirmed", note=BLOCKED+" Site address withheld in the ranking. No permit record. No contractor found."),
}
rows = list(csv.DictReader(open(RANKED, encoding="utf-8-sig")))[:N]
out = []
for r in rows:
    k = int(r["rank"]); d = D[k]; con = d.get("con", [])
    for c in con:
        assert ";" not in c[0] + c[1] + c[2], c
    out.append({
        "rank": k, "company_name": r["company_name"], "site_address": d.get("addr", r["site_address"]), "zip": r["zip"],
        "match_confidence": d["match"], "site_phone": d.get("phone", ""), "phone_type": d.get("ptype", ""),
        "phone_source_url": d.get("purl", ""), "phone_checked_date": CHECKED if d.get("phone") else "",
        "permit_contact_role": d.get("role", ""), "permit_contact_org": d.get("org", ""),
        "permit_contact_relation": d.get("rel", ""), "permit_contact_source": d.get("src", ""),
        "contractors": "; ".join(c[0] for c in con), "contractor_roles": "; ".join(c[1] for c in con),
        "contractor_sources": "; ".join(c[2] for c in con), "coverage_note": d["note"],
        "zoominfo_name": "", "zoominfo_title": "", "zoominfo_phone": "", "zoominfo_email": "", "call_notes": ""})
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(out)
c = lambda fn: sum(1 for o in out if fn(o))
print("rows", len(out))
print("site", c(lambda o: o["phone_type"] == "site"), "hq_only", c(lambda o: o["phone_type"] == "hq_only"), "none_found", c(lambda o: o["phone_type"] == "none_found"),
      "not checked (blocked)", c(lambda o: o["coverage_note"].startswith("Phone not checked")), "skipped", c(lambda o: o["coverage_note"].startswith("Phone lookup skipped")))
print("permit contact", c(lambda o: o["permit_contact_role"]), "on_site", c(lambda o: o["permit_contact_relation"] == "on_site"),
      "third_party", c(lambda o: o["permit_contact_relation"] == "third_party"), "unknown", c(lambda o: o["permit_contact_relation"] == "unknown"))
print("contractor", c(lambda o: o["contractors"]))
print("match", {m: c(lambda o, m=m: o["match_confidence"] == m) for m in ("confirmed", "possible", "")})
