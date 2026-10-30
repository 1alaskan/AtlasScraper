# Adams County back-test, group `north_cities` (Thornton, Brighton, Westminster, Northglenn, Federal Heights)

Date of test: 2026-10-30. Method per `validation_brief_shared.md`. Companion file: `matches_north_cities.csv` (55 rows).

## Sources tested and endpoints

| Rank | Source | Endpoint used | Date field used |
|---|---|---|---|
| 3 | Thornton Building Permits (2017 to present) | `https://maps.thorntonco.gov/citydevweb/rest/services/Permits/MapServer/1/query` | DateEntered |
| 5 | Thornton Development Projects | `https://maps.thorntonco.gov/citydevweb/rest/services/DevelopmentProjects/MapServer/0/query` | OnMapDate (created_date is one day later) |
| 20 | Thornton Addresses with Certificates of Occupancy | `https://maps.thorntonco.gov/citydevweb/rest/services/Permits/MapServer/0/query` | attDateCO (none found) |
| 9 | Brighton Planning Development Status | `https://services6.arcgis.com/FoIoSLUvgp6HznSK/arcgis/rest/services/Brighton_Planning_Development_Status/FeatureServer/0/query` | CreationDate |
| 10 | Brighton Commercial Permits Issued PDF | `https://www.brightonco.gov/DocumentCenter/View/39910` (current month only) | Permit/License Issued Date |
| 25 | Brighton County Report, Adams County PDF | `https://www.brightonco.gov/DocumentCenter/View/39907` (current month only) | Permit/License Issued Date |
| 18 | Brighton Legistar Web API | `https://webapi.legistar.com/v1/brightonco/Matters?$filter=...` | MatterIntroDate (MatterAgendaDate noted) |
| 11 | Westminster Proposed and Current Developments | `https://maps.cityofwestminster.us/server/rest/services/Planning/CurrentDevelopments/MapServer/0/query` | CPRMEETINGDATE (populated on 12 of 76 rows) |
| 34 | Federal Heights monthly permit PDFs | `.../uploads/08_AUGUST_2026_PERMITS_ADA.pdf` via `fedheights.org` | Issue Date |

All ArcGIS queries used `f=json`, `returnGeometry=false` except for the geometry tie checks, user agent `step3-research-validation/1.0`, one request a second. Nothing was downloaded in bulk beyond the two noise months on source 3 (324 and 378 rows) and the full small layers 9 (75 rows), 11 (76 rows) and 5 (303 rows).

## Assumptions

- Press dates and bases are taken from `ground_truth_adams_extract.csv` as given. X15 Izzio carries the caution "opening date not confirmed"; the 2026-01-13 date is a first press mention of an opened plant, so Izzio lead times are measured against a late press date and look larger than they would against an announcement.
- Lead time is months before or after the first press story, nothing else.
- For C23 Solid Power the ground truth has no street address. The permits layer itself gives it: 14902 Grant St Unit 120 (25 North Building 2), Adams PIN 157315101004. Records from the original 2021 to 2022 SP2 build-out fall inside the 36-month window of the 2024-09-25 press date; they are listed as `possible` with a note that they belong to the earlier build, and they are not counted as "before press" hits for the pilot-line project below.
- Kiosk Information Systems is a subsidiary of Posiflex. LEGALOWNER "Posiflex Business Machines LLC" on 251 E 126th Ave records was treated as a tie to Kiosk only together with the later permits that name Kiosk at that address. LEGALOWNER is the current assessor owner joined live, not the owner at permit time, so it cannot date when a company arrived at a site (the 2023 spec shell at 251 E 126th shows Posiflex although it was permitted by the developer).
- Geometry ties for source 5 were done by comparing the layer point to the permit point for the known address (15 m for Kiosk, 30 m for Santa Monica Seafood, 40 m for Solid Power, same parcel for Izzio).
- Personal names in Applicant, Description, Comments and owner fields were not reproduced.

## Source 3: Thornton Building Permits (2017 to present) layer

