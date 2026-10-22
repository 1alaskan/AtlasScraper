# Step 5 v3: Denver ranking, full rebuild

Run 2026-10-11. One pass from the Step 4 files, tier A and tier B rows scored together under the fixed points table. Nothing was re-scraped and no flag was changed.

Files in this folder: `denver_ranked_accounts_v3.csv` (707 rows), `denver_evidence_v3.csv` (1,587 source rows), `rank_changes_v3.csv` (481 rows that moved more than 10 places against the tier B run, each with a cause), `v3_report.json` (every count in this note), `scripts\` (the build, runnable with one command; see `scripts\README.md`).

Read `analysis_notes.md` and `analysis_notes_v2.md` for the history. This note stands on its own for the method.

## Assumptions (read first)

1. **This is a rebuild, not a re-run on top of the old rows.** The ranking is computed from the Step 4 files alone. The two earlier ranked files are read only after ranking, to fill `rank_step5`, `rank_step5b` and the rank-change report. Three things are carried over as fixed inputs in `scripts\v3_config.py`, because they are not in the Step 4 files: the first run's web checks (22 fit texts and two drops, kept as written), the Step 3 tie between the PepsiCo plant permits at 19301 E 70th Ave and the air permit at 19300 E 72nd Ave, and the Step 3 name for the occupier of 4301 N Forest St (Safeway milk plant).
2. **Candidates come only from flagged rows that survive the cuts.** Tier A or tier B. Unflagged rows are support only.
3. **Run date for recency is 2026-10-11.** Twelve months back is 2025-10-11, 24 months is 2024-10-11, six months (the fit-out window for a finaled permit) is 2026-04-11.
4. **Denver scope, in this order:** county field in a water permit; AIRS prefix 031 in an air permit; the two Denver layers; then, for UCC and registration rows, the zip (99% or more of the zip in Denver County); then the Census geocoder for a split zip, and for a Denver mailing city in a zip that is not a Denver zip. 151 addresses went through the geocoder (55 were in the cache, 96 were looked up today): 97 Denver, 32 Adams, 12 Jefferson, 6 Arapahoe, 4 no match.
5. **An address the geocoder places outside Denver stays in the "county unconfirmed" section only if its mailing city is Denver.** If the mailing city is Littleton, Lakewood or Aurora and the geocoder also says another county, the row is left out. The first run kept those rows in the unconfirmed section; the tier B script left them out for new rows. This removes eight rows the earlier files carried (KCL Consulting, Ludvik Electric, JBBR, IRV Landscaping, Freespan, Elevate Storage, Datahelm, Cyberhelm).
6. **The water permit county field is taken as the source states it,** as in Step 5. It is not always right: Sealy Mattress (18701 E 38th Ave, Aurora) and Lineage Logistics (Henderson) carry county Denver in the state sheet. Where the field and the geocoder disagree about the same address, the row goes to the unconfirmed section and says so (one row: Vance Brothers, 380 W 62nd Ave).
7. **Join classes.** Confirmed: the name and the address agree, or a suite matches, or the Step 3 tie applies. Possible: the same name at another address, or a join by street address alone. Possible rows score half.
8. **Which side holds an address.** This had to be settled for a one-pass build, because the two earlier runs settled it by the order rows arrived.
   - A company holds the address when a state permit puts it there (air permit applicant or water permit operator, including rows cut as noise) or an equipment filing does (a tier A compressor or machinery filing, or a tier B B1a filing). Permits, site plans and press rows at that street address then join the company as possible, at half points, unless the suite matches. If two such companies share the street address the address rows stay unattached.
   - A company known at an address only from a registration, a blanket or vague lien, or a weak-tier filing does not hold it. If the address has its own permit, site plan or press signal, the address is the row and the company is a possible occupier at half points. It is not promoted. If the address has no signal of its own, the company is its own row, as before.
   - Counts: 73 address rows joined a company as possible, 3 as confirmed by suite, 8 by the PepsiCo tie, 650 stayed with an unattached address. 21 rows are named only from a state permit at the address. 5 flagged companies were folded into an address row as possible occupiers.
9. **A construction stormwater "facility" is a project name, not a company.** Step 5 used names such as "3875 Walnut St. Multifamily" and "Roslyn Safety Improvements" as the row's company and halved the permit points. Here those rows are unattached addresses at full permit points, the stormwater row is kept as support, and a project name that says housing, school, solar, substation or similar sets the fit to weak. 12 rows moved more than 10 places for this reason. Industrial stormwater, no-exposure and individual permits still name the operator.
10. **One name found at an unattached address** in the UCC or registration files (not at an agent suite, not dissolved) is listed as a possible occupier and its best row counts at half as support (1.5 or 2 points). Two or more names are listed and add nothing. 72 addresses have one such name.
11. **Name merges.** Identical name key; co-debtors on one filing (7 merges); water facility and permittee; two names at one address that share a distinctive leading word or their first two words (14 merges, including Mountain Packaging LLC with Mountain Packaging Est. 2007, and three Highline Machining entities). "Co" and "Company" are dropped only at the end of a name, so "CB CO Manufacturing LLC" does not merge into CB Manufacturing (PepsiCo).
12. **Registered-agent suites and mailbox buildings.** An address and suite with 10 or more 2024-26 registrations is an agent address. Three tests are used: the Step 4b text key; a normalised street, suite and zip key, so that "Ste 700" matches "Suite 700"; and a building test, 200 or more registrations at one street address and zip whatever the suite, which catches mailbox services that give every customer a different box number (1500 N Grant St has about 32,000 registrations). The second and third tests are new in v3. Together the three cut 138 tier A registrations (121 in Step 5) and 9 tier B. The building test touches only downtown mailbox and office-tower addresses; no industrial address reaches 200. A UCC debtor at such an address stays in, in the unconfirmed section, with the reason given (3 rows: Radical Botanicals at 44 Cook St Ste 100, a suite with 490 registrations; Liberty Oilfield; Altius Space Machines).
13. **UCC tier A classes.** 30 points needs a compressor word that is not a towable unit, a forklift, a restaurant or a pharmacy boilerplate. 25 points needs a production-machinery word in the flag words or the visible text; process chillers beside process equipment and welders count, as they did in Step 5. The weak tier (8 points) is restaurant, commissary-kitchen and survey equipment, towable compressors, and a flagged word with no machinery (small boilers).
14. **Permit classes.** Step 4b's B3a rule has no ceiling, so six tier B permits are worth $250k or more (they sit on industrial parcel classes outside industrial zoning, which is why tier A missed them). They are scored on the table's $250k lines (18 or 22, plus 3 at $1M), not at 12. The largest is a $2.1M new building at 3480 S Poplar St, now rank 50. New Building, Addition, Foundation Only, Phased Construction and New Non-Building Structure score as new (22). Everything else scores as alteration (18). A permit marked cancelled is cut unless a change-of-contractor record at the same address and valuation carried the work on (one tier A permit, 1305 N Osage St, is kept this way with the later record's final date). The Step 5 parcel-class cut on tier A also drops the twelve assessor classes that carry the INDUSTRIAL prefix but are churches, schools, cemetery buildings and the like, the same list Step 4b used for tier B.
15. **Repeat months.** The table says 3 points for each further month with a signal of 12 or more in the source. That is applied to every source and both tiers. Step 5 applied it to "strong" signals and not to site plans; the tier B run applied it only to new rows. This is the largest single reason scores of address rows rose (see the rank changes).
16. **Source bonus.** +8 for each source beyond the first with 5 points or more (maximum 24), +3 for each source with less (maximum 6). When no source reaches 5, the best support source is the first and each further one adds 3.
17. **Thresholds are applied after halving.** The 12-point repeat test, the 5-point source test and the 4-point recency test all use the halved points of a possible row. Recency looks at the latest row worth 4 or more, flagged or not, so a generic lien at the company's own address (4 points) can set it. A registration at 3, or a small permit joined at 3, earns none. A water certification that has since been terminated still scores as a new certification (three rows: Electric Equipment & Engineering, Daffy Apple, Sealy Mattress).
18. **Stage.** As in Step 5, with the $50k cap. A permit joined as possible still sets the stage. An equipment filing sets "buying equipment" only when it is confirmed, not when the company is a possible occupier.
19. **Fit, in order:** web check; manufacturing SIC on a water permit (the facility's own code, or another code on the row unless the main code is transport, wholesale or retail); machinery named in a UCC filing; a lien held by a machinery maker; kitchen or survey equipment (weak); a maker word in the name, labelled "not confirmed"; process units on an air permit (concrete batch plants and engine test cells are moderate); a trade word (moderate); a weak word. A name that carries both a maker word and a weak word is read as weak, as the tier B script did. For an address row: a stormwater project name that says housing or similar (weak), then the assessor parcel class of its flagged permits, using the tier B run's list for every address row.
20. **An unflagged permit, or a flagged permit that was cut, at an account's address is support:** 6 points at half, so 3, unless the suite matches. It attaches to an address row, or to a company that holds the address (assumption 8). It does not attach to a company known there only from a registration or lien, unless the suite matches: in a multi-tenant building that would be noise.
21. **Reach.** Rows under the same name anywhere in the eight files count as possible when the address differs, including out-of-state filings. A press story counts as naming the company only when the post's city is Denver or blank; this drops the King Soopers store opening in Louisville that Step 5 counted.
22. **Home-address rule.** A UCC or registration street address is shown only when it has a suite or unit, appears in a site-based source, carries two or more business names among the ranking's flagged rows (name variants and co-debtors of one company count, as they did in Step 5), or was shown in the first run on the strength of its web check (four names), or was confirmed by today's check (Direct Polymers). An address with an apartment or private-mailbox number is never shown. Where the address is withheld, street addresses inside the collateral text are replaced with "[address removed]". 130 rows show "withheld", 12 of them in the top 60. This is stricter than a count of every name in the files, which would have shown some addresses that look like homes with two small companies.
23. **Evidence file.** `points` is what the row is worth after halving. Flagged rows are all listed. Unflagged support rows are listed up to five per source per account, best first (138 further support rows add no points and are not listed; this is a departure from "every source row"). The "lender not named" mark is in `flag_rule_v2` as well as in `top_evidence`. Press rows carry the headline only. Email addresses and phone numbers inside collateral text are replaced with "[contact detail removed]".
24. **People's names, phone numbers, emails and home addresses.** No phone number or email is in any output. No free-standing person's name is in any output. Two limits remain. First, a registered entity that is named after a person appears under its registered name where it is the ranked company or the single possible occupier of an address; the other names found at an address are counted, not listed. Second, the home-address rule is a rule of thumb: an address with a suite or unit is shown, and a home office with a suite number would pass. Debtors with no business word in the name are left out of everything.
25. **No Atlas Copco data. No contact with any agency, vendor or company. No records requests. No Accela lookups.** Web use: the Census geocoder (96 addresses), and searches for three companies (below).
26. **Step 3 ground-truth corrections are not applied,** except the PepsiCo aliases, as before.

## Points table (fixed, not retuned)

Possible matches score half. Within one source only the best signal counts, plus 3 points for each further month with a signal of 12 or more in that source (maximum 9).

| Signal | Points |
|---|---|
| UCC filing naming an air compressor or compressed-air system (tier A) | 30 |
| UCC filing with a tier B process-equipment word (B1a) | 30 |
| UCC filing naming production machinery (tier A) | 25 |
| Air permit application, modification or approval for process units | 25 |
| Denver permit, new building or addition, industrial property, $250k or more (+3 if $1M or more) | 22 |
| Construction stormwater permit with a manufacturing SIC or company-named facility | 20 |
| Denver permit, alteration or tenant finish, industrial property, $250k or more (+3 if $1M or more) | 18 |
| Denver permit, $50k to $250k, industrial property (B3a) | 12 |
| Air permit APEN-only or exempt; new industrial stormwater or no-exposure certification; concept or site plan on I-A or I-B zoning | 12 |
| UCC flagged word without production machinery; towable compressor; press story naming the company | 8 |
| Vague lien held by an equipment lender (B1b); blanket lien on a maker (B1c) | 8 |
| Flagged tier A registration; concept or site plan on industrial mixed-use zoning; Denver permit under $50k on industrial property (B3b); unflagged permit at the company's address | 6 |
| Press story naming only the address; OEDIT code-name approval | 5 |
| Generic or blanket UCC lien; other site plan at the address | 4 |
| Tier B registration (B2a); unflagged registration | 3 |
| Air or water row cut as noise | 2 |

- **Independent sources:** +8 for each source beyond the first with a signal of 5 or more (maximum 24); +3 for each source with support only (maximum 6).
- **Recency** (latest row worth 4 points or more, run date 2026-10-11): +15 within 12 months, +8 within 24 months.
- **Stage:** buying equipment +12; fit-out +12; under construction +8; operating and expanding +8; planned +4; unknown 0. A permit under $50k adds at most 4 stage points, whatever its status.
- **Compressed-air fit:** strong +15; moderate +6; unknown 0; weak -15.

Each row's `top_evidence` ends with its own points breakdown. `scripts\verify_v3.py` recomputes every score from the evidence file; it reports no differences.

## Noise cuts and counts

Counts are rows removed at that step, in the order applied, unless the text says otherwise. "Rows kept as signals" for UCC tier A includes the 15 weak-tier rows listed above it.

| Source | Step | Rows |
|---|---|---|
| Colorado UCC filings, tier A | flagged rows statewide | 901 |
| Colorado UCC filings, tier A | outside Denver scope (state, zip, mailing city, geocoder) | 794 |
| Colorado UCC filings, tier A | debtor name has no business word (may be an individual) | 10 |
| Colorado UCC filings, tier A | SBA continuations (none are flagged) | 0 |
| Colorado UCC filings, tier A | pharmacy and copier blanket liens where the flag word sits in boilerplate (Cardinal Health, Canon) | 5 |
| Colorado UCC filings, tier A | paving and road-milling equipment ('pneumatic' rollers, Wirtgen milling machines) | 3 |
| Colorado UCC filings, tier A | forklifts and other lift or earthmoving equipment (Doosan, 'pneumatic' tyre) | 7 |
| Colorado UCC filings, tier A | dry-cleaner and laundry boilers | 2 |
| Colorado UCC filings, tier A | 'bottling' only in a debtor's own name (blanket liens) | 7 |
| Colorado UCC filings, tier A | dropped after the first run's web check (Valor Peak Distillery, Longmont) | 1 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): restaurant, commissary-kitchen or survey equipment | 4 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): towable construction compressor | 8 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): flagged word without production machinery | 3 |
| Colorado UCC filings, tier A | rows kept as signals | 72 |
| Colorado UCC filings, tier B | flagged rows statewide | 374 |
| Colorado UCC filings, tier B | outside Denver scope | 313 |
| Colorado UCC filings, tier B | rows kept as signals (8 B1a, 8 B1b, 45 B1c) | 61 |
| Colorado business registrations, tier A | flagged rows statewide | 2,211 |
| Colorado business registrations, tier A | no Colorado address (foreign entity showing an out-of-state head office); kept for name matching only | 1,707 |
| Colorado business registrations, tier A | Colorado address outside Denver scope | 273 |
| Colorado business registrations, tier A | February 2026 bulk filings through Colorado Registered Agents Inc | 4 |
| Colorado business registrations, tier A | registered-agent, virtual-office or mailbox address (assumption 12) | 138 |
| Colorado business registrations, tier A | entity since withdrawn, dissolved, converted or merged | 5 |
| Colorado business registrations, tier A | rows kept as signals | 84 |
| Colorado business registrations, tier B | flagged rows statewide | 815 |
| Colorado business registrations, tier B | no Colorado address | 90 |
| Colorado business registrations, tier B | Colorado address outside Denver scope | 626 |
| Colorado business registrations, tier B | February 2026 bulk filings through Colorado Registered Agents Inc | 2 |
| Colorado business registrations, tier B | registered-agent, virtual-office or mailbox address (second and third tests) | 9 |
| Colorado business registrations, tier B | rows kept as signals | 88 |
| Denver commercial construction permits, tier A | flagged rows | 509 |
| Denver commercial construction permits, tier A | zero-valuation permits in the full layer (never flagged in tier A; listed for the record) | 1,707 |
| Denver commercial construction permits, tier A | flagged rows in the DIA neighborhood (all) | 200 |
| Denver commercial construction permits, tier A | DIA neighborhood on airport zoning or Pena Blvd (terminal and concourse tenant work) | 145 |
| Denver commercial construction permits, tier A | special events and change-of-contractor records | 24 |
| Denver commercial construction permits, tier A | assessor parcel class is not industrial, or no industrial zoning and no industrial parcel class | 259 |
| Denver commercial construction permits, tier A | cancelled with no change-of-contractor record (ADDED in v3) | 0 |
| Denver commercial construction permits, tier A | rows kept as signals | 81 |
| Denver commercial construction permits, tier A | of the kept rows, received in the last 90 days (kept at full weight; the layer undercounts this window) | 3 |
| Denver commercial construction permits, tier B | flagged rows | 476 |
| Denver commercial construction permits, tier B | permit cancelled | 3 |
| Denver commercial construction permits, tier B | rows kept as signals: B3a, $50k to $250k | 142 |
| Denver commercial construction permits, tier B | rows kept as signals: B3a, $250k or more, scored on the $250k lines | 6 |
| Denver commercial construction permits, tier B | rows kept as signals: B3b, under $50k | 325 |
| Denver concept and site plans | flagged rows (every row is flagged) | 1,348 |
| Denver concept and site plans | not industrially zoned; kept as supporting evidence by address | 1,184 |
| Denver concept and site plans | no usable street address | 3 |
| Denver concept and site plans | rows kept as signals (62 on I-A or I-B, 99 on industrial mixed use) | 161 |
| State water permits (WQCD) | flagged rows statewide | 1,867 |
| State water permits (WQCD) | flagged rows with county Denver | 161 |
| State water permits (WQCD) | flagged rows with a Denver mailing city but another county in the source (left out) | 38 |
| State water permits (WQCD) | industrial stormwater general-permit renewal wave, May to July 2024 (kept as identity and SIC evidence) | 70 |
| State water permits (WQCD) | renewals (received more than a year after issue) | 22 |
| State water permits (WQCD) | wastewater plants, hauling and detention or water-quality facilities | 4 |
| State water permits (WQCD) | airport construction and airline facilities at DEN | 24 |
| State water permits (WQCD) | portable plants with no fixed site | 0 |
| State water permits (WQCD) | flagged on acreage alone (no manufacturing SIC, no company-named facility) | 18 |
| State water permits (WQCD) | transit, public works, retail and contractor-coded sites with no manufacturing SIC | 7 |
| State water permits (WQCD) | rows kept as signals | 16 |
| APCD air permit status | flagged rows statewide (not oil and gas) | 1,064 |
| APCD air permit status | county column says Denver but AIRS prefix is not 031 (left out) | 4 |
| APCD air permit status | flagged rows with AIRS prefix 031 (Denver) | 90 |
| APCD air permit status | fuel stations and bulk fuel | 19 |
| APCD air permit status | emergency generators and fire pumps only | 33 |
| APCD air permit status | hospitals, crematories, prisons, utilities, airport and city facilities, data centres, land development | 17 |
| APCD air permit status | rows kept as signals (17 process, 4 APEN-only or exempt) | 21 |
| Mile High CRE | flagged rows statewide (industrial category) | 160 |
| Mile High CRE | flagged rows with city Denver | 54 |
| Mile High CRE | no single street address (market reports, portfolio sales, round-ups) | 35 |
| Mile High CRE | rows kept as address signals | 19 |
| OEDIT EDC approvals | flagged rows (every row is flagged) | 139 |
| OEDIT EDC approvals | rows from minutes (mostly non-industrial) | 39 |
| OEDIT EDC approvals | no Denver County or Metro Denver reference | 87 |
| OEDIT EDC approvals | rows kept as code-name candidates | 13 |

Against the Step 5 table: the kept counts for water (16), air (21), site plans (161), press (19) and OEDIT (13) are the same. UCC tier A keeps 72 where Step 5 kept 78: five fewer for assumption 5 and one for the Valor Peak drop, which Step 5 made after its table. Tier A permits keep 81 where Step 5 kept 83. Tier A registrations keep 84 where Step 5 kept 104, because of the two new agent tests. Within the water and air tables a few rows fall under a different cut than in Step 5 (the airport cut is tested before the acreage cut here); the rows kept are the same.

The 45 blanket-lien debtor rows are 39 filings. Eight of the rows, from three filings, were filed through an agent (CHTD, CSC, CT Corporation, Financial Agent Services); six of the eight are spellings of Mountain Packaging on one filing. They keep their 8 points and are marked "lender not named: filed through an agent".

## Result

- **707 rows:** 655 in Denver County (264 companies, 391 addresses), 39 county unconfirmed, 13 OEDIT code names.
- **85 Denver rows score 50 or more.**
- **Tier:** 272 rows rest on tier A flags only, 373 on tier B only, 62 on both. In the top 100: 48 tier A, 38 both, 14 tier B only.
- **Sources per Denver row:** one 454, two 149, three 36, four or more 16.
- **Fit:** strong 178, moderate 32, unknown 326, weak 119.
- **Stage:** buying equipment 18, fit-out 158, under construction 18, operating and expanding 192, planned 80, unknown 189.
- **The tail is long.** 195 Denver rows are one or more permits and nothing else, 128 are a registration and nothing else, 63 are a site plan and nothing else. 135 address rows rest only on permits under $50k; the highest is at rank 129 and 125 of them score under 30.
- **390 Denver rows are unattached addresses** (74 with a possible occupier), plus the Safeway milk plant row.

### Top 25

| Rank | Step 5 | Tier B run | Company or address | Site | Stage | Score | Tier |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | PepsiCo Beverages North America (CB Manufacturing Company, Inc.), High Point plant | 19300 E 72nd Ave | fit-out | 122.0 | A+B |
| 2 | 7 | 7 | Safeway milk plant (occupier named in a Step 3 record, not in the scraped files) | 4301 N Forest St | fit-out | 96.0 | A+B |
| 3 | 2 | 3 | Conagra Foods Packaged Foods, LLC | 4735 Florence St | fit-out | 96.0 | A |
| 4 | 3 | 2 | King Soopers, Inc. | 60 Yuma St | fit-out | 93.0 | A+B |
| 5 | 4 | 4 | Quality Linings & Painting, Inc | 8250 E 40th Ave | operating and expanding | 89.0 | A |
| 6 | 6 | 5 | Nestle Purina Petcare Company | 4555 York St | fit-out | 89.0 | A+B |
| 7 | 5 | 6 | Dawn Food Products, Inc | 4500 Lipan St | operating and expanding | 83.0 | A |
| 8 | 27 | 8 | Lakin Tire West LLC | 3750 Nome St | fit-out | 78.5 | A+B |
| 9 | 9 | 10 | Colorado Truckwashing, LLC | 5150 Brighton Blvd | buying equipment | 77.0 | A |
| 10 | new | new | Verde Prickly Pear, LLC | withheld | buying equipment | 76.5 | B |
| 11 | 10 | 11 | Titan Fittings LLC | 11795 E 45th Ave Unit 100 | buying equipment (repeat buyer) | 76.0 | A |
| 12 | 18 | 12 | Blazy Susan LLC | 10660 E 51st Ave | buying equipment (repeat buyer) | 75.0 | A+B |
| 13 | 8 | 9 | Cargill, Inc. | 4545 Madison St | operating and expanding | 74.0 | A |
| 14 | 36 | 13 | 2401 W 6th Ave LLC | 2401 W 6th Ave | operating and expanding | 73.5 | A+B |
| 15 | 41 | 18 | Unattached address | 3939 N Kearney St | fit-out | 72.0 | A+B |
| 16 | 34 | 40 | Lemon Powers Inc | 1925 S Rosemary St Unit H | buying equipment | 72.0 | A |
| 17 | new | 14 | Hearth Baking LLC | withheld | buying equipment | 72.0 | B |
| 18 | 11 | 15 | Frito Lay Inc | 11645 E 37th Ave | fit-out | 71.5 | A+B |
| 19 | 14 | 19 | Unattached address | 95 S Tejon St | fit-out | 71.0 | A+B |
| 20 | 12 | 16 | Amcor Rigid Packaging | 4990 Ironton St | under construction | 70.5 | A |
| 21 | 13 | 17 | CO-Innovate, LLC | withheld | buying equipment | 70.0 | A |
| 22 | 15 | 20 | Unattached address | 4460 N Madison St | under construction | 68.0 | A |
| 23 | new | 21 | Copeland Enterprises, Inc. | withheld | operating and expanding | 68.0 | B |
| 24 | 16 | 22 | Unattached address | 3100 N Brighton Blvd 1200 | fit-out | 67.5 | A+B |
| 25 | 17 | 23 | Pacific Air Incorporated | 2550 W 2nd Ave Unit 110 | buying equipment | 67.0 | A |

Ranks 25 to 33 are nine ties at 67: single-source UCC machinery buyers (Pacific Air, R B Machine, Custom Stone, Big Metal Additive, Native Foods, Intertech Plastics, Never Summer, Starko Gear, Skyline Motors). Order inside the tie is by latest filing date and means little.

Read the top with these cautions:

- **The rebuild lands close to both earlier runs.** 23 of this top 25 were in the tier B run's top 25, and all of this top nine were in its top ten. That was not forced: the old rows are not an input. The two newcomers are Verde Prickly Pear and Lemon Powers.
- **Safeway milk plant (rank 2, was 7)** rises on the repeat-month rule: flagged permits in three months and I-B site plans in two. The row's name and its fit come from a Step 3 record, not from the Step 4 files. The compressors in that record may be refrigeration.
- **Verde Prickly Pear (rank 10, new)** was missing from both earlier files. Its equipment filing carries zip 80126, which is not a Denver zip, so the tier B script dropped it; the geocoder places the street address in Denver, and the company's two later filings give the same street with zip 80216. The filing lists rosin presses, cartridge fillers and dryers (October 2025). A web search found nothing on the company. Not confirmed.
- **Colorado Truckwashing (rank 9)** still carries the June 2026 concept review at 5150 Brighton Blvd as a possible match. That review is very likely SRM Concrete's.
- **Lemon Powers (rank 16, was 40)** has a compressor and a CNC router in one filing. The fit rule reads the CNC as production machinery (strong); Step 5 had set it by hand to moderate.
- **Copeland Enterprises (rank 23)** lists a planetary mixer beside a 30 HP LeRoi gas package. What it makes is not confirmed. It may be oil-field kit.
- **King Soopers (rank 4)** still rests on a 2023 air permit in process and address joins. An existing bakery; treat the score as generous.
- **Conagra, Nestle Purina, Frito-Lay** have open permits joined by address. The permit layer has no description, so whether the work adds process equipment is not known.
- **Lakin Tire (rank 8)** and **2401 W 6th Ave LLC (rank 14)** sit where the tier B run put them: a no-exposure certification plus a tier B permit joined by address.

### Named companies that are not in the Step 5 file, top 100

| Rank | Company | Score | What the record shows |
|---|---|---|---|
| 10 | Verde Prickly Pear, LLC | 76.5 | Rosin presses, cartridge fillers, dryers, October 2025. New in v3. Not confirmed |
| 17 | Hearth Baking LLC | 72.0 | Gas deck oven, December 2025 |
| 23 | Copeland Enterprises, Inc. | 68.0 | Two May 2025 filings: planetary mixer, 30 HP gas package. Not confirmed |
| 47 | Bakery Four L.L.C. | 61.0 | Electric roaster on an equipment contract, October 2025 |
| 48 | Direct Polymers LLC | 61.0 | Granulator, January 2025. Ground-truth project X06. Web check today: plastics recycler at 3601 E 44th Ave |
| 73 | DBTL Capital Corp | 53.0 | Industrial stormwater permit, SIC 3993 (signs), 2518 S Delaware St, plus a tier B permit joined by address. Was an unattached address at 149 |
| 74 | Sleeping Giant Brewing Company | 53.0 | 40-head can filler, February 2024. The wording may describe an auction |
| 80 | Primo Brands | 51.5 | Water permit SIC 3121, 11700 E 47th Ave, plus a tier B permit joined by address. Was an unattached address at 205 |
| 88 | Colorado Supply Chain Center | 49.0 | Stormwater permit SIC 2045 (the permittee is a pizza chain's dough plant), 10252 E 51st Ave, plus tier B permits joined by address |

### Rows checked on the web

- **County:** 151 addresses through the Census geocoder, 96 of them new today.
- **Carried over unchanged from the first run:** 22 fit texts (list in `v3_config.py`), the Valor Peak and Bron Tapes drops, and the names the first run searched without confirming (Colorado Truckwashing, CO-Innovate, Pacific Air, R B Machine, Custom Stone, Native Foods, Starko Gear, Skyline Motors, Lakin Tire, American Building Supply, Manny's Welding, Lemon Powers, B & B Machine, 2401 W 6th Ave LLC, Arclin, Accu-Tube, Holcim, RC Services, 1395 South Acoma, ADM, Nauhaus).
- **Carried over from the tier B run** (search titles only, not used in the fit column): Hearth Baking (a bakery opening a second Denver location), Bakery Four (a Berkeley bakery planning to expand), Sleeping Giant (a contract brewer), Copeland Enterprises and Northwest Confections (not confirmed).
- **Added today, for named companies in the new top 50 that had no check: three.**
  - Acme Manufacturing Company (rank 45): confirmed. The company site describes a maker of metal products (threaded rod, chain, landscape edging, door hardware) headquartered in Denver. The page gives no street address.
  - Direct Polymers LLC (rank 48): confirmed. A recycling trade directory lists a plastics recycling plant producing flakes and pellets at 3601 E 44th Ave, Denver.
  - Verde Prickly Pear, LLC (rank 10): two searches, nothing usable. Fit rests on the filing.

## Check against the ground truth

**7 of 17 Denver projects appear, the same seven as the tier B run. Three are matched by name and four by address only.**

| Project | Step 5 | Tier B run | v3 | How |
|---|---|---|---|---|
| D01 PepsiCo | 1, 113 | 1, 185 | 1, 191 | Name and address. Rank 191 is the old Brighton Blvd bottling plant |
| X06 NextRun hub (Direct Polymers) | not ranked | 45 | 48 | Name and address. Granulator filing |
| D11 Elemental Bakery | not ranked | 225 | 173 | Name and suite. Blanket lien, plus a press mention of the address |
| D14 SRM Concrete | 9 | 10 | 9 | Address only, on the truck wash row |
| D15 Maybell Quantum | not ranked | 304 | 310 | Address only: 3821 N Steele St, small permits |
| D13 Vinyl Me Please plant | not ranked | 588 | 536 | Address only: 4201 N Brighton Blvd, one $0 permit |
| D07 BrewDog Denver | not ranked | 555 | 560 | Address only: 3950 Wynkoop St, two $0 permits |
| D02, D03, D04, D06, D08, D09, D10, D12, X12, X13 | not ranked | not ranked | not ranked | No usable flagged record, as before |

- Matched by name: 3 projects (PepsiCo, Direct Polymers, Elemental Bakery). Only PepsiCo and Direct Polymers land where a rep would see them.
- Matched by address only: 4 projects. SRM appears only because the truck wash at its site bought a compressor. The other three are among 390 unattached addresses and nothing on the row names the tenant.
- **Nothing was tuned to the 17.** The first complete run of the rebuild gave the same seven (PepsiCo 1 and 201, Direct Polymers 51, Elemental 178, SRM 9, Maybell 326, Vinyl 576, BrewDog 600). The changes made after that run were: the numbered-street fix to the address key, the two new agent tests, the change-of-contractor rule, the stormwater project-name fit, the primary-SIC rule, trimming the fit word lists, the stricter home-address test, the cap on listed support rows, and the fixes that followed an independent review (below). None was made because of a ground-truth project and none changed which projects appear. The small rank shifts above come from other rows moving.
- The zoning-only small-permit flag (Step 4b) was chosen knowing it would reach the Maybell, Vinyl and BrewDog addresses, so those three are not independent evidence that the rule works. That caution from the tier B notes still stands.

## Sensitivity of the Denver top 25

| Re-weighting | Rows of the top 25 that change | Top 10 the same set |
|---|---|---|
| Recency doubled | 0 | yes |
| Recency removed | 3 | yes |
| Source bonus doubled | 4 | no |
| Source bonus removed | 8 | no |
| Tier B points halved | 4 | no |
| Tier B points doubled | 5 | no |

- **Recency removed:** in come 890 N Navajo St, Mannys Welding and Acme Manufacturing; out go Copeland Enterprises, 3100 N Brighton Blvd and Pacific Air.
- **Source bonus doubled:** in come 890 N Navajo St, 5590 N Joliet St, 2323 W Mulberry Pl and American Building Supply; out go Hearth Baking, CO-Innovate, Copeland and Pacific Air.
- **Source bonus removed:** eight single-source machinery buyers come in (R B Machine, Custom Stone, Big Metal Additive, Native Foods, Intertech, Never Summer, Starko Gear, Skyline Motors); out go Lakin Tire, 2401 W 6th Ave LLC, Frito Lay, Amcor and four addresses.
- **Tier B points halved:** in come R B Machine, Custom Stone, Big Metal Additive and Native Foods; out go Verde Prickly Pear, Hearth Baking, Copeland and 2401 W 6th Ave LLC.
- **Tier B points doubled:** in come Bakery Four, Direct Polymers, Sleeping Giant, 2323 W Mulberry Pl and 5590 N Joliet St; out go Amcor, CO-Innovate, Pacific Air and two addresses.

Reading: the food plants, PepsiCo, the Safeway site and Titan hold in every run. The contest is still between single-source machinery buyers and multi-source rows built on address joins. The source bonus is the weight the top 25 is most sensitive to. Tier B at the agreed points changes four or five places at the bottom of the top 25, mostly the 30-point equipment-word filings.

## Rank changes against the tier B run

701 of the 707 rows match a row in the tier B file. **481 moved more than 10 places.** All 481 are in `rank_changes_v3.csv` with the old and new rank, both scores, the points that changed and a cause.

| Cause | Rows |
|---|---|
| Score unchanged; other rows moved around it (mostly large tie groups at 39, 34 and 18 points, and the 42 rows that left the list) | 318 |
| Source bonus differs: a support row found or lost (one name at the address, a same-name filing, a press mention) | 85 |
| Fit rule gives a different class | 24 |
| Was named after a stormwater project (12) or was a company row that is now a possible occupier (4); now an address row | 16 |
| Repeat-month points, now counted for every row of 12 or more | 13 |
| Now named from a state permit at the address; address rows score half | 9 |
| Recency points differ | 3 |
| Stage rule gives a different stage | 4 |
| Signal points differ (including the six large tier B permits) | 7 |
| Moved from the Denver section to county unconfirmed | 2 |

The moves that matter, in or out of the top 100:

| Row | Tier B run | v3 | Why |
|---|---|---|---|
| Lemon Powers Inc | 40 | 16 | Fit moderate to strong: the filing names a CNC router |
| 2323 W Mulberry Pl | 49 | 35 | Site plans in three months now earn repeat points |
| 18309 E 65th Ave | 171 | 43 | Was named after a stormwater project (an auto repair shop) and halved; now an address at full permit points. Parcel class is auto service, fit moderate |
| 3480 S Poplar St | 94 | 50 | The $2.1M tier B new-building permit now scores 25, not 12 (assumption 14). Parcel class is auto service |
| 3490 Park Ave | 72 | 54 | Parcel-class fit (auto service garage) now applies to every address row |
| 3625 E 48th Ave | 179 | 55 | Was named after a stormwater project; now an address with I-B site plans at full points |
| 3875 Walnut St | 80 | 56 | Was named "3875 Walnut St. Multifamily" and halved; now full permit points, and fit weak because the project name says housing |
| 1485 40th St | 92 | 65 | Same as above ("GWS Residential") |
| DBTL Capital Corp, 2518 S Delaware St | 149 | 73 | Now named from its industrial stormwater permit (SIC 3993); fit strong |
| 5440 N Roslyn St | 123 | 77 | Was named after a stormwater project and halved |
| Atlas Metal and Iron Denver | 169 | 79 | Three liens under the permittee's name at the address now count as support and bring recency points |
| Primo Brands, 11700 E 47th Ave | 205 | 80 | Now named from its water permit (SIC 3121); fit strong |
| 3869 N Steele St 1258 | 95 | 81 | Repeat-month points |
| 1160 S Colorado Blvd | 106 | 64 | A $275k tier B permit now scores 18, not 12; one registration at the address counts as support |
| Colorado Supply Chain Center, 10252 E 51st Ave | 51 | 88 | Now named from its stormwater permit, so its tier B permits score half |
| 4001 N Monroe St | 104 | 90 | Repeat-month points |
| 2000 N Broadway | 122 | 96 | Parcel-class fit (auto service) |
| 11100 E 45th Ave | 158 | 99 | Repeat-month points and one UCC name at the address |
| 3930 Blake St | 126 | 100 | Two flagged registrations at a multi-tenant address are now possible occupiers; the permit scores in full |
| 4665 N Paris St 212 | 90 | 116 | More than one name at the address, so none counts as support |
| 4895 N Peoria St | 82 | 143 | Fit weak: assessor class is Industrial-School |
| 845 N Navajo St (KT8 Industries) | 61 | 168 | Was a company row on a flagged registration; now a possible occupier of an address row (assumption 8), so the name-based fit no longer applies |
| 3463 Walnut St | 73 | 172 | Fit weak: assessor class is multi-unit apartments |
| 2670 S Delaware St (Northwest Confections) | 88 | 211 | Was a company row on a blanket lien; now a possible occupier of an address row |
| 4511 E 46th Ave | 70 | 505 | The $2.2M permit is on a parcel classed County Jail. The tier A parcel cut now removes it; two $0 permits remain |
| Radical Botanicals, 44 Cook St Ste 100 | 34 | 660 | Moved to county unconfirmed: the suite has 490 registrations, so it is an agent address, not a site. Score 59 |

**Rows in the tier B file that are not in v3 (42):** 26 registrations at agent, virtual-office or mailbox addresses under the new tests (16 of them at 1500 N Grant St; all were registration-only rows); eight with a non-Denver mailing city that the geocoder places outside Denver (assumption 5); five merged into another row (Mountain Packaging Est. 2007, two Highline Machining entities, QB Energy Operating, and Solutions Machining, a co-debtor of Green Machine 303); two folded into address rows as possible occupiers (Secret Garden Manufacturing, FDS Manufacturing); one permit on a cemetery-building parcel (5201 N Brighton Blvd, was rank 100).

**Rows in v3 that are not in the tier B file (6):** Verde Prickly Pear (rank 10); 2975 N Iola St (rank 182), a $495k tier A permit on a car-wash parcel that the first run cut and the parcel rule as written keeps; and four tier B companies with a Denver mailing address in a zip outside the Denver list, now in the unconfirmed section (Family Machine, Bayou Lane Fabrication, Mikuts Manufacturing, Rocky Packaging and Supply).

## What the data could not show

- **Who is behind a Denver permit.** 390 of 655 Denver rows are addresses with no company attached. 74 carry a possible occupier, which is one name from a registration or lien at the street address and nothing more.
- **What a permit is for.** The layer has no description. A $2M alteration at a food plant may be a new line or a new roof.
- **Compressed air itself.** Six filings in scope name a compressor: a truck wash, an oil-change shop, a tyre and welding shop, a woodworking shop, and in the unconfirmed section a tyre shop and a body shop marked dissolved. Eight more are towable construction units. No plant-scale compressor purchase is visible in Denver County.
- **Blanket liens.** Most equipment loans to small makers read "all assets". 45 such debtor rows (39 liens on makers) are in the ranking at 8 points, three of the liens with the lender hidden behind a filing agent.
- **Whether a registered company operates in Denver.** 147 flagged registrations sit at agent or mailbox addresses. 128 Denver rows are a registration and nothing else.
- **County for some state permits.** The water permit county field is wrong for at least two rows (Sealy Mattress, Lineage Logistics). They are in the Denver section because the source says Denver.
- **Anything after 2026-08-07 in water permits,** air permit applications that left the six-month window, and permits received but not yet issued.
- **Plant status.** PepsiCo's opening date is still not confirmed.
- **What Verde Prickly Pear, Copeland Enterprises, CO-Innovate and the other unconfirmed names make.** The fit column says "not confirmed" or names the filing where that is all there is.

## Independent review

A second reviewer, who did not write the scripts, traced all evidence rows back to the raw Step 4 files with its own script, re-added every score, compared the points table with the brief and checked about 90 numbers in this note. Arithmetic, points table, reproducibility and the ground-truth handling were confirmed. It found these defects, all fixed before the files were saved:

- Apartment addresses of 11 small companies were being shown (an "Apt" number counted as a suite), and two withheld addresses appeared inside collateral text. Fixed (assumption 22).
- Mailbox buildings escaped the agent test because every box number is different. Fixed with the building test (assumption 12); 18 rows left the list.
- Six tier B permits of $250k or more were scored at 12. Fixed (assumption 14).
- The "lender not named" mark was missing from the evidence file; four unattached addresses in the unconfirmed section had a county next step in place of "tenant not identified"; three numbers in this note were wrong. Fixed.
- Unflagged office permits were being attached as support to registration-only companies in multi-tenant buildings. Fixed (assumption 20).

Left as they are and disclosed above: person-named registered entities (assumption 24), the cap on listed support rows (assumption 23), terminated water certifications scoring as new (assumption 17), and same-name support rows from other addresses, some of which may be a different company with the same name (for example other "Mountain Packaging LLC" registrations in Parker and Boulder; worth 1.5 points).

## What could not be finished

- **The scripts were written and run in the cloud workspace against copies of the Step 4 files staged from Matthew's computer.** The run on the computer itself, from `step5-analysis\v3\scripts\`, is described in the chat summary for this run: check there whether it was done. The scripts use the standard library only and the geocode cache is complete, so the same command should reproduce these files exactly.
- **The project copy was not updated.** The project is full; the v3 files are in this folder only.
- Everything else in the brief was completed.

## How to re-run for another county

`python3 build_v3.py <step4-scrape> <step5-analysis>` rebuilds Denver. For another county:

1. **Zip list.** Build `<county>_zip_share.json` from the Census 2020 ZCTA to county file (share of each zip's land area in the county) and point `build_v3.py` at it. The 99% and 10% thresholds stay.
2. **County tests in `v3_signals.py`.** Water permits: change the county name in the two `== "DENVER"` tests. Air permits: change the AIRS prefix `031`. UCC and registrations: change the mailing-city test (`DENVER`) to the county's main mailing cities.
3. **Geocoder.** The cache is keyed by address, so a new county starts nearly empty. Statewide, about 2,400 flagged UCC and registration rows across both tiers have a Colorado address, and only those in split zips need a lookup. At one a second with the 150-second budget a large county may take several re-runs of the same command; raise `--budget` where the shell allows.
4. **The two Denver layers have no equivalent elsewhere.** Without them there are no address rows, no fit-out stage and no possible occupiers; the ranking rests on UCC, air, water, registrations, press and OEDIT. Remove the permit and site plan blocks or leave them: they only read Denver files.
5. **Cuts.** Keep all of them except the DIA and airport cuts, which are Denver only. The agent-suite rule works anywhere. Expect construction stormwater (20 points) to matter outside Denver; none survives the cuts here.
6. **Ties and web checks** in `v3_config.py` are Denver facts. Clear `KNOWN_TIES`, `STEP3_OCCUPIERS` and the web-check tables for another county, and replace the ground-truth list if there is one.
7. **Oil and gas** stays out through the Step 4 operator list.

## Decisions for Matthew

1. **Assumption 8, which side holds an address.** A registration or blanket lien at an address with its own permit now makes the company a possible occupier rather than its own row (5 rows today, including KT8 Industries and Northwest Confections). An equipment filing still makes the company the row and halves the permit. Say if you want it the other way for either case.
2. **Assumption 9, stormwater project names.** Twelve addresses moved more than 10 places because their permits now score in full. Five are in the top 80: 18309 E 65th Ave (an auto repair shop by its project name), 3625 E 48th Ave, 5440 N Roslyn St, and 3875 Walnut St and 1485 40th St, which are housing projects on industrial zoning and are marked weak. If you would rather keep the Step 5 treatment, say so.
3. **Assumption 15, repeat months at 12 points.** This is the brief's wording, and it lifts the Safeway milk plant from 7 to 2 and several site-plan addresses by 3 to 6 points. If repeat points should need a stronger signal (18 or more), say so.
4. **The unconfirmed section (39 rows).** It holds real machine shops that the geocoder places in Adams County with Denver mailing addresses: Imperial Machining (70), Quattro Machining (60), Vexor (59), Harrelson (56), Per Revolution Machining (56). Also Radical Botanicals (59) at an agent suite. Decide whether these belong to this territory.
5. **Withheld addresses (130 rows, 12 in the top 60).** Hearth Baking, CO-Innovate, Copeland, R B Machine, Big Metal Additive, Never Summer, Starko Gear, Skyline Motors, Verde Prickly Pear and others have a real street address in the source row. Say whether a UCC debtor address of a company that finances production machinery can be shown.
6. **Verde Prickly Pear (rank 10).** New and unconfirmed. Worth one look before a call.
7. **The water permit county field.** Sealy Mattress and Lineage Logistics are almost certainly not in Denver County. Say whether water-permit addresses outside Denver zips should go through the geocoder too.
8. **Still open from earlier runs:** parcel owner names for the 390 unattached addresses; whether to add "bread", "beer" and Geneva Capital to the Step 4b lists; whether to go statewide.
