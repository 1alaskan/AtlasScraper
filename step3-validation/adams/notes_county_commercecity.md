# Adams County back-test, group `county_commercecity`

Step 3 validation, written 2026-10-30. Companion file: `matches_county_commercecity.csv` (same folder). All queries were read-only GETs against the public endpoints below, user agent `step3-research-validation/1.0`, one request a second, 2,000 rows a page. No forms were submitted, no accounts, no browsing of the browser-only portals.

## Sources tested and endpoints

| Rank | Source | Endpoint used |
|---|---|---|
| 1 | Adams County Planning Cases layer (Eye On Adams) | `https://services3.arcgis.com/4PNQOtAivErR7nbT/arcgis/rest/services/Planning_Cases/FeatureServer/0/query` |
| 2 | Adams County Building Permits layer (Eye On Adams) | `https://services3.arcgis.com/4PNQOtAivErR7nbT/arcgis/rest/services/Building_Permits_Eye_On_Adams/FeatureServer/0/query` |
| 7 | Commerce City Active Development Under Review and Under Construction | `https://gisserver.c3gov.com/gisserver/rest/services/Central_Square/CS_Active_Development_UnderReview/MapServer/0/query` and `.../CS_Active_Development_UnderConst/MapServer/0/query` |
| 12 | Adams County Assessor Property Sales table | `https://services3.arcgis.com/4PNQOtAivErR7nbT/arcgis/rest/services/Property_Sales/FeatureServer/0/query`, joined by hand to `.../Parcels/FeatureServer/0` (rank 29, used only as the parcel-number lookup) |
| 14 | Adams County PrimeGov meeting portal | `https://adamscounty.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` (JSON index), then `/Portal/Meeting?compiledMeetingDocumentFileId=<id>` for the HTML Agenda of every Board of County Commissioners public hearing and study session and every Planning Commission meeting, 2022 to 2026 |
| 15 | Commerce City Legistar | `https://webapi.legistar.com/v1/commerce/Matters?$filter=substringof('<term>', MatterTitle) eq true` |
| 17 | Adams County Current Land Use Cases page | `https://adamscountyco.gov/our-county/community-economic-development/planning-development/current-land-use-cases/` (one GET, sample only) |

Terms check only (no record browsing): 8 Commerce City eTRAKiT, 19 Adams County Accela Citizen Access, 22 Landmark Web.

## Assumptions

- Project addresses, press dates and bases come from `ground_truth_adams_extract.csv`. D16 and X02 use FALLBACK press dates. C18 CEMCO uses the UNVERIFIED BusinessDen date 2025-08-12, as the ground truth allows at month precision; its lead times are therefore approximate to about two weeks.
- Record date fields: Planning Cases `DATE_OPENED`; Building Permits `CaseOpened`; Commerce City layers `APPLIED_DT`; Property Sales `saledt` (deed date; `docdt`, the recording date, is given in the summary where it differs); PrimeGov the meeting date of the agenda the item sits on; Legistar `MatterIntroDate`.
- The Planning Cases layer holds one row per parcel, so one case can appear up to 20 times; counts below are distinct `RECORD_ID`s. The Building Permits layer also duplicates a few multi-address permits.
- Windows: 36 months before press to 12 months after the latest milestone (D16 to 2027-08; D17 to 2025-12; D05 to about 2026-05; X08 to 2025-01; C18, C25, C22 open).
- Lead time is months between the record date and the first press story. Negative means the source fired first. It says nothing about when equipment was bought.
- The four "possible Adams" rows (X02, X03, X09, X23) were run against the county layers and the Parcels layer by address and are reported separately under corrections.
- Property Sales has no address or land-use field, so every address test went through the Parcels layer to get `parcelnb`, then into Sales. Grantee names are LLCs or parents more often than operating companies, so most sale matches are `possible` by rule even when the price and month line up with press.
- Noise samples are September 2025 and March 2026, classified by eye from the record alone (type, address, description); "plainly not industrial" follows the brief's list (housing, roofing, signs, retail, schools, roads) plus liquor licences, residential plats and HVAC or water-heater swaps.

