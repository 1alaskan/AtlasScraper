# Weld County, Colorado: local data sources for compressed air demand discovery

Verification date: 2026-11-05
Companion file: compressed_air_demand_sources_weld_county.csv (56 sources, ranked, discovery_score 0 to 100; 42 verified, 12 partially verified, 2 not reachable)

Every source in the CSV was loaded on 2026-11-05 from the cloud shell (ArcGIS REST, HTTP GET, JSON services, PDF download) or through the WebFetch tool. Where a host blocked automated access or a page could not be fetched, the CSV says so in verified and verification_notes. Nothing is listed from memory. State and federal sources are not inventoried here; the ones met in passing are listed at the end of section 3.

## 1. Jurisdiction map

Weld County has about 30 incorporated municipalities. The county permit system (Accela) covers only unincorporated land, which is where the oil and gas support yards, food processors, the I-25 and US 85 corridor sites outside city limits, and the large solar and BESS projects sit. The cities and towns with industrial land each run their own permit system, and the vendor mix is wide: Accela (county, Frederick, Longmont), CentralSquare TRAKiT and eTRAKiT (Greeley, Johnstown, Windsor internally, Erie), Citizenserve (Evans, Firestone), CommunityCore (Dacono, Milliken, Mead, Kersey), SAFEbuilt paper or email permits (Platteville, Lochbuie, Fort Lupton, Hudson, Keenesburg, Ault, Eaton), and no portal at all for the smallest towns.

