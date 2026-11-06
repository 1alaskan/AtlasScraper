# Weld County validation notes, group `county`

Tested 2026-11-05 and 2026-11-06 from the cloud shell, user agent `step3-research-validation/1.0`, one request a second. Ground truth: `ground_truth_weld_extract.csv` (6 projects: C34 Colorado Premium, C35 Hirsh Precision, C36 Sphere Renewables, X26 Agilent, X27 Microvast (county unconfirmed, shown separately), X28 TFP Nutrition). Matches are in `matches_county.csv`. Raw OCR text of the 18 agreements is in `raw/lf_<document id>.txt`.

## Sources tested and endpoints

| Rank | Source | Endpoint used |
|---|---|---|
| 1 | Weld BOCC Laserfiche WebLink, Commissioner Records template | `https://minutes.weld.gov/WebLink/` : GET `Welcome9.aspx?repo=CTBIMAGES` for the session cookie; POST `SearchService.aspx/GetSearchListing` (payload `repoName, searchSyn, startIdx, endIdx, getNewListing, searchUuid`); POST `FolderListingService.aspx/GetDocumentInfo` (`dId`) for page counts; POST `DocumentService.aspx/GetTextHtmlForPage` (`documentId, pageNum, showAnn, searchUuid`) for OCR text |
| 2 | Planning Cases for Development Activity Map (active view) | `.../Planning_Cases_for_Development_Activity_Map_view/FeatureServer/0/query` |
| 7 | Site Plan Review recorded cases | `.../Site_Plan_Review_open_data/FeatureServer/0/query` |
| 4 | Assessor Property Sales points | `.../Sales_Point_open_data/FeatureServer/1/query` |
| 12 | Assessor Ownership table | `.../Ownership2/FeatureServer/17/query` |
| 15 | Access Permit points | `.../Weld_Accela/FeatureServer/1/query` |
| 13, 41 | Accela Citizen Access (legacy) and Accela Public Portal | terms check only; one CapDetail sample |

All ArcGIS layers are on `https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/`.

## Assumptions

- Record date for Laserfiche is the `Hearing Date` template field (the BOCC approval date). Several packets also contain an earlier internal "pass-around review" sheet with its own date (for example Colorado Premium 2023-05-30, Airxcel 2023-05-30, Owens-Brockway 2023-07-06, TFP Nutrition 2024-06-25) and the agreement text carries its own execution date. Those are noted but not used as the record date, because the document is not visible until it is filed with the hearing.
- Record date for Sales is `SALEDATE` (the deed date, not the recording date; `RECEPTIONNO` is given but the recording date is not a field).
- Record date for the SPR layer is `DATE_` (plat recording date). The Planning Cases view and the Ownership table have no date field. The Access Permit layer's `created_date` is populated only for 2,130 of 12,832 points (all 2016 to 2017); for every other point the permit year prefix (AP25-...) is the only time signal.
- Lead time is months before or after the first press story, never months before a compressor purchase.
- Addresses used for the back-test came from the ground truth where it gave one, otherwise from the OCR of the incentive agreement (Hirsh 4300 Godding Hollow Pkwy, Agilent 7051 Eagle Blvd, Microvast 31815 Great Western Dr). Those three addresses are therefore not independent of source 1; the sales and ownership hits for them confirm the address rather than discover it.
- The Weld AGOL items all carry the same license line; the brief asked for it to be quoted, not decided. See the license section.

## Rank 1: Weld BOCC Laserfiche WebLink, Tax Incentive Agreements and Commissioner Records

**Coverage: 5 confirmed, 1 possible, of 6 (X27 Microvast confirmed, shown separately; X26 Agilent possible under rule 4).** Every one of the six projects has a 30-11-123 Tax Incentive Agreement whose `Names` field carries the company and whose OCR text carries the facility street address.

Lead times (Hearing Date minus earliest press date):