## Source 1: Adams County Planning Cases layer (rank 1)

Coverage: 1 confirmed (D16), 2 possible (D05 park-level, X08 other site), 6 none, of 9. The four "possible Adams" rows: none (three are not Adams parcels; X09 is inside Westminster).

Lead times (months, negative = before press):
- D16 Metro Water Recovery: PRE2021-00059 -20.0 (confirmed, names the substation project), PLN2022-00010 -9.6 (confirmed, names the company and the IGA), TVM2022-00023 -5.1 (possible). An earlier PRE2018-00009 (2018-01-23) for the same substation sits before the window.
- X08 Boise Cascade: PRE2022-00072 -10.2 (possible: right company, its existing 1448 E 68th Ave sawmill, not the Commerce City door shop).
- D05 Craft Beverage Warehouse: PLT2025-00013 +4.8 (possible, park plat amendment). Pivot Denver district and fill cases run 2022-07 to 2023-03 (-27 to -19 months) at park level.
- D17 Vartega: none. Pecos Logistics Park cases (rezone, plats, inert fill) run 2019-03 to 2021-10 and never name a tenant.

Before-press count: 2 projects (D16 confirmed, X08 possible). Nothing for the Commerce City, Aurora or Denver-mailing tenant projects: the layer only covers unincorporated county, and tenant moves into spec buildings (Vartega, Craft Beverage, Wanderment) never reach planning.

Noise sample (distinct cases by DATE_OPENED): September 2025 = 32 cases (74 rows), March 2026 = 45 cases (100 rows). Classified all of them by eye:
- Sep 2025: 19 plainly not industrial (4 liquor renewals, 6 Welby Junction residential PUD/plat items, 3 other residential plats or concepts, 2 hangar variances, chile stand, Kubota dealership, produce retail, truck stop and RV storage); 6 ambiguous (two solar or storage projects, an Xcel substation CUP, a landfill expansion, a QuikTrip redevelopment, a lot-size variance); 7 industrial-relevant (D&K Industrial Park concept, Permagreen I-2 office and production concept, Engineered Paving HQ, Precision Gates and Automation shop, two Huron Industrial Tract plat corrections, Powhaton compressor station amendment). About 59 percent plainly not industrial, 22 percent relevant.
- Mar 2026: 34 plainly not industrial (12 liquor, 9 residential, 4 indoor-recreation parking items, 2 food trucks, grocery, fireworks, campground, car dealership, parking variance, alley vacation, commercial plat); 9 ambiguous (Riverdale Rd rezoning items, airport rezonings, landfill items, Xcel fill); 2 industrial-relevant (Red Bird Farms landscape relief at the 1485 E 61st Ave poultry plant, Quantum 56 Building 6 inert fill). About 76 percent plainly not industrial, 4 percent relevant.
- Filtering to RECORD_TYPE in (PRE, RCU, PRC, PLN, PLT, PUD, TVM) and dropping LIQ, MEL, VSP, PRA cuts the noise by roughly half; keyword flags (industrial, I-1/I-2/I-3, warehouse, manufacturing, processing, plant, fill) do the rest.

Join quality: ADDR_FULL_LINE (free text, inconsistent: "5675 Pecos ST", "5751 N Pecos ST", "0 -", blank), PARCEL_NBR (one row per parcel, good for the assessor join), RECORD_NAME (usually the project or applicant name: "Metro Water Recovery Project", "Boise Cascade - Saw Mill Structure", "Pivot Denver Plat Amendment") and DESCRIPTION (free text, sometimes names the operator). RECORD_NAME is the company field; it can also hold an individual's surname, so output must be screened. LinkToAccela gives the full record for manual lookup.

Access: open ArcGIS Online feature layer, no key, 12,496 rows, `DATE` comparisons and `UPPER(x) LIKE` both work, `returnCountOnly` works. No refusals.