**Coverage (Thornton projects):** confirmed 2 of 4 (X15 Izzio, X16 Kiosk), possible 2 of 4 (C23 Solid Power, X05 Santa Monica Seafood), none 0 of 4. C19 Prost (Northglenn) is outside the layer. Out-of-jurisdiction name checks for Amprius, VSK and Creation Technologies: none, as expected.

**Lead-time list (months, earliest in-window record that is not the prior build):**
- X15 Izzio: -10.0 (PRCALT202501646 foundations, 2025-03-14, names Izzio Bakery, confirmed), then -9.3 and -8.7 for the Phase 1 and Phase 2 TIs.
- X16 Kiosk: -31.5 (PRCNEW202301098 spec shell, possible, developer's building), -2.2 (PRCALT202506164 fabrication and assembly TI $4.0M, confirmed), +7.1 (nitrogen, oxygen and argon tanks), +9.8 (first record naming Kiosk in text).
- X05 Santa Monica Seafood: -14.9 (PRCALT202304179 TI $2.67M at Unit 110, possible, no name).
- C23 Solid Power (pilot line, press 2024-09-25): -8.5 (process wiring $380k), -6.5 (hazardous gas monitoring), +2.5 (modular test lab $495k), +5.0 (names Solid Power), +14.5 (SP2.5 interior TI $12.0M with process equipment). All possible under the expansion rule. The original build shows -32.0 (TI $24.3M naming Solid Power) and -29.2 (bulk nitrogen and argon tanks), outside the pilot-line story.

Before-press records: 3 of 4 Thornton projects had an in-window record before press (Izzio confirmed, Kiosk confirmed, Santa Monica Seafood possible); Solid Power had unnamed process-electrical records before press (possible).

**Noise sample.** Records by DateEntered: September 2025 = 324, March 2026 = 378. Type mix (Sept 2025): Residential Alteration 74, Plumbing 65, Mechanical 58, Electrical 41, Right of Way 32, Residential Addition 12, Fire Protection 10, Commercial Alteration 9, Sign 9, Residential New 5, Commercial New 4, other 5. March 2026: Plumbing 97, Mechanical 60, Residential Alteration 60, Electrical 40, Residential New 33, Right of Way 30, Fire Protection 15, Commercial Alteration 12, Residential Addition 11, Sign 7, Commercial New 5, other 8. Fifty rows read by eye from each month (every 6th or 7th row): September 2025, 48 of 50 plainly not industrial (furnace and water heater swaps, siding, basements, signs, sewer repairs, a daycare, a cell antenna), 2 possibly relevant (a $118k multi-RTU replacement at 12789 Emerson St and an $875k data center expansion at 12396 Grant St). March 2026, 47 of 50 plainly not industrial, 3 commercial but ambiguous (a $250k UPS and battery backup at 2211 Eppinger Blvd, a new sprinkler system in a suite at 2300 E 120th Ave, a fire alarm change for proposed construction at 13801 Grant St). So about 95 percent of raw rows are noise. Filtering to Type in (Commercial New, Commercial Alteration, Commercial Addition, Commercial Accessory, Commercial Miscellaneous, Fire Protection) keeps 26 of 324 (8 percent) and 35 of 378 (9 percent), and within that the Fire Protection Tank and High Piled Storage TypeOfWork values and the Description keywords (process, nitrogen, argon, manufacturing, fabrication, racking, generator) carry the signal.

**Join quality.** Description text did the matching for every confirmed row (Solid Power, Izzio Bakery, Kiosk written in staff or applicant text); ADDRESS plus UNT did the site grouping; LEGALOWNER gave the Posiflex tie. BUS_NAME was empty on every project record (it is populated on 1,660 of 84,285 rows and mostly for storefronts, for example a daycare and a Panda Express in the area search). So the layer carries company names, but in free text and the owner field, not in a dedicated tenant field. Expect to match on address first and regex the Description second.

**Access notes.** Live, no key, 2,000 rows a page. ORing two LIKE clauses on ADDRESS returned HTTP 500 on this server; one address pattern a request and the `_` wildcard avoided work. DateIssued can lag DateEntered by months (Kiosk shell: entered 2023-03-14, issued 2025-12-19), so DateEntered is the fire date.

**Verdict: build** (back-tested). Every Thornton project in the ground truth appears at its site with permits entered 2 to 10 months before press, the Description names the tenant on the capex permits, and bulk gas tank and process equipment permits are visible; noise is high but a Type filter removes 90 percent of it.

## Source 5: Thornton Development Projects layer

**What "active only" means here.** The REST layer holds 303 rows with OnMapDate from 2024-01-01 (95 rows carry exactly that date, a bulk load) to 2026-10-23. 104 rows have an OffMapDate already in the past (oldest 2024-05-15) and 118 rows have OnMap = N, so rows are not deleted when they leave the public app; the app filters on OnMap. There is nothing before 2024-01-01, so the layer cannot back-test a project whose planning filing predates 2024 and the depth of history is only what has accumulated since the bulk load. 206 of the 303 rows have no PermitNumber, PermitType or PermitAddress; they are the administrative DPA type (Name, Type, Phase, StatusAlt and Applicant filled, geometry only for location). Three of the four Thornton projects are in that address-less subtype, so geometry is the join.

**Coverage:** confirmed 3 of 4 (X15 Izzio, X16 Kiosk, X05 Santa Monica Seafood, all by Name or Applicant plus geometry), possible 1 of 4 (C23 Solid Power, modular test lab DPA, expansion rule). 4 of 4 Thornton projects present by company name.

**Lead-time list:** X15 Izzio -10.6 (2025-02-24, the earliest Izzio record in any source), X05 Santa Monica Seafood -3.5 (2024-07-29), C23 Solid Power +0.3 (2024-10-03), X16 Kiosk +0.4 (2025-11-10, although the building permit was entered 80 days earlier). Before press: 2 of 4.

**Noise sample.** Rows by OnMapDate: September 2025 = 2, March 2026 = 9 (all read; far too few for 50). September 2025: a restaurant tenant finish and a subdivision infrastructure permit; none industrial. March 2026: 6 Non-Residential (a med spa TI, a credit union TI, an auto parts store TI, an auto repair change of use, two commercial buildings with a restaurant, a retail planning area), 2 Mixed Use (a 54-acre preliminary plan and a transit-oriented rezoning), 1 Institutional (a 13,000 sf medical office); none industrial. Across the full layer DevelopmentType is Non-Residential 179, Residential 77, Mixed Use 26, Institutional 21, and the industrial keyword rows named in discovery (Creekside Innovation Park, Pulse 25, Sack Creek, Ace Thermal, BSM Business Park) are all present. Roughly 1 row in 10 of the Non-Residential set is industrial or flex.

**Join quality.** Name and Applicant fields carry the company (Izzio Bakery, Solid Power, Kiosk, Santa Monica Seafood) on all four; PermitAddress is null on the DPA subtype, so geometry to the permits layer or parcel is the site join. Applicant often holds an individual, which has to be stripped. Comments carry staff contact details, also to strip.

**Access notes.** Live, no key. Snapshot weekly as discovery said: OnMap flips to N and OffMapDate is set when a case closes, and although rows were retained through this test there is no guarantee they will be.

**Verdict: build** (back-tested). Names every Thornton project, fires 3 to 11 months before press on the two projects that filed a planning case before announcement, and is small (about 20 new rows a month) so the whole layer can be diffed weekly.

## Source 20: Thornton Addresses with Certificates of Occupancy layer

52,521 rows. 6,472 rows carry a PermitNumber and 5,676 of those are PRRNEW (residential new); zero rows carry a PRCNEW or PRCALT permit number; CO_DATE is null on every row; all 927 attDateCO values since 2024-01-01 are residential. None of the four Thornton sites or company names appears. Coverage 0 of 4.

**Verdict: drop** (back-tested). The layer holds only residential-new COs and cannot confirm industrial occupancy.

## Source 9: Brighton Planning Development Status layer

75 rows, CreationDate 2021-07-07 to 2026-10-07, OBJECTIDs run to 319, so about three quarters of rows ever created have been removed. It is a curated featured-projects list.

**Coverage (Brighton projects):** possible 1 of 2 (C20 Amprius site as "Mile High Logisitics Center Site Plan", 18875 E Bromley Lane, Industrial, created 2024-05-15), none 1 of 2 (C21 VSK, nothing at 76 Commerce Center or naming VSK). Lead-time list: C20 +14.3 months, after press; the 2023-09 rezoning in the ground truth is not in the layer. Before press: 0 of 2.

**Noise sample.** Rows created September 2025 = 1 (a residential final plat), March 2026 = 3 (a saloon conditional use permit, a commercial PUD amendment, the Case Farms zone change, mixed use): 4 of 4 not industrial. Whole layer read by eye: 5 of 75 rows are industrial (Magpie Properties subdivision, Mile High Logistics Center, Brighton Terrace Dyno Bldg, Bromley Park Filing 101 Cold Storage, Bromley Park PUD 39th Amendment), 33 residential, 26 commercial retail or service, 8 public, 3 mixed use.

**Join quality.** Location is a street address or an intersection; Project_Name carries the developer or end user name, never a tenant inside a logistics center. CreationDate is when staff added the row, not the application date, so lead times from this layer are late by an unknown amount.

**Verdict: park** (back-tested). Cheap to snapshot and it does flag industrial site plans in Brighton, but it fired 14 months after press on the one testable project, is curated and undated, and missed VSK entirely. Keep as a context feed behind the Brighton permit reports once those can be archived.

## Source 10: Brighton Commercial Permits Issued monthly PDF

Only the current month is published; the DocumentCenter link is reused each month and no archive was found on the Reports page (`/1143/Reports`), the DocumentCenter index or the Archive Center (both render only the site shell without JavaScript). The September 2026 report (5 permits) parses cleanly with pdftotext: Record Type, Full Address, Owner Name, Description of Work, Property Type, Issued Date, Valuation, Record number. One industrial row (BP-26-1296 conveyor system TI, 4353 E Bromley Ln, $460k). No 2023 month exists online, so Amprius and VSK cannot be tested; coverage 0 of 2 by unavailability, not by miss. Noise: 1 of 5 industrial in the one month seen. Owner Name holds individuals on small permits.

**Verdict: park** (back-tested, not testable). Right fields and Property Type = Industrial is a clean filter, but with no archive the source only starts producing value the month archiving starts. Build the monthly archiver if the Brighton pull is wanted at all; a back-test needs the OpenGov export by CORA that discovery suggested.

## Source 25: Brighton County Report, Adams County monthly PDF

September 2026 report downloaded (243 KB, 131 permits). The chart page is garbled by rotation but the table pages extract: Record number, Record Type, Name, Address, Issued Date, Description, Location Flags, Total Paid, Valuation. Record Type counts for the month: MEP 35, New Single Family Detached 19, Fence 15, Plumbing 13, Electrical 18, Water/Sewer Repair 5, and so on; 1 New Commercial/Industrial Construction (a hotel) and 1 Tenant Improvement (the same conveyor permit as source 10). About 1 percent industrial. Same archive problem as source 10, so Amprius and VSK are untestable here too.

**Verdict: drop** (back-tested, not testable). It is a superset of source 10 with 130 residential and trade rows a month added; source 10 already carries every commercial row.

## Source 18: Brighton Legistar Web API

**Coverage:** C20 Amprius confirmed (ID-69-23 incentive resolution, intro 2023-02-23, agenda 2023-02-28; ID-72-24 incentive amendment, intro 2024-02-21) plus possible (ID-270-23 Mile High Logistics Center PD ordinance, intro 2023-08-24, agenda 2023-09-19, matches the ground-truth rezoning milestone of 2023-09-28). C21 VSK none after searching VSK, Vikram, photovoltaic, solar, Energy, Commerce Center, incentive, ECONOMIC and Executive Session titles in 2022 to 2024; the only 76 Commerce Center matter is the developer's 2017 incentive. Coverage 1 confirmed of 2.

**Lead-time list:** C20 -0.4 months (intro), -0.2 (agenda), then +5.6 and +11.6. Before press: 1 of 2, and only by days: the city resolution was on the agenda six days before the Governor's release.

**Noise sample.** Matters introduced September 2025 = 23 (7 informational reports, 7 resolutions, 4 ordinances, 3 minutes, 2 proclamations) and March 2026 = 31 (10 resolutions, 8 proclamations, 7 informational reports, 4 ordinances, 2 minutes) by MatterIntroDate. Titles are council business (proclamations, appointments, budget, contracts, zoning); keyword filtering on "incentive", "economic", "planned development", "rezoning", "industrial" is the only way to use it. No per-row classification was done because matters are not permits.

**Join quality.** MatterTitle names the company on incentive resolutions and the development on PD ordinances; no address field. Cross-reference to source 9 by project name. History back to 2014.

**Access notes.** Read-only OData, no key, fast; substringof is case-sensitive.

**Verdict: build** (back-tested). Small keyword watcher on incentive and PD matters: it named Amprius a week before the state release and is the only Brighton source that did.

## Source 11: Westminster Proposed and Current Developments layer

76 polygon rows; CASENUM years 2019 to 2026; CPRMEETINGDATE populated on 12 rows only (2023-08-21 to 2026-02-02); no application or status date on the rest. X09 Creation Technologies, 1401 W 122nd Ave: none (no row at the address, none naming the company). Coverage 0 of 1. The expansion was a TI inside an existing building, which this layer would not carry.

**Noise sample.** Rows with CPRMEETINGDATE in September 2025 = 0 and March 2026 = 0, and no other date exists, so a monthly noise count is not possible. Whole layer read by eye: 6 of 76 are industrial or flex (Altus Light Industrial, Novera Commerce Center PA2 380,000 sf flex, Novera PA4 employment flex, Mandalay Gardens Employment Flex 9,939 sf, PLN26-0026 three industrial flex buildings 132,928 sf, Tri-State critical operations facility), the rest housing, retail, medical, schools, churches and city facilities. About 92 percent not industrial.

**Join quality.** LOCATION is an address or intersection, Owner_Developer is the developer, CASENUM links to eTRAKiT (browser only). No tenant names.

**Verdict: park** (back-tested). Missed the one Adams-side project, has no usable record date, and its industrial rows are speculative flex parks; keep as context for the Huron St corridor only.

## Source 34: Federal Heights monthly permit PDFs

August 2026 report parsed: 29 permits, none industrial (one QuikTrip $5.0M, signs, fences, mobile-home decks and sheds, residential furnaces and roofs, two right-of-way permits, one cell antenna). Fields: Permit No, Type code, Parcel, Issue Date, Owner Name (mostly individuals), Address, Valuation, Description, Contractor. Reports exist monthly from January 2025. No ground-truth project is in Federal Heights.

**Verdict: drop** (back-tested on one month). No industrial land and no industrial content.

## Browser-only portals: terms check only

- (28) Thornton CityView Portal, `cityviewportal.thorntonco.gov/robots.txt`: `User-agent: *` allows only `/Home`, `/Home/Ping` and `/Account/Logon` and disallows everything else; GPTBot and ChatGPT-User are disallowed outright. Manual lookup only. The GIS mirrors (sources 3, 5, 20) are on `maps.thorntonco.gov`, which has no robots.txt (404) and no published terms.
- (32) Westminster eTRAKiT, `develop.cityofwestminster.us/robots.txt`: Cloudflare managed content signals `search=yes, ai-train=no, use=reference` with `Allow: /` for `*` and a block list of named training crawlers; the portal itself answers curl with a Cloudflare challenge (403 at discovery). Manual lookup only. The GIS host `maps.cityofwestminster.us` has no robots.txt and no terms.
- (38) Brighton OpenGov portal, `brightonco.portal.opengov.com/robots.txt`: `User-agent: * Disallow: /`. Manual lookup only. `brightonco.gov/robots.txt` disallows admin, search and events paths only and allows the DocumentCenter; the host resets connections intermittently (one reset in this test, retry succeeded).
- (39) Northglenn CommunityCore, `app.communitycore.com/robots.txt`: allows only login, copyright, EULA and forgot-password pages, disallows everything else. Manual lookup only.
- Also noted: `fedheights.org/robots.txt` disallows a list of named AI training crawlers (GPTBot, ClaudeBot, CCBot and others) from the whole site, with no rule for other agents; the single PDF sampled here was fetched with the research user agent and nothing else was collected. Legistar hosts have no robots.txt (404).

## Sources not tested, and why

- (24) Thornton CivicClerk: browser SPA; API not confirmed at discovery; agenda packets are press-like documents, not records. Would need a browser session to validate.
- (26) Westminster Agenda Center: agenda PDFs, not records; Adams-side industrial volume too low to justify until source 11 shows otherwise.
- (27) Brighton EDC Available Properties layer: inventory snapshot, inverse signal only when a parcel leaves; undated for our purpose; contains broker contact details.
- (41) Brighton EDC newsletters: press-style PDFs, two or three a year.
- (42) Westminster support layers: context data (vacant land, zoning, business points), not event records.
- (43) Northglenn CivicClerk: browser SPA, same as 24.
- (48) Thornton support layers: context data (enterprise zones, URA, pre-approved sites).
- (51) United Power minutes: PDFs not text-extractable, no customers named at discovery.
- (53) Northglenn storefront list: stale since Q4 2024.

## Corrections the test suggests to the ground truth (not applied)

- C23 Solid Power: facility address is 14902 Grant St Unit 120, Thornton 80023 (25 North Building 2), Adams PIN 157315101004, from the permits layer.
- X15 Izzio Bakery: permitted address is 15107 Grant St (not 15101); the plant is a TI in a 176,000 sf spec shell permitted 2023-03-22 by Rockefeller Group (RG Commerce Park LLC). The 2026-01-13 press date is a late "has opened" mention; city records show the project filed 2025-02-24, so any lead time measured against this press date overstates how early the sources fire relative to an announcement that never happened.
- X16 Kiosk: the new building is 251 E 126th Ave, Thornton 80241 (126th and Washington, not 128th), a spec shell permitted 2023-03-14 and now owned by the parent company Posiflex; the fabrication and assembly TI permit was entered 2025-08-22, two months before the BizWest story. Grand opening event permits are dated 2026-10-14 to 16.
- X05 Santa Monica Seafood: the space is Unit 110 of 1101 E 126th Ave (TI entered 2023-08-17, planning DPA 2024-07-29), about 15 months before the "build-out completion" press date; the record set suggests an earlier announcement may exist.
- C20 Amprius: Brighton's incentive resolution was introduced 2023-02-23 and heard 2023-02-28, before the 2023-03-06 release; the ground truth could carry that as a local incentive milestone. The site plan record for the building is dated 2024-05-15 in Brighton's layer.
- X09 Creation Technologies: 1401 W 122nd Ave is well east of Sheridan Blvd, which is the Adams and Jefferson line in Westminster, so the county is very likely Adams; confirm with the assessor as the ground truth already says.
- C19 Prost Brewing: no source in this group covers Northglenn; the county-level agents should check Adams County records for 351 W 104th Ave.

## Not finished

- Brighton sources 10 and 25 could not be back-tested because only the current month is published; a CORA export from OpenGov for 2023 to 2025 is the only way to test them against Amprius and VSK.
- Source 5 noise months had only 11 and 14 rows, so the 50-row sample was not reachable; all rows in those months were read instead.
- Source 11 has no monthly date, so its noise count is by whole-layer classification only.
- Legistar matters were counted for the two noise months but not classified row by row, since they are council items rather than permits.
- The Thornton permits layer rejected ORed LIKE clauses on ADDRESS with HTTP 500; every address was queried one pattern at a time, so an address variant not tried here (for example a Grant St number other than 15101 to 15111 for Izzio) could still exist.