| Project | Document | Hearing Date | Press date | Lead (months) | Facility address quoted from OCR |
|---|---|---|---|---|---|
| C34 Colorado Premium | 20231862 | 2023-07-05 | 2024-02-05 (FALLBACK) | -7.06 | "Taxpayer's Facility at 2400 29th Street, Greeley, CO" (OCR drops the W) |
| C35 Hirsh Precision | 20220470 | 2022-02-07 | 2022-02-23 | -0.53 | "Taxpayer's Facility at 4300 Godding Hollow Pkwy, Frederick, CO 80504" |
| C36 Sphere Renewables | 20223348 | 2022-12-05 | 2024-06-14 | -18.30 | "Taxpayer's Facility at 13516 CR 8, Fort Lupton, CO" |
| X26 Agilent (possible) | 20223599 | 2022-12-28 | 2023-01-09 | -0.39 | "Taxpayer's Facilities at 7051 Eagle Boulevard, Fredrick, CO 80530", equipment placed in service 2023 to 2027 |
| X27 Microvast (separate) | 20232050 | 2023-07-19 | 2023-07-11 | +0.26 | "Taxpayer's Facility at 31815 Great Western Drive, Windsor, CO" |
| X28 TFP Nutrition | 20242850 | 2024-10-28 | 2025-11-17 | -12.65 | "Taxpayer's Facility at 450 N. Front Street, Platteville, Colorado" |

Five of six fired before press (Microvast 8 days after). Four of the six records predate the 2024-01-01 scrape window (C34, C35, C36, X26); only TFP (2024-10-28) is inside it. All are in window under rule 4. A second Colorado Premium record, tax abatement petition 20233607 (2023-12-11), is `possible` because it concerns the older 2nd Ave plant's personal property account.

Every Tax Incentive Agreement since 2022-01-01, found by `{[Commissioner Records]:[Notes]="*TAX INCENTIVE*"} & {[Commissioner Records]:[Hearing Date]>="1/1/2022"}` (23 hits, of which 5 are Section 179D energy deduction forms for county buildings and are not incentives). The 18 agreements, with the address from OCR:

| Document | Hearing Date | Names | Facility address (OCR) | Pages |
|---|---|---|---|---|
| 20220249 | 2022-01-17 | GG Colorado II LLC (Gotham Greens) | Great Western Industrial Park, Lot 15, Windsor | 5 |
| 20220438 | 2022-01-31 | Colorado Stud Company | 850 and 910 Lone Tree, Nunn | 5 |
| 20220470 | 2022-02-07 | Hirsh Precision Products | 4300 Godding Hollow Pkwy, Frederick | 5 |
| 20223348 | 2022-12-05 | Sphere Renewables | 13516 CR 8, Fort Lupton | 5 |
| 20223525 | 2022-12-19 | Norfolk Iron and Metal Company | 31825 Great Western Drive, Windsor | 5 |
| 20223599 | 2022-12-28 | Agilent Technologies | 7051 Eagle Boulevard, Frederick | 6 |
| 20231861 | 2023-07-05 | Airxcel Inc / Aqua-Hot Heating Systems | 7755 Miller Drive, Frederick | 18 |
| 20231862 | 2023-07-05 | K2D Inc / Colorado Premium Foods | 2400 W 29th Street, Greeley | 18 |
| 20232050 | 2023-07-19 | Microvast Energy Inc | 31815 Great Western Drive, Windsor | 16 |
| 20232178 | 2023-07-31 | Owens-Brockway Glass Container | 11133 Eastman Park Drive, Windsor | 15 |
| 20242850 | 2024-10-28 | Texas Farm Products / TFP Nutrition | 450 N Front Street, Platteville | 16 |
| 20242851 | 2024-10-28 | North American Machines of Colorado / TruLog Siding | 20684 Niobrara Blvd, LaSalle | 15 |
| 20251360 | 2025-05-19 | Charm Industrial Inc | 2290 S Rollie Avenue, Fort Lupton | 6 |
| 20251988 | 2025-07-14 | The Scotts Company / Hyponex | 1338 County Road 39, Brighton | 16 |
| 20252178 | 2025-08-04 | EcoMod LLC | 22303 I-76 Frontage Road, Hudson | 15 |
| 20262236 | 2026-09-02 | US Engineering Metalworks (with Upstate Colorado) | 390 Mountain View Road and 510 Basher Drive, Johnstown | 18 |
| 20262237 | 2026-09-02 | Motherload Co Packing LLC (with Upstate Colorado) | 560 Dahlia Street, Hudson | 13 |
| 20262355 | 2026-09-16 | BAE Systems Space and Mission Systems (Project Mercury) | 4120 Specialty Place, Longmont (Weld County) | 20 |