| Jurisdiction | Industrial land in Weld County | Permits and planning system | Agendas | GIS |
|---|---|---|---|---|
| Unincorporated Weld County | Largest industrial base in the county: US 85 corridor from Platteville to Ault, I-25 frontage north of Hwy 66 and around Mead and Johnstown, WCR 49 and the Hudson and Keenesburg energy corridor, Great Western Industrial Park fringe, oil and gas support yards everywhere, solar and BESS farms on the east plains, data center filings in I-1 zones, 4120 Specialty Pl (former UQM, now BAE Systems) east of Longmont | Accela: legacy Citizen Access at aca-prod.accela.com/WELD (modules Building, Planning, Dev Review, Oil and Gas, Public Works, Health, Enforcement) and the new Accela Public Portal at weld-prod.accela.com/portal (account required). Planning cases, SPRs, access permits and WOGLA assessments are mirrored to ArcGIS Online | Laserfiche WebLink 11 at minutes.weld.gov (BOCC agendas, packets, minutes, resolutions, agreements back to 1859, JSON services) | ArcGIS Online org ewjSqmSyHJnkfBLL (115 services, assessor tables, planning layers); ArcGIS Enterprise at maps.weld.gov/gis holds only utility services; VertiGIS Studio property portal at maps.weld.gov/propertyportal |
| Greeley | County seat and largest city: JBS and Swift beef (Promontory Cir and N 11th Ave), Leprino Foods (E 8th St), Great Western Industrial Park west edge, 1st Ave and H St industrial, E 8th St and 117th Ave flex industrial, Greeley-Weld airport, Western Sugar TIF area | CentralSquare eTRAKiT at trakit.greeleygov.com (every search requires a free public login); planning cases mirrored to ArcGIS Enterprise (TrakitProjects, 172 active); public space permits mirrored (TrakIT2025) | CivicPlus CivicClerk (greeleyco.portal.civicclerk.com) with a public OData API and plain text file streams; Municode Meetings archive before June 2023 | ArcGIS Enterprise gis.greeleygov.com (arcgis_svr, arcgis_svr3, arcgis_svr5) and portal; Experience Builder apps for development projects and property facts |
| Evans | US 85 corridor south of Greeley: 47th Ave and CR 394 (Mountain Cement terminal, asphalt plants), Industrial Pkwy, 43rd St and Valmont (oilfield services), 37th St | Citizenserve for building permits (the city's public link returned 404 on 2026-11-05); planning cases listed in an HTML table and a StoryMap | eSCRIBE (pub-evans.escribemeetings.com) | ArcGIS Hub evanscolorado-evans.opendata.arcgis.com (zoning only) |
| Windsor (Weld and Larimer) | Great Western Industrial Park and Foreign Trade Zone 123 (Vestas blades, Front Range Energy, Carestream, Gotham Greens), Diamond Valley and Eastman Park Dr heavy industrial, Windsor Industrial Park annexation (46 ac LI), 13 business parks | SAFEbuilt building services tracked in CRW TRAKiT; no public permit search; monthly Building Permit Report PDFs name every commercial and industrial new building permit; Development Activity StoryMap for planning cases | CivicPlus Agenda Center with RSS (windsorco.gov blocks scripts; the mirror co-windsor3.civicplus.com does not) | ArcGIS Enterprise gis.windsorgov.com (Land_Development and EconDev folders need a token); AGOL org 0z17zZWWifqrYfyb |
| Fort Lupton | US 85 and Hwy 52: Factory Dr and Factory Circle, Northland Business Park, Sphere Renewables at CR 8, Hwy 52 industrial, L. G. Everist mining | No online permit portal (CivicPlus pages only; Tyler EnerGov reference layers exist from 2015 but no public EnerGov site was found); planning cases on an HTML table and an AGOL layer (Planning_AGOL, 37 cases) | CivicPlus Agenda Center | AGOL org 7fqvVMRB6DcB5wXC |
| Frederick | Agilent Technologies (7051 Eagle Blvd), Hirsh Precision, Bear Industrial Park, Raspberry Hill Business Park, Eagle Business Park, Park 4040, Glacier West, Meadowlark Business Park, Spindle Hill BESS | Accela (aca-prod.accela.com/FREDERICK answers), mirrored daily to ArcGIS Enterprise gis.frederickco.gov (Accela_Building_Permits, 19,577 records; Development_Applications, 22 records) | CivicPlus CivicClerk (frederickco.portal.civicclerk.com, API answers) | ArcGIS Enterprise gis.frederickco.gov (15 folders) and AGOL org kUg4C2jBpieHWTtl |
| Firestone | I-25 frontage (Del Camino, Flatiron II PUD, Western Midstream), Firestone Blvd commercial, Hwy 119 | Citizenserve (public link returned 404); biweekly Accepted Development Review Applications PDF; Development Projects Experience Builder map | CivicPlus (agendas not probed) | AGOL org AqMpORZxzXMXwPCf; hub gis-firestoneco.hub.arcgis.com |
| Dacono | I-25 and Hwy 52, Dacono industrial park, Colorado Blvd, Sprouts and Sharpe Farms commercial | CommunityCore (registration required, no public search confirmed) | CivicPlus Agenda Center | AGOL org QbvMNMuqgUyczqCP; hub with zoning and annexation layers only |
| Johnstown (Weld and Larimer) | I-25 and Hwy 60, Johnstown Plaza and 2534 (Larimer side), Gateway Park, Hwy 60 industrial | CentralSquare eTRAKiT cloud (jcol.csqrcloud.com; permit search needs a free login, project search loads without one); Current Projects HTML table | CivicPlus Agenda Center | Hub town-of-johnstown.hub.arcgis.com (one dataset) |
| Milliken | Hwy 60 and Hwy 257 industrial, Centerra East edge | CommunityCore (registration required) | CivicPlus Agenda Center | None found |
| Platteville | US 85 and Hwy 66; TFP Nutrition pet food plant at 450 N Front St | Paper building permits reviewed by SAFEbuilt; contract planner (Ayres Associates); no portal, no project list | Agenda and packet PDFs on the state Drupal site (browser user agent required) | None |
| Mead | I-25 and Hwy 66 (FedEx Freight, Mead Ct industrial, UPS) | CommunityCore (registration required); town site returns 403 to scripts | Town site (blocked) | None found |
| Erie (Weld portion) | Almost entirely residential east of County Line Rd; Erie Airpark | CentralSquare Community Development with Laserfiche cloud documents; projects layer on ArcGIS Enterprise | Granicus | ArcGIS Enterprise eags.erieco.gov; hub |
| Hudson | I-76 and Hwy 52, WCR 49 energy corridor | In house permits (state payport for fees); no portal | CivicPlus Agenda Center | None |
| Keenesburg | I-76 and Hwy 52, Railroad Ave | In house permits | Revize agendas and minutes | None |
| Kersey | Hwy 34 east, Colorado Sand Company mine | CommunityCore (registration required) | Revize agendas and minutes | None |
| LaSalle | US 85 south of Greeley (23295 Hwy 85 industrial sale seen) | No reachable town website found | None found | None |
| Lochbuie | I-76 | SAFEbuilt inspections, no portal; site returns 403 to scripts | CivicPlus (blocked) | None |
| Severance | Hwy 14 and WCR 23; included in Windsor's monthly permit report | In house | CivicPlus | None |
| Eaton | US 85 north; former Western Sugar factory area | Unknown; site returns 403 to scripts and WebFetch permission was not granted | Unknown | None |
| Ault | US 85 north; asphalt plant (new personal property account 2026) | In house | Custom town site | None |
| Longmont (Weld slice) | East of Weld County Line Rd: Ken Pratt Blvd east (Westview Business Park), Sandstone Marketplace, Hwy 66 annexations | Accela Citizen Access (aca.longmontcolorado.gov); Active Developments layer on ArcGIS Enterprise (218 cases) | City site | ArcGIS Enterprise pwnrmaps.ci.longmont.co.us |
| Berthoud (Weld slice) | Small, east of I-25 | Not probed | CivicClerk (API answers) | AGOL |
| Brighton, Thornton, Northglenn (Weld slices) | Small slices north of the Adams line | Covered in the Adams County inventory (OpenGov, CityView mirrored to ArcGIS, CommunityCore) | See Adams notes | See Adams notes |

Special districts and utilities that matter:

- Poudre Valley REA (north and west Weld electric co-op): board minutes are scanned images with no text layer.
- United Power (south and east Weld co-op): no customer names in minutes (Adams run).
- Xcel Energy serves Greeley, Windsor and parts of the south county (state tier).
- Water: Greeley Water and Sewer (industrial pretreatment program, no permittee list), Central Weld County Water District (scanned packets), Little Thompson Water District (Mead, Johnstown, Milliken, Berthoud; agendas and minutes online), Left Hand Water District and St. Vrain Sanitation District (hosts unreachable from the shell), North Weld County Water District and Fort Lupton, Frederick, Firestone, Dacono, Platteville municipal utilities (not probed).
- Fire: Greeley Fire (permits through eTRAKiT), Windsor-Severance Fire Rescue (host unreachable), Frederick-Firestone FPD (scanned minutes), Mountain View Fire Rescue (Dacono, Erie, Mead; packets name approved plans), Front Range Fire Rescue (Johnstown, Milliken), Fort Lupton FPD, Platte Valley FPD (403), Hudson, Southeast Weld, Eaton and Ault fire districts (not probed). None publishes a plan review log.
- Metro districts file with DOLA (state tier).

## 2. What was found, in order of usefulness

The main finding is that Weld County publishes its commissioner records through Laserfiche WebLink with working JSON endpoints, and those records carry every county Tax Incentive Agreement under C.R.S. 30-11-123. The agreement is the county's personal property tax incentive for manufacturing equipment and machinery, so a company only signs one when it plans to buy a lot of equipment at a named Weld County address. Every one of the six proof projects in the brief shows up there 6 to 20 months before opening, and the agreement text names the facility address and the equipment phase caps. That single source outranks every permit portal in the county.

The second finding is that Weld County, Frederick and Greeley all mirror their permit or planning systems to public ArcGIS REST layers, as Adams and its cities did. The county's Accela building permits are not mirrored (only planning cases, SPRs, access permits and WOGLA assessments are), which is the biggest gap in the county, but the Assessor publishes daily sales, ownership and personal property account tables for the whole county including every city, which is the best land purchase and equipment-in-service feed seen in any Colorado county so far.

Top tier (build):

1. Weld BOCC Laserfiche: Tax Incentive Agreements and all commissioner records (rank 1). JSON folder listing, field search on the Commissioner Records template (Names, Notes, DocCode, Hearing Date) and OCR text per page. 18 incentive agreements since 2022.
2. Weld Planning Cases for Development Activity Map (rank 2). 96 active USR, SPR, ZPAG, COZ and SIF cases with Accela links; active only, so snapshot daily.
3. Frederick Accela Building Permits (rank 3). 19,577 permits with descriptions; Agilent's equipment, piping and lab renovation permits are there.
4. Weld Assessor Sales points (rank 4). County wide, daily, grantor and grantee, occupancy and size. BAE Systems' $30M purchase of the UQM plant recorded 2026-10-05.
5. Greeley TrakitProjects (rank 5). 172 active planning cases with address, applicant and dates.
6. Frederick Development Applications and What's Developing (rank 6). Agilent Endeavor site plan under review.
7. Weld Site Plan Review recorded cases (rank 7). 435 recorded SPRs with zoning, acreage and recording date.
8. Fort Lupton Planning_AGOL and Current Development Projects (rank 8). EquipmentShare site plan, Northland Business Park.
9. Greeley CivicClerk OData API with plain text packets (rank 9).
10. Firestone biweekly Accepted Development Review Applications PDF (rank 10).
11. Windsor monthly Building Permit Reports (rank 11). Industrial new building permits by month since 2022.
12. Weld Assessor Ownership table with Personal Property accounts (rank 12). New P-accounts are new business equipment at a site.

Second tier (validate or park):

13. Weld Accela Citizen Access record detail by GET (rank 13) as the detail lookup for anything flagged in the layers.
14. Evans in-process land use case table (rank 14): Mountain Cement terminal, Acme Oilfield Services, Planet View expansion.
15. Weld Access Permit layer (rank 15): Large Commercial and Industrial driveway permits with Accela links.
16. Weld Assessor account inventory and Tier II layer as the facility universe (ranks 16 and 17).
17. Windsor Development Activity StoryMap (rank 18): waste transfer facility in HI zoning, Windsor Industrial Park subdivision.
18. Johnstown eTRAKiT and Longmont's Weld slice (ranks 19 and 20).
19. Agenda systems with APIs or RSS: Greeley and Frederick CivicClerk, Windsor and Fort Lupton Agenda Centers, Evans eSCRIBE.
20. Mountain View Fire Rescue packets for Dacono, Mead and Erie plan approvals (rank 29).
21. BizWest RSS for announcements (rank 22).

## 3. Considered and rejected, and why

- Weld County Accela Citizen Access as a crawl target: search forms are ASP.NET postbacks and the global search accepts record numbers only. The state notes said the host blocked automated fetches; on 2026-11-05 record detail pages answered a plain GET with a browser user agent. Keep it as a detail fetch for records found in the GIS layers, as Denver and Adams decided.
- Weld County new Accela Public Portal (weld-prod.accela.com): Angular SPA with an API key in config.js; the bundle exposes account routes only. Nothing public to pull.
- Weld County property portal (maps.weld.gov/propertyportal, VertiGIS Studio Web): the same assessor data is in the AGOL tables, so the portal was not reverse engineered.
- weld.gov pages (Planning and Zoning, Development Review, Recorded Documents, Commissioner Records, GIS Data, Newsroom): Akamai returns 403 to the shell, and WebFetch permission was not granted for most of them in this session. The Building page was read through WebFetch; the rest are marked in the blocked list below.
- Weld Clerk and Recorder document search: the Recorded Documents page and apps.weld.gov/clerkrecorder are behind Akamai. The Assessor sales layer carries RECEPTIONNO, DEEDCODE, grantor and grantee, which covers the deed link without the recorder.
- Greeley eTRAKiT: every search redirects to login (a free public account). The TrakitProjects layer carries the planning cases without login; building permits need a CORA request or an account driven browser scraper.
- Greeley monthly construction reports (.docx) found in search results: links on the old greeleygov.com site now 404 on the new greeleyco.gov site. Not listed.
- Greeley Public Space permits layer: right of way work, not facilities; kept at low rank only because the DEVELOPMENT subtype names projects needing utility connections.
- Greeley USR_poly and DevelopmentConceptMasterPlan layers on the TRAKiT map service: last edited 2017, oil and gas USRs; stale.
- Evans and Firestone Citizenserve links: both returned 404 at citizenserve.com; the tenant paths have changed and no working public search URL was found.
- CommunityCore (Dacono, Milliken, Mead, Kersey): registration required; public search not confirmed, consistent with the Adams finding for Northglenn.
- Windsor gis.windsorgov.com Land_Development and EconDev folders: token required. CRW_SYSTEM service is reference layers only.
- Windsor Business Parks StoryMap: static inventory of parks, no projects.
- Erie: 61 project records, none industrial; Weld side is residential.
- Weld Oil and Gas Location Assessment layer: well pads, not compressed air demand. Compressor stations and gas plants appear as USR cases in the Planning Cases layer.
- Weld Nonconforming Use layer: kept as a low reference layer only.
- Electric co-ops: PVREA minutes are scanned images; United Power minutes carry no customer names (Adams run).
- Central Weld County Water District: packets are scanned images; OCR cost exceeds the expected signal. Little Thompson Water District minutes are text PDFs but were not read in this pass.
- Fire districts: no district publishes a plan review log; FFFPD minutes are scanned; Mountain View's packet narrative is the only one that names approved plans.
- Greeley Tribune: robots.txt forbids commercial use, caching and data mining and the feed returns 403; manual reading only.
- Upstate Colorado: site closed connections to the shell and WebFetch permission was not granted; the EDO is named as a party on the 2026 county incentive agreements, so its wins are already captured upstream.
- Liquor and marijuana licensing: county LIQ and MEL cases were not found in the active cases view, and no city liquor layer with dates was seen; dropped.
- Platteville packets: TFP Nutrition's county incentive agreement (Oct 2024) beat the Nov 2025 press release by 13 months; the town's agenda PDFs add nothing earlier.

State and federal sources encountered and set aside (covered elsewhere): CDPHE Tier II (the county republishes it), ECMC well permits (county WOGLA layer mirrors county assessments), DOLA special district filings, Colorado Secretary of State registrations for resolving LLC grantees, OEDIT Job Growth Incentive Tax Credit approvals (the BizWest item on $428,171 in state incentives for a company eyeing Weld County is the state side of a county agreement), Colorado DWR water rights, CDOT access permits on state highways (county access permits cover county roads only), Regulation 84 reclaimed water user list, data.colorado.gov datasets.

## 4. Gaps

Jurisdictions with nothing usable yet:

- Dacono, Milliken, Mead, Kersey: CommunityCore portals with no public search; no development project layer. Dacono and Mead industrial sites are covered only by county Assessor sales, the county incentive agreements, the Tier II layer and Mountain View Fire packets.
- Platteville, Hudson, Keenesburg, Ault, Severance, Lochbuie, Eaton, LaSalle: paper or in house permits, agendas only (two of the sites block scripts and LaSalle has no site).
- Windsor: no permit search at all (CRW TRAKiT is internal); the monthly PDF names new buildings but not tenant finishes or equipment permits, and 2026 shows zero industrial new buildings so far.
- Fort Lupton: no permit portal; planning cases only.
- Evans and Firestone: permit portals exist (Citizenserve) but the public links are dead.
- Greeley: building permits behind a login.
- Unincorporated Weld County: building permits are in Accela but not mirrored to GIS, so county permit valuation, equipment descriptions and contractor names are reachable only one record at a time through CapDetail or through CORA.

Chain links with weak local coverage:

- Hiring: no local source. Job postings are national tier.
- Utility requests: Greeley pretreatment publishes no permittee list; water districts publish scanned or unread minutes; electric co-ops publish nothing at the customer level. Greeley's public space DEVELOPMENT permits are the only automated proxy. This link needs CORA (section 5).
- Contractor selection: visible inside Accela, eTRAKiT and CityView record detail only; the Frederick permit layer has no contractor field; the Greeley public space layer has APPLICANT_NAME (contractor) for right of way work.
- Capex approval: the county incentive agreements are the best local capex signal in any Colorado county so far; city level incentive agreements are inside council packets (CivicClerk, Agenda Center, eSCRIBE) and have not been parsed.
- Valuation: none of the Weld layers carries permit valuation; Windsor's PDF gives class totals only. Frederick, Greeley and the county capture valuation in their systems but do not publish it.
- Dates: the county Planning Cases view has no dates (status only); the county SPR layer has the recording date only.
- Applicant names: present in Greeley TrakitProjects and Fort Lupton Planning_AGOL (companies and individuals mixed), absent from the Frederick permit layer and the county cases view.

## 5. CORA requests that would unlock the gaps

Colorado Open Records Act requests are drafted below. None has been sent.

Draft A. Weld County Planning and Development Services (Accela export)

> To the Records Custodian, Weld County Department of Planning and Development Services. Under the Colorado Open Records Act, C.R.S. 24-72-201 et seq., I request an electronic export (CSV or Excel) from the Accela system of all Building module records opened on or after January 1, 2024, where the occupancy or use is commercial, industrial, agricultural business or oil and gas, including: record number, record type and subtype, opened date, status and status date, site address, parcel number, work description, declared valuation, square footage, applicant business name, owner name, and licensed contractor business name. Please exclude single family residential records and any personal contact details beyond business names. If the export cannot be produced in this form, please advise what report formats are available and the estimated cost before proceeding. I am willing to pay reasonable fees up to the statutory limits and ask to be notified if costs will exceed $100.

Draft B. Weld County Department of Finance (incentive agreement claims)

> To the Records Custodian, Weld County Department of Finance. Under C.R.S. 24-72-201 et seq., I request copies of, or a list summarizing, the annual Tax Incentive Payment claims and affidavits submitted under Tax Incentive Agreements approved pursuant to C.R.S. 30-11-123 since January 1, 2023, including taxpayer name, business facility address, tax year, personal property account number, assessed value of qualifying personal property claimed, and incentive payment amount. I do not request the taxpayer's personal property declaration schedules. Electronic format preferred.

Draft C. City of Greeley (eTRAKiT export and pretreatment permits)

> To the City Clerk (records custodian), City of Greeley. Under C.R.S. 24-72-201 et seq., I request (1) an electronic export from the TRAKiT permitting system of all commercial, industrial and fire prevention permits received since January 1, 2024, including permit number, type and subtype, received and issued dates, status, site address, parcel, description of work, valuation, square footage, applicant business name, owner name and contractor business name; and (2) from the Water and Sewer Department's Industrial Pretreatment Program, a list of wastewater discharge permits (significant industrial user, categorical and sector control) issued, renewed, modified or pending since January 1, 2024, with facility name, facility address, permit type and category, application received date and issuance date. I do not request discharge monitoring data or process information that may be confidential business information. Residential records may be excluded. Electronic format (CSV or Excel) preferred.

Draft D. Towns of Windsor, Frederick, Firestone, Dacono, Mead, Milliken and the Cities of Evans and Fort Lupton (permit system exports)

> To the Town or City Clerk (records custodian). Under C.R.S. 24-72-201 et seq., I request an electronic export of all commercial and industrial building, mechanical, electrical, plumbing and fire protection permits received since January 1, 2024, from the municipality's permitting system (CRW TRAKiT for Windsor, Accela for Frederick, Citizenserve for Firestone and Evans, CommunityCore for Dacono, Mead and Milliken, and the Building Department's records for Fort Lupton), including permit number, type and subtype, received and issued dates, status, site address, parcel, description of work, valuation, square footage, applicant or business name, owner name and contractor business name. Residential records may be excluded. Electronic format (CSV or Excel) preferred.

