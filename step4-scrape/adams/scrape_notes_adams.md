# Step 3 (scrape), Adams County: notes

Run 2026-10-31, three agents in parallel by portal platform, each following `datasource-validator-scraper`. Nine of the ten build-verdict sources from step 2 were pulled in full for their scope; one (Adams County PrimeGov) was blocked by robots.txt on the day of the pull. Group cards with the full detail: `notes_county_commercecity.md`, `notes_thornton.md`, `notes_aurora_brighton.md`. Pull scripts in `scripts/`, raw JSON pages under `raw/` (git-ignored; every pull reruns from its script).

## Assumptions (read first)

1. **Scope** is Adams County sites, records dated 2024-01-01 onward, plus still-active 2023 construction permits. Aurora rows were cut to the Adams side with the development layer's County field (108 rows) and, where that field is null, the PropY > 1,695,150 Colfax-line test (32 rows, tagged in `county_basis`). The Aurora permit layer has no status field, so its 378 "still active" 2023 carry-ins are 2023 construction permits with no later closing record, not permits known to be open.
2. **Residential rows were left out entirely**, as the brief allowed, and counted: Adams County 11,773, Thornton 25,034 (plus 1,380 right-of-way permits with no description), Aurora 12,245, property sales 52,570 sales on residential parcels. The Commerce City snapshot keeps its 331 residential rows (marked `residential = Y`) because the layer is kept whole as a snapshot.
3. **Flag rules follow the brief.** Permits: tier A at $250k or more with industrial zoning, use or word (Adams County's layer has no valuation, so tier A there is non-residential construction with an industrial word); B3a $50k to $250k on industrial or commercial-industrial property; B3b under $50k or no valuation on industrial property. Every planning, development and site-plan row is flagged Y with `industrial_use` set as an extra column. Property sales flag at $2M or more on an industrial or commercial-industrial parcel. Meeting items flag on an incentive, agreement, rezoning, planned development, use by special review, site plan, plat or annexation word.
4. **Private individuals.** Owner and applicant fields that hold a person's name were blanked (Adams County planning 579, property sales 476 grantees and 556 grantors, Thornton 36 owners plus 83 applicant strings reduced to the firm, Aurora attention lines). Descriptions were scrubbed of staff stamps, emails and phone numbers. Residual risk: a bare surname inside free text can survive; the group notes say where.
5. **Company names are thin on the permit layers.** Adams County permits carry no applicant (97 percent blank; 40 tenant names were read out of descriptions). Aurora permits carry no name field (94 percent blank; 564 code names and suffixed project names were extracted). Thornton's description names the tenant and BUS_NAME is filled on 53 percent of commercial rows. The planning and development layers carry project or applicant names on most rows.
6. **Snapshot sources.** Commerce City's two active layers and Thornton's development projects keep no history of their own; the scripts append rows never seen before and never delete, so history starts today. Rerun them weekly.
7. **The Commerce City snapshot holds 4 rows dated before 2023** because the layer still lists them as active; they are kept as the snapshot rule says and marked by date.
8. **PrimeGov was not fetched and is dropped.** Its robots.txt on 2026-10-31 reads "User-agent: * / Disallow: /" (last modified 2026-10-08; step 2 had seen a 406 and used the JSON API). The script carries a robots gate and stops; the header-only CSV was removed. Matthew dropped the source on 2026-10-31 (no manual read).
9. **No Atlas Copco data, no contact with anyone, no records requests, no browser-only portals opened.** The step 2 ground-truth corrections are not applied.
10. **Seven of these files are read by the v3 analysis** through the county-layer loader approved on 2026-10-31 (`step5-analysis/v3/scripts/v3_local.py`): the three permit files as the permit layer and the four planning files as the planning layer. Property sales and Brighton Legistar are pulled but have no slot in the method yet (see `step5-analysis/adams/adams_analysis_notes.md`).

## Results at a glance

| Source | File | Rows | Source's own count | Flagged Y | Date range |
|---|---|---|---|---|---|
| Adams County planning cases | scrape_adams_county_planning_cases.csv | 2,712 (1,297 distinct cases; one row per parcel) | 2,712 | 2,712 (industrial_use 765) | 2023-01-03 to 2026-10-29 |
| Adams County building permits | scrape_adams_county_building_permits.csv | 1,352 non-residential | 13,125 fetched | 341 (A 252, B3b 89) | 2023-01-06 to 2026-10-29 |
| Adams County property sales | scrape_adams_county_property_sales.csv | 1,603 on non-residential parcels | 56,616 sales fetched | 296 | 2024-01-03 to 2026-10-27 |
| Commerce City active development (snapshot) | scrape_commerce_city_active_development.csv | 499 distinct (556 features) | 556 | 499 (industrial_use 20) | 2021-11-03 to 2026-10-31 |
| Adams County PrimeGov items | (dropped 2026-10-31; blocked by robots.txt, no file) | 0 | n/a | 0 | n/a |
| Thornton building permits | scrape_thornton_building_permits.csv | 1,996 (1,962 since 2024 + 34 active 2023) | 1,962 + 627 | 414 (A 86, B3a 54, B3b 274) | 2023-01-06 to 2026-10-28 |
| Thornton development projects | scrape_thornton_development_projects.csv | 302 | 303 | 302 (industrial_use 31) | 2024-01-01 to 2026-10-23 |
| Aurora development applications (Adams side) | scrape_aurora_development_applications.csv | 140 | 414 all counties | 140 (industrial_use 61) | 2023-03-27 to 2026-11-02 |
| Aurora building permits (Adams side) | scrape_aurora_building_permits.csv | 9,783 (9,405 since 2024 + 378 2023) | 90,227 all counties since 2024 | 3,344 (A 685, B3a 494, B3b 2,165) | 2023-01-03 to 2026-10-29 |
| Brighton Legistar items | scrape_brighton_legistar_items.csv | 877 | 2,573 items | 74 | 2024-01-02 to 2026-10-15 |
| **All county sources** | scrape_flagged_adams.csv | 19,264 | | **8,122** | |

Checked after the agents finished: every file starts with the exact 17 shared columns, `flag` is only Y or N, no description exceeds 500 characters, no row outside the date scope except the four snapshot rows noted, every row's county is Adams, no em dashes in any file or script, and row counts match the agents' reports.

Null rates on the three key fields (company_name, site_address, record_date): Adams County permits 97 / 0 / 0 percent; planning cases 21 / 16 / 0; property sales 30 / 14 / 0; Commerce City 79 / 0.2 / 0; Thornton permits 6 / 3 / 0; Thornton projects 0 / 64 / 0 (DPA rows have a point but no address); Aurora applications 1 / 62 / 0 (new-build site plans carry no address); Aurora permits 94 / 0.1 / 0; Brighton Legistar 92 / 100 / 0.

## Things that will bite Step 4

- **Flag volume is uneven.** Aurora permits are 3,344 of 8,122 flagged rows and planning cases another 2,712. The B3b rule alone flags 2,165 Aurora rows (generators, tanks, signs on industrial property). A loader should score tier A and B3a first and keep B3b as support.
- **Three of the four permit layers carry no applicant.** Address is the join key; the tenant has to come from the Thornton description, the state permits, UCC, or a hand lookup in the browser-only portals (Accela, eTRAKiT, CityView, AMANDA).
- **Aurora intake and permit pairs duplicate scopes.** `scope_key` in the Aurora file groups them; count a scope once.
- **Planning cases are one row per parcel.** 1,297 distinct cases behind 2,712 rows; de-duplicate on `record_id`.
- **Property sales have no zip** (99.9 percent blank) and no land use on the Parcels layer; land use came from the Property_Values account type and zoning from the county zoning polygons at the parcel centroid.
- **Code names.** Aurora permits name the PMI plant "Project Waterfall" and other large projects by code; they resolve only through the development application or a tie recorded elsewhere.
- **Snapshots start today.** Commerce City and Thornton projects have no history before this pull; the step 2 verdict rests on fields, not on a back-test hit.

## What broke, and how to rerun

- Thornton's server returns HTML 500 on ORed address clauses: each request is one date range and one BuildingUse clause, filtered client-side (`scripts/thornton_common.py`).
- Aurora's Cloudflare front returns 403 on some where-clause shapes (IS NULL with date literals): pulls are date-range queries filtered client-side (`scripts/aurora_brighton_common.py`).
- PrimeGov: robots.txt disallows all; nothing fetched; dropped by decision.
- gisserver.c3gov.com serves no robots.txt (the connection drops); services3.arcgis.com returns 403 on robots.txt. Both were read as no stated rule and pulled at one request a second with an identifying user agent.
- Brighton's Legistar has bodies only for City Council and the South Brighton GID; Planning Commission and BURA items are not there.

Rerun: `python3 scripts/pull_<slug>.py` rebuilds from the cache; `--since YYYY-MM-DD` fetches only newer rows; `--fresh` ignores the cache. Snapshot scripts append and never delete. Weekly is enough for the snapshots, monthly for the rest.

## Not pulled

PrimeGov (blocked, then dropped). Nothing else in scope is missing. By design: residential rows, personal names, attachments and record detail pages, and every browser-only portal.