The 2022 agreements are 5 or 6 pages (resolution plus agreement). From mid 2023 the packets run 13 to 20 pages because the Finance "pass-around review" sheet, the Upstate Colorado request letter and the commissioners' email approvals are filed with the agreement; the agreement itself starts on page 2 to 8, so the address must be found by regex over all pages (`Facility at ...`), not by reading page 2. The `thumbnailPageCount` in search results is capped at 5; `GetDocumentInfo` gives the true count. Two 2026 agreements (US Engineering, Motherload) no longer carry "30-11-123" in the Notes field, so the search should use "TAX INCENTIVE" in Notes rather than the statute. `Names` is clean upper case and can hold two parties separated by a newline.

Noise sample (all Commissioner Records by Hearing Date): September 2025 had 260 records, of which 0 were incentive agreements (50 AGRMT of all kinds, 14 CORESP, 12 PUBLIC, 12 CONTRACT, the rest warrants, appointments, minutes, oil and gas, land use). March 2026 had 300 records, 0 incentive agreements (50 AGRMT, 25 CORESP, 21 CONTRACT, 18 PUBLIC). So the unfiltered stream is roughly 99.5 percent noise for this purpose (18 agreements in 57 months against roughly 280 records a month), but the Notes field filter removes it exactly. Two side streams worth keeping from the same template: the `PUBLIC` DocCode files CDPHE Air Pollution Control Division permit notices with the operator in Names (12 in September 2025, 18 in March 2026, almost all oil and gas, but Mountain Cement 2025-07-21 and Leprino 2026-03-30 appear), and the land use DocCodes (USR, COZ, ZPAG, SPR) record the BOCC action on county planning cases with the applicant in Names.

Join quality: `Names` (company) is the match key; the facility address comes only from OCR. No parcel or account number in the template, but the OCR address joins to the Ownership table situs fields (done above for every agreement). The source carries the company name in every record.

Access: no robots.txt (404). JSON services answered with a session cookie from one GET of the home page; no login. The full text search (`LF:Basic`) was not used. Portal disclaimer (from discovery) is liability only. Hearing Date is a template field so date range searches work in seconds.

**Verdict: build** (back-tested). 6 of 6 projects found by company name with a street address in OCR, 5 of 6 before press, median lead about 4 months and up to 18 months; the 18 agreements since 2022 also cover 12 projects the ground truth missed. Filter on Notes containing TAX INCENTIVE (not the statute number), OCR every page, and snapshot new meeting folders weekly.

## Rank 2: Weld County Planning Cases for Development Activity Map (active only)

This layer carries no dates and no address field, so it cannot score lead time and is treated as undated. 96 active cases on 2026-11-05: USR 48, ZPAG 24, SPR 18, COZ 4, SIF 2; status Under Review 57, Conditionally Approved 25, Under Construction 14.

Sample classification of all 96 by Title and Description: utility and energy (solar, wind, BESS, substations, water, injection well, telecom) 21; trucking, outdoor and RV storage, junkyards, car dealer, gas station, landscaping 21; kennels, event centers, golf, winery, agritourism 17; industrial buildings or process uses (warehouse and office SPRs in I-2 and I-3, two gas compressor stations, a data center USR, hemp processing, seed distribution, lumberyard, coffee roaster, Empire Industrial Business Park) 13; contractor shops and ag support 12; mining 7; change of zone (three to I-2 or I-3, one to C-3) 4; other 1. Plainly non-industrial share: about 70 percent (67 of 96); about 18 percent (17) are candidate pneumatic users.

