# Adams County back-test, group `aurora`

Tested 2026-10-30 against the ground truth extract. Projects: C22 Philip Morris ZYN (Project Waterfall), C25 RK Industries, C24 Pretred, and X02 Cerebral Brewing (possible-Adams row, reported separately). Controls: 5675 Pecos, 9410 Heinz, 11011 E 104th Ave. Matches are in `matches_aurora.csv` (23 rows).

## Sources tested and endpoints

| Rank | Source | Endpoint used |
|---|---|---|
| 4 | Aurora Active Development Applications | `https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/180/query` |
| 6 | Aurora Building Permits, full 2021 to present | `https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/44/query` |
| 13 | Aurora Businesses (All Non-Home) licences | `https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/77/query` |
| 37 | Council and Planning Commission agendas | `https://www.auroragov.org/city_hall/mayor___city_council/council_meetings` (attempted, see below) |
| 56 | Building Permit Statistics monthly PDFs | one PDF sampled (November 2017, the only month with a static URL found) |

All three ArcGIS layers answered `f=json` queries with `outFields=*`, `returnCountOnly=true`, and `resultOffset` paging (2,000 rows a page). User agent `step3-research-validation/1.0`, one request every 2 seconds.

## Assumptions

1. **County split for layer 44.** Layer 44 has no County field. Layer 180 does, and its ADAMS and ARAPAHOE points separate cleanly at projected Y = 1,695,150 ft (Colorado Central state plane, wkid 2232), which is the E Colfax Ave line: odd-numbered (north side) Colfax addresses are ADAMS, even-numbered (south side) are ARAPAHOE. I used `PropY > 1695150` as "Adams side" on layers 44 and 77. Layer 180's own County field has about 1 percent of rows with coordinates on the wrong side (null-address records), so the spatial rule is at least as good as the field.
2. **Press dates.** C24 Pretred has a FALLBACK month only (2024-07); I used 2024-07-01 and also give the lead against the lease announcement (2025-10-28) in the notes column. X02 uses the FALLBACK company update of 2023-01-20.
3. **Window.** 36 months before press to 12 months after the latest milestone: C22 2021-07-16 to 2027-07-27; C25 2022-08-29 to 2027-04-01; C24 2021-07-01 to 2027-05-31; X02 2020-01-20 to 2024-01-20.
4. **Record date** is `InDate` (date the folder was entered in AMANDA) on layers 180 and 44, and `Issue_Date` on layer 77 (Start_Date given alongside). `IssueDate` on layer 44 is null for most "Online Building Folder" rows, which are the intake copies that precede the Limited or Commercial permit of the same scope, so InDate is the earlier and more complete field.
5. Layer 180 noise: the layer holds only 1 Adams row in September 2025 and 5 in March 2026, so I classified every Adams row entered since 2025-01-01 (64 rows) instead of 50 per month.

## Source 4: Aurora Active Development Applications (layer 180)

Not an active-only layer despite the name: 1,808 rows from 2012-02-06 to a scheduled 2026-11-02 intake, 1,606 of them Retired, so it keeps history. 581 ADAMS, 829 ARAPAHOE (plus 4 misspelt), 21 DOUGLAS, 373 with County null. Since 2024-01-01: 265 rows, 101 ADAMS, 122 ARAPAHOE, 42 null.

**Coverage: 1 confirmed, 2 possible (3 distinct projects with a record), of 3 Adams projects; X02 none.**

| Project | Record | InDate | Lead (months) | Class |
|---|---|---|---|---|
| C22 PMI | DA-2284-02 Project Waterfall site plan and plat, 755,000 sq ft light manufacturing on 140 ac | 2024-05-24 | -1.7 | confirmed |
| C22 PMI | DA-2284-05 Project Waterfall site plan amendment, 86.71 ac | 2026-05-11 | +21.8 | confirmed |
| C25 RK | 1997-6051-05 minor amendment, new exterior opening, 3301 N Lewiston St | 2026-08-20 | +11.7 | possible |
| C25 RK | 1981-6070-06 Michelin Tire Corporation SP AM, loading ramp, 20101 E 36th Dr (RK Industries LLC licence address) | 2026-08-13 | +11.5 | possible |
| C24 Pretred | DA-1478-12 Denali Logistics Park PA-7 site plan, three spec industrial buildings 759,620 sq ft | 2022-01-03 | -29.9 | possible |
| X02 Cerebral | none | | | none |