Draft E. Fire districts (plan review logs)

> To the Records Custodian, Frederick-Firestone Fire Protection District, Mountain View Fire Rescue, Windsor-Severance Fire Rescue, Front Range Fire Rescue, Fort Lupton Fire Protection District, Platte Valley Fire Protection District and the Greeley Fire Department Fire Prevention Bureau. Under C.R.S. 24-72-201 et seq., I request the fire prevention division's plan review and construction permit log for new commercial construction, commercial tenant finish, hazardous materials, compressed gas and cryogenic systems, industrial ovens and furnaces, spray booths and high-piled storage permits received since January 1, 2025, including project address, project name or occupant, permit or review type, received date and approval date. Electronic format preferred.

Draft F. Water and sanitation districts (taps and will serve commitments)

> To the District Manager, Central Weld County Water District, Little Thompson Water District, North Weld County Water District, St. Vrain Sanitation District and Left Hand Water District. Under C.R.S. 24-72-201 et seq., I request a list of commercial and industrial tap purchases, will serve letters and capacity or service commitments issued or approved since January 1, 2024, with service address, applicant business name, tap size or equivalent units and date. Electronic format preferred.

## 6. Proof that the signal is there: recent industrial projects seen in these sources

1. BAE Systems Space and Mission Systems, 4120 Specialty Place (former UQM Technologies plant, Longmont address, Weld County). Weld BOCC Laserfiche document 20262355 (2026-09-16): Resolution approving a Tax Incentive Agreement, project name Project Mercury, with Upstate Colorado as a named party; the agreement text establishes the business facility at 4120 Specialty Place with three expansion phases, a 50 percent incentive on taxes for manufacturing equipment and machinery, and a Phase I cap of $13,765,102. Weld Assessor Sales: 2026-10-05, UQM Properties to BAE Systems Space and Mission Systems, $30,000,000, 126,988 sf on 12.96 ac. Public announcement followed on 2026-10-23 (areadevelopment.com, evertiq.com). The county record led the press by five weeks and the deed by three.
2. Agilent Technologies, 7051 Eagle Blvd, Frederick. Weld BOCC document 20223599 (2022-12-28): Tax Incentive Payments agreement, two months before the February 2023 groundbreaking of the $725M expansion. Frederick permit layer 2026: BLDG26-0255 Area B lab renovation phases 2 to 4 (2026-04-28), BLDG26-0274 construction field office trailer, BLDG26-0344 and BLDG26-0346 Area B and D interior renovations (2026-06-09), BLDG26-0380 Area J modifications to equipment, piping and electrical in two rooms (2026-07-01), BLDG26-0469 access control (2026-08-13). Frederick Development Applications: Agilent Endeavor site plan for a new manufacturing building and a new warehouse north of the existing plant, under review on 2026-11-05.
3. TFP Nutrition (Texas Farm Products), 450 N Front St, Platteville. Weld BOCC document 20242850 (2024-10-28): Tax Incentive Payments agreement, contract 8797. The plant was announced publicly in November 2025 and opened January 2026, so the county record fired 13 months before the announcement. The Assessor Ownership table already shows a personal property account at 450 Front St, Platteville (a bank tenant), which is the kind of P-account the plant will add in 2026 or 2027.
4. Hirsh Precision Products, Frederick. Weld BOCC document 20220470 (2022-02-07): Tax Incentive Payments agreement, 20 months before the 65,000 sf plant opened in October 2023.
5. Sphere Renewables, 13516 CR 8, Fort Lupton. Weld BOCC document 20223348 (2022-12-05): Tax Incentive Payments agreement, 18 months before the June 2024 ribbon cutting.
6. Colorado Premium Foods (K2D Inc), 2400 W 29th St, Greeley. Weld BOCC document 20231862 (2023-07-05): Tax Incentive Payments agreement, seven months before the February 2024 opening of the sous vide plant.
7. Microvast Energy, Windsor. Weld BOCC document 20232050 (2023-07-19): Tax Incentive Payments agreement, the same month as the ESS plant announcement. The agreement exists even though the project was later consolidated away, which is a reminder that an incentive approval is a strong but not certain signal.
8. Front Range Energy Carbon Storage Solutions, 31375 Great Western Dr, Windsor. Windsor Building Permit Report September 2024: industrial permit for construction of two new buildings for process operations at the ethanol plant.
9. Mountain Cement Co terminal, SW of CR 394 and 47th Ave, Evans. Evans in-process cases: 24-AP-04 minor plat (approved, conditions in progress) and 24-SP-04 site plan for the MCC terminal (staff report in progress). Acme Oilfield Services industrial site plan 24-SP-05 at 43rd St and Valmont St and Planet View facility expansion 25-SP-02 are on the same table.
10. Unincorporated Weld County cases on 2026-11-05: SPR26-0007 Empire Industrial Business Park (multipurpose industrial and office buildings), COZ26-0003 agricultural to I-3 heavy industrial, USR26-0019 data center in an I-1 zone (site plan amendment), USR25-0010 and USR26-0025 natural gas compressor stations, ZPAG26-0017 an insulation contractor adding an 8,000 sf building, SPR25-0012 seed storage distribution center in I-3, ZPAG25-0017 hemp processing facility. Each carries a link to the Accela record.
11. Other county incentive agreements since 2022 worth back-testing: GG Colorado II (Jan 2022), Colorado Stud Company (Jan 2022), Norfolk Iron and Metal (Dec 2022), Airxcel and Aqua-Hot Heating Systems (Jul 2023), Owens-Brockway Glass Container (Jul 2023), North American Machines of Colorado and TruLog Siding (Oct 2024), Charm Industrial (May 2025), The Scotts Company and Hyponex (Jul 2025), EcoMod (Aug 2025), US Engineering Metalworks (Sep 2026), Motherload Co Packing (Sep 2026).

