# Adams County, Colorado: local data sources for compressed air demand discovery

Verification date: 2026-10-30
Companion file: compressed_air_demand_sources_adams_county.csv (57 sources, ranked, discovery_score 0 to 100)

Every source in the CSV was loaded on 2026-10-30 from the cloud shell (ArcGIS REST, HTTP GET, PDF download) or through the WebFetch tool. Where a host blocked automated access or a page could not be fetched, the CSV says so in verified and verification_notes. Nothing is listed from memory.

## 1. Jurisdiction map

Adams County has roughly a dozen permitting authorities. The county portal covers only unincorporated land. Each city runs its own permit system and its own GIS, and the vendors differ, so each needs its own loader.

| Jurisdiction | Adams County share and industrial land | Permits and planning system | Agendas | GIS |
|---|---|---|---|---|
| Unincorporated Adams County | Welby and North Washington corridor (I-25, Washington St, E 58th to E 70th), Pecos Logistics Park (5675 to 5725 Pecos St), York St and Dahlia St corridors, Rail Park Dr, the Monaco and Dahlia industrial area east of Commerce City, Colorado Air and Space Port (Watkins), I-70 east toward Bennett and Strasburg, I-76 and Brighton Rd | Accela Citizen Access (aca-prod.accela.com/adamsco), modules Building, Permits, Planning, Enforcement. Data mirrored daily to ArcGIS Online (Building_Permits_Eye_On_Adams, Planning_Cases) | PrimeGov (adamscounty.primegov.com) since late 2022; Legistar (adcogov) holds 2022 and earlier | ArcGIS Online org 4PNQOtAivErR7nbT, hub data-adcogov.opendata.arcgis.com (CC BY 4.0) |
| Commerce City | All in Adams. Irondale and Derby, Brighton Rd and Hwy 85, Suncor area, E 96th to E 120th at Tower Rd (Prairie Gateway, Victory Crossing), E 104th and E 112th corridors, Heinz Way (CEMCO), E 60th Ave | CentralSquare eTRAKiT (comc.csqrcloud.com/community-etrakit), public search without login | Granicus Legistar (commerce.legistar.com) with Web API | ArcGIS Enterprise gisserver.c3gov.com; Central_Square folder carries active development layers |
| Brighton | Adams and Weld; county seat. Bromley Business Park and Bromley Business Pkwy, E Bromley Ln and I-76 (Amprius site at 18875 E Bromley Ln), Kuner Rd, Telluride St, Lovette Interstate Logistics Center (90 ac, I-1) | OpenGov Permitting and Licensing (brightonco.portal.opengov.com); monthly permit PDFs on brightonco.gov | Granicus Legistar (brightonco.legistar.com) with Web API | ArcGIS Online org FoIoSLUvgp6HznSK plus maps.brightonco.gov; Interactive Development Map |
| Thornton | Nearly all in Adams (small Weld portion). Washington St corridor from E 84th to E 160th (Washington Square, 25 Commerce Park, 126th and Washington, LPC Mile High One, Sack Creek, Creekside Innovation Park), Grant St and I-25 (Solid Power, Izzio), E 126th Ave (Kiosk, Santa Monica Seafood) | Harris CityView Portal (cityviewportal.thorntonco.gov); robots.txt disallows crawlers. Data mirrored to ArcGIS Enterprise (Permits, DevelopmentProjects) | CivicPlus CivicClerk (thorntonco.portal.civicclerk.com) | ArcGIS Enterprise maps.thorntonco.gov/citydevweb; hub data-cityofthornton.opendata.arcgis.com |
| Westminster | Adams and Jefferson. Adams side is east of Sheridan Blvd: Huron St corridor north of W 112th (Novera Commerce Center, Orchard, Tri-State), Westminster Station area at W 72nd and Federal | CentralSquare eTRAKiT (develop.cityofwestminster.us/etrakit) behind a Cloudflare challenge | CivicPlus Agenda Center (westminsterco.gov/AgendaCenter) | ArcGIS Enterprise maps.cityofwestminster.us; Planning/CurrentDevelopments layer |
| Northglenn | All in Adams except Section 36 (Weld). Small industrial base: Irma Dr and Huron St business parks (E 104th to E 120th), Cherokee St | CommunityCore public portal (app.communitycore.com) | CivicPlus CivicClerk (northglenn.portal.civicclerk.com) | ArcGIS Online org found but no development layers |
| Federal Heights | All in Adams. Very little industrial land (Federal Blvd corridor, W 84th to W 92nd) | In-house Building Department; electrical permits run through the state (DORA). Monthly permit PDFs on fedheights.org | City site (GovOffice) | None found |
| Arvada | Mostly Jefferson; a small eastern slice in Adams | CentralSquare eTRAKiT3 (arvadapermits.org); Development Map layer on ArcGIS Online | Not checked | ArcGIS Online org eQyVgDz2cjhzbzN7 |
| Aurora | Mostly Arapahoe; the Adams portion is north of about E 26th Ave to E 56th Ave and east to E-470 and beyond: Gateway Park (Lewiston St, RK Industries), Smith Rd industrial, Majestic Commercenter (E 36th Dr, Michelin, Medline), Porteos, High Point, Aurora Highlands, PMI at E 48th Ave and Harvest Rd (25315 E 48th Ave), Pretred at 6550 N Denali St | Infor Public Sector AMANDA; new Customer Portal (devportal.auroragov.org/citizenportal) live 2026-05-29. Data mirrored to ArcGIS Enterprise (Building Permits, Active Development Applications) | Static agenda PDFs on auroragov.org; no Legistar or Granicus found | ArcGIS Enterprise ags.auroragov.org; hub data-auroraco.opendata.arcgis.com |
| Bennett | Adams and Arapahoe. I-70 corridor; Colorado Air and Space Port is adjacent but in unincorporated Adams | New permit system (vendor not identified; account required). Town site blocks automated access | Town site | None found |
| Lochbuie | Mostly Weld; negligible Adams share | Site behind Cloudflare; not loaded | n/a | n/a |