Coverage: 0 of 6. All six ground-truth sites are inside towns (Greeley, Frederick, Windsor, Platteville) or finished before the snapshot (Sphere at 13516 CR 8), so none could be present. Supplementary: EcoMod's SPR25-0010 is in the layer (Under Construction); its Epermit link resolves to the Accela record whose work location is 22303 I-76 Frontage Rd, Hudson, the address in the incentive agreement.

Join quality: Title sometimes names the company (Gilbert Contracting, Taelor Solar, Empire Business Park); otherwise only the use type. Join to the Accela record is by the `Epermit` capID link; join to the SPR layer is by case number. `Planner` and `PlannerEmail` fields and the Description tail hold a county employee's name and email and were not copied.

AGOL license (item 538680ec32cf468a9353bf53716c0ca1, owned by a county staff account rather than the WeldCounty org account, access public), `licenseInfo`: "This product has been developed solely for internal use only by Weld County. The GIS database, applications, and data in the product is subject to constant change and the accuracy and completeness cannot be and is not guaranteed. The designation of lots or parcels or land uses in the database does not imply that the lots or parcels were legally created or that the land uses comply with applicable State or Local law. UNDER NO CIRCUMSTANCE SHALL ANY PART THE PRODUCT BE USED FOR FINAL DESIGN PURPOSES. WELD COUNTY MAKES NO WARRANTIES OR GUARANTEES, EITHER EXPRESSED OR IMPLIED AS TO THE COMPLETENESS, ACCURACY, OR CORRECTNESS OF SUCH PRODUCT, NOR ACCEPTS ANY LIABILITY, ARISING FROM ANY INCORRECT, INCOMPLETE OR MISLEADING INFORMATION CONTAINED THEREIN." `accessInformation`: "Weld County Government".

**Verdict: build** (inherited + spot-checked). Same type as the Adams planning case mirrors; holds no ground-truth project because all six sit in towns; undated, so start a daily snapshot now and date each case by first appearance; keep only the 13 industrial and 4 COZ style cases.

## Rank 7: Weld County Site Plan Review recorded cases

435 polygons, 418 with a `DATE_`, from 1982 to 2026-09-16 (one 1899 placeholder). Zoning: I-3 134, C-3 134, PUD 71, I-2 15, I-1 10. `CASE_NAME` is just the case number; there is no description, applicant, owner or address field, so the only join is `PARCEL__` (12 digit assessor parcel, zero padded inconsistently; 8 rows have parcel 0).

Coverage: 0 of 6 by parcel (the six sites are in towns, and the unincorporated Sphere parcels 147120102001 and 147120102006 carry no SPR). Supplementary: EcoMod SPR25-0010 recorded 2026-02-04 on parcel 147302001001 (I-3, 9.13 ac), six months after its incentive agreement; TruLog 3AMSPR25-18-0004 recorded 2026-01-21 on parcel 105723201007 (I-3, 4.55 ac), 15 months after its agreement, with an earlier amendment 1AMSPR23-17-0015 (2023-10-18) on the adjacent parcel. Both fire after the incentive record, as the discovery notes expected.

Noise sample by month: 2025 had 10 recordings and 2026 (to September) 16. September 2025: 0. March 2026: 1 (1AMSPR24-88-111, C-3, 8.8 ac). Of the 26 recordings since 2025-01-01, 16 are in I-1, I-2 or I-3 zones, 6 in C-3, the rest PUD or blank. The stream is small enough to review by hand; the non-industrial share depends on the zoning filter (C-3 and PUD rows are storage yards, dealerships and retail).

License: item 957de6a1420c4d9095cec5ac185d33e4, owner WeldCounty, public; same `licenseInfo` text as rank 2, `accessInformation` "Weld County Government".

**Verdict: build** (inherited + spot-checked). Dated, parcel keyed, roughly one recording a month, and the two supplementary projects on county land both appear; but it lags the incentive agreement by 6 to 15 months and carries no name, so it only works joined to the Ownership table on parcel and to the active cases layer for the description.

