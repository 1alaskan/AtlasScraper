# Weld County, step 4: analysis notes (v3 method, county layers loaded)

Run 2026-11-06. Three builds: `run1_nolayers` (statewide sources only, 236 ranked), `run2_layers` (county layers added, 357 ranked), `run3_webchecks` (web checks on the top 60 applied through the config, 357 ranked, final). `verify_v3.py` recomputes every score from the evidence file: 0 problems on the final build.

Files in this folder: `weld_ranked_accounts.csv` (357 rows), `weld_evidence.csv` (961 source rows behind them), `weld_manual_lookup_list.csv` (24 addresses or names for a hand lookup), `weld_county_incentives.csv` (the 18 county Tax Incentive Agreements, the side list), `weld_flagged_sales.csv` (188 assessor sales of $2M or more on industrial or commercial-industrial parcels), `weld_side_list_matches.csv` (45 ties between the side lists and ranked rows), `weld_frs_names.csv` (empty: no EPA registry facility at any unattached address scoring 40 or more), `web_checks_weld.md` (the 60 web checks and their sources), `v3_report_run3.md` and `run3_webchecks/v3_report.json` (every count in this note), the raw build outputs under `run*/`, the build logs, `review_findings.md` (the independent review) and the two helper scripts `side_list_weld.py` and `frs_names_weld.py`. The county config is `v3/scripts/county_configs/weld.py`; the county-layer loader is `v3/scripts/v3_local.py` (unchanged for Weld).

## Assumptions (read first)