Special districts and utilities that matter:

- South Adams County Water and Sanitation District (SACWSD): water and sewer for Commerce City and south unincorporated Adams; runs its own industrial pretreatment program. Board agendas monthly (Revize site).
- Metro Water Recovery: regional wastewater for Thornton, Westminster, Northglenn, Brighton, Aurora and others; issues industrial discharge permits but publishes no list.
- United Power: electric co-op for Brighton and the east and north county. Board minutes are PDFs with unreadable font encoding.
- Xcel Energy serves the west and south county (state-level source, not covered here).
- Fire: South Adams County Fire Department (Commerce City and south county; First Due permit portal since April 2026), Adams County Fire Rescue (west unincorporated), Brighton Fire Rescue District, North Metro Fire Rescue District (Northglenn), and the Thornton, Westminster and Aurora city fire departments. None publishes a plan review log.
- Metro districts (The Aurora Highlands, Porteos, High Point, Majestic Commercenter, Bromley Park and dozens more) file with DOLA, which is a state source.

## 2. What was found, in order of usefulness

The county and the three largest cities all mirror their permit systems into public ArcGIS REST layers that update daily. That is the main finding: for unincorporated Adams, Thornton, Aurora and Commerce City there is no need to scrape a permit portal. The browser-only portals (Accela, CityView, eTRAKiT, AMANDA) become detail lookups for flagged records.

Top tier (build):