## Rank 4: Weld County Assessor Property Sales points

243,609 sales with `SALEDATE`, `SALEPRICE`, `GRANTOR`, `GRANTEE`, `DEEDCODE`, `RECEPTIONNO`, `ACCOUNTNO`, `PARCELNO`, `PROPERTYADDRESS`, `PROPERTYCITY`, `PROPERTYTYPE`, `OCCCODEDESCRIPTION1..3`, `TOTALIMPSF`, `LANDNETACRECOUNT`, `BLTASYEARBUILT`. Covers every town in the county.

**Coverage: 2 confirmed (X28 TFP, and X27 Microvast shown separately), 3 possible (C34, C36, X26), 1 none (C35), of 6.**

| Project | Sale | Grantor to grantee | Lead (months) | Class |
|---|---|---|---|---|
| C34 Colorado Premium | 2021-12-22, $8.0M, 2400 W 29th St Greeley, 171,725 sf | T&B Greeley LLC to an individual (Ownership now shows JKL Development LLC, business name TELETECH/COLORADO PREMIUM) | -25.46 | possible (address only) |
| C35 Hirsh Precision | no in-window sale; 2018-06-15 sale to STAG Industrial (landlord) is out of window | | | none |
| C36 Sphere Renewables | 2022-10-04, $1.46M, 13516 County Road 8, 8.39 ac residential on ag | Villano Brothers Family Investments LLC to Harbour Asset Management LLC | -20.34 | possible (address; grantee differs; Sphere's P account sits on the same parcel) |
| X26 Agilent | 2021-10-25, $1.98M, 4951 Carbide St Frederick, 10.01 ac vacant | Black Diamond Real Estate to Agilent Technologies Inc | -14.49 | possible (right company, adjacent parcel, existing plant) |
| X27 Microvast | 2023-07-06, $11.0M, 31815 Great Western Dr Windsor, 99,536 sf warehouse | Hexcel Corporation to Microvast Inc; exit 2024-08-29 $10.2M to The Bar S U Inc | -0.16 (exit +13.63) | confirmed |
| X28 TFP Nutrition | 2023-06-09, $4.12M, 450 Front St Platteville, 3.5 ac | JD Heiskell Holdings LLC to TFP Nutrition | -29.30 | confirmed |

Five of six have an in-window sale and all five fired before press (0.2 to 29 months). All five are before the 2024-01-01 scrape window. Supplementary sales found through the Ownership table's `SALEDT` (same CAMA data): BAE Systems 2026-10-05 $30.0M at 4120 Specialty Pl (18 days before press, 19 days after the incentive agreement); Norfolk Iron and Metal 2022-02-24 $5.0M at 31825 Great Western Dr (10 months before its agreement); Aqua-Hot 2022-07-26 $6.5M at 7755 Miller Dr (11 months before); GG Colorado 2021-12-23 $2.56M at 1700 CR 23 Windsor (25 days before); EcoMod's EM Property LLC 2025-06-18 $3.25M (7 weeks before); Rollie LLC 2022-05-12 $1.02M at Charm's 2290 S Rollie Ave (3 years before). In 6 of the 9 cases with both records the land purchase precedes the incentive agreement.

Noise sample: September 2025 had 925 sales, of which 499 Residential, 47 manufactured homes, 33 townhouse, 28 condo, 16 Commercial by `PROPERTYTYPE`; by occupancy 9 Warehouse, 3 Outdoor Storage, 3 Quonset, 2 Retail, 2 Office. March 2026 had 850 sales: 559 Residential, 51 manufactured homes, 10 Commercial; by occupancy 10 Warehouse, 2 Equipment Building, 1 Equipment Storage, 7 Retail. So 98 to 99 percent of the raw stream is plainly not industrial, but `OCCCODEDESCRIPTION1` in (Warehouse, Manufacturing, Equipment Building, Outdoor Storage, Quonset) plus `TOTALIMPSF` or `LANDNETACRECOUNT` thresholds cuts it to about 10 to 15 rows a month, and most of those are small warehouse condo units (1,000 to 3,000 sf at Stagecoach Rd, Mt Elbert Ave, Imperial St) that a 10,000 sf or 3 acre floor removes. Grantees in the filtered set are mostly LLCs that need resolving through state registrations.

Join quality: `PROPERTYADDRESS` plus `PROPERTYCITY` (street number and name formatted consistently in upper case, county roads as COUNTY ROAD 8), `PARCELNO`, `ACCOUNTNO`, and `GRANTEE` and `GRANTOR` company names. `GRANTEE` can hold a private individual (it did for Colorado Premium); store only entity names.

Why this layer does better than Denver's property sales (park verdict): Denver's layer gave a sale and price without the parties or the use, so an industrial purchase could not be told from a portfolio transfer and the buyer could not be named. Weld's layer carries `GRANTOR`, `GRANTEE`, `OCCCODEDESCRIPTION`, `PROPERTYTYPE`, building size, acreage and year built, so an operating company buying a warehouse or acreage is identifiable in one row (Microvast, TFP, BAE, Norfolk, Aqua-Hot all appear by name), and it covers every town in the county including the Great Western Industrial Park and Frederick, which the county planning layers do not. It also records the exit (Microvast's resale) which no other source did.