1. **Scope.** Weld County sites. A row is in scope when its county is stated by the source (water permits), its AIRS ID carries the 123 prefix (air permits; 14 rows whose county column says Weld but whose prefix is not 123 were left out as office addresses), its zip is wholly inside Weld County (Census 2020 ZCTA file, `weld_zip_share.json`, 26 zips wholly inside, 17 straddling), the Census geocoder places the address in Weld County (174 addresses looked up: 65 Weld, 44 Larimer, 17 Boulder, 9 Adams, 3 Broomfield, 36 no match), or the row comes from the Weld permit or planning layers (Frederick, Greeley, Fort Lupton and unincorporated Weld lie wholly in Weld). Rows with a Weld mailing city and no other basis are kept in a separate "county unconfirmed" section (24 rows). Rows in a split city (Windsor, Johnstown, Erie, Longmont, Brighton, Berthoud, Lochbuie, Thornton, Northglenn) that the geocoder places outside Weld were dropped (13 Mile High CRE rows), not kept as unconfirmed.
2. **The points table, word lists, normalisers and fit rules are Denver's, unchanged** (`v3_config.py`). The Denver rebuild was checked byte for byte at the start of this run (2026-11-05, identical). Nothing was tuned to the Weld ground truth.
3. **County layers.** Six of the nine Weld step 3 files are read through the county-layer loader: Frederick building permits as the permit layer (no valuation in the layer, so tier A is a construction permit type with an industrial word, as for Adams County), and the Weld planning cases, Weld site plan reviews, Frederick development applications, Greeley TRAKiT projects and Fort Lupton projects as the planning layer. The loader's holds apply: low-value permit types (signs, fire, racking, generators, trailers, demolition and the like) are held at B3b whatever step 3 said, commercial-use buildings at B3a, and cancelled permits are cut (2 tier A, 18 tier B).
4. **No slot in the method (Matthew's decision, 2026-11-06: side list, no code change).** The county Tax Incentive Agreements, the assessor sales and the personal property accounts are not scored. They are published beside the list and every ranked row that matches one by exact name or exact address carries the match in `next_step` (35 rows). The scores therefore stay comparable with Denver and Adams, and the single best Weld source sits beside the ranking rather than inside it.
5. **Web checks.** 60 top-ranked rows from the second build were checked on the web for what the company makes at the site (one or two lookups each; `web_checks_weld.md` lists the source for every one). 42 were confirmed and applied through `WEB_CHECKS` in the config (15 strong, 10 moderate, 17 weak); 17 could not be confirmed in two lookups and keep the pipeline's own fit (`WEB_NOT_CONFIRMED_V3`); one (an unattached address) had nothing to check. Fit points: strong +15, moderate +6, unknown 0, weak -15. The downgrades are the Weld noise profile the air-permit rule cannot see: gravel pits and dirt mines (J-2 Contracting's Sunset pit, Asphalt Specialties' Marcovich pit, SVW Farms, Colorado Sand), rail transload and fuel terminals (USRL Hudson, Cando Rail, Western Proppants), a dairy digester (CEA Greeley), a landfill (Waste Management), medical waste (Stericycle), a bulk fuel plant (Agfinity), a dairy, a battery storage site, a water utility, a plumbing contractor and a fire district.
6. **Web drops.** 5507 Distilling: the UCC collateral text itself places the distillation equipment on Fifth Street, Loveland (Larimer County), and the Weld zip is a mailing address. The config's `WEB_DROPS` hook reaches UCC tier A and Mile High CRE rows only; this is a tier B lien, so the row stays at rank 8 with the finding in `next_step`. The scripts were not changed for Weld.
7. **Mailing-address trap.** 24 rows sit in the "county unconfirmed" section (`county_basis` = Weld mailing address, county unconfirmed). Eclipse Engineering (rank 21, 2540 S Main St, Erie) is in the main section on its zip share but Erie straddles Boulder and Weld and the parcel's county was not confirmed; Legacy Pie (rank 22) has Denver shops and no Windsor production site on the web.
8. **Person-named entities.** None of the top 60 is a private individual's name; `PERSON_NAMED` is empty for Weld. Registered entities that carry a founder's name (Jim's Automotive Machine Shop, C. Simpson Farms) are businesses and stay.
9. **Local noise cuts.** The water-permit airport cut (`WAT_AIRPORT`) removed 3 rows (airport construction and airline facilities). No other Weld-specific cut was added; the Denver cuts removed, among others, 87 water permits flagged on acreage alone (schools, parks, housing, roads, pipelines), 45 transit and public-works sites, 63 rows of the May to July 2024 industrial stormwater renewal wave (kept as identity evidence), 15 fuel stations and 8 emergency-generator-only air permits. The full cut table with counts is in `v3_report_run3.md`.
10. **EPA registry names.** 10 unattached addresses score 40 or more; none matches a facility in `frs_filtered.csv` (12,404 Weld rows, mostly oil and gas) on house number and street, so `weld_frs_names.csv` is empty. Parcel owner names were not used (they need Matthew's sign-off).
11. **No Atlas Copco data; no contact with anyone; no records requests; no browser-only portal opened; no personal names.** OEDIT code names are never decoded; the 8 OEDIT rows are "possible" at most. The step 2 ground-truth corrections are not applied.
12. **Windsor** has no permit layer in this build (manual download source). Its sites appear only through the statewide sources, the county assessor sales and the incentive agreements.

## Points table (fixed, not retuned; identical to Denver and Adams)

The table in `step5-analysis/adams/adams_analysis_notes.md` applies unchanged, with "County permit (Frederick layer)" in place of the Adams layers. In short: UCC naming an air compressor or a B1a process word 30; UCC naming production machinery 25; air permit for process units 25; county permit new building or addition on industrial property 22; construction stormwater permit with a manufacturing SIC or company-named facility 20; county alteration or tenant finish on industrial property 18; B3a permit 12; APEN-only or exempt air permit, no-exposure certification, site plan on heavy industrial zoning 12; weak UCC word, towable compressor, press story naming the company 8; vague or blanket lien 8; tier A registration, mixed-use site plan, B3b permit 6; address-only press story, OEDIT code name 5; generic lien, other site plan 4; tier B registration 3; cut row 2. Independent sources +8 each beyond the first (max 24), support-only +3 (max 6). Recency +15 within 12 months, +8 within 24. Stage: buying equipment +12, fit-out +12, under construction +8, operating and expanding +8, planned +4. Fit: strong +15, moderate +6, weak -15. Possible matches score half.

## Method

1. Scope records to Weld County (assumption 1). 2. Cut known noise, counted per cut (`v3_report_run3.md`). 3. Resolve records to companies by normalised name and address, keeping every name variant (225 company accounts; 4 co-debtor merges, 3 same-address leading-word merges). 4. Attach address-only records (permits, site plans) to companies by address: 15 addresses named from county permit rows, 3 from a state permit operator, 32 attached to a company as possible, 18 with one unflagged name as a possible occupier, 223 left as their own candidates. A contractor is not the account. 5. Pull every row for each candidate from every source, flagged or not (312 support rows not listed on their own). 6. Score tier A and tier B signals together under the fixed table; rank. 7. Name unattached addresses from the EPA registry (none matched). 8. `verify_v3.py`: 0 problems.

## Result

357 ranked rows: 325 in Weld County (206 companies and 119 addresses), 24 county unconfirmed, 8 OEDIT code names. 77 rows score 50 or more. Tier: 186 rows on tier A evidence, 17 on both, 154 on tier B only; of the top 100, 84 are tier A. Sources per row: 267 with one, 72 with two, 17 with three, 1 with four. Stage: operating and expanding 113, unknown 92, fit-out 62, planned 37, buying equipment 29, under construction 24. Fit: strong 148, moderate 14, unknown 161, weak 34.

**How many are solid.** 53 rows are strong fit, county confirmed and score 50 or more; 15 of those were confirmed on the web as plants or shops in Weld County, and the other 38 rest on the pipeline's own evidence (a named machine in a UCC filing, a manufacturing SIC on a state permit, or process units on an air permit). The rest of the list is unconfirmed: single-source UCC rows at a withheld address, planning cases with no occupier, and addresses with no company attached.

Top 25 (one line of evidence each):

| Rank | Company | Site | Score | Stage | Fit | Evidence |
|---|---|---|---|---|---|---|
| 1 | Agilent Technologies | 7051 Eagle Blvd, Frederick | 91.0 | fit-out | strong (web) | Air permit modification for the pharmaceutical plant; Frederick permits for Project Endeavor (new manufacturing building and warehouse); 2022 county incentive agreement |
| 2 | Boulder Scientific Company | 4161 Specialty Pl, Longmont (Weld) | 78.0 | operating and expanding | strong (web) | Air permits for the Specialty Place catalyst plant and the Mead chemical plant; state water permit SIC 2899 |
| 3 | Ursa Major Technologies | 19750 County Road 7, Berthoud (Weld) | 75.0 | operating and expanding | strong (web) | Air permit for solid-fuel testing; UCC for an EOS M450 metal 3D printer; water permit SIC 3364 |
| 4 | Old School Industries | Dacono (address withheld) | 73.0 | buying equipment, repeat | strong (web) | UCC 2026-04: DMG Mori CMX 1100 V vertical mill and a second machine |
| 5 | High Plains Steel Services | 2055 Howard Smith Ave E, Windsor | 73.0 | operating and expanding | strong (web) | UCC 2025-01: angle processing line with a 20 HP compressor and dryer; water permit SIC 3441 |
| 6 | Underground Manufacturing | 2950 Colorful Ave, Longmont (Weld) | 72.5 | operating and expanding | strong (name) | Air permit 2026-06 for an HP Indigo 25K press; UCC from a packaging supplier; not confirmed on the web |
| 7 | Quantum J's Canning | 1725 Skyway Dr, Longmont (Weld) | 72.0 | buying equipment | strong (UCC) | UCC 2026-09: 30-ton chiller with dual compressors, conveyor; no web presence |
| 8 | 5507 Distilling | zip 80634 (Greeley mailing) | 72.0 | buying equipment | strong (UCC) | UCC 2026-01 blanket lien on distillation equipment; the collateral text places it in Loveland (Larimer): flagged |
| 9 | Loudwire Diesel | Fort Lupton (withheld) | 71.0 | buying equipment | strong (UCC) | UCC 2025-12: Superior 36x125 conveyor and a screening plant; reads as aggregate, not confirmed |
| 10 | Jim's Automotive Machine Shop | Gill (withheld) | 70.0 | buying equipment, repeat | strong (UCC) | UCC 2026-07 and 2024-01: Haas CNC machining centre and lathe |
| 11 | Pioneer Press of Greeley | 2965 S 27th Ave, Greeley | 70.0 | operating and expanding | strong (web) | Air permit modification 2024-09 for printing; UCC for a Sharp production printer |
| 12 | Impact Equipment Rentals | 8127 W I-25 Frontage Rd, Erie (Weld) | 69.0 | buying equipment, repeat | unknown | Two UCC filings on compressors (a rental fleet, most likely); not confirmed |
| 13 | Swift Beef Company (JBS) | 800 N 8th Ave, Greeley | 69.0 | operating and expanding | strong (web) | Facility-wide air permit and WWTF flare; UCC 2025-06; water permit SIC 2011 |
| 14 | Schlosser Signs | 31815 Great Western Dr, Windsor | 68.5 | buying equipment | moderate (web) | UCC 2026-06: Kaishan rotary screw compressor, paint booth, CNC router; the site is the former Microvast building (assessor sale 2024-08) |
| 15 | T&T Grinders | Kersey (withheld) | 68.0 | operating and expanding | strong (UCC) | UCC: Mighty Giant tub grinder, wheel loader; mobile grinding likely, not confirmed |
| 16 | Raptor Materials | 8490 Highway 66, Platteville | 68.0 | operating and expanding | moderate (web) | Air permits for a screen and material extraction; ready-mix plant on site; water permit SIC 3273 |
| 17 | JW Fabrication | Ault (withheld) | 68.0 | operating and expanding | strong (web) | UCC 2025-06: Timesaver finishing line; metal fabrication shop |
| 18 | DesignLogic | Windsor (withheld) | 67.0 | buying equipment | strong (web) | UCC 2025-12: Haas CNC; precision milling and turning shop |
| 19 | Cutting Edge Steel | Dacono (withheld) | 67.0 | buying equipment | strong (web) | UCC 2026-08: Trumpf laser; structural metal fabricator |
| 20 | Pneu Line Supply | 2881 31st Ave, Greeley | 67.0 | buying equipment | strong (web) | UCC 2026-07: Nissei 55-ton injection moulding machine; cleanroom moulder |
| 21 | Eclipse Engineering | 2540 S Main St, Erie (county unconfirmed) | 67.0 | buying equipment | strong (web) | UCC 2026-04: Haas CNC and lathe; engineered seal maker; Erie parcel county not confirmed |
| 22 | Legacy Pie Co. | Windsor mailing (withheld) | 67.0 | buying equipment | strong (UCC) | UCC 2026-04: Vemag Robot 500 depositor; web shows Denver shops only |
| 23 | Absolute Countertops & More | Fort Lupton (withheld) | 67.0 | buying equipment | strong (UCC) | UCC 2026-01: Park Industries CNC sawjet and digital slab station |
| 24 | Big Thompson Compost | Johnstown (withheld) | 67.0 | buying equipment | strong (UCC) | UCC 2025-11: stacker conveyor and track crusher; compost or recycled aggregate likely |
| 25 | Live Sharp Industries | 13782 E I-25 Frontage Rd, Mead | 67.0 | buying equipment | strong (UCC) | UCC 2025-10: CNC machining centre; no web presence |

Read by eye, 13 of the top 25 are confirmed plants or shops, 3 are moderate-fit trades (signs, ready-mix, equipment dealer), 8 are small UCC-only firms with a named production machine and no web footprint, and 1 (5507 Distilling) is probably outside the county.

## The check against known projects

Six known projects (five confirmed Weld, Microvast a best guess). Three appear:

- **X26 Agilent: rank 1** (name). Air permit, four Frederick permits naming Project Endeavor, the 2022 county incentive agreement in the side list.
- **X28 TFP Nutrition: rank 68** (Texas Farm Products, name) and **rank 92** (J.D. Heiskell & Co., the WQCD permittee, name). Air permit 06WE0240 at 450 N Front St; the 2024-10 county incentive agreement and the 2023-06 land purchase in the side lists.
- **C35 Hirsh Precision: rank 326** (name; a 2025 registration row at 4300 Godding Hollow Pkwy) and **rank 159** (the address, with Hirsh as a possible occupier). The plant opened in October 2023, before the window, so only trailing records remain.

Three are missed, for reasons the data shows:

- **C34 Colorado Premium** (opened February 2024): the only 2024 or later state record is a WQCD pretreatment billing row (COPB90825) with no address and no county, so it fails scope; the 32 UCC rows under the name are at the old 2035 2nd Ave plant and unflagged. The 2023-07 county incentive agreement is in the side list.
- **C36 Sphere Renewables** (opened June 2024): the construction stormwater permit was received 2023-05-31, before the window; the Fort Lupton planning layer holds a 2026 "Sphere Renewables Lot 3 Site Plan" (SPR26-002) with no address, so it could not be attached. That case is a live expansion signal and is listed in `weld_county_incentives.csv` against the 2022 agreement.
- **X27 Microvast** (announced 2023, consolidated away): no record under the name after 2024; the site at 31815 Great Western Dr was sold in August 2024 and now carries Schlosser Signs (rank 14). The side lists hold the 2023 agreement and both sales.

Nothing was tuned to these projects. Three of six is the same picture as Denver and Adams: the statewide sources catch an expansion while it is under way and miss plants that opened before the window; the county incentive agreements, which caught all six before press, sit beside the list by decision.

## What the county layers added

Without the county layers: 236 ranked. With them: 357 (plus 91 rows based on the Frederick permit layer and 28 on the planning layers). Agilent moved from rank 79 to rank 1 once its Frederick permits were read. Frederick is the only Weld town with a permit mirror, so the permit layer covers one town; the planning layers cover unincorporated Weld, Greeley, Frederick and Fort Lupton but carry an address on fewer than half their rows (66 planning rows had no usable street address), which is why 119 of the 325 Weld rows are addresses with no company attached.

## The side list: county incentive agreements

18 agreements, 7 matched to a ranked row (Agilent rank 1 by name; TFP Nutrition rank 68 by address; Hirsh rank 326 by name and rank 159 by address; Microvast's address at rank 14, now Schlosser Signs; TruLog's address at rank 133 as a possible occupier; Airxcel/Aqua-Hot's address at rank 289 as a possible occupier; Scotts/Hyponex rank 23 by lead word, possible). 11 are not in the ranked list at all, and they are the plainest leads in the county: BAE Systems (Project Mercury, 4120 Specialty Pl, agreement 2026-09, Phase I cap $13.8M), US Engineering Metalworks (Johnstown, 2026-09), Motherload Co Packing (Hudson, 2026-09), EcoMod (Hudson, 2025-08), Charm Industrial (Fort Lupton, 2025-05), Owens-Brockway Glass (Windsor, 2023-07), Norfolk Iron and Metal (Windsor, 2022-12), Sphere Renewables, Colorado Premium, Colorado Stud Company, Gotham Greens. Of the 188 flagged assessor sales, 33 matched a ranked row.

## What the data could not show

- Valuation on any Weld permit (Frederick's mirror carries none), so tier A rests on permit type plus an industrial word.
- Building permits for Greeley (behind the eTRAKiT login), unincorporated Weld County (Accela, not mirrored), Windsor (manual PDFs), Evans, Firestone, Dacono, Mead, Milliken (no public feed). The county's largest industrial sites outside Frederick appear only through state permits, UCC filings and the side lists.
- Occupiers of the 119 unattached addresses and of the 66 planning cases with no address.
- Whether a UCC-only firm at a withheld address runs a plant or a mobile fleet (Loudwire Diesel, T&T Grinders, Big Thompson Compost, Impact Equipment Rentals).
- Any county placement for the 24 unconfirmed rows and the Erie parcel at rank 21.
- Lead time against a compressor purchase: no source here says when a compressor is bought.

## Review

An independent review agent audited these outputs against the skill and the raw data after the final build; its findings are in `review_findings.md` and summarised in the report to Matthew.