1. Adams County Planning Cases layer. 12,496 Accela planning records back to 2011, daily refresh. Carries PRE Conceptual Review meetings (612 since 2024), which are the earliest formal filing the county produces. Free-text descriptions name the use and often the company.
2. Adams County Building Permits layer. 72,438 permits back to 2011, daily refresh, with Description, TypeOfWork, BuildingUse, square footage and Accela link. No valuation, no applicant name.
3. Thornton Building Permits (2017 to present). 84,285 permits with valuation, square footage, BUS_NAME and staff notes. Fire protection permits for bulk gas tanks and high-piled storage are an unusually direct process-equipment tell.
4. Aurora Active Development Applications. 1,808 cases, 581 in Adams County, with scope, acreage, zoning and status. Minor site plan amendments at existing plants (Michelin, R+L, Medline) are expansion tells that press never covers.
5. Thornton Development Projects. 303 active cases with Applicant, scope and OnMapDate. Records roll off at OffMapDate, so snapshot weekly.
6. Aurora Building Permits (full). 161,942 permits since late 2021 with valuation and free text. Carries the PMI factory ($206M Factory Use Building) and the RK Industries crane foundation.
7. Commerce City active development layers plus eTRAKiT project pages. Active-only snapshot, so history has to be built by snapshotting. eTRAKiT exposes full project records by direct URL, including plan sets and fire district referral comments.

Second tier (validate or park):

8. Brighton Planning Development Status layer (curated, 75 records) and the monthly Commercial Permits Issued PDF (owner, description, valuation).
9. Westminster Proposed and Current Developments layer (CPR meeting date, square footage, owner or developer).
10. Adams County Assessor Property Sales table (769,559 sales, daily, grantor and grantee) for the land purchase link, joined to Parcels.
11. Aurora business licenses with NAICS (Pretred appears with NAICS 326299 at 6550 N Denali St, start 2026-08-10).
12. Adams County PrimeGov agendas (JSON API plus HTML agendas) and the Commerce City and Brighton Legistar APIs for incentive agreements, rezones and lease approvals.
13. Tier II facility list (county-wide, annual) as a facility universe and new-filer detector.
14. Local press RSS (Brighton Blade, Northglenn-Thornton Sentinel, Sentinel Colorado).

## 3. Considered and rejected, and why

- Adams County Accela Citizen Access as a scrape target: ASP.NET postbacks, no API, and the same data is in the two ArcGIS layers. Keep for manual detail lookups only, consistent with the Denver decision on Accela.
- Thornton CityView Portal: robots.txt disallows every path except Home and Logon for all user agents and names GPTBot and ChatGPT-User. The GIS mirror carries the data, so there is no reason to touch the portal.
- Westminster eTRAKiT: Cloudflare bot challenge (HTTP 403, Just a moment) and robots content signals ai-train=no. Manual only.
- Aurora Customer Portal (AMANDA): account-oriented SPA; GIS mirrors already expose permits and development applications.
- Brighton OpenGov and Northglenn CommunityCore: SPA shells, public search not confirmed without a browser. Brighton's monthly PDFs substitute; Northglenn's industrial base is small.
- United Power board minutes: no customer names in the sampled minutes and the PDFs are not text-extractable.
- Aurora Building Permit Statistics: aggregate counts only.
- Adams County Code Enforcement layer: noise.
- City liquor and marijuana license layers (Commerce City, Westminster): no dates, so no lead time. The county's LIQ and MEL cases are dated and already inside the Planning Cases layer.
- Northglenn New Storefront Businesses list: stopped at Q4 2024.
- Brighton Community Development Weekly Report: counts only (permits issued, applications received), no names.
- AC-REP, Commerce City (redefiningcommerce.com) and Westminster economic development sites: blocked to automated access (403 or Cloudflare) and WebFetch was not permitted for them in this session. Incentive approvals show up in Legistar and PrimeGov anyway.
- Eye On Adams email alerts: useful for a rep, redundant for the pipeline.

State and federal sources encountered and set aside (covered elsewhere): CDPHE Tier II program (the county republishes it), ECMC oil and gas layer, DOLA special district filings, DORA electrical permits (Federal Heights routes electrical permits to the state), Colorado Secretary of State registrations for resolving LLC grantees, Mile High CRE and Denver business press.