**Verdict: build** (back-tested). Found the one unincorporated county project that went through planning (D16) 20 months before press with the project named, plus an unrelated Boise Cascade expansion; low volume (30 to 50 cases a month), company names in RECORD_NAME, daily refresh. Pull everything from 2024-01-01 with the type and keyword filters above.

## Source 2: Adams County Building Permits layer (rank 2)

Coverage: 2 confirmed (D17, D16), 2 possible (D05, X08), 5 none, of 9. Possible-Adams rows: none.

Lead times:
- D17 Vartega: BDP22-2790 +1.1 (confirmed, "Pecos Logistics Park (Building 2) - Vartega (Suite 203)"), BDP24-0212 +17.3 (confirmed, 30,000 sq ft addition, 11 months before the second line). BDP20-0519 -29.7 is the developer's spec core-and-shell for Building 2 (possible, no tenant).
- D16 Metro Water Recovery: BDP23-0829 +0.3 (confirmed, 42 MVA substation at RWHTF); BDP24-3540 +18.1 (possible, pedestrian bridge).
- D05 Craft Beverage Warehouse: BDP24-3933 +0.4 (possible, 154,476 sq ft TI for Suite 100, Building 3 at Pivot, no name) and BDP24-4212 +1.1 (possible, "tenant improvements for Craft Labeling at Building 3 of Pivot Denver Industrial Park", 5925 Washington St). The name differs from the press name, so it stays possible by rule, but the park and business line up and this is the best address lead the test produced for D05.
- X08 Boise Cascade: BDP23-2173 -1.7 (possible, sawmill cover at the existing 1448 E 68th Ave site; different project from the door shop).
- X04 Wanderment: none. The last permits at 800 E 64th Ave are January 2022 TIs for units 14 and 15; nothing for Unit 8 and nothing in 2023 to 2025.

Before-press count: 1 project (X08, possible, and for a different project). The layer fires at tenant finish, which for these projects came 0.3 to 1.1 months after the first story, then again at expansion. It does not fire before press for leased space.

Noise sample (distinct permits by CaseOpened): September 2025 = 365, March 2026 = 251. Random 50 by eye each month:
- Sep 2025: 50 of 50 plainly not industrial (45 residential re-roofs, furnaces, solar, patio covers, single-family dwellings and barns; 2 commercial signs; 1 industrial re-roof at 6590 Downing St; 2 agricultural barns). 0 relevant.
- Mar 2026: 47 of 50 plainly not industrial (43 residential, 2 cell tower items, 1 sign, 1 commercial electrical repair); 2 relevant (BDP26-0487 twelve pallet-racking bays at 635 E 52nd Ave; BDP26-0549 office package in an existing metal building at Colorado Air and Space Port); 1 borderline (BDP26-0626 new-tenant sign at 5925 Washington St Suite 200, Pivot Building 3).
- Layer-level counts for the same months: BuildingUse Industrial 8 and 2, Commercial 27 and 31, CensusCode "37 - Commercial or Industrial" 31 and 27, "20 - Industrial Buildings" appears on the big TIs. Filtering to CensusCode 37 or 20, BuildingUse Industrial or Commercial, and TypeOfWork in (Tenant Finish, Warehouse, Office, Boiler, Service Change, Service Equipment, Other/New) keeps about 10 percent of records and all five project hits.

Join quality: CombinedAddress (free text, suite numbers rarely present, "5675 PECOS ST" vs "5675 Pecos Street"), Parcel_ (good), Description (free text; carried the tenant name in all five project hits: Vartega twice, Craft Labeling, Metro Water Recovery, Walgreens and Molson Coors at the same park). No applicant, owner or contractor field; TotalSQFT populated for the larger TIs only. Address matching needs `LIKE '%5675%PECOS%'` patterns on CombinedAddress and the name search needs Description.

Access: open ArcGIS Online feature layer, 72,438 rows, same syntax as source 1. No refusals.

**Verdict: build** (back-tested). Confirmed Vartega and Metro Water Recovery and almost certainly Craft Beverage Warehouse (under a variant name) within five weeks of press, and it is the only source that showed the Vartega expansion; noise is 90 percent residential but a four-field filter removes it. Same loader as Denver commercial permits.