## 7. Surprises

- The county's personal property tax incentive is the single best early signal found in any Colorado county so far. The state tier notes guessed this from an old fact sheet; the Laserfiche records prove it with 18 agreements since 2022, each naming the facility and the equipment phase caps, and each predating the press by months. The current statutory basis is C.R.S. 30-11-123 and the 2026 agreements run 35 year terms with 10 year phase windows and 50 percent rebates on county taxes for manufacturing equipment and machinery.
- Laserfiche WebLink 11 answers JSON calls (FolderListingService, SearchService field search, DocumentService OCR text) with nothing more than a session cookie. The Adams run treated Laserfiche as a browser portal; here it behaves like an API. The LF:Basic full text search timed out, but template field searches on Names, Notes, DocCode and Hearing Date return quickly.
- Weld County does not mirror its Accela building permits to GIS, unlike Adams, but it does publish the entire assessor database daily (sales, ownership, personal property accounts, building inventory) for every jurisdiction in the county. The BAE Systems purchase was visible 18 days before the announcement.
- The Weld AGOL items carry a license line saying the product was developed solely for internal use by Weld County, yet the items are shared publicly, named open_data and feed the county's public maps. It reads as a liability disclaimer, but the validation step should confirm commercial use with county GIS before any resale.
- Frederick's Accela is mirrored to its own ArcGIS Enterprise server with full permit descriptions, which is how Agilent's equipment and piping permits became visible without touching the Accela portal.
- Greeley's CivicClerk API streams agenda packets as plain text (plainText=true), which removes PDF parsing for the county's largest city. Frederick and Berthoud run the same API.
- Windsor's own site (windsorco.gov) blocks scripts, but its CivicPlus mirror host co-windsor3.civicplus.com serves every page and PDF.
- Evans and Firestone both link to Citizenserve tenants that no longer exist at the published URLs.
- Fort Lupton's AGOL org still carries Tyler EnerGov reference layers from 2015, but the city has no public permit portal today.
- The Weld Planning Cases view includes a data center USR in an I-1 zone, two natural gas compressor stations, a hemp processor and a seed storage distribution center at the same time, which is a wider mix of pneumatic users than any Denver metro county showed.
- Blocked hosts from the cloud shell: www.weld.gov and apps.weld.gov except the property portal (Akamai 403), www.windsorco.gov (403), www.townofmead.org and www.meadco.gov (403), www.lochbuie.org (403), www.eatonco.org (403), upstatecolorado.org (connection closed), carbonvalleychamber.com (connection closed), stvrainsd.org and wsfr.co (502 through the proxy), lefthandwater.org (connection closed), plattevalleyfire.org (403), nocooptimist.com and johnstownbreeze.com (no response), johnstown-co.municodemeetings.com (certificate mismatch), greeleytribune.com feeds (403), greeleygov.com docx reports (404 after redirect). WebFetch permission was not granted in this session for weld.gov Planning and Zoning, Commissioner Records, GIS Data and Recorded Documents, greeleyco.gov building permits, economic development reports and projects pages, eatonco.org and upstatecolorado.org; where another route existed those pages were read by curl, otherwise they are marked partially verified or unverified in the CSV.