## 4. Gaps

Jurisdictions with nothing usable yet:

- Bennett: permit vendor unknown, town site blocks automation, no project list. Industrial activity around Bennett and the Colorado Air and Space Port is mostly unincorporated and shows up in county sources.
- Lochbuie: negligible Adams land; site not reachable.
- Northglenn: no development or permit GIS layer; CommunityCore portal unverified.
- Federal Heights: monthly PDFs work but there is almost no industrial land.
- Arvada (Adams slice): eTRAKiT3 and a development map layer exist but no Adams-side industrial case was seen.

Chain links with weak local coverage:

- Hiring: no local source. Job postings are national-tier.
- Utility requests: SACWSD agendas carry an ERU report but no customer names; Metro Water Recovery and United Power publish nothing at the customer level. This link needs CORA (section 5).
- Contractor selection: only visible inside Accela, eTRAKiT and CityView record detail (contacts tab), not in the GIS layers. Commerce City eTRAKiT exposes contacts by direct URL; the others are manual.
- Capex approval: not visible locally except through incentive agreements in Legistar and PrimeGov.
- Valuation: the Adams County permit layer has no valuation field; Thornton, Aurora, Brighton and Federal Heights do.
- Applicant names: absent from the Adams County and Aurora permit layers; present in Thornton Development Projects (Applicant), Brighton PDFs (Owner Name), Westminster (Owner_Developer) and Federal Heights PDFs.

## 5. CORA requests that would unlock the gaps

Colorado Open Records Act requests are drafted below. None has been sent.

Draft A. Adams County Community and Economic Development (Accela export)

> To the Records Custodian, Adams County Community and Economic Development Department. Under the Colorado Open Records Act, C.R.S. 24-72-201 et seq., I request an electronic export (CSV or Excel) from the Accela permitting system of all Building module and Planning module records opened on or after January 1, 2024, where the record's building use or occupancy is commercial, industrial or agricultural business, including: record ID, record type, opened date, status and status date, site address, parcel number, work description, declared valuation, square footage, applicant name and company, owner name, and licensed contractor name and license number. Please exclude residential records and any personal contact details beyond business names. If the export cannot be produced in this form, please advise what report formats are available and the estimated cost before proceeding. I am willing to pay reasonable fees up to the statutory limits and ask to be notified if costs will exceed $100.

Draft B. Metro Water Recovery (industrial discharge permits)

> To the CORA Coordinator, Metro Water Recovery. Under C.R.S. 24-72-201 et seq., I request a list of industrial discharge permits (significant industrial user and categorical industrial user permits) issued, renewed or pending since January 1, 2024, for facilities located in Adams County, Colorado, including facility name, facility address, connector (member city or district), permit type and category, application received date and issuance date. I do not request discharge monitoring data or process information that may be confidential business information. Electronic format (CSV or Excel) preferred.

Draft C. South Adams County Water and Sanitation District (taps and pretreatment)

> To the District Clerk, South Adams County Water and Sanitation District. Under C.R.S. 24-72-201 et seq., I request (1) a list of commercial and industrial water and sewer tap purchases and capacity or service commitments since January 1, 2024, with service address, applicant business name, tap size or ERUs and date; and (2) a list of industrial pretreatment permits issued or pending since January 1, 2024, with facility name, address, permit type and dates. Electronic format preferred.

Draft D. South Adams County Fire Department, Brighton Fire Rescue District, North Metro Fire Rescue District (plan review logs)

> To the Records Custodian. Under C.R.S. 24-72-201 et seq., I request the fire prevention division's plan review and construction permit log for new commercial construction, commercial tenant finish, hazardous materials, compressed gas systems and high-piled storage permits received since January 1, 2025, including project address, project name or occupant, permit or review type, received date and approval date. Electronic format preferred.