## Source 7: Commerce City Active Development Under Review and Under Construction layers (rank 7)

Coverage: 0 of 3 Commerce City projects (C18 CEMCO, X08 Boise Cascade, X11 AMP), 0 of 9. C25 RK also none.

The layers are regenerated nightly from eTRAKiT and keep only active records: 127 under review (applied 2023-06-02 to 2026-10-24) and 429 under construction (329 of them residential new construction, applied 2021-11-03 to 2026-10-15). CEMCO's 2025 permits at 9410 Heinz Way and Boise Cascade's 2023 door-shop work at 11011 E 104th Ave have closed and are gone; the only "9410" left is a house on Telluride Ct. What this means for a back-test: none is possible. The layer cannot be scored against any project whose permits have closed, which is every project in the ground truth, and it will never be scorable until snapshots have accumulated for a year or more. The industrial content that is there now (Aberdeen Truck Terminal amendment, 104th Commerce Park at 11551 E 104th Ave, Recycling Connections CUP, Shamrock Foods rezone via Legistar) shows the fields carry what is needed: PROJECT_NO, PROJECTTYP, SITE_ADDR, APPLIED_DT, DESCRIPTIO (project name on planning rows, "NA" on permit rows), URL to the eTRAKiT record.

Noise: not sampled by month (no history). Of the 556 active rows, 329 residential new construction and 66 final plats are noise on sight; about 40 rows (commercial new construction, commercial addition, development plans, CUPs, use-by permits) are the pool to watch.

Join quality: SITE_ADDR and PIN (Adams County parcel number, joins to the assessor tables), DESCRIPTIO for the project name. Multi-parcel plats repeat one project over up to 30 rows.

Access: open ArcGIS Enterprise map service, no key. No refusals. No archived or closed-records layer exists on the server (checked the Central_Square folder).

**Verdict: build** (back-tested, inconclusive: 0 of 3 because closed records drop). Build only as a weekly snapshot that keeps every row ever seen; it is the only machine-readable feed for Commerce City permits and the fields are right, but nothing can be validated until the snapshot history exists. If a snapshot pipeline is not going to run, park it instead.

## Source 12: Adams County Assessor Property Sales table (rank 12)

Started from Denver's "park" and tested the purchase-type projects first.

Coverage: 0 confirmed, 5 possible (C18, C25, D17, D16, X08), 4 none (D05, X04, X11, C22), of 9. Also C20 Amprius: none (lease; the Brighton building sold to its current owner in 2018). Possible-Adams rows: X09's landlord sale (2020-10-13, $9.4M) is outside the window; the other three are not Adams parcels.

Lead times:
- C18 CEMCO: reception 2025000044328, saledt 2025-07-31 (recorded 2025-08-01), -0.4 months. 9410 Heinz Owner LLC to PMDEN LLC c/o JFE Shoji America Holdings, $29,250,000, which is the $29.3M in the press. Possible only because the grantee is a holding entity, not CEMCO.
- C25 RK Industries: reception 2025000035204, saledt 2025-06-12, -2.6 months. HD Builder Solutions Group to RK 3301 Lewiston EAT LLC and a co-owner, $23,600,000, at 3301 Lewiston St, Aurora (Adams County parcel). Possible: the LLC name carries RK and the address but no document names RK Industries. This is the earliest dated record for RK in any source tested here, 2.3 months before the EDC approval and 4.5 months before the OEDIT announcement.
- D17 Vartega: 2021-12-10, -8.2, investor purchase of the whole park ($103.8M); not a tenant signal.
- D16 Metro Water Recovery: 2021-06-22, -21.0, a $0 renaming deed from Metro Wastewater Reclamation District across 20 parcels; not a project signal. Two small adjacent-parcel purchases by MWR in 2024 (+14.0, +18.2).
- X08 Boise Cascade: 2024-12-05, +14.8, investor sale of the leased building ($27.2M); not a tenant signal.
- C22 Philip Morris: none. The 148-acre site is in Adams County (parcel 0181917301001, 25301 E 48th Ave, owner Kairus Inc, Stamford CT), but the table holds no sale for that parcel or any Sun Empire parcel in 2024, and no Adams sale between $55M and $70M in July to December 2024 is the $61.5M purchase. The new plat parcel may carry the deed under an old parcel number, or the conveyance was recorded without a doc fee; either way the signal is missing here.

