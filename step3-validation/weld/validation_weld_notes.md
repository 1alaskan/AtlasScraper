# Weld County, step 2: validation of the local sources (back-test)

Run 2026-11-05 to 2026-11-06. Companion file: `validation_weld_matches.csv` (129 rows: one row per project per source tested, supplementary projects after the ground-truth rows, `group` column says which agent produced the row). The per-group write-ups with endpoints, noise samples and license text are `notes_county.md`, `notes_tri_towns.md` and `notes_cities.md`; this file is the summary and the verdict list.

## Bottom line

Weld County has 6 known projects in the ground truth (5 confirmed Weld, X27 Microvast best guess), so the method was a back-test, as in Denver. 56 county sources were found in step 1; 18 were tested; 9 earned a build verdict (3 back-tested, 5 inherited and spot-checked, 1 spot-checked only as a resolver); 7 parked; 2 dropped; 1 (Windsor permit reports) set aside as a manual download; the rest not tested.

| Rank | Source | In scope | Confirmed | Possible | Before press (confirmed) | Verdict | Basis |
|---|---|---|---|---|---|---|---|
| 1 | Weld BOCC Laserfiche: Tax Incentive Agreements (C.R.S. 30-11-123) | 6 | 5 | 1 (Agilent, expansion rule) | 4 of 5 (Microvast +0.3 months; the other four -0.5 to -18.3) | build | back-tested |
| 4 | Weld Assessor Property Sales points | 6 | 2 | 3 | 2 of 2 (TFP -29.3, Microvast -0.2); the 3 possible also before press | build | back-tested |
| 3 | Frederick Accela Building Permits layer (ArcGIS mirror) | 2 | 1 (Agilent, 4 permits naming Project Endeavor) | 1 | 0 of 1 (first named permit +1.9 months; 4 unnamed permits at the parcel -15.2 to -1.1) | build | back-tested |
| 2 | Weld Planning Cases for Development Activity Map | 6 | 0 | 0 | undated | build | inherited + spot-checked |
| 7 | Weld Site Plan Review recorded cases | 6 | 0 | 0 | none in scope | build | inherited + spot-checked |
| 5 | Greeley TRAKiT Projects layer | 1 | 0 | 0 | active only, 2022 case rolled off | build | inherited + spot-checked |
| 6 | Frederick Development Applications layer plus What's Developing page | 2 | 0 | 1 (Agilent Endeavor site plan, undated) | undated | build | inherited + spot-checked |
| 8 | Fort Lupton Planning_AGOL layer plus Current Development Projects page | 1 | 0 | 0 | layer starts 2023-10 | build | inherited + spot-checked |
| 12 | Weld Assessor Ownership table, personal property accounts | 6 | 2 | 3 | undated (no creation date) | build as the resolver, not a signal | spot-checked only |
| 9 | Greeley CivicClerk OData API (plain-text packets) | 1 | 0 | 1 (C34, $7.4M tenant finish permit at 2400 29th St in a July 2023 construction report, -6.4 months) | 0 | park | back-tested |
| 10 | Firestone Accepted Development Review Applications PDF | 0 | | | | park | spot-checked only |
| 14 | Evans Current Development Projects table | 0 | | | | park | spot-checked only |
| 15 | Weld Access Permit points | 6 | 0 | 0 | dates end 2017 | park | spot-checked only |
| 18 | Windsor Development Activity StoryMap | 1 | 0 | 0 | undated | park | spot-checked only |
| 20 | Longmont Active Developments, Weld slice | 0 | | | | park | inherited + spot-checked |
| 26 | Frederick CivicClerk OData API | 2 | 0 | 0 | | park | spot-checked only |
| 11 | Windsor monthly Building Permit Reports | 1 | not tested | | | manual download (Matthew's decision 2026-11-06) | not tested |
| 28 | Firestone Development Projects map layer | 0 | | | | drop | spot-checked only |
| 19 | Johnstown Current Projects page | 0 | | | | drop (page); portal not tested | spot-checked only |

Lead time here means months before or after the first press story. It says nothing about months before a compressor purchase.

The county incentive agreement is the single best early source found in any Colorado county so far. The commissioners approve a personal property tax rebate for manufacturing equipment before the equipment goes into service, the resolution names the company, and the agreement text names the facility street address. 18 agreements since 2022, every one of the six known projects among them, median lead about 4 months before press and up to 18 (Sphere Renewables) and 13 (TFP Nutrition). The twelve agreements that are not in the ground truth (Gotham Greens, Colorado Stud, Norfolk Iron and Metal, Airxcel/Aqua-Hot, Owens-Brockway, TruLog, Charm Industrial, Scotts/Hyponex, EcoMod, US Engineering Metalworks, Motherload Co Packing, BAE Systems) are the first Weld lead list in their own right.

Assessor sales is the second finding: unlike Denver's property sales layer (parked), Weld's carries grantor, grantee, occupancy code, building size and acreage, so an industrial filter is possible and 5 of 6 projects have an in-window sale before press. Two are confirmed by company name (TFP Nutrition bought from J.D. Heiskell 2023-06-09, 29 months before press; Microvast bought 31815 Great Western Dr 2023-07-05 and sold it 2024-08-29, a dated exit seven months before the 10-K). Three are possible (a related entity or a landlord bought the site).

## Assumptions and definitions

1. Earliest press date, match classes, record date, lead time and window are the Denver rules, repeated in `validation_brief_shared.md`. C34 and C36 use FALLBACK or EDO-adjacent press dates, so their leads are weaker than they look.
2. Four of the six projects were announced in 2022 or 2023, so their earliest records predate the 2024-01-01 scrape window. The back-test counted them; the scrape step pulls 2024-01-01 onward and carries in active 2023 records.
3. X27 Microvast is reported separately in the group notes. The incentive agreement and the assessor sale both place the facility at 31815 Great Western Drive, Windsor, parcel 080726103003, Weld County. The ground truth still says best guess; the correction is listed below and not applied.
4. A browser-style user agent on the Weld Accela portal was refused by the session's permission classifier; the plain user agent worked for the one sample fetch. No crawl of any portal was run.

## Terms

- Weld County AGOL items (Planning Cases view, Site Plan Review, Sales Point, Ownership, Weld Accela): all shared `access: public`, each with the same `licenseInfo`: "This product has been developed solely for internal use only by Weld County. The GIS database, applications, and data in the product is subject to constant change and the accuracy and completeness cannot be and is not guaranteed. ... UNDER NO CIRCUMSTANCE SHALL ANY PART THE PRODUCT BE USED FOR FINAL DESIGN PURPOSES. WELD COUNTY MAKES NO WARRANTIES OR GUARANTEES ..." `accessInformation`: "Weld County Government". The text reads as a liability disclaimer rather than a use restriction and the items feed the county's public maps, but it is not decided here. The scrape step pulls them for internal prospecting use; any resale or redistribution should be confirmed with Weld County GIS first. Decision for Matthew.
- Laserfiche WebLink (minutes.weld.gov): no robots.txt (404), no terms page; public commissioner records under CORA.
- Frederick ArcGIS Enterprise: open data, copy and adapt freely.
- Greeley and Fort Lupton layers: no restriction found.
- Weld Accela Citizen Access and the new Accela Public Portal, Greeley eTRAKiT, Johnstown eTRAKiT: no robots.txt, liability-only disclaimers, login or postback search. Manual lookup sources, as Denver decided for its Accela.
- Windsor: windsorco.gov returns 403 to scripts even for robots.txt; the CivicPlus mirror host serving the PDFs publishes `Disallow: /`. Not pulled; manual download.

## Corrections the tests suggest to the ground truth (not applied)

- X27 Microvast: county confirmed Weld; address 31815 Great Western Drive, Windsor; exit sale 2024-08-29 ($10.2M) is a dated cancellation milestone.
- C35 Hirsh Precision: address 4300 Godding Hollow Pkwy, Frederick, CO 80504 (and 4356 Godding Hollow on the second parcel); incentive confirmed (agreement 20220470, 2022-02-07).
- X26 Agilent: address 7051 Eagle Blvd, Frederick, CO 80530 (parcel 131326401001; construction trailer on 7400 Eagle Blvd); town project name "Project Endeavor"; incentive confirmed (agreement 20223599, 2022-12-28); adjacent 10 ac at 4951 Carbide St bought 2021-10-25.
- C34 Colorado Premium: the site sale is 2021-12-22 ($8M) to a related entity, not 2022; K2D Inc holds the personal property accounts; Greeley permit BCX2307-0129 (2023-07-25, $7.4M tenant finish at 2400 29th St) suggests the plant was a tenant finish of an existing building rather than new construction; the county agreement of 2023-07-05 is an earlier dated milestone than the FALLBACK press date.
- C36 Sphere Renewables: parcel bought 2022-10-04 by Harbour Asset Management LLC; agreement 2022-12-05 is the earliest dated company milestone.
- X28 TFP Nutrition: land purchase 2023-06-09 from JD Heiskell Holdings LLC ($4.1M), which dates the WQCD "J.D. Heiskell" permittee note.

## Not finished

- Windsor monthly permit reports: not pulled (host and mirror refuse scripts); Microvast, Vestas, Front Range Energy, Owens-Brockway and Gotham Greens are untested on permits.
- Firestone PDF archive unreachable (rolling document id); only the current report was parsed.
- Greeley CivicClerk: 8 of 20 packets streamed empty; other months' construction reports not located.
- Laserfiche: phase caps and dollar amounts in the agreements not parsed; Small Business Incentive Program applications listed but not back-tested.
- Hirsh Precision could not be tied in the Frederick permit layer during the test (no address then; the address found in the agreement OCR can be used in the scrape step).