License: item c85fc41cf189402caf5dc4c86ab4b646, owner WeldCounty, public; `licenseInfo` is the same text as rank 2 wrapped in a span tag; `accessInformation` "Weld County Government".

**Verdict: build** (back-tested). 5 of 6 projects have an in-window sale, all before press, 2 confirmed by company name plus address; grantee, occupancy and size fields make the industrial filter possible, unlike Denver's layer.

## Rank 12: Weld County Assessor Ownership table, Personal Property accounts

Spot-check only. The table carries `ACCOUNTNO`, `NAME`, `BUSINESSNAME`, `ACCTTYPE` (Personal, Leasing, Industrial, Commercial, Possessory, Agricultural...), situs fields and, on real accounts only, `SALEDT`, `SALEP`, `DEEDTYPE`, `RECEPTION_NO`. **It carries no date that says when an account was created; it is undated.** The account number sequence (P91xxxxx newest) is the only ordering.

P accounts at the six addresses: C34 yes (P9104866 and P9109619 K2D Inc / Colorado Premium Foods at 2400 W 29th St); C35 no (no Hirsh P account at 4300 Godding Hollow Pkwy; the landlord's Industrial real account carries BUSINESSNAME HIRSH PRECISION PRODUCTS INC, and three Leasing accounts of equipment lessors sit at the address); C36 yes (P9110302 Sphere Renewables LLC at 13516 County Road 8); X26 yes (P9104657 Agilent Technologies, "Agilent NASD Facility" at 7051 Eagle Blvd, the 2018 plant); X27 no (no Microvast account remains; Schlosser Signs now); X28 no (only a bank's P account at 450 N Front St; the Industrial real account is in TFP Nutrition's name). So 3 of 6 have a P account in the company's name, and the two newest plants (TFP opened January 2026, Microvast cancelled) do not, which fits a declaration lag of a year or more.

Supplementary P accounts found by name: Motherlode Co-Packing (560 Dahlia St Hudson), US Engineering Metalworks (390 Mountain View Rd Johnstown; the new 510 Basher Dr parcels are in USEREH Johnstown II LLC with business name US ENGINEERING), EquipmentShare (15549 Highway 52 Fort Lupton and 4037 Salazar Way Frederick), GG Colorado II / Gotham Greens (1700 County Road 23 Windsor), Colorado Stud (900 Lone Tree Cir Nunn), Charm Industrial (2360 S Rollie Ave), TruLog (20684 Niobrara Blvd), Front Range Energy (31375 Great Western Dr), Owens-Brockway (11133 Eastman Park Dr, with Linde and five equipment lessor accounts). Scotts has no P account yet; the real account's business name is SCOTTS MIRICLE GRO.

Join quality: situs `STREETNO`, `STREETNAME`, `STREETSUF`, `LOCCITY` (street name holds the direction for some rows, "W 29TH" against "29TH"), `PARCELNB`, `NAME` and `BUSINESSNAME`. The `BUSINESSNAME` on a real account names the tenant even when the owner is a REIT, and the Leasing account type lists equipment lessors at a site, which is itself an equipment-in-place tell.

License: item fc83c33f01c441f4b26e60f1f27a5f11, owner WeldCounty, public; same `licenseInfo` text; `accessInformation` "Weld County Government".

**Verdict: build** (spot-checked only). Undated and lagging, so it cannot score lead time, but it is the address and tenant resolver for every other Weld source (incentive OCR address to parcel, SPR parcel to owner and business name) and a monthly diff on P account numbers will date new equipment accounts from now on.

## Rank 15: Weld County Access Permit points

12,832 points. `Type`: Residential 4,990, Oil and Gas 3,331, Agriculture 1,295, Temporary 1,106, Small Commercial 815, TO BE CLOSED 663, Large Commercial 330, Industrial 179, Equipment Crossing 73, Commercial 30, Subdivision 15. `created_date` is populated only for 2,130 points, all 2016 to 2017; every other point is undated apart from the permit year in the number (AP26-00202 was the highest seen). There is no address field; `Applicant` holds the landowner (often a private individual) with a "c/o company" tail, `Notes` sometimes cites the USR, SPR, RECX or CMN case, and `ACALink` opens the Dev Review record.

Coverage: 0 of 6. No applicant name hit for any project entity and no point within 500 m of any of the six parcels (the five town sites would not have county access permits; Sphere's CR 8 frontage has none in the layer). Supplementary: TruLog's owner T&R Properties LLC has AP20-00500 (Large Commercial, "Existing. Shared. 1AMSPR20-18-0004") 197 m from the parcel; Norfolk Iron and Metal has AP21-00195 (Industrial) at a different location from its Windsor plant; GG Colorado's site is 257 m from AP18-00548 (Great Western Industrial Park, 2018). Noise sample by `created_date` is impossible for September 2025 and March 2026 (zero dated rows after 2017); by permit year 2025 the layer holds the Industrial and Large Commercial types the discovery notes listed, but they cannot be put in a month.

License: item 80c14163fbc945e2a462d32982fdcf7c, owner WeldCounty, public; same `licenseInfo` text; `accessInformation` is empty.

**Verdict: park** (spot-checked only). Undated after 2017, no address, no ground-truth hit, and the applicant field is a private landowner; the two supplementary hits were found only because the owner entity or case number was already known from another source. Revisit if the county starts populating `created_date`.

## Ranks 13 and 41: Accela portals, terms check only

- `https://aca-prod.accela.com/robots.txt` and `https://weld-prod.accela.com/robots.txt`: both 404 (no robots file).
- Legacy ACA (rank 13): `WELD/Default.aspx` redirects to an Angular login panel (`AngularUI/CommunityView/fa-login-panel?inLegacyUI=true`); `Cap/CapHome.aspx?module=Planning` returns the search form (218 KB) with no terms, disclaimer, privacy or copyright text on the page. The only disclaimer link is `Cap/CapApplyDisclaimer.aspx` on the "Create an Application" path, which is behind login and was not opened. Record detail pages carry no terms text either. One sample `CapDetail.aspx` GET (SPR25-0010, capID 25CAP-00000-002IU) returned 272 KB of HTML with record status (Recorded), Work Location (22303 I-76 FRONTAGE RD HUDSON CO 80642), Project Description, Application Information (description of use, general location, referral due date 09/05/2025, water and sewer), reception number 5081163 and plat recording date 02/04/2026, plus tabs for Related Records, Attachments, Conditions and Inspections. The page embeds a county referral contact's name and email, which must not be stored. Treat as a manual or single-record lookup keyed by the capID in the Planning Cases and Access Permit layers; no crawling, no date search (ASP.NET postbacks).
- New Accela Public Portal (rank 41): `portal/core/index` returns a 42 KB SPA shell with no terms text and no public search route; account required to do anything. Not tested beyond that.

## Not tested, and why

- Rank 16, Assessor Account Inventory and Improvements tables: undated reference universe (year built and square footage change yearly); use as the facility denominator, not a signal.
- Rank 17, Tier II chemical facilities: undated annual reference layer; a new filer appears the spring after start up.
- Rank 33, Zoning polygons: undated reference layer for filtering.
- Rank 35, Nonconforming Use cases: undated legacy reference layer.
- Rank 36, WOGLA points: oil and gas well pads only; not a compressed air signal.

## AGOL license text

All five Weld County items tested (538680ec32cf468a9353bf53716c0ca1 Planning Cases view, 957de6a1420c4d9095cec5ac185d33e4 Site Plan Review, c85fc41cf189402caf5dc4c86ab4b646 Sales Point, fc83c33f01c441f4b26e60f1f27a5f11 Ownership, 80c14163fbc945e2a462d32982fdcf7c Weld Accela) are shared with `access: public` and carry the identical `licenseInfo` quoted in full under rank 2 ("This product has been developed solely for internal use only by Weld County. ... NOR ACCEPTS ANY LIABILITY, ARISING FROM ANY INCORRECT, INCOMPLETE OR MISLEADING INFORMATION CONTAINED THEREIN."). `accessInformation` is "Weld County Government" on four and empty on the Weld Accela item. Not decided here; reported as asked.

## Corrections the test suggests to the ground truth (not applied)

- X27 Microvast: county can be set to Weld, confirmed. The county incentive agreement names the facility at 31815 Great Western Drive, Windsor, and the assessor records the parcel (080726103003) in Weld County. Add the address. The exit sale of 2024-08-29 (Microvast Inc to The Bar S U Inc, $10.2M) is a dated cancellation milestone seven months before the 10-K disclosure.
- C35 Hirsh Precision: street address 4300 Godding Hollow Pkwy, Frederick, CO 80504 (agreement OCR; also 4356 Godding Hollow on the second STAG parcel). The incentive is confirmed: agreement 20220470 approved 2022-02-07, 50 percent of personal property tax for equipment placed in service in 2022, ten year term.
- X26 Agilent: street address 7051 Eagle Blvd, Frederick, CO 80530. The incentive is confirmed: agreement 20223599 approved 2022-12-28 for equipment placed in service 2023 to 2027. Agilent also bought the adjacent 10 ac at 4951 Carbide St on 2021-10-25, which is a candidate earlier milestone for the expansion.
- C34 Colorado Premium: the only recorded sale at 2400 W 29th St is 2021-12-22 ($8M, to an individual; the Ownership table shows JKL Development LLC as owner), so "land purchase 2022" should probably read "site purchased December 2021 by a related entity; K2D holds the personal property accounts". The incentive agreement (2023-07-05) is an earlier dated milestone than the 2024-02-05 fallback press date and would replace the FALLBACK label if a county record is allowed as a milestone.
- C36 Sphere Renewables: the 13516 CR 8 parcel was bought 2022-10-04 by Harbour Asset Management LLC (not Sphere); the incentive agreement of 2022-12-05 is the earliest dated company milestone, 18 months before the first press mention.
- X28 TFP Nutrition: the site was bought 2023-06-09 (JD Heiskell Holdings LLC to TFP Nutrition, $4.1M), which dates the "J.D. Heiskell" WQCD permittee note and gives a land purchase milestone 29 months before press.

## Not finished

- Agreement OCR was regex-parsed for the "Facility at" phrase; the phase caps and dollar amounts were not extracted (BAE's $13.77M Phase I cap was read at discovery but not re-parsed here).
- The Small Business Incentive Program applications (APPL DocCode, 13 seen since 2022, almost all sole proprietors and kennels) were listed but not back-tested; none matched a project.
- The SPR layer's pre-2022 rows were not joined to the Ownership table to estimate how many recordings are expansions of operating industrial sites.
- Nothing was committed to git.