Draft E. City of Thornton, City of Brighton, City of Commerce City (permit system exports)

> To the City Clerk (records custodian). Under C.R.S. 24-72-201 et seq., I request an electronic export of all commercial, industrial and fire protection permits and all planning or development applications received since January 1, 2024, from the city's permitting system (CityView for Thornton, OpenGov for Brighton, eTRAKiT for Commerce City), including record number, type and subtype, received and issued dates, status, site address, parcel, description of work, valuation, square footage, applicant or business name, owner name and contractor name. Residential records may be excluded. Electronic format (CSV or Excel) preferred.

## 6. Proof that the signal is there: recent industrial projects seen in these sources

1. Vartega expansion, 5675 Pecos St (unincorporated Adams). Adams County Building Permits layer record BDP24-0212, opened 2024-01-24: "Vartega has occupied the northern half of 5675 Pecos Street and has worked out lease terms to take an additional 30ksf." The same address shows later TI permits for Helena Agri-Tech (2025-04-04), Stevens Supply (2025-05-15), a 400A 480V service and step-down transformer TI (2025-04-30) and a Volley Automation sign (2026-05-08). One address, four tenants, all with dated permits.
2. Philip Morris ZYN campus ("Project Waterfall"), 25315 E 48th Ave, Aurora (Adams). Aurora Building Permits layer: 26-2513918 Commercial Building Permit, Factory Use Building, valuation $206,309,176, with fire alarm revisions and gas detection systems through 2026-10-14; 26-2507554 ethanol building, Hazardous Occupancy, $4.44M; LPG tanks for construction temp heat 2026-10-29; "Phase 2 WP 1 secondary buildout" $3M (2026-08-24). Aurora Active Development Applications: DA-2284-05 Project Waterfall site plan amendment, 86.71 acres, 2026-05-11.
3. RK Industries expansion, 3301 N Lewiston St, Aurora (Adams). Aurora Building Permits: 26-2651612 "Overhead cranes foundation" $370,000, entered 2026-09-03 (Online Building Folder 2026-08-18), plus a $100,000 gating system (2026-10-20). Aurora ADA: 1997-6051-05 minor amendment for a new exterior opening and driveway at 3301 N Lewiston St (2026-08-20). Cranes and dock openings are the kind of record that fires months before a compressor order.
4. Solid Power, 14902 Grant St Unit 120, Thornton. Thornton Building Permits: PRFPT202201932 bulk nitrogen gas storage and distribution system ($367,150) and PRFPT202201933 argon gas tank and distribution ($218,928), both entered 2022-04-21; high-piled storage racking 2022-09-09; TI "Solid Power DVPR construction project" $7.26M entered 2023-03-07; modular clean lab building 2025-02-24.
5. ABCO Contracting, 2185 E 74th Pl (unincorporated Adams). Adams County Planning Cases: PRE2025-00100 conceptual review for a 12,075 sf office and warehouse, opened 2025-12-29. Adams County Building Permits: BDP26-1661 new tilt-up office and warehouse, opened 2026-06-30. Six months from concept meeting to building permit, both visible in free layers.
6. Amprius site, 18875 E Bromley Ln, Brighton. Brighton Planning Development Status: "Mile High Logistics Center Site Plan" created 2024-05-15, Industrial, Under Construction (edited 2026-06-03). The site plan replaced the cancelled Amprius plant and shows the parcel moving to a new user.
7. Kiosk Information Systems, 251 E 126th Ave, Thornton. Thornton Building Permits: PREL202605278 generator for a "new building celebration" 2026-09-22, confirming the new building near 128th and Washington is occupied.
8. Pretred, 6550 N Denali St Ste 100, Aurora. Aurora business license layer: NAICS 326299 All Other Rubber Product Manufacturing, start 2026-08-10, issued 2026-08-22.
9. Ardent Mills, Commerce City. Commerce City Legistar Res 2026-096 (2026-06-17): first amendment to incentive agreement with Ardent Mills, LLC.
10. Process equipment at 4405 Rail Park Dr (unincorporated Adams). BDP26-1837 (2026-07-16): two Miura LX-100SG boilers with feedwater tank and blowdown separator. Boiler permits are a strong correlate of new process steam and air.

