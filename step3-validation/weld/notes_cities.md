# Weld County validation, group `cities` (Greeley, Fort Lupton, Evans, Johnstown, Longmont slice)

Run date 2026-11-05 (UTC). Raw pulls are in `step3-validation/weld/raw/cities/` (git-ignored). Matches are in `matches_cities.csv`.

## Sources tested and endpoints

| Rank | Source | Endpoint used |
|---|---|---|
| 5 | Greeley TRAKiT Projects layer | `https://gis.greeleygov.com/arcgis_svr/rest/services/Data_Services/TrakitProjects/MapServer/0/query` (172 records, one request) |
| 9 | Greeley CivicClerk OData API | `https://greeleyco.api.civicclerk.com/v1/Events?$filter=...` (68 City Council and Planning Commission events 2023-07-01 to 2024-03-31) and `/v1/Meetings/GetMeetingFileStream(fileId=N,plainText=true)` (29 agendas, 20 packets) |
| 8 | Fort Lupton Planning_AGOL layer and Current Development Projects page | `https://services2.arcgis.com/7fqvVMRB6DcB5wXC/arcgis/rest/services/Planning_AGOL/FeatureServer/1/query` (37 records) and `https://www.fortluptonco.gov/463/Current-Development-Projects` (browser user agent) |
| 14 | Evans Current Development Projects table | `https://www.evanscolorado.gov/building-business-development/planning-and-development/current-development-projects/` |
| 20 | Longmont Active Developments layer, Weld slice | `https://pwnrmaps.ci.longmont.co.us/arcgis_public/rest/services/PLANNING/Planning_Map_2025/FeatureServer/10/query` (218 records, `returnCentroid=true`, `outSR=4326`) clipped with `https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/County_Boundary_open_data/FeatureServer/0` |
| 19 | Johnstown Current Projects table (same row as the eTRAKiT portal) | `https://www.johnstownco.gov/539/Current-Projects` |

Browser-only portals, terms check only: rank 19 Johnstown eTRAKiT (`jcol.csqrcloud.com/community-etrakit/`), rank 27 Greeley eTRAKiT (`trakit.greeleygov.com/etrakit/`).

Not tested: rank 21 Greeley Public Space permits, rank 23 Evans eSCRIBE, rank 25 Fort Lupton Agenda Center (reasons below).

## Assumptions