Before press: 1 of 3 (the Waterfall site plan, 53 days ahead of the PMI announcement). The Denali spec site plan is also before press but is a landlord record with no tenant.

**Noise (all 64 Adams rows entered since 2025-01-01, classified by eye from FolderName and folderdescription):** 9 new industrial or warehouse site plans or amendments naming a project (Project Frontier 130,500 sq ft warehouse, Forgotten Star Brewery, ABC Cross Docking warehouse and truck repair, High Point 4A and 4B 418,300 sq ft, High Point Building 11 276,481 sq ft, Sable Garage Suites flex, R+L expansion, Trident data center 860,000 sq ft, Project Waterfall amendment); 12 minor amendments at existing industrial or distribution sites (FedEx Ground fence, ABC Supply staging yard, Foleys warehouse drainage, Medline guard house, Specialty Wood Products fencing, Prologis Park 70 gates, Roadway Express gates, Eagle USA Freight generator pad, Michelin loading ramp, Smith Road Industrial Park fence, 3301 N Lewiston opening, 18920 E Smith Rd); 43 plainly not industrial (Aurora Highlands and Windler housing plats and ISPs, apartments, ADUs, QuikTrip and 7-Eleven, Porteos retail pads, hotels, signs, animal shelter, RTD lots, oil and gas, vet clinic, auto sales). Share plainly not industrial: 43 of 64 (67 percent). September 2025 alone: 1 row (apartments). March 2026: 5 rows (affordable housing, Roadway Express gates, Porteos retail, Aurora Highlands replat, Sable Garage Suites).

**Join quality.** Matching was by FolderName (project or codename) and by Address. The layer carries a project name but not an applicant or owner: FolderName is the name given when the parent site plan was first filed, so minor amendments at older plants carry the original occupant (Arvada Hardwood Floor Company for the RK site, Michelin Tire Corporation for the RK Mission Critical building). About half of the site-plan rows have Address and Parcel null (all five DA-2284 rows, all DA-1478 rows), so new-build site plans can only be joined by name or by the point geometry. County is populated on 79 percent of rows.

**Access.** Open, no key. Cloudflare sits in front of `ags.auroragov.org` and returned HTTP 403 "Attention Required" pages for some where clauses, deterministically for `InDate >= DATE '...' AND InDate < DATE '...' AND County IS NULL` (and `IS NOT NULL`), and intermittently for one two-date clause with `County LIKE 'ARAP%'`, while the identical clause sent by curl, and simpler clauses, returned 200. Treat it as a WAF signature on SQL-like text, not a block on the client: pull by date range only and filter County, nulls and names client-side. Do not probe for the pattern.

**Verdict: build** (back-tested). The only source in this group that fired before press (Waterfall site plan, -1.7 months) and it names new industrial buildings with square footage; low volume (2 to 6 Adams rows a month), but the name join needs a keyword list and the Address field is often null.

## Source 6: Aurora Building Permits, full layer (layer 44)

161,942 rows from 2021-10-31. Since 2024-01-01: 90,227 rows, of which 19,366 (21 percent) are on the Adams side by PropY, 66,127 Arapahoe, 4,734 with no coordinates. Sample months: September 2025 2,613 rows (599 Adams, 1,886 Arapahoe, 128 no XY); March 2026 2,279 rows (508 Adams, 1,633 Arapahoe, 138 no XY). So roughly 22 to 23 percent of Aurora permits are on the Adams side.

**Coverage: 3 confirmed of 3 Adams projects (C22, C25, C24), plus X02 confirmed on the Arapahoe side.**

Earliest record per project and lead against press:

| Project | Earliest record | InDate | Lead (months) |
|---|---|---|---|
| C22 PMI | 24-2475986 temporary construction office, PROJECT WATERFALL, 25315 E 48th Ave | 2024-09-30 | +2.5 |
| C25 RK | 25-2563038 partial demolition, RK INDUSTRIES, 3301 N Lewiston St | 2025-09-25 | +0.9 |
| C24 Pretred | 25-2563829 tenant finish 4.5M, PRETRED - BLDG 2, 6550 N Denali St | 2025-09-29 | +14.9 against the FALLBACK month; -1.0 against the lease announcement of 2025-10-28 |
| X02 Cerebral | 21-2086752 phase one revisions, CEREBRAL BREWING, 9990 E Colfax Ave | 2021-12-17 | -13.1 (FALLBACK press; Arapahoe side) |

Before press: 0 of 3 Adams projects against the earliest press date. Against the first dated public tie of the company to the site, Pretred's permit was 29 days ahead. Both discovery examples confirmed: the Project Waterfall permits exist at 25315 and 25305 E 48th Ave (337 Waterfall-named rows across 12 addresses, main factory shell 24-2481368 entered 2024-10-21 at 257.6M, tenant improvement 25-2513918 entered 2025-03-13 at 206.3M; discovery wrote 26-2513918), and the RK overhead-crane foundation is 26-2647459 (online folder 2026-08-18) with the Limited Building Permit 26-2651612 dated 2026-09-03. PMI is named in the text once (24-2483738, "PROJECT WATERFALL PMI TEMPORARY CONSTRUCTION TRAILER", 2024-10-31); otherwise the project is the codename. Controls returned nothing (no Pecos, Heinz or E 104th Ave addresses in the layer), as expected for a city layer.

**Noise sample, 50 rows each, systematic every-nth draw from the Adams-side rows, classified by eye from SubDesc and FolderDescription:**

- September 2025 (599 Adams rows): 4 industrial-relevant (Denali PA-7 Bldg 1 warehouse fit-out with forklift charging, Chadwell Supply racking, two Project Waterfall items); 46 plainly not (16 residential reroofs, 11 single-family detached, 6 residential solar, utility street cuts, signs, a pharmacy remodel, a nonprofit campus, residential mechanical). Not industrial: 92 percent.
- March 2026 (508 Adams rows): 7 industrial-relevant (Amazon BJC1 material-handling alteration 2.68M and automated sorting 1.46M, Project Chorro mezzanine and generator, RK Industries electrical, two Project Waterfall items, a Project Early Bird fire sprinkler at 25000 E 56th Ave); 43 plainly not (12 single-family detached, basement finishes, furnaces, residential EV chargers, reroofs, a hotel, a school art room, a vet clinic, the animal shelter). Not industrial: 86 percent.

Type mix on the Adams side (September 2025): Roofing-RT2 138, Single-Family Detached 80, Plan Revisions 78, Electrical 52, Solar PV Residential 41; Commercial Building Permit only 8 and Factory Use Building 5. Filtering to FolderDesc in (Commercial Building Permit, Limited Building Permit) with a commercial SubDesc and valuation over about 100,000 removes most of the noise.

**Join quality.** Matching was by Address (exact street number plus street name worked on every project) and by FolderDescription text (project names and codenames, tenant names, equipment descriptions). No applicant, owner or contractor field; the company appears only when the applicant typed it into the description, which happened for RK, Pretred and Cerebral but for PMI only once. Each scope appears twice (Online Building Folder intake, then the Limited or Commercial permit a few days later), so counts double unless deduplicated on FolderRSN or on description plus address.

**Access.** Same host and Cloudflare behaviour as layer 180. Discovery's note holds: FULL_ADDRESS and PropStreet do not exist on layer 44; Address works.