Before-press count: 2 meaningful (C18, C25), both purchases by the operator's own entity; 2 more that are landlord or administrative deeds.

Noise sample (saledt): September 2025 = 1,423 rows (60 at or above $1M, 9 at or above $5M); March 2026 = 1,702 rows (204 at or above $1M, 154 at or above $5M, most of them one multi-parcel $11.2M land deal and a $10.2M retail sale). Random 50 by eye each month: 50 of 50 and 50 of 50 plainly not industrial (individual-to-individual house sales, builder lot sales, trusts, quit claims, death certificates, one senior-housing sale to the housing authority, one metro-district transfer). 0 industrial in either sample. The industrial rows exist (they appear in the price-filtered views) but are under 1 percent of the table.

Join quality: no address, no land use, no building size in the table itself. The join is parcelnb to the Parcels layer (site address, owner, legal description) and then, for use, to Property Improvements. Grantee is the matching field for the two meaningful hits and is a holding LLC in both cases; resolving it needs the SOS registration or the Landmark Web deed. recptno gives the Landmark reception number for manual lookup. Future-dated typos exist (saledt up to 2029 per discovery).

Access: open ArcGIS Online table, 769,559 rows, `saledt` DATE comparisons and `salep` numeric filters work. No refusals.

**Verdict: build** (back-tested), as a filtered feed, not a bulk pull: join to Parcels, keep salep at or above $2M on parcels whose land use or zoning is industrial or commercial, grantee an entity, then resolve the grantee. It is the only source that fired before press for CEMCO and RK Industries, the two owner-occupier purchases in the set, and it missed the lease projects and the PMI deed entirely. Denver's park stands for lease-driven projects; the upgrade here is for the purchase cases.

## Source 14: Adams County PrimeGov meeting portal (rank 14)

Method: JSON index of archived meetings for 2022 to 2026 (495 BOCC public hearings, study sessions and Planning Commission meetings; 2022 only from October, as discovery noted, with earlier 2022 meetings present in the index anyway), then the HTML Agenda of each (about 46 MB in all), keyword-searched for every project name, address and the words incentive, agreement, codename-style "Project X". Packets were not read (one was opened for the Kairus item and holds only the agenda text; attachments are PDFs).