## 7. Surprises

- All four large permitting authorities (county, Thornton, Aurora, Commerce City) expose their permit systems through public ArcGIS REST layers. For Denver the pipeline had to live with a browser-only Accela portal for trade permits; here the county's Accela data is a daily feature layer with descriptions and Accela links.
- The Adams County Planning Cases layer includes pre-application Conceptual Review meetings. That is the earliest formal footprint a project leaves and it is rarely published anywhere.
- Aurora's development application layer carries a County field and 581 Adams County cases, which makes the county split trivial. It also lists minor site plan amendments at operating plants (Michelin loading ramp, R+L truck yard, Medline guard house), a class of expansion tell that never reaches press.
- Thornton's permit layer includes fire protection permits for bulk gas tank systems and high-piled storage with valuations, which point straight at process build-outs.
- Commerce City's eTRAKiT returns full project pages, attachments and referral comments to a plain HTTP GET by activity number, with no robots.txt served.
- Brighton City Council passed a one-year data center moratorium ordinance in October 2026 (ID-300-26), and the Brighton Blade reported a small AI data center maker arriving in Brighton. Both are local press and Legistar signals that would be missed by state sources.
- The county's Tier II facility layer is a ready-made universe of 469 chemical-handling facilities across the whole county including Aurora.
- Adams County left Legistar in September 2022 for PrimeGov; the Legistar API still answers but stops at 2022-09-27, which would silently truncate any history pull.
- The Adams County permit layer has no valuation field even though Accela captures it; the Brighton and Thornton exports do.
- Blocked hosts from the cloud shell: gisapp.adcogov.org and recording.adcogov.org (Cloudflare), develop.cityofwestminster.us (Cloudflare), c3gov.com economic development pages and redefiningcommerce.com (Akamai 403), bennettco.gov (403), lochbuie.org (Cloudflare), westminstereconomicdevelopment.org and auroraedc.com (Cloudflare), members.ac-rep.org (403). WebFetch permission was not granted in this session for brightonco.gov/1134, northglenn.org project updates, auroragov.org portal instructions, recording.adcogov.org, metrowaterrecovery.com pretreatment and redefiningcommerce.com; those pages were read by other routes where possible and are marked partially verified or unverified in the CSV.

## 8. Notes for the validation step

- Inherit Denver's build verdict for the commercial permit layers (Adams County, Thornton, Aurora) and the concept or site plan layers (Adams County Planning Cases, Thornton Development Projects, Aurora Active Development Applications, Commerce City active layers, Westminster CurrentDevelopments, Brighton status layer), then spot-check each on 50 to 200 rows.
- Known projects in the county that can be back-tested: Vartega, PMI, RK Industries, Solid Power, Kiosk, Pretred, Amprius site, CEMCO (9410 Heinz Way, Commerce City; check eTRAKiT and Property Sales), Boise Cascade (11011 E 104th Ave, Commerce City), Izzio (15101 Grant St, Thornton; only a monument sign permit was seen in the Thornton layer under that address, so check the Grant St and 25 Commerce Park address variants), Santa Monica Seafood (1101 E 126th Ave, Thornton), Prost Brewing (351 W 104th Ave, Northglenn; Northglenn has no layer).
- Snapshot the three active-only layers (Commerce City under review and under construction, Thornton Development Projects, Brighton status) weekly from the start; they do not keep history.
- Aurora layer 44 rejects queries that reference fields that exist only on the 1-month and 6-month views (FULL_ADDRESS, PropStreet). Use Address on layer 44.