**Verdict: build** (back-tested). 3 of 3 confirmed with exact addresses and equipment-level descriptions (crane foundation, dust collection system, equipment packages), but it fires after press for announced projects (+0.9 to +2.5 months); its value is confirming site and stage, and catching unannounced tenant fit-outs (Pretred's permit preceded its lease announcement).

## Source 13: Aurora Businesses (All Non-Home) licence layer (layer 77)

8,507 active licences (every hit has End_Date 9999-12-31, so this is a current snapshot, not a history); 1,964 on the Adams side. Issue_Date runs to 2026-10-23; 849 issued in 2026 so far. Issue_Date minus Start_Date on Adams-side licences issued since 2024: median 30 days, 20 percent issued before the stated start.

**Coverage: 1 confirmed, 1 possible, 1 none of 3 Adams projects; X02 confirmed (Arapahoe side).**

| Project | Licence | Issue_Date | Lead (months) | Class |
|---|---|---|---|---|
| C22 PMI | KAIRUS INC., 25315 E 48th Ave, 312230 Tobacco Manufacturing (start 2026-01-01) | 2025-09-09 | +13.8 | possible (different legal name) |
| C25 RK | none at 3301 N Lewiston St (licence there is the previous occupant AURORA SHOP, 2023); RK INDUSTRIES LLC at 20101 E 36th Dr issued 2019-10-11, out of window | | | none |
| C24 Pretred | PRETRED, INC., 6550 N Denali St Ste 100, 326299 (start 2026-08-10) | 2026-08-22 | +25.7 (+9.9 against the lease announcement) | confirmed |
| X02 Cerebral | CEREBRAL BREWING COLFAX, 9990 E Colfax Ave, 312120 (start 2021-04-15) | 2022-07-06 | -6.5 | confirmed |

Before press: 0 of 3 Adams projects. The only negative lead is Cerebral against a FALLBACK date set after production began, so it does not show the licence beating press. Pretred's licence came 11 months after its first permit and 10 months after the lease story. Could the date ever precede press: only for a company that never announces; for announced projects the licence is the last signal (0 to 6 months before operations, as discovery said).

**Noise.** Adams-side licences issued: September 2025, 18 (sectors 81 personal services 6, 72 food 4, 54 professional 2; manufacturing 2); March 2026, 15 (81: 5, 72: 4, 45 retail 3; manufacturing 1, wholesale 1). Since 2024: 523 Adams-side licences, 44 manufacturing (NAICS 31 to 33) and 29 wholesale (42). A NAICS 31 to 33 filter leaves about 1 to 2 rows a month.

**Join quality.** Business_Name and Business_Address with suite, plus NAICS. Business_Owner exists (not used, may hold individuals). The legal name may differ from the trade name (Kairus for the PMI plant).

**Verdict: park** (forward test only) (back-tested). Clean names and NAICS, but it never fired before press and lags permits by about a year; keep as a confirmation field for the ranking, not a discovery source.

## Source 37: Council and Planning Commission agendas

Attempted, not completed. The council page carries one static URL, the current agenda (`.../Council Meetings/Agendas/AuroraCouncilAgenda.pdf`). Past agenda packets, minutes and vote results sit in a CivicLive "document container" widget (object 493563) and the "View Other Agendas and Minutes" link opens a CivicLive calendar (calendar id 16446440); both are populated by script through web services that `https://www.auroragov.org/robots.txt` disallows (`/WebServices/`, `/WebApi/`, the calendar and CalendarPicker `.asmx` endpoints), so I did not call them. Web search found no Aurora, Colorado agenda PDF mentioning Project Waterfall or RK Industries (only committee packets under `/UserFiles/DBFiles/...`, which have unguessable ids). Press coverage of the PMI announcement (CPR, 2024-07-16) names only the state EDC approval and no council vote date; the April 2026 Hoodline piece on RK names the state credit and no council date. Whether an agenda item preceded press is therefore untested.

**Verdict: park** (not back-tested: archive not reachable by static URL). Manual lookup through the council page's document widget if a specific vote date is needed.

## Source 56: Building Permit Statistics monthly PDFs

One month sampled (November 2017, `/UserFiles/DBFiles/server_1881137/202003/16528948/11_2017.pdf`, the only month with a static URL found by search; recent months sit in the same document-container widget). One page: inspections, plan reviews, permits issued, valuation and fees, with counts by class (single family, multi-family, commercial, tenant improvement, roofing, electrical, and so on). No facility-level rows, as discovery said.

**Verdict: drop** (back-tested on one month). Aggregate only.

## Not tested

- **(31) Sentinel Colorado RSS.** Press feed; not a back-test source under rule 7. Keep for the RSS watcher.
- **(33) Aurora Customer Portal (AMANDA Citizen Portal).** Browser-only portal; terms check only, below.

## Terms findings

- `https://ags.auroragov.org/robots.txt`: 404 (no robots file). The ArcGIS REST endpoints are open, no key, and the Aurora open-data hub items carry the Aurora Data Download Disclaimer (liability and indemnity, no commercial-use restriction, as recorded at discovery). Cloudflare WAF blocks some SQL-like where clauses (see source 4).
- `https://devportal.auroragov.org/robots.txt`: 404. The portal root redirects to `/citizenportal/app/` (Angular single-page app). The landing page links only to the city privacy policy (`https://www.auroragov.org/city_hall/contact_us/privacy/`), which covers what the site collects about visitors (log data, cookies, email) and says nothing about automated access, scraping or commercial use. No separate terms of use or disclaimer page was found on the portal. Login is needed for applications; public record search was not exercised. Treat as a manual lookup source; the GIS layers already expose the same AMANDA folders (FolderRSN links them).
- `https://www.auroragov.org/robots.txt`: disallows `/Search/`, `/WebApi/`, `/WebServices/`, `/portal/svc/` and the staff directory, workspace calendar and calendar picker web services, plus some archived pages. The static PDF paths under `/UserFiles/` are not disallowed.

## Corrections the test suggests to the ground truth (not applied)

1. **X02 Cerebral Brewing county: Arapahoe.** Both Aurora layers place 9990 E Colfax Ave south of the county line (layer 44 PropY 1,694,969; layer 77 Y 1,694,969; line at about 1,695,150), and layer 180's Colfax rows show even-numbered addresses coded ARAPAHOE. This agrees with the SBA record. Drop it from the Adams set.
2. **C22 county: Adams confirmed.** Every Project Waterfall record carries County = ADAMS on layer 180 and PropY 1,712,903 on layer 44 (well north of the line). The "sources conflict with Arapahoe" caution can be resolved.
3. **C22 earliest record could be moved earlier.** The city's site plan DA-2284-02 (2024-05-24) predates the 2024-07-16 announcement; worth adding as a milestone. The equipment-package permits (Korber and Clevertech, 2025-05-22) are a useful "equipment ordered" milestone.
4. **C25 address and milestones.** 3301 N Lewiston St is confirmed as the HQ project site by RK-named permits from 2025-09-25, and the ground truth's RK Mission Critical address 17450 E 32nd Pl is a separate existing plant; a third RK site is 20101 E 36th Dr (licence since 2019, RKMC1 permits 2026-10). Office remodel 4.89M entered 2025-10-10, warehouse and shop renovation 3.0M entered 2026-06-13, crane foundation 2026-08-18.
5. **C24 Pretred.** The tenant-finish permit of 2025-09-29 precedes the lease announcement of 2025-10-28 and could replace the FALLBACK month as the earliest dated tie of Pretred to 6550 N Denali St; the licence (start 2026-08-10) suggests operations began around August 2026, which bears on the "move-in not confirmed" caution. Pretred's existing plant is 3700 N Salida St, Unit 20 (Gateway Park Building 24).
6. **Layer 180 is not active-only.** Discovery called it "Active Development Applications"; it holds Retired records back to 2012, so weekly snapshots are not needed for this layer.

## Not finished

- Source 37 agenda sampling (archive behind script-driven widgets whose services are disallowed by robots.txt).
- Source 56 sampled on a 2017 month, not a recent one, for the same reason.
- Layer 180 noise was classified on all 64 Adams rows since 2025 rather than 50 per sample month, because the layer has 1 and 5 rows in those months.
- The Cloudflare 403 pattern was not fully characterised; the scrape step should query by date range only and filter client-side.