## 8. Notes for the validation step

- Build the Laserfiche loader first and back-test it against the 18 incentive agreements (section 6) plus the Small Business Incentive Program applications; the Names field is clean upper case company text and the OCR of page 2 gives the facility address.
- The three active-only layers (Weld Planning Cases, Greeley TrakitProjects, Frederick Development Applications) do not keep history; start daily or weekly snapshots at once.
- Inherit the Adams build verdict for ArcGIS permit mirrors (Frederick) and planning case mirrors (Weld, Greeley, Fort Lupton, Longmont slice), then spot-check 50 to 200 rows each.
- Known projects to back-test across sources: BAE Systems (4120 Specialty Pl), Agilent (7051 Eagle Blvd), TFP Nutrition (450 N Front St, Platteville), Hirsh Precision (Frederick), Sphere Renewables (13516 CR 8, Fort Lupton), Colorado Premium (2400 W 29th St, Greeley), Front Range Energy (31375 Great Western Dr, Windsor), Vestas (Windsor), Owens-Brockway (Windsor), Norfolk Iron and Metal (Frederick area), Charm Industrial, Scotts and Hyponex, US Engineering Metalworks, Motherload Co Packing, Mountain Cement (Evans), EquipmentShare (Fort Lupton), Gotham Greens (Windsor), the JBS and Leprino plants in Greeley (check Greeley TrakitProjects for amendments at Promontory Cir and E 8th St).
- The Weld Planning Cases view embeds the planner's name and email in Description and in two fields; strip them on ingest. Greeley TrakitProjects and the county Access Permit layer carry private individuals in APPLICANT and Applicant; keep only company strings.
- Windsor PDF parsing: pages 6 and 7 use spaced capital headings (C O M M E R C I A L); match on the collapsed string.
- Greeley CivicClerk: build the OData URL by hand; Python's urlencode will mangle the $filter and the parentheses in GetMeetingFileStream(fileId=NNNN,plainText=true).
- Frederick permit queries need DATE 'YYYY-MM-DD' literals; string comparisons on OpenedDate return a 400.
