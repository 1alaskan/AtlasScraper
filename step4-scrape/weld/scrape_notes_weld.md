# Weld County, step 3: scrape of the nine build sources

Run 2026-11-06 from the cloud shell by four agents (`laserfiche`, `county_agol`, `frederick`, `greeley_fortlupton`), each following the `datasource-validator-scraper` skill. This file is the summary; the per-group notes (`notes_laserfiche.md`, `notes_county_agol.md`, `notes_frederick.md`, `notes_greeley_fortlupton.md`) hold the full source cards: route, terms, counts, null rates, gotchas, refresh commands. Pull scripts are under `scripts/`; raw JSON and OCR caches under `raw/` (git-ignored).

## Assumptions (read first)

1. **Scope** is Weld County sites, records dated 2024-01-01 onward, plus still-active 2023 construction permits (Frederick, 37 carry-ins) and 2023 industrial-occupancy sales (234 carry-ins, marked `carry_in`). The county incentive agreements are pulled from 2022-01-01 because an agreement precedes the equipment purchase by up to five years and the 2022 and 2023 agreements are inside their phase windows.
2. **Residential rows were left out** where the source distinguishes them, and counted: Frederick residential permit types and master-plan submittals; residential-occupancy sales (see `notes_county_agol.md` for the count); personal property accounts with no company string (250). The planning layers (Weld, Greeley, Fort Lupton, Frederick applications) are kept whole as snapshots with `industrial_use` marking the industrial rows.
3. **Flag rules follow the shared brief.** Frederick permits: the layer carries no valuation, so tier A is a construction permit type with an industrial word (45 rows), B3b is the rest of the non-residential permits on industrial property (175) and industrial words on trade or accessory permits (13); 199 rows N. Property sales: 188 rows at $2M or more on industrial or commercial-industrial parcels. Every planning and development row Y (424 rows across five files, 289 of them `industrial_use` = Y). Every incentive agreement Y (18); the five 179D deduction allocations found by the same search are N. Personal property accounts all N (resolver).
4. **Private individuals.** Grantor, grantee, owner and applicant fields that hold a person's name were blanked (property sales: 799 grantee and 6,173 grantor names whole or part; personal property accounts 779; planning applicants where individuals). A QA pass after the first pull found 12 assessor-format names ("SURNAME GIVEN I") and share-tagged names ("(1/6 INT)", "(LE)") that had slipped through; the scrub in `weld_agol_common.py` was tightened (trailing-initial rule, given-name rule with a strong-corporate guard, parenthetical stripping) and the three AGOL files rebuilt from cache. The planner name and email embedded in the Weld planning cases view were stripped from every description.
5. **Company names are thin on the permit and planning layers.** Frederick permits name a tenant or project on 50 percent of rows (read from the description or the parcel's business name); Weld planning cases 19 percent (most titles are use descriptions such as "Contractor Shop"); Greeley 33 percent; Fort Lupton 82 percent; Weld SPRs 80 percent (joined from the Ownership table on parcel). The incentive agreements name the taxpayer on every row and the facility address on every row.
6. **Snapshot sources.** Weld planning cases, Greeley TRAKiT projects, Fort Lupton projects and Frederick development applications keep no history of their own; the scripts append rows never seen before and never delete (`first_seen`, `last_seen`, `active`), so history starts 2026-11-06. Rerun them weekly. The personal property account table is a monthly snapshot; new P accounts can be dated from now on.
7. **Frederick: use the point layer, not the table layer step 2 tested.** `Accela_Building_Permits/FeatureServer/3` drops a third of the volume and all closed permits; the point layer is the full mirror. Counts in step 2's notes are therefore low.
8. **Windsor monthly permit reports were not pulled** (Matthew's decision 2026-11-06: manual download; the town host blocks scripts and the CivicPlus mirror disallows all crawling). Nothing else was blocked. Fort Lupton's DocumentCenter folder listings sit under a disallowed path and were not opened; the folder links are carried in `web_link`.
9. **Terms.** The five Weld County AGOL items carry the "developed solely for internal use only by Weld County" `licenseInfo` quoted in step 2; the data is pulled for internal prospecting use and the question of any wider use is Matthew's. Frederick GIS terms allow copying and adapting. Laserfiche `WebLink/robots.txt` disallows only the MyWebLink, Login and Search pages; the JSON services and document pages are not disallowed and were read at one request a second. Greeley and Fort Lupton hosts carry no rule.
10. **No Atlas Copco data, no contact with anyone, no records requests, no browser-only portals opened.** The step 2 ground-truth corrections are not applied.
11. **Five of these files are read by the v3 analysis** through the county-layer loader: Frederick permits as the permit layer; Weld planning cases, Weld SPRs, Frederick development applications, Greeley TRAKiT projects and Fort Lupton projects as the planning layer. The incentive agreements, property sales and personal property accounts have no slot in the method; Matthew decided (2026-11-06) to keep the method unchanged and publish the agreements as a side list, with ranked rows that match an agreement or a sale marked in the analysis notes.

## Results at a glance

| File | Rows | Flagged Y | Rule counts | Date range | company_name blank | site_address blank |
|---|---|---|---|---|---|---|
| scrape_weld_incentive_agreements.csv | 23 | 18 | county tax incentive agreement 18 | 2022-01-17 to 2026-09-16 | 0 | 4 (179D rows) |
| scrape_weld_county_planning_cases.csv | 96 | 96 | all planning and development cases 96 | snapshot 2026-11-06 | 78 | 96 (layer has no address; parcel and point carried) |
| scrape_weld_county_site_plan_reviews.csv | 49 | 49 | all planning and development cases 49 | 2023-02-01 to 2026-09-16 | 10 | 13 |
| scrape_weld_county_property_sales.csv | 2,250 | 188 | sale 2M+ on industrial or commercial-industrial parcel 188 | 2023-01-04 to 2026-10-19 | 765 | 945 (vacant land) |
| scrape_weld_county_personal_property_accounts.csv | 2,202 | 0 | resolver, all N | snapshot 2026-11-06 | 0 | 81 |
| scrape_frederick_building_permits.csv | 432 | 233 | tier A 45; B3b industrial property 175; B3b trade or accessory with industrial word 13 | 2023-01-30 to 2026-11-05 | 216 | 11 |
| scrape_frederick_development_applications.csv | 67 | 67 | all planning and development cases 67 | 2024-06-10 to 2026-11-06 | 36 | 18 |
| scrape_greeley_trakit_projects.csv | 172 | 172 | all planning and development cases 172 | 2023-03-01 to 2026-11-03 | 115 | 26 |
| scrape_fort_lupton_planning_projects.csv | 40 | 40 | all planning and development cases 40 | 2023-10-04 to 2026-11-06 | 7 | 35 |
| **Total** | **5,331** | **863** | | | | |

`scrape_flagged_weld.csv` holds the 863 flag = Y rows in the 17 columns plus `industrial_use` and `source_file`. Of the 424 planning and development rows, 289 are `industrial_use` = Y.

## The incentive agreements (the Weld lead list in their own right)

18 Tax Incentive Agreements under C.R.S. 30-11-123 since 2022, each naming the taxpayer and the facility address: Gotham Greens (Windsor, 2022-01), Colorado Stud Company (Nunn, 2022-01), Hirsh Precision (Frederick, 2022-02), Sphere Renewables (Fort Lupton, 2022-12), Norfolk Iron and Metal (Windsor, 2022-12), Agilent (Frederick, 2022-12), Airxcel / Aqua-Hot (Frederick, 2023-07), K2D / Colorado Premium (Greeley, 2023-07), Microvast (Windsor, 2023-07; site since resold), Owens-Brockway Glass (Windsor, 2023-07), TFP Nutrition (Platteville, 2024-10), North American Machines / TruLog Siding (LaSalle, 2024-10), Charm Industrial (Fort Lupton, 2025-05), Scotts / Hyponex (Brighton address, Weld parcel, 2025-07), EcoMod (Hudson, 2025-08), US Engineering Metalworks (Johnstown, 2026-09), Motherload Co Packing (Hudson, 2026-09), BAE Systems Space and Mission Systems "Project Mercury" (4120 Specialty Pl, Longmont address, Weld County, 2026-09). Phase caps, rebate percentage and term are parsed where the OCR gave them clearly (see `notes_laserfiche.md`).

## Refresh

- `python3 scripts/pull_weld_incentive_agreements.py --since 2026-09-01` (monthly; one field search plus OCR of new documents).
- `python3 scripts/pull_weld_county_planning_cases.py`, `pull_greeley_trakit_projects.py`, `pull_fort_lupton_planning_projects.py`, `pull_frederick_development_applications.py` (weekly snapshots).
- `python3 scripts/pull_weld_county_site_plan_reviews.py --since <date>`, `pull_weld_county_property_sales.py --since <date>`, `pull_frederick_building_permits.py --since <date>` (monthly incrementals; de-duplicate on record_id downstream).
- `python3 scripts/pull_weld_county_personal_property_accounts.py` (monthly snapshot).

## What was not pulled

Windsor monthly permit reports (manual download). Fort Lupton submittal PDFs. Greeley building permits (behind the eTRAKiT login; CORA draft in the step 1 notes). Unincorporated Weld County building permits (in Accela, not mirrored to GIS; CORA draft in the step 1 notes). Evans, Firestone, Dacono, Mead, Milliken permits (no public feed). The agenda systems (Greeley and Frederick CivicClerk, Windsor and Fort Lupton Agenda Centers, Evans eSCRIBE) and Mountain View Fire packets, all parked.