Coverage: 2 confirmed (D16, C25), 3 possible (C22, D17, D05), 4 none (X04, C18, X08, X11), of 9. Also C20 Amprius: confirmed (tested at the brief's request). Possible-Adams rows: none.

Lead times:
- C22 Philip Morris: 2024-07-09 incentive agreement with Kairus Inc, -0.2 months (possible). The county incentive the ground truth attributes to Adams County is this one; Kairus Inc holds the 148-acre parcel at 25301 E 48th Ave under a Stamford CT mailing address. The agreement PDF was not read, so the PMI tie stays unproven in this test.
- D16 Metro Water Recovery: 2022-04-12 amendment to a lease for construction purposes, -11.3 (possible, names the company only); 2023-04-25 land use hearing PLN2022-00010 Metro Water Recovery, +1.1 (confirmed, the substation IGA case).
- C25 RK Industries: 2026-10-06 incentive agreement with RK Industries, LLC, +13.2 (confirmed, but after the plant opened). An unnamed executive session on incentive agreement terms on 2025-07-23 is -1.2 months and cannot be tied.
- D17 Vartega: 2022-09-27 final acceptance of Pecos Logistics Park improvements, +1.4 (possible, park-level).
- D05 Craft Beverage Warehouse: 2022-10-25 hearing on PLN2022-00012 Pivot Denver, -23.5 (possible, park-level).
- C20 Amprius: 2023-03-14 incentive agreement, +0.3 (confirmed; amendments 2024-03-12 and 2024-09-10).
- Not in my set but seen: Prost Brewing incentive agreement 2022-06-28 (same day as its press date; amendment 2024-01-30).

Before-press count: 1 meaningful (C22 via Kairus, possible), plus D16 and D05 items that name the company or park but not the project. Incentive agreements land on the hearing agenda within about a week of the press release in three of four cases (Amprius +8 days, Prost 0 days, Kairus -7 days) and 13 months late in one (RK). Study sessions discuss them earlier only as unnamed executive sessions.

Other incentive agreements seen 2022 to 2026, none in the ground truth: Performance Food Group (2022-07-12), Ardent Mills LLC (2024-08-13; Commerce City passed its own on 2024-06-24), NTT Global Data Centers Americas business personal property tax incentive (2025-11-18). These are candidates for the ground truth or the target list.

Noise: an agenda holds 20 to 60 items; incentive and land use items are a handful a month. A keyword watcher (incentive, agreement, PRC/RCU/PLN case numbers, lease, final acceptance, rezone, Industrial) keeps the volume to a few items a week. Study sessions add staff presentations but the economic development items there were unnamed executive sessions.

Join quality: company name in the item title (incentive agreements, IGAs, leases) and planning case numbers in land use hearing titles, which join to the Planning Cases layer. No address field; the HTML agenda lists attachment titles but not their text.

Access: unauthenticated JSON API and HTML pages; the portal's own text search is a form post and was not used. robots.txt returns 406. No refusals at one request a second.

**Verdict: build** (back-tested). It is the county's incentive record (Amprius, Prost, Kairus for PMI, RK, plus PFG, Ardent Mills and NTT that the ground truth lacks) and it names companies, which the permit layers often do not; lead over press is about zero for incentives, so its value is as a confirmation and a source of names, with land use hearings 1 to 11 months after the planning case opens.

## Source 15: Commerce City Legistar (rank 15)

Coverage: 0 confirmed, 1 possible (D16), 2 none of the 3 Commerce City projects (C18, X08, X11), 8 none elsewhere, of 9.

Lead times: D16 Metro Water Recovery, Pres 25-118 / AH24-0001 height exception to 110 ft at 6450 York St, 2025-01-31, +22.4 (possible: existing plant, does not name the substation). Nothing for CEMCO, Boise Cascade or AMP by name, address or keyword (steel, door, robot, sortation, recycl). Named incentive items since 2022: Ardent Mills (2024-06-24, amended 2026-06-17), two lodging tax rebates, a 2025 policy revision. Seven executive sessions on "incentives for a potential economic development project" (2022-05-19, 2022-11-17, 2023-04-18, 2023-05-03 for three prospects, 2023-07-10, 2024-02-28, 2024-06-24) name nothing; 23-157 on 2023-07-10 is two months before the Boise Cascade story and may or may not be it.

Before-press count: 0.

Noise: the Matters API returned 66 matters with "industrial" in the title since 2022, mostly rezonings, CUPs, variances and plats, each appearing twice (Planning Commission presentation and Council ordinance); 16 with "incentive". Industrial rezone and CUP items name applicants (Shamrock Foods, Waste Connections, Rocky Mountain Recycling, Nebraska Ash, Doka USA, JFW Trucking), so the land use side has signal even though the incentive side missed all three projects. Applicant fields often hold an individual's name on behalf of a company, so output must be screened.

Join quality: company and case number in MatterTitle only; addresses appear in the title text for zoning items; no structured address or parcel. Case numbers (Z, CUP, PUDA, D, AV) join to eTRAKiT and the active layers.

Access: Legistar Web API, no key, OData substringof filter works (case-insensitive). No refusals.

**Verdict: park** (back-tested). None of the three Commerce City projects appeared; incentive agreements are rare (one manufacturer in four years) and the land use items duplicate what the active layers and eTRAKiT carry with names. Revisit if the Commerce City snapshot feed is built, as the cheap source of applicant names for its rezones and CUPs.

## Source 17: Adams County Current Land Use Cases page (rank 17)

Sample only. One GET returned 100 case numbers (EXG, PLN, PLT, PRA, PRC, PUD, RCU, VSP, 2024 to 2026) and 175 PDF links. None of the nine projects or their addresses appear. Twelve case numbers drawn at random were all present in the Planning Cases layer with the same opening dates, so the page adds nothing to coverage. What it adds per case: submittal and resubmittal dates, the application and referral PDFs (narratives with the operations description) and the case manager's name, which is a personal name and must be dropped. Industrial items on the page today (PRC2025-00004 minor subdivision and rezone to I-1, 1970 Imboden Rd rezone to I-1, Prime Air drone facility, a storage-container CUP in I-2, two slaughterhouse CUPs) are all in the layer too.

Coverage: 0 of 9 (none had a hearing-level case in the current list). Noise: not sampled; hearing-level only.

**Verdict: park** (back-tested). Use it to fetch the narrative PDF for a case the Planning Cases layer has already flagged; no separate pull.

## Sources not tested

- 8 Commerce City eTRAKiT: browser-only portal (ASP.NET postbacks), terms check only, below.
- 19 Adams County Accela Citizen Access: browser-only portal, terms check only, below.
- 22 Landmark Web: browser-only portal, terms check only, below.
- 16 Tier II locations: annual, lagging (filed by March for the prior year), context data for the facility universe, not a signal.
- 23 Eye On Adams email hub: email subscription on the same two layers; sign-up is a form, and the REST layers are the system source.
- 29 Parcels layer: support data (used here only as the parcel-number and owner lookup behind source 12; it worked for every address tested and settled county membership for X02, X03, X09, X23).
- 30 Assessor quick search: browser-only, Cloudflare on curl; replaced by the open tables.
- 35 Property Improvements: lagging post-construction inventory; context for sizing.
- 36 SACWSD agendas: PDF and DOCX board packets with no developer names in the sampled month; not a dated signal source.
- 44 Metro Water Recovery pretreatment: no public permit list; needs a CORA request.
- 45 AC-REP news: press feed, and the news page returned 403 at discovery.
- 46 Commerce City and Westminster ED pages: press feeds, blocked to automated access at discovery.
- 47 South Adams County fire permits: applicant portal with no public search; needs a CORA request.
- 49 Development parcels: static boundary context.
- 52 Licence layers: undated; county LIQ and MEL cases are already in source 1.
- 57 Code enforcement: not a demand signal.

## Terms findings for the browser-only portals

- 8 Commerce City eTRAKiT (`comc.csqrcloud.com/community-etrakit/`): robots.txt returns HTTP 500 (none served). The landing page carries CentralSquare "Terms and Conditions of Use": use only for purposes authorised by Commerce City; no uploading of unlawful content; the city may monitor content; use is at your own risk with no warranty of accuracy or availability; the city may terminate access for violations. No clause on commercial use or automated access. The direct record URL (`project.aspx?activityno=...`) answers a plain GET, but the search pages are postbacks. Treat as a manual lookup source behind the active layers' URL field.
- 19 Adams County Accela Citizen Access (`aca-prod.accela.com/ADAMSCO/Default.aspx`): robots.txt 404 on the host. The landing page shows no terms of use; its footer links to the county's "Privacy and Policy Disclaimers" page, which on the current county site reads as a liability disclaimer: the county does not warrant the accuracy, completeness or timeliness of website information, official printed documents take precedence, and the county is not liable for damages from use or reliance; it also contains a disclaimer of endorsement for commercial products. No restriction on commercial use; nothing on scraping. The per-module "disclaimer" pages are for applicants (registration). Manual lookup only, per the Denver decision.
- 22 Landmark Web (`recording.adamscountyco.gov/landmarkweb/`): the new host failed the TLS handshake from the cloud shell (same as discovery) and the old host (`recording.adcogov.org/LandmarkWeb/`) answers with a Cloudflare challenge (403), so no terms or robots.txt could be read. The county service page (per discovery) states uncertified copies are free to download or print. Manual lookup by reception number only; do not automate.
- County site robots.txt (`adamscountyco.gov`): disallows `/wp-admin/` only, crawl-delay 10.

## Corrections the test suggests to the ground truth (not applied)

- X02 Cerebral Brewing, X03 Curated Barrel Project, X23 Stay Tuned Brewing: none of 9990 E Colfax Ave, 5525 W 56th Ave or 5127 W 64th Ave is an Adams County parcel. They belong to Arapahoe (X02) and Jefferson (X03, X23), matching the SBA records cited in the extract. Move them out of Adams.
- X09 Creation Technologies: 1401 W 122nd Ave is Adams County parcel 0157333006021 (owner ICP-Flywheel Park Centre LLC) inside the City of Westminster. County is Adams; permits come from Westminster.
- C22 Philip Morris ZYN: the 148-acre site is Adams County parcel 0181917301001, 25301 E 48th Ave, Sun Empire Subdivision Filing 2, owner Kairus Inc with a Stamford CT mailing address, and Adams County approved an incentive agreement with Kairus Inc on 2024-07-09. County should be Adams (confirmed), with Kairus Inc recorded as the site entity (unverified as a PMI affiliate from these records alone).
- C18 CEMCO: the purchase is dated 2025-07-31 (recorded 2025-08-01), $29,250,000, grantee PMDEN LLC c/o JFE Shoji America Holdings. The ground truth's "$29.3M" and "August 2025" stand; the deed date is a usable milestone.
- D05 Craft Beverage Warehouse: the Pivot Denver permits point to 5925 Washington St, Building 3 (Suite 100 TI 2024-10-21 and "Craft Labeling" TI 2024-11-13), Denver CO 80216 mailing in unincorporated Adams County. The park parcel is 0182510401037 (525 E 58th Ave, owner Denver Mart Industrial Partners JV LLLP). Worth confirming the name link before adopting the address.
- D17 Vartega: parcel 0182509313005 (owner Pecos I Holding Acquisition LLC); tenant finish for Suite 203 opened 2022-09-19, five months before the reported lease date of 2023-02-21, so the lease was probably signed in mid 2022.
- C25 RK Industries: the 3301 Lewiston St purchase (2025-06-12, $23.6M, RK 3301 Lewiston EAT LLC) and the county incentive agreement (2026-10-06) are new dated milestones.
- C20 Amprius: no Adams parcel carries the address 18875 E Bromley Ln. The 1.28M sq ft Brighton warehouse is probably the former Kmart distribution center at 4353 E Bromley Ln (parcel 0156900022003, Starboard Platform Brighton JV LLC). The county incentive agreement is on the 2023-03-14 hearing agenda as the extract says, with amendments 2024-03-12 and 2024-09-10 (the second amendment is a new milestone before the 2025-06-24 cancellation).
- Candidates missing from the ground truth, from PrimeGov: Performance Food Group incentive agreement (2022-07-12), Ardent Mills incentive agreements (Commerce City 2024-06-24, Adams County 2024-08-13; height exception for a 141 ft building 2024-02-05 in Legistar), NTT Global Data Centers business personal property tax incentive (2025-11-18).

## What was not finished

- PrimeGov attachments (resolutions and incentive agreements) were not opened, so the Kairus Inc to PMI link and the RK agreement terms are unread; the match classes reflect agenda titles only.
- Property Sales was not joined to land use or zoning for the noise sample; the "0 industrial of 50" figures come from grantor and grantee names and prices alone.
- The Commerce City layers could not be back-tested at all; the first snapshot has not been taken.
- The Commerce City eTRAKiT record pages for CEMCO and Boise Cascade were not opened (browser-only rule), so their permit dates in Commerce City remain unknown to this test.
- Legistar attachments (PDF) were not read; the executive sessions could not be resolved to prospects.