- Each city source was searched for all six ground-truth projects by full-text search of the dump, but only the project inside that city's jurisdiction can score. The other five are `none` rows marked "out of jurisdiction" in the CSV; they do not count against coverage.
- Greeley TRAKiT drops the W prefix from 29th Street addresses (PUD2026-0004 at `3502 29TH ST` is described as "Culver's on W 29th St"), so `2400 29TH ST` is taken as the same site as the ground truth's 2400 W 29th St. This matters for the CivicClerk permit-report hit below.
- Colorado Premium's press date is a FALLBACK (opening article 2024-02-05), so every lead time for C34 is measured from the opening, not from an announcement.
- The county line for the Longmont slice is the Weld `County_Boundary_open_data` polygon (point-in-polygon on each case's centroid and on every vertex). Near Longmont the boundary vertices sit at longitude -105.0552 to -105.0555, which is Weld County Line Rd; a longitude cut at -105.0553 gives the same six cases.
- CivicClerk: the task allowed 20 packet streams. I also streamed 29 agendas (small files, 2 to 9 KB) to pick the packets; those are counted separately below. One request a second throughout.
- "Industrial" in the noise samples means a manufacturing, warehouse, industrial-park, outside-storage or process-facility case. Oil and gas well pads, solar gardens, car washes, restaurants, housing, schools, wireless and zoning letters are non-industrial.

## Rank 5. Greeley TRAKiT Projects layer

Coverage: 0 confirmed, 0 possible of 6 (C34 Colorado Premium is the only in-jurisdiction project; X27 Microvast is out of jurisdiction, none).

Back-test of C34: no case at 2400 (W) 29th St and no PROJECT_NAME or APPLICANT with PREMIUM, K2D or SOUS. The layer is active-only: 172 records, APPLIED from 2023-03-01 to 2026-11-03 (only one record before 2024-05 and 156 of 172 applied since 2025-11). Colorado Premium bought the land in 2022 and opened in February 2024, so its site plan review would have been a 2022 or early 2023 case that has rolled off. The miss says nothing about whether the layer would have carried it at the time; it only says the layer keeps no history. Lead time cannot be scored for this project from this source.

Supplementary searches: JBS / Swift Beef (Promontory Cir, N 11th Ave, 800 N 8th Ave): none; the only 11th Ave hit is a pizza business-license address check. Leprino (E 8th St): no case names Leprino. SPR2024-0023 at 330 E 8TH ST (applied 2024-08-09, approved 2026-10-05, MAJOR SITE PLAN REVIEW, "SPR Amendment - Building Expansion", applicant an individual) is an industrial-corridor expansion with no company named; listed as `none` for Leprino and worth a manual look. Industrial land cases currently in the layer: SPR2026-0019 Loveland Industries site improvements at 14520 CR 64 (2026-10-28); SPR2026-0018 and PUD2026-0005 outside storage yard added to an existing industrial use at 1299 H St (2026-10-14); SUB2026-0026 merging lots into a single industrial lot at 2301 1st Ave (2026-09-28); SPR2026-0010 storage building addition at 2340 117th Ave (2026-06-23); ZON2026-0001 Great Western Industrial Park establishment of zoning (2026-03-18); SPR2025-0027 30,962 sf industrial flex building at 2334 117th Ave (2025-09-18, applicant Roche Constructors Inc). The two USE BY SPECIAL REVIEW cases in the layer are a car wash and a multi-family use. A sibling service, `Data_Services/TRAKiT2/MapServer/7` (USR_poly, 23 records), holds only 2010 to 2016 oil and gas USRs; not useful.

Dates: APPLIED, SUBMITTED and APPROVED are proper date fields and APPLIED is filled on all 172 records (date field used: APPLIED). Not undated, but history-less.

Noise sample (rule 5): September 2025 has 1 case (SPR2025-0027, industrial flex, so 0 percent non-industrial but n=1); March 2026 has 11 cases, 10 non-industrial (91 percent: two zoning letters, a 7 Brew coffee site plan and plat, sidewalk phasing, a downtown water project, an address verification, a residential lot line adjustment, two historic-preservation alterations) and 1 industrial (Great Western Industrial Park zoning). The 50 most recent cases (2026-07-15 to 2026-11-03): 4 industrial or industrial-adjacent (Loveland Industries, the two 1299 H St outside-storage cases, the 2301 1st Ave industrial lot consolidation), 46 non-industrial (92 percent: 17 zoning verification letters and records requests, wireless, apartments, Jiffy Lube, 7 Brew, Walmart, Culver's, Weld County Justice Center, church, auto repair, a test record). Over the whole layer, 41 of 172 records are PUBLIC RECORDS REQUEST (zoning letters) and 13 are ADDRESS cases; only 26 are SITE PLAN REVIEW, 2 USE BY SPECIAL REVIEW, 8 REZONE, 9 ANNEXATION.

Join quality: SITE_ADDRESS (TRAKiT style, no W/E prefix on numbered streets, often blank on annexations and rezones), PARCEL_ID, LAT/LON. PROJECT_NAME is free text that sometimes names the business (Loveland Industries, Crabtree Brewing, Culver's, Walmart) but usually describes the work. APPLICANT is filled on 157 records but is a company string on only 19; the rest are individuals and must be dropped on ingest, as must PLANNER and EMAIL.

Access: ArcGIS Enterprise MapServer, no key, `maxRecordCount` 1000, no copyright text on the service, `/robots.txt` on gis.greeleygov.com returns 404. Not a Weld County AGOL item, so rule 9 does not apply.

**Verdict: build** (inherited + spot-checked). Same type as the Adams planning-case mirrors; carries real dates, parcel and address; cannot be back-tested because it holds no history, so start snapshots now and filter to SITE PLAN REVIEW, USE BY SPECIAL REVIEW, REZONE, ANNEXATION and SUBDIVISION with industrial keywords (about 8 percent of the current stock).

## Rank 9. Greeley CivicClerk OData API

Coverage: 0 confirmed, 1 possible of 6 (C34; the other five out of jurisdiction, none; X27 none).

What was pulled: 68 City Council and Planning Commission events from 2023-07-01 to 2024-03-31 (paged with `@odata.nextLink`, 15 per page). Plain-text streams: 29 agendas (every non-cancelled Planning Commission meeting, regular Council meeting and special Council meeting in the window) and 20 packets (14 regular Council packets: 2023-07-18, 08-01, 08-15, 09-05, 09-19, 10-03, 10-17, 12-05, 12-19, 2024-01-16, 02-06, 02-20, 03-05, 03-19; 6 Planning Commission packets: 2023-07-25, 08-08, 08-22, 09-26, 2024-01-23, 03-12). Eight of the 20 packet streams returned 0 bytes of plain text (Council 2023-09-19, 10-17, 12-05, 12-19, 2024-02-06, 02-20, 03-05; Planning Commission 2023-09-26 and 2024-03-12), so for those meetings only the agenda was searched; the PDF stream was not fetched. A HEAD request is refused (405, GET only).

Earliest dated mention of Colorado Premium: none by name. No agenda or packet in the window names Colorado Premium, K2D or sous vide, and no incentive, site plan, use by special review or annexation item names it. The address does appear once: the Planning Commission packet of 2023-08-22 (fileId 3958, 166 pages) ends with the Building Inspection Division "Monthly Construction Report, July 2023", a table of issued permits (Permit Number, ISSUED, JOBVALUE, SITE_ADDR, PERMITTYPE, PERMITSUBTYPE; 338 rows for the month). Row `BCX2307-0129  07/25/2023  7,400,000  2400 29TH ST  COMMERCIAL EXISTING  TENANT FINISH`. Record date 2023-07-25 (ISSUED column); press date 2024-02-05 (FALLBACK, opening article); lead -6.41 months (meeting date 2023-08-22 would be -5.5). In window; sits before the 2024-01-01 scrape window. Match class `possible`: address only, no company name or suite. So the source does fire before the press date for C34, but through a permit report embedded in a packet, not through a hearing item.

Other items read: the 2023-07-18 Council packet lists an executive session "regarding an economic incentive agreement for a company relocating to the City of Greeley" without naming it; the 2023-08-15 packet shows that item was the Alquist 3D Relocation Incentive Agreement and Capital Funding Agreement (approved 2023-08-15). The 2024-03-19 packet's "tax incentive" hit is the DDA sales-tax allocation. Leprino appears only as the Leprino Foods Company Foundation funding Delta Park (2023-10-03). Industrial-land hearing items in the window were an oil and gas well pad USR (USR2023-0004) and two solar USRs on I-M land (USR2022-0017, USR2023-0001).

Noise (development-related agenda items per meeting, counted from the agendas by keyword: annexation, rezone, zoning, use by special review, site plan, subdivision, plat, PUD, development agreement, incentive): regular Council meetings 0 to 7 of 15 to 29 items (median 2); Planning Commission meetings 0 to 4 of 7 to 11 items (median 2). Most development items are residential subdivisions, annexations for housing, PUDs, a car wash and a parking lot; none in the window was an industrial end user. The Monthly Construction Report appeared in only 1 of the 6 Planning Commission packets read, so it is not a reliable monthly feed from this API alone (the other months may be in packets that returned no plain text, or not attached at all).

Join quality: free text. Addresses and case numbers in staff reports; company names in agreements. In the permit report, SITE_ADDR only (no applicant, no description beyond PERMITSUBTYPE). Permit numbers (BCX, BCN, MECH, PLB) are the TRAKiT numbers that the login-walled Greeley eTRAKiT would resolve.

Access: no key, JSON. `greeleyco.api.civicclerk.com/robots.txt` returns a Cloudflare "content signals" preamble (search, ai-input, ai-train definitions); no disallow lines were seen in the part read. No terms text on the API. Behind Cloudflare; all requests answered.

**Verdict: park** (back-tested). One `possible` hit for C34 at -6.4 months, but by address inside an embedded permit report rather than a named hearing or agreement item; 8 of 20 packets stream no text; the per-meeting development-item count is low and residential. Worth a weekly poll of agendas plus a search of Planning Commission packets for the Monthly Construction Report table (which is the only commercial building-permit list Greeley publishes without a login), not a standalone build.

## Rank 8. Fort Lupton Planning_AGOL layer and Current Development Projects page

Coverage: 0 confirmed, 0 possible of 6 (C36 Sphere Renewables is the only in-jurisdiction project; X27 none).

Back-test of C36: all 37 layer records and all 33 HTML table rows (4 tables: 11 under review, 14 approved, 0 on hold, 2 withdrawn) were read. No Sphere Renewables, no 13516, no CR 8 / WCR 8 / County Road 8 in Project_Name, Applicant, Comments, Doc_Link or the table. The "County Road 8.5 Annexation and Special Use Permit" (ANX26-001, SUP26-001, applicant 8 1/2 Enterprises LLC, hearings 2026-05-14 and 2026-06-02, withdrawn) is a different site. The layer's dates run from Ref_Response_Date 2023-10-04 (South Platte Villas plats, withdrawn) to 2026-10-12; Sphere's county incentive agreement was 2022-12-05 and its construction certification 2023-05-31, so its Fort Lupton case, if one existed, predates the layer. Lead time cannot be scored.

Does the layer carry dates: yes, three date fields, PC_Date (hearing), CC_Date (hearing) and Ref_Response_Date (referral comments due), plus a Year string. There is no submittal or application date; Ref_Response_Date (filled on 31 of 37) is the earliest and sits a few weeks after submittal. Date field used: Ref_Response_Date.

Supplementary: EquipmentShare Administrative Site Plan, ADM26-004, applicant EquipmentShare.com Inc, Status Under Review, Ref_Response_Date 2026-08-12, Doc_Link path `EquipmentShare 145 14th St (ADM26-004)`; point geometry at -104.8174, 40.0956. `confirmed` (company plus street address in the record). Northland Business Park: COZ25-003 change of zone (KCP Northland I and II LLC, PC 2025-11-13, CC 2025-12-02, approved), LLA26-001 lot line adjustment and PPL26-002 North Land PUD Fourth Filing (Ref 2026-07-16, under review); `confirmed` as a park, no end user named. Other industrial-leaning records: 2183 S Denver Ave change of zone and administrative site plan (Vecchiarelli Holdings LLC, 2025), 1325 Factory Circle AT&T equipment (ADM26-003), L.G. Everist mining SUP and two annexations (2025), Western Midstream Parsnip pipeline SUP (2026), Xcel Energy SUP (2026).

Noise sample (all 37 records, undated snapshot rule): 11 industrial or industrial-adjacent (the records above), 26 non-industrial (70 percent: residential plats and annexations for South Platte Villas, Vista Meadows, Lancaster Crossing, Sunrise, High Pointe Hills, Sweetgrass Meadows, Cottonwood Downs, Wildflower Flats; City Hall; a variance; a historical society site plan).

Join quality: no address field. Project_Name sometimes carries the address (2183 S Denver Avenue, 1325 Factory Circle, 100 McKinley Ave); Doc_Link is an internal Windows path (`G:\...` or `C:\BD\Box\...`) that carries the case number and sometimes the street; Web_Link points to a DocumentCenter folder; polygon and point geometry on both layers. Applicant is a company on 29 of 33 filled records but holds individuals on 4 (and the HTML table names the planner on every row): write "individual" and drop planner names on ingest. Project_Num is blank on 34 of 37.

Access: ArcGIS Online feature service, open, item `77fbc0728e40475088e10eb3ca212fc1` owned by `ftluptongis`, `licenseInfo` null, `accessInformation` "City of Fort Lupton GIS", access public (not a Weld County item, so rule 9 does not apply). The city website answers a browser user agent (200, 134 KB).

**Verdict: build** (inherited + spot-checked). Planning-case mirror of the Adams type with hearing dates, company applicants and a case-number link to the DocumentCenter; small (37 records) and history-less from 2023-10, so it cannot be back-tested against Sphere; carries the EquipmentShare and Northland signals the discovery notes named.

## Rank 14. Evans Current Development Projects table

Coverage: not applicable; no ground-truth project is in Evans (6 `none` rows, out of jurisdiction).

Parse: two tables. In-process table, 14 cases (columns Case No., Applicant, Location, Brief description, Status). Expired or stalled table, 5 rows. No date column anywhere; the only dates are embedded in status text of the second table (comments sent 11/14/22, 10/26/22, 1/17/23; SUP recorded 9/25/2023; CC continued to 11/7/23). The page carries no "updated" stamp. Case numbers encode the filing year (24-SP-04 is a 2024 site plan). Treated as undated; no lead time possible.

In-process cases: 23-SP-01 Zavala duplexes; 24-AP-01 Evans Redevelopment Agency replat; 24-SP-02 Dollar General; 24-SP-03 Prairie View multifamily; 24-AP-03 minor plat; 24-AP-04 Mountain Cement Co minor plat (approved, COAs in progress); 24-SP-04 Mountain Cement Co site plan for MCC Terminal, SW of CR 394 and 47th Ave (staff report in progress); 24-FINAL-02 Liberty Draw final plat; 24-SP-05 Acme Oilfield Services site plan for industrial company, SW corner 43rd St and Valmont St (approved, COAs in progress); 24-ANNEX-01 annexation; 25-AP-01 replat; 25-SP-01 Industrial Parkway LLC parking facility, NE corner Brantner and Industrial (referrals in progress); 25-AP-02 Liberty Draw minor plat; 25-SP-02 Planet View site plan for facility expansion, SW of Carson and 37th St (comprehensive review in progress). Expired table includes 22-COZ-02 change of zone I-1 to I-3 with SUP for a batch plant at 49th St and 23rd Ave (comments sent 11/14/22).

Industrial flags: 24-AP-04 and 24-SP-04 (Mountain Cement), 24-SP-05 (Acme Oilfield Services), 25-SP-02 (Planet View), 25-SP-01 (Industrial Parkway LLC, a parking facility), 22-COZ-02 (batch plant). All `possible` for the supplementary rows: company named, but locations are corner descriptions, not street addresses.

Noise (all 14 in-process rows): 5 industrial-leaning, 9 non-industrial (64 percent: duplexes, replats, Dollar General, multifamily, residential final plat, annexation).

Join quality: Applicant (company or surname) and Location (corner text or address) only; no parcel, no geometry, no dates. The Story Map was not opened.

Access: plain GET, 200, 74 KB, no terms stated.

**Verdict: park** (spot-checked only). Carries three named industrial cases for a city with no other open feed, but 14 rows, no dates, corner-text locations and no history; a monthly diff of the page is cheap and enough. The eSCRIBE packets (rank 23) would supply the dates.

## Rank 20. Longmont Active Developments layer, Weld County slice

Coverage: not applicable; no ground-truth project is in Longmont (6 `none` rows).

Weld slice: 6 of 218 cases have their centroid inside the Weld `County_Boundary_open_data` polygon, and the same 6 are the only cases with any vertex inside it. All six sit between longitude -105.0544 and -105.0389 at latitude 40.157 to 40.162 (the Ken Pratt Blvd / Brien Ave / Common Dr area east of Weld County Line Rd): DV-SITE PLAN-21-00038 Westview Business Park site plan and minor plat, 2500 E Ken Pratt Blvd, two high bay warehouses, 176,800 sf, submitted 2021-11-24, status A; DV-SITE PLAN-21-00012 Sandstone Ranch Apartments (2021-02-19, UC); DV-SITE PLAN-24-00020 Shops at Sandstone Marketplace (2024-10-10, R); DV-SITE PLAN-25-00006 Gallery at Longmont senior living (2025-04-14, UC); DV-CUSP-26-00020 Sandstone Marketplace Building C (2026-06-11, R); DV-SITE PLAN-26-00010 Advance Auto Parts at 2170 Brien Ave (2026-06-18, R). The Beauprez Farms No. 2 and Puma cases on Ute Hwy that the discovery row mentions are at longitude -105.11 to -105.12, west of the county line, so they are Boulder County cases. Cases straddling the line: none (Remedy Longmont MOB at 1800 Cowles Ave has a centroid at -105.0556 to -105.0570, just west of the line, and no vertex inside Weld).

Supplementary: 4120 Specialty Pl (BAE Systems) does not appear; no record matches SPECIALTY, BAE, UQM or 4120 anywhere in the 218 records. The BAE incentive (2026-09-16) and deed (2026-10-05) have not produced an active Longmont development case as of this pull.

Noise (the full Weld slice, 6 records): 1 industrial (Westview Business Park, speculative warehouses), 5 non-industrial (83 percent: apartments, senior living, retail, auto parts).

Dates: Submittal_Date is a string field in M/D/YYYY form (filled on all six). Date field used: Submittal_Date.

Join quality: Location (street address), ParcelNo, polygon geometry, Project_Description free text, capID1 to capID3 (Accela record IDs), Applicant (company or individual; not stored here). Project_Manager and Creator hold staff names and must be dropped.

Access: ArcGIS Enterprise feature service, no key, 218 records in one request; `pwnrmaps.ci.longmont.co.us/robots.txt` answers 200.

**Verdict: park** (inherited + spot-checked). The Weld slice is six cases, one of them industrial and already built; the layer is a planning-case mirror of the build type, but the Weld share is too small to justify a Weld-side build. If the Boulder County run builds this layer, take the Weld slice from that pull with the county-boundary clip above.

## Rank 19. Johnstown eTRAKiT portal and Current Projects page

Portal (browser-only, terms check only, no search attempted): `https://jcol.csqrcloud.com/robots.txt` returns HTTP 500 with an empty body (no robots file). The portal home page (200) carries a disclaimer: the Town "makes every effort to produce and publish the most current and accurate information on this website but makes no representation or warranty as to the accuracy of the information. No warranties express or implied, are provided ... Any person using the information on this website does so at their own risk and accepts the information AS IS, WITH ALL FAULTS ... Utilization of this website and this resource constitutes acceptance of these statements." Liability only; no clause on automated access, commercial use or redistribution. The page footer is "Powered by CentralSquare Technologies"; no separate terms or privacy page is linked from the portal. The home page also embeds a full public contractor list (hundreds of licensed contractors) in the page source. Treat as a manual lookup source.

Current Projects page (parsed): four tables, 8 projects. Amendments: Thompson River Ranch Trail Amendment AMD25-0002 (3961 River Ranch Pkwy, in review); Candlelight Performing Arts Center AMD26-0004 (4743 Marketplace Dr, in review); Atlas Garage and Storage at Gateway Park AMD26-0003 (355 Mountain View Rd, in review). Annexations: Bakersky ANX24-0004 (approved); Morning Star ANX25-0001 (in review). Development: Quik Trip DEV21-0013 (parcel 8527000018, in review). Subdivisions: Thompson River Ranch F.13 SUB20-0010; Revere North F.3 SUB24-0004. No industrial case; no dates on the page.

**Verdict (page only): drop** (spot-checked only). Eight undated cases, none industrial, no history. Portal: not tested (browser-only).

## Rank 27. Greeley eTRAKiT (terms check only)

`https://trakit.greeleygov.com/robots.txt` returns 404 (redirects into `/etrakit/robots.txt`, IIS "file or directory not found"). The home page disclaimer: "The City of Greeley, Colorado makes every effort to produce and publish the most current and accurate information possible. No warranties, expressed or implied, are provided for the data herein, its use, or its interpretation. Utilization of this Web site indicates understanding and acceptance of this statement, as well as the privacy and security policy http://greeleygov.com/privacy." That privacy link redirects to `https://greeleyco.gov/privacy/`, which returns a 404 page, so the referenced policy could not be read. Liability-only disclaimer; nothing on automated or commercial use. All searches require a free public account (confirmed at discovery; not retried). Not tested; manual lookup only. Note that the permit numbers it would resolve (BCX2307-0129 style) are exactly what the Planning Commission Monthly Construction Report lists, so the CivicClerk packet route is the login-free substitute.

## Not tested

- Rank 21 Greeley Public Space permits layer: an active-only right-of-way and utility-connection permit layer; the discovery row already parks it, and it holds contractor names rather than end users. Not in this group's test plan; no ground-truth project would be expected to appear.
- Rank 23 Evans eSCRIBE: an agenda feed that was not parsed (rule 7). It is the natural date source for the Evans table above.
- Rank 25 Fort Lupton Agenda Center: an agenda feed that was not parsed (rule 7); the site is user-agent sensitive.
- Greeley eTRAKiT and Johnstown eTRAKiT: browser-only portals (rule 8); terms reported above.

## AGOL license text (rule 9)

The only Weld County AGOL item used in this group is the county boundary, used as a clip and not as a signal source. Item `033ff493690c4b51b52678e31f04247d` (`County_Boundary_open_data`, owner `WeldCounty`, access public), `accessInformation`: "Weld County Government". `licenseInfo`: "This product has been developed solely for internal use only by Weld County. The GIS database, applications, and data in the product is subject to constant change and the accuracy and completeness cannot be and is not guaranteed. The designation of lots or parcels or land uses in the database does not imply that the lots or parcels were legally created or that the land uses comply with applicable State or Local law. UNDER NO CIRCUMSTANCE SHALL ANY PART THE PRODUCT BE USED FOR FINAL DESIGN PURPOSES. WELD COUNTY MAKES NO WARRANTIES OR GUARANTEES, EITHER EXPRESSED OR IMPLIED AS TO THE COMPLETENESS, ACCURACY, OR CORRECTNESS OF SUCH PRODUCT, NOR ACCEPTS ANY LIABILITY, ARISING FROM ANY INCORRECT, INCOMPLETE OR MISLEADING INFORMATION CONTAINED THEREIN." Reported, not decided. The Fort Lupton item has no licenseInfo; the Greeley and Longmont services carry no copyright text.

## Corrections the test suggests to the ground truth (not applied)

- C34 Colorado Premium: Greeley issued building permit BCX2307-0129 (commercial existing, tenant finish, job value 7,400,000) at 2400 29th St on 2023-07-25, per the July 2023 Monthly Construction Report. If the owner's team confirms this is the plant, it is a dated milestone ("building permit issued 2023-07-25") between the 2022 land purchase and the 2024-02 opening, and it shows the plant was a tenant finish of an existing building rather than new construction (the ground truth says "new 175,000 sq ft plant"). The permit number also implies an application in July 2023 (BCX2307). Not applied; the row names no company.
- C36 Sphere Renewables: Fort Lupton's layer starts in 2023-10, so a city-side milestone would have to come from the Agenda Center or a records request; nothing here changes the row.

## What was not finished

- CivicClerk: 8 of 20 packet streams returned empty plain text; the PDF streams for those meetings were not fetched (would exceed the 20-stream budget). Monthly Construction Reports for months other than July 2023 were not located, so the earliest named mention of Colorado Premium in Greeley records remains unknown.
- Fort Lupton Doc_Link folders (DocumentCenter) were not opened; the address in a submittal sheet would turn the EquipmentShare match from name-plus-path to name-plus-sheet.
- Evans Story Map and the Fort Lupton point layer attributes beyond geometry were not read.
- No lead time could be scored for the two in-jurisdiction ground-truth projects on the two planning layers (both history-less), so the before-press count for this group is 1 (CivicClerk, C34, `possible`).
