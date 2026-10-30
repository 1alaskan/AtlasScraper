# Step 2 (validation), Adams County: back-test of 18 local sources against the ground truth

Run 2026-10-30, three agents in parallel by jurisdiction group (county and Commerce City; Thornton, Brighton, Westminster, Federal Heights; Aurora). Companion files in this folder: `validation_adams_matches.csv` (178 rows, one per project per source, with a `group` column), the three group notes (`notes_county_commercecity.md`, `notes_north_cities.md`, `notes_aurora.md`), the three group match files, the shared brief (`validation_brief_shared.md`) and the ground-truth extract used (`ground_truth_adams_extract.csv`).

Method: back-test, because Adams County has 17 known projects in the Step 3 overlay (five or more). The four overflow projects whose county is "Adams or a neighbour" (X02, X03, X09, X23) were tested and reported separately; the test itself settled three of them (see corrections).

## Bottom line

Of 57 sources found in discovery, 18 were tested, 10 earned a build verdict, all on the basis `back-tested`. Nine are machine-readable ArcGIS REST layers or JSON APIs. Seven more are parked and the rest were not tested (press, snapshots without dates, context data, or browser-only portals, which got a terms check only).

| Rank | Source | Tested against | Confirmed | Possible | Confirmed before press | Verdict |
|---|---|---|---|---|---|---|
| 1 | Adams County Planning Cases layer (Accela via ArcGIS Online) | 9 | 1 | 2 | 1 of 1 (D16 at -20.0 months) | build |
| 2 | Adams County Building Permits layer (Accela via ArcGIS Online) | 9 | 2 | 2 | 0 of 2 (+0.3 and +1.1) | build |
| 3 | Thornton Building Permits 2017 to present (CityView via ArcGIS) | 7 | 2 | 2 | 2 of 2 (Izzio -10.0, Kiosk -2.2); possible Santa Monica Seafood -14.9, Solid Power -8.5 | build |
| 4 | Aurora Active Development Applications (AMANDA via ArcGIS) | 3 | 1 | 2 | 1 of 1 (PMI Project Waterfall site plan -1.7) | build |
| 5 | Thornton Development Projects layer (CityView via ArcGIS) | 7 | 3 | 1 | 2 of 3 (Izzio -10.6, Santa Monica Seafood -3.5) | build |
| 6 | Aurora Building Permits 2021 to present (AMANDA via ArcGIS) | 3 | 3 | 0 | 0 of 3 (+0.9 to +2.5; Pretred's permit beat the lease announcement by 29 days) | build |
| 7 | Commerce City active development layers (eTRAKiT via ArcGIS) | 9 | 0 | 0 | none (closed records drop out, so untestable) | build as a weekly snapshot only |
| 12 | Adams County Assessor Property Sales (ArcGIS) | 10 | 0 | 5 | none confirmed; 4 possible before press (CEMCO purchase -0.4, RK Lewiston -2.6) | build, filtered (upgrade from Denver's park) |
| 14 | Adams County PrimeGov meeting portal (JSON API) | 10 | 3 | 3 | 0 of 3 confirmed; possible PMI via a Kairus Inc agreement at -0.2 | build |
| 18 | Brighton Legistar (Web API) | 2 | 1 | 0 | 1 of 1 (Amprius incentive resolution -0.4) | build, keyword watcher |
| 9 | Brighton Planning Development Status layer | 7 | 0 | 1 | none (+14.3) | park |
| 10 | Brighton Commercial Permits monthly PDF | 2 | 0 | 0 | not testable (no archive) | park |
| 11 | Westminster Proposed and Current Developments layer | 7 | 0 | 0 | none | park |
| 13 | Aurora Businesses licence layer | 3 | 1 | 1 | 0 | park (forward test only) |
| 15 | Commerce City Legistar | 9 | 0 | 1 | none | park |
| 17 | Adams County Current Land Use Cases page | 9 | 0 | 0 | duplicates the layer | park |
| 37 | Aurora council agendas | sampled | | | archive unreachable | park (not back-tested) |
| 20 | Thornton Certificates of Occupancy layer | 4 | 0 | 0 | residential only | drop |
| 25 | Brighton County Report monthly PDF | 2 | 0 | 0 | not testable | drop |
| 34 | Federal Heights permit PDFs | 1 month | | | no industrial content | drop |
| 56 | Aurora permit statistics PDFs | 1 month | | | aggregate only | drop |

Lead time throughout is months before or after the earliest press date. It says nothing about months before a compressor purchase.

What the test showed, in three lines:

- The Thornton layers are the best local sources in the county: they name the tenant in the permit description, and fired 2 to 15 months before press on four of four Thornton projects.
- The Adams County layers carry the unincorporated sites (Vartega, Metro Water Recovery, the Pivot Denver park) and the Planning Cases layer named the Metro Water substation 20 months before any post. Both fire at tenant finish or site plan, which is around press for a new plant and ahead of it for an expansion at an existing site.
- Aurora's layers settle the Adams side of Aurora cleanly (County field on the development layer; a Colfax-line Y cut on the permit layer) and carried PMI's site plan 1.7 months before the announcement, with 337 permit rows after it.

## Assumptions and definitions

1. Press dates come from `ground_truth_adams_extract.csv`: the earliest rumor, press mention or announcement not labelled UNVERIFIED. FALLBACK rows (D16 company post, C24 Mile High CRE site-search note, C18 release) give weaker leads; the group notes say where that matters. X11 AMP has no usable press date.
2. Record date is the record's own date field, named in the `date_field` column of the matches file (InDate, DateEntered, CreationDate, agenda date, sale date, and so on).
3. Lead time = (record date minus press date) in days / 30.44. Negative means the source fired first.
4. Window: 36 months before press to 12 months after the latest milestone.
5. Match classes as in Denver: confirmed needs name plus site address or a document naming both; possible for address-only, variant-name or timing-only ties. A wrong match is worse than a miss.
6. Browser-only portals (Commerce City eTRAKiT, Adams County Accela Citizen Access, Landmark Web, Thornton CityView Portal, Westminster eTRAKiT, Brighton OpenGov, Northglenn CommunityCore, Aurora Citizen Portal) were not browsed; robots.txt and terms were read and are quoted in the group notes. Landmark Web could not be reached at all (TLS failure on the new host, Cloudflare on the old).
7. No agent opened PrimeGov attachments or eTRAKiT records. No forms, accounts, requests or contact.
8. Noise samples were September 2025 and March 2026, classified from the record alone (50 rows per source).

## Coverage by project (17 Adams projects)

| Project | Found by | Earliest local record versus press |
|---|---|---|
| D05 Craft Beverage Warehouse | county permits (possible, variant name "Craft Labeling" at 5925 Washington St), Planning Cases (park plat), PrimeGov | +1.1 months |
| D16 Metro Water Recovery substation | Planning Cases, county permits, PrimeGov, Property Sales, Commerce City Legistar | -20.0 (Planning Cases) |
| D17 Vartega | county permits (confirmed), Property Sales, PrimeGov | +1.1 (TI permit), +17.3 (30k sq ft expansion) |
| C18 CEMCO | Property Sales (possible, $29.25M deed to an LLC c/o the parent) | -0.4 |
| C19 Prost Brewing | PrimeGov only (incentive agreement); Northglenn has no layer | not dated before press |
| C20 Amprius | Brighton Legistar (confirmed), PrimeGov, Brighton status layer | -0.4 (Legistar) |
| C21 VSK Energy | none | no record anywhere; the project never filed |
| C22 Philip Morris | Aurora development layer (confirmed), Aurora permits (337 rows), PrimeGov (Kairus Inc agreement), licence layer | -1.7 (site plan) |
| C23 Solid Power | Thornton permits and projects (possible; unnamed process-electrical records at 14902 Grant St Unit 120) | -8.5 |
| C24 Pretred | Aurora permits (confirmed $4.5M tenant finish), development layer, licence layer | +0.9 against the fallback press date; 29 days before the lease announcement |
| C25 RK Industries | Aurora permits (confirmed, 3301 N Lewiston St), Property Sales, PrimeGov, development layer | -2.6 (deed, possible); permits from +0.9 |
| X04 Wanderment Brewing | none | small tenant, no permit found |
| X05 Santa Monica Seafood | Thornton projects (confirmed), Thornton permits (possible) | -3.5 to -14.9 |
| X08 Boise Cascade door shop | county layers (a different Boise sawmill site, possible), Property Sales | -10.2 (other site) |
| X11 AMP | none | no address and no press date to test |
| X15 Izzio Bakery | Thornton permits and projects (confirmed) | -10.0 to -10.6 |
| X16 Kiosk Information Systems | Thornton permits and projects (confirmed) | -2.2 |

Twelve of 17 have at least one local record; four of those are before press on a confirmed match and four more on a possible one. The five with nothing (VSK, Wanderment, AMP, and in practice Prost and Craft Beverage before press) are a cancelled project, two small tenants and two whose jurisdiction has no machine-readable source.

## Noise

Counts per month and share plainly non-industrial, from the group notes: Adams County Planning Cases 30 to 50 cases a month, 59 to 76 percent non-industrial (liquor, housing); Adams County Building Permits 94 to 100 percent non-industrial raw, about 10 percent kept by a CensusCode, BuildingUse and TypeOfWork filter; Thornton permits about 95 percent raw, 8 to 9 percent after a Type filter; Aurora permits on the Adams side 599 and 508 rows in the two sample months, 86 to 92 percent non-industrial; Aurora development applications 2 to 6 Adams rows a month, 43 of 64 since 2025 non-industrial; Property Sales 0 of 50 industrial without the parcel join.

## Join quality

Thornton's permit description names the tenant (BUS_NAME was empty on every project row). Aurora's permit description names the project or tenant and the development layer carries square footage, use and a County field. Adams County's layers are address and description only, with no applicant name; the Planning Cases layer does carry the project name. Property Sales carries grantor and grantee, which are mostly LLCs; it needs the Parcels join for land use. PrimeGov items name the company in the agreement title.

## Sources not tested, with the reason

Press: Brighton Standard Blade and sister papers (21), Sentinel Colorado (31), AC-REP news (45), Brighton EDC newsletters (41), Commerce City ED pages (46, blocked). Snapshots or context without dated history: Tier II locations (16), parcels (29), property improvements (35), Westminster and Thornton support layers (42, 48), development parcels (49), licence layers (52), Northglenn storefront list (53), Brighton EDC properties (27), code enforcement (57). Agendas without an API or with nothing industrial: SACWSD (36), Westminster Agenda Center (26), Thornton and Northglenn CivicClerk (24, 43), United Power (51). Needs a login or a records request: Eye On Adams email hub (23), fire district permits (47, 50), Metro Water Recovery pretreatment (44), assessor quick search (30, Cloudflare). Browser-only portals (8, 19, 22, 28, 32, 33, 38, 39): terms check only. Bennett and Lochbuie (54, 55): blocked and negligible.

## Terms findings for the browser-only portals (summary; detail in the group notes)

- Commerce City eTRAKiT: robots.txt restricts crawlers; records open by direct URL but were not opened. Manual lookup source.
- Adams County Accela Citizen Access: no robots.txt found; ASP.NET postback search; Accela's own terms (read for Denver) are the governing text. Manual lookup source, same as Denver.
- Landmark Web (recorded documents): not reachable (TLS failure on the new host, Cloudflare on the old). Terms not read.
- Thornton CityView Portal, Brighton OpenGov, Northglenn CommunityCore: robots.txt disallow all. Manual lookup only. The Thornton layers carry the same data through ArcGIS, which is the route used.
- Westminster eTRAKiT: Cloudflare plus "ai-train=no" content signals. Not touched.
- Aurora Citizen Portal: no robots.txt; only a privacy policy, with no automation or commercial-use language. Account needed for search. Manual lookup only.

## Corrections the test suggests to the ground truth (not applied)

- X02 Cerebral Brewing (9990 E Colfax Ave) is in Arapahoe County: even side of Colfax, below the county line in Aurora's own layer. Not Adams.
- X03 Curated Barrel (5525 W 56th Ave, Arvada) and X23 Stay Tuned (5127 W 64th Ave, Arvada) are not Adams County parcels. Jefferson.
- X09 Creation Technologies (1401 W 122nd Ave, Westminster) is an Adams County parcel.
- C22 Philip Morris: county Adams confirmed; the site is parcel 0181917301001, 25301 to 25315 E 48th Ave, owned by Kairus Inc, which is the entity on the Adams County incentive agreement (2024-07-09) and the state water permit.
- C25 RK Industries: site 3301 N Lewiston St, Aurora, confirmed by permits; two other RK sites noted in the Aurora notes.
- C23 Solid Power SP2: 14902 Grant St, Unit 120, Thornton (from the Thornton layer and the state water permit).
- X15 Izzio: 15107 Grant St (not 15101). X16 Kiosk: 251 E 126th Ave (126th and Washington). X05 Santa Monica Seafood: Unit 110.
- C20 Amprius: Brighton incentive resolution 2023-02-23; the site address is likely 4353 E Bromley Ln rather than 18875.
- D05 Craft Beverage Warehouse: likely 5925 Washington St (county permit under "Craft Labeling"), unincorporated Adams.
- Aurora permit "26-2513918" cited in discovery is 25-2513918.

## What was not finished

- Commerce City active layers could not be back-tested because closed records drop out; the build verdict rests on the layer's fields and on discovery's proof examples, not on a hit.
- Brighton's monthly permit PDFs have no archive, so Amprius and VSK could not be tested there.
- Property Sales was tested by address only; a grantee-name sweep was not run.
- PrimeGov attachments were not opened, so agreement amounts and sites come from item titles only.
- The Aurora council agenda archive was not reachable by static URL.
- The Thornton server returns HTTP 500 on ORed address clauses; the scrape must query one clause at a time.
