# Weld County step 3 validation notes: group `tri_towns` (Frederick, Firestone, Windsor)

Date of test: 2026-11-05. Agent user agent `step3-research-validation/1.0`, one request a second, standard-library Python plus curl and pdftotext. Raw downloads in `step3-validation/weld/raw/tri_towns/` (git-ignored). Companion file: `matches_tri_towns.csv`.

## Sources tested and endpoints

| Rank | Source | Endpoint used | Result |
|---|---|---|---|
| 3 | Frederick Accela Building Permits layer | `https://gis.frederickco.gov/arcgis/rest/services/Accela_Building_Permits/FeatureServer/3/query` (table layer, 19,578 rows, OpenedDate 1890-01-02 (bad) to 2026-11-05) | tested, back-tested on X26 and C35 |
| 6 | Frederick Development Applications Under Review layer plus What's Developing page | `https://gis.frederickco.gov/arcgis/rest/services/Development_Applications/FeatureServer/0/query` (22 rows) and `https://frederickco.gov/855/Whats-Developing` | tested, spot-checked all records |
| 26 | Frederick CivicClerk OData API | `https://frederickco.api.civicclerk.com/v1/Events?$filter=...` and `/v1/Meetings/GetMeetingFileStream(fileId=N,plainText=true)` | light test only |
| 10 | Firestone Accepted Development Review Applications PDF | `https://www.firestoneco.gov/DocumentCenter/View/6086` (resolves to `2026-10-16-QJ-Legis-Dev-Review-Apps`) | tested, one PDF (no archive reachable) |
| 11 | Windsor monthly Building Permit Reports | `https://co-windsor3.civicplus.com/414/Building-Permit-Reports` (listing page loaded; PDFs not downloaded) | blocked, see below |
| 18 | Windsor Development Activity StoryMap | `https://www.arcgis.com/sharing/rest/content/items/5891ebaec0c64a50ae8ff9b25560f244/data?f=json` | tested, spot-checked all 66 text nodes |
| 28 | Firestone Development Projects map | web map `e4168bec592d41eea6c36e244e76a152` resolves to hosted layer `https://services8.arcgis.com/AqMpORZxzXMXwPCf/arcgis/rest/services/service_fac9eddf498043fa936b58f122d2001d/FeatureServer/0` (48 rows) | spot-checked (turned out to be a plain feature layer) |
| 24 | Windsor Agenda Center RSS | not fetched | not tested |

## Assumptions

- Ground-truth projects in this group: C35 Hirsh Precision (Frederick, no street address in the ground truth) and X26 Agilent (Frederick, 7051 Eagle Blvd per the discovery notes; the ground truth gives no street address). X27 Microvast (Windsor, county unconfirmed) is reported separately. No ground-truth project sits in Firestone.
- Press dates used: X26 2023-01-09 (announcement), C35 2022-02-23 (announcement), X27 2023-07-11 (announcement). None is a FALLBACK row.
- Window for X26: 36 months before press (2020-01-09) to 12 months after the latest milestone (planned completion 2026-12, so 2027-12). All X26 records found fall inside it.
- Rule 4 applied to X26: Agilent's plant at 7051 Eagle Blvd opened in 2018, so an in-window record at the site is `possible` unless its text names the Endeavor project or the new manufacturing building.
- Frederick's permit layer is an Accela mirror on ArcGIS Enterprise, the same type as the Adams County and Thornton build sources, so the verdict basis is `back-tested` because X26 hits.
- The Frederick `FullAddress` field holds the applicant mailing address rather than the site on many pre-2022 HST-era rows (for example `C/O ...`, `PO BOX`, and a Santa Clara street for Agilent); the parcel field is the stable site key on those rows.
- Personal names: the Development Applications layer's `Email` field and the What's Developing page's planner column hold town staff names; neither is copied here.

## Rank 3: Frederick Accela Building Permits layer

**Coverage:** confirmed 1, possible 0 further projects, of the 2 ground-truth projects in Frederick (1 of 6 overall). X26 Agilent confirmed on four records naming Project Endeavor or the new manufacturing building; C35 Hirsh none.

**Lead-time list (X26, press 2023-01-09, OpenedDate):**

| Record | Opened | Class | Lead (months) | What it is |
|---|---|---|---|---|
| HST19052-2021-949 | 2021-10-04 | possible | -15.18 | three construction office trailers, same parcel (12100 Andrews Dr) |
| HST19356-2022-104 | 2022-02-16 | possible | -10.74 | grading 19,000 CY on the 7400 Eagle lot, applicant mailing address in Santa Clara |
| BLDG22-0065 | 2022-04-22 | possible | -8.61 | foundation permit, 7051 Eagle Blvd, no text |
| BLDG22-0558 | 2022-12-06 | possible | -1.12 | temporary power for construction trailers, 7400 Eagle |
| BLDG23-0036 | 2023-01-30 | possible | +0.69 | grading for Agilent 40,000 CY, 7051 Eagle |
| BLDG23-0110 | 2023-03-08 | confirmed | +1.91 | foundation for the Tank Farm, Project Endeavor |
| BLDG23-0143 | 2023-03-20 | confirmed | +2.30 | Endeavor construction trailer, 7400 Eagle |
| BLDG23-0146 | 2023-03-21 | confirmed | +2.33 | core and shell, new manufacturing building |
| BLDG23-1897 | 2023-09-06 | confirmed | +7.88 | interiors package, new manufacturing building |
| BLDG26-0380 | 2026-07-01 | possible | +41.69 | Area J equipment, piping and electrical in the existing building |

Before-press count: 0 confirmed, 4 possible (all generic records at the Agilent parcels, none naming the company). The first confirmed record came 1.9 months after the announcement and three weeks after the 2023-02-16 groundbreaking. Every X26 record except the 2026 ones predates the 2024-01-01 scrape window. Earlier Agilent permits (2021-04-13, Project Synergy; 2017 to 2020 core and shell, fit-out, cafe, fitness center) sit before the window and are noted only.

**C35 Hirsh Precision:** no row in `Description`, `Name` or `FullAddress` matches HIRSH, PRECISION, CNC, MACHIN, 65,000 or 65000 in 2021 to 2023 (the only machining hits are 2013 to 2020 rows for other shops). The layer has no applicant or owner field, so an unnamed tenant finish cannot be tied to Hirsh, and the ground truth gives no street address. Not guessed. Two observations for whoever supplies the address: only six Commercial New Construction permits were opened 2021 to 2023 in the whole layer (none a 65,000 sf building), and the layer holds tenant-finish permits for 4160 Busch Pl (2022-10-25 "tenant improvement work for the core and shell being constructed currently", 2023-06-30 east tenant fit-out) but not the core-and-shell permit itself, so the 2022 to 2023 commercial series in the mirror looks incomplete around the HST-to-Accela changeover.

**Noise sample (OpenedDate, query on the live layer):**

- September 2025: 36 permits. Residential mechanical 8, residential roofing 7, residential plumbing 6, sign 4, residential electrical 3, residential alteration 3, residential addition 2, residential new construction 1, commercial new construction 1 (Brakes Plus auto service), commercial plumbing 1 (water line). Plainly not industrial: 36 of 36 (100 percent).
- March 2026: 46 permits. Residential plumbing 12, residential mechanical 7, residential roofing 7, residential alteration 6, residential new construction 3, residential addition 3, residential electrical 1, residential solar 1, sign 1, temporary structure 1, commercial mechanical 1, commercial plumbing 1, commercial alteration 1, commercial new construction 1. Plainly not industrial: 43 of 46 (93 percent). The three worth a look: BLDG26-0137 interior improvements to 5,086 sf of work space at 3761 Eureka Way, BLDG26-0124 two unit heaters in a shop at 9250 Bruin Blvd, BLDG26-0173 modular substation control building for the Spindle BESS.
- For scale, 2021 to 2023 held 32 Commercial Alteration, 26 Commercial Electrical, 15 Commercial Accessory Structure, 10 Commercial Mechanical, 6 Commercial New Construction and 5 Commercial Foundation permits against about 1,700 residential ones.

**Join quality:** matched on `Description` text (company and project names appear there on the 2023 and 2026 Agilent rows), `FullAddress` (street number plus street) and `ParcelID`. The `Name` field on 2026 rows is a project title that sometimes repeats the company; there is no applicant, owner or contractor field and no valuation. Pre-2022 rows often carry the applicant mailing address in `FullAddress`, so parcel is the safer site key for history.

**Access notes:** no key, no robots.txt on the GIS host (404), `DATE 'YYYY-MM-DD'` literals required. The town's open data terms at `https://www.frederickco.gov/769/Terms-of-Use` say the user "can copy, distribute, transmit and adapt the data in this GIS catalog freely" with an "as is" disclaimer on accuracy and completeness. Not a Weld County AGOL item, so no county license line applies.

**Verdict: build** (back-tested). X26 confirmed on four permits that name the project or the new building, first at +1.9 months after press; the layer is daily, free and queryable, and the 2026 Agilent equipment permits show it carries capex at an existing plant. Weakness: no applicant field, so unnamed projects (Hirsh) cannot be tied without an address, and the 2022 to 2023 commercial series looks thin.

## Rank 6: Frederick Development Applications Under Review layer and What's Developing page

**Coverage:** X26 Agilent `possible` (OBJECTID 24, "Agilent Endeavor" site plan for a new manufacturing building and a new warehouse north of 7051 Eagle Blvd, I district, Documents folder DocumentCenter/Index/1259); C35 none. The layer has no date field of any kind (fields: Application_Type, Project_Type, Description, Project_Name, Zoning_Existing, Zoning_Proposed, Public_Hearing, Contact, Email, Documents), so it is undated and cannot score lead time.

**Dates:** the What's Developing HTML page does carry dates: an application submittal date on each "Applications Under Review" row and an approval date on each "Approved Applications" row, plus neighborhood meeting dates. The page and the layer disagree: the page lists 24 applications under review (submitted 2023-12-26 to 2026-09-28) and about 18 approved (2025-08-12 to 2026-07-15), and Agilent Endeavor is on neither list, while the layer still shows it among its 22 records. The layer looks stale relative to the page; the page is the better feed and the only one with dates.

**Spot-check of all 22 layer records:** residential plats, PUDs and rezones 8; auto dealer, vehicle storage and car wash 6 (one dealership listed twice); industrial or flex 8 (Agilent Endeavor; Park 4040 Replat B Lot 2 55,500 sf industrial flex building; Bear Industrial Park Lot 4 Block 2 Craft Solutions 7,506 sf light industrial; Golden Triangle Construction yard with 4,800 sf office; Flight Workspaces office and storage campus; Full Metal Iron storage yard expansion; Raspberry Hill Lot 11 grading; Bear Industrial Park fence variance). Industrial items on the page but not in the layer: Mile High Metal Works new 20,000 sf plus industrial building at 4501 Salazar Lane (submitted 2025-11-17), Meadowlark Business Park Filing 3 Replat C about 20,000 sf industrial building at 5520 Iris Parkway (2025-09-08; the permit layer's BLDG26-0585 22,476 sf building at 5520 Iris Parkway opened 2026-10-13, 13 months later), Raspberry Hill Lot 17 industrial warehouse and office at 8440 Raspberry Way (2025-03-24), Grantham Buildings 4 and 5 (two 4,400 sf light industrial, 2026-06-02), Forge X Workspaces four 10,000 sf light industrial buildings (neighborhood meeting 2026-06-22), Carbon Valley Rec maintenance building (2026-09-07). Non-industrial share of the page's under-review list: about 15 of 24 (residential, oil and gas well pads, schools, car washes, dealer parking, road paving).

**Join quality:** Project_Name and Description text only; the company name appears when the applicant is the end user (Agilent, Craft Solutions, Mile High Metal Works, Transwest, Stapp Toyota). Street address on the page's Location column; the layer has point geometry and a DocumentCenter folder link. No parcel.

**Access notes:** no key; the page is a plain CivicPlus HTML table (200 to a scripted GET). The layer's `Email` field and the page's planner column carry staff names; strip on ingest.

**Verdict: build** (inherited + spot-checked). Same type as the planning-case mirrors built in Adams; X26 appears by name but undated. Snapshot the HTML page (dated) at least weekly and the layer alongside it; treat the layer as a point-geometry supplement, not the feed.

## Rank 26: Frederick CivicClerk OData API

**Light test:** `Events` with a `startDateTime` range and `categoryName eq 'Board of Trustees'` returns 35 Board of Trustees events for 2025 (`$count=true` works; pages of 15 with `@odata.nextLink`; URL built by hand). Two packets streamed as plain text: fileId 703 (2025-04-08 meeting, 405 KB) and fileId 750 (2025-05-13, 306 KB). Neither mentions Agilent or Hirsh; an Events filter on `contains(eventName,'Agilent') or contains(eventDescription,'Agilent')` returns nothing. Items found in the sampled text: Resolution 25-R-32 approving a rezoning of Lot 1, Maplewood Subdivision Filing Two (land use); Resolution 25-R-26 awarding 2025 business assistance program funds under Ordinance 1127 (a town incentive line); membership dues to Upstate Colorado. No site plan or annexation item in the two packets. The portal starts in 2024, so the 2022 to 2023 Agilent and Hirsh approvals are out of reach here.

**Coverage:** 0 of 2 (no project in the sample). **Noise:** not sampled (agenda feed). **Join:** free text only.

**Verdict: park** (spot-checked only). The API works exactly as the Greeley pattern describes and the packets are plain text, so it can share the Greeley poller when that is built; nothing here beats the dated What's Developing page for Frederick land-use timing, and the business assistance resolutions would need parsing to be a signal.

## Rank 10: Firestone Accepted Development Review Applications PDF

**What was reached:** the current report only (DocumentCenter/View/6086, one page, dated 2026-10-16, 132 KB, text layer, `pdftotext -layout` parses it). No archive could be reached: the only link on the town site (Current Development Projects page) points to this single rolling document ID; the DocumentCenter listing is a React app that renders nothing server-side, and the host reset the connection when the app's script bundle was requested with the project user agent. I did not retry with a browser user agent, and I did not probe document IDs.

**Count:** 39 applications on the 2026-10-16 report (annexation 3, initial zoning 2, rezoning 1, preliminary plat 3, final plat 14, final development plan 16; the PUD, special review use and code amendment sections are empty). Accepted dates run 2022-04-06 to 2026-09-22. Non-residential: 18 of 39 (46 percent): two right-of-way items, one 5 acre annexation at 2010 Highway 119 (use not stated), one business park replat (Del Camino Junction 5th, the Porsche site), one three-lot non-residential replat (Firestone Community), and 13 of the 16 final development plans. Industrial applications: none. Closest to industrial: FDPA-25-019 Western Midstream 47-space off-site parking lot (Flatiron II PUD, accepted 2025-08-14) and FDPA-25-002 Fowler Kia 17,487 sf building addition at 10258 E I-25 Frontage Rd (2025-02-07). The rest are a Porsche dealership (35,893 sf), WinCo (84,000 sf), a fire station, restaurants, a credit union, a vet clinic, an oil change and a sidewalk.

**Join quality:** project name, free-text location (lot and block or address), file number, acreage, status. No parcel, no applicant.

**Access notes:** robots.txt on www.firestoneco.gov disallows only admin and search paths; no terms page found for the PDF; the site resets some scripted connections (the PDF itself and the HTML pages answered 200). Citizenserve permit link remains dead per discovery.

**Verdict: park** (spot-checked only). The parser is trivial and the report is dated and biweekly, but the current list holds zero industrial applications and the archive is unreachable, so there is nothing to back-test and little to pull. Revisit if an industrial FDP appears.

## Rank 11: Windsor monthly Building Permit Reports

**Blocked, not pulled.** `https://www.windsorco.gov/robots.txt` returns 403 to the project user agent (the whole canonical host refuses scripts, as discovery noted). The mirror host `https://co-windsor3.civicplus.com/robots.txt` answers 200 with `User-agent: *` `Disallow: /` (the only allowances are a named SEO crawler and Twitterbot on `/m/newsflash/`). The listing page itself loaded (200) and links 57 monthly PDFs from January 2022 to September 2026 (DocumentCenter/View/24838 through 29632). With the canonical host refusing and the mirror's robots forbidding all crawling, pulling 45 reports of about 7 MB each through the mirror would be a workaround of a refusal, which the brief rules out, so I stopped. X27 Microvast (county unconfirmed) and the supplementary Front Range Energy, Vestas, Owens-Brockway and Gotham Greens tests are therefore not done on this source; the monthly industrial and commercial counts were not produced. Discovery's three sample reports (Sept 2026, Dec 2024, Dec 2023) are the only evidence in hand and they listed Front Range Energy (Sept 2024 report, per the discovery row) and no Microvast.

**Verdict: not tested** (host refuses scripts; mirror robots.txt disallows all). Decision for the caller: either accept the mirror despite its robots line (the content is the same public record and a human can download it by hand), or treat Windsor permits as a manual monthly download.

## Rank 18: Windsor Development Activity StoryMap

**Spot-check:** item created 2024-07-12, modified 2026-11-02, `access: public`, `licenseInfo` and `accessInformation` both null. 172 story nodes, 66 text nodes. Projects named (case numbers are the only date-like content; the story carries no record dates):

- Under construction: Windshire Park 6th Filing senior complex (SP18-036, MAJS20-008); Raindance 11th Filing condos (SP20-018, MAJS20-007); Tacincala 1st and 2nd Filings (MAJS21-012, MAJS23-002); Greenspire Tract H commercial (SP22-011); Trevenna (MAJS22-011); Poudre Heights 5th (SP22-012, MAJS22-012); Tacincala 4th Filing community building (MINS24-009, SP24-027); Greenspire 1st and 7th Filings; Shutt's 5th Filing townhomes (MINS25-001, SP25-001); Windsor Middle School renovation (SP26-003); Greenspire 8th Filing Sherwin Williams 4,840 sf (MINS25-009, SP25-012).
- Under review: Water Valley South 24th Filing self storage (MINS24-005, SP24-017); Windsor Industrial Park Annexation major subdivision, 46 acres LI zoned into 13 lots, with a King Soopers Marketplace site plan (MAJS25-004, SP24-018); Hayden Annexation 40 acres (ANNX24-003); Eagle Crossing 11th Filing 122-room hotel (SP24-021); Walmart Supercenter 191,300 sf (MINS25-010, SP25-013); 5th Street backlots parking; Greenspire 8th Filing Murphy USA (SP25-018); Diamond Valley 14th Filing waste transfer facility on 10.5 acres in the Heavy Industrial district, three buildings including a maintenance shop (MINS24-007, SP24-019); East Point 5th Filing daycare (SP25-009); Greenspire 9th Filing senior patio homes (MAJS25-001); Grasslands Park 5th Filing; Windsor Villages at Ptarmigan Banner MD Anderson 90,000 sf cancer center (MAJS26-009, MINS26-007); Greenspire 8th Filing Bank of America (SP26-006); Great Western Industrial Park 15th Filing Lot 1 fire training facility, 10.8 acres HI zoned (SP26-007, MINS26-002); East Pointe 6th Filing Firestone Auto Care (MINS26-004, SP26-010).

Industrial content: two of about 27 projects (the waste transfer station and the fire training center in the Great Western Industrial Park); none is a manufacturer. No ground-truth or supplementary company appears. Join is by project name and case number only. Access: ArcGIS Online public item, no license text.

**Verdict: park** (spot-checked only). Undated, curated and explicitly incomplete; worth a monthly JSON diff only as a cheap supplement if Windsor is in scope at all.

## Rank 28: Firestone Development Projects map

Turned out to be a plain hosted feature layer, so it was spot-checked. The Experience Builder's web map holds a group layer whose four sublayers (Other, Mixed Use, Residential, Commercial) all point at `service_fac9eddf498043fa936b58f122d2001d/FeatureServer/0` (AGOL item ae72ba0857fe4250928e8f1cd09b51c8, owner a town account, public, `licenseInfo` and `accessInformation` null, modified 2025-10-23). Schema includes DateAccepted, FileNumber, ProjectStatus, PCHearingDate, BOTMeetingDate, Address, Archived and PDF links. 48 rows, none archived. **DateAccepted and FileNumber are null on all 48 rows**, PCHearingDate and BOTMeetingDate were not populated in the dump, and EditDate is 2026-11-05 on every row (a bulk edit), so in practice the layer is undated. Project types: residential 23, commercial 17 (Target 128,660 sf, WinCo, Porsche, Windish RV plat and FDP at 10300 E I-25 Frontage Rd, QuikTrip, Bellco, Fowler Kia addition, Western Midstream parking lot, Summit Vet, restaurants, Valvoline), other 7 (annexations, fire station, roads), mixed use 1. Industrial: 0. No ground-truth project (none expected). Street addresses are present on about a third of rows.

**Verdict: drop** (spot-checked only). Duplicates the rank 10 PDF without its dates, carries no industrial project, and the date fields exist but are empty.

## Sources not tested and why

- Rank 11 Windsor monthly Building Permit Reports: canonical host 403 to scripts, mirror host robots.txt `Disallow: /`; see the section above.
- Rank 24 Windsor Agenda Center RSS: an agenda feed not parsed in this pass, and it lives on the same two hosts as rank 11 (windsorco.gov 403, mirror robots disallow), so the same block applies.

## Terms findings

No browser-only portal is in this group. Frederick GIS: open data terms (copy, distribute, adapt freely; as-is disclaimer). Firestone: robots.txt blocks only admin and search paths; no terms stated for the PDF; scripted connections are sometimes reset. Windsor: see rank 11. Weld County AGOL license text: not applicable, none of this group's sources is a Weld County AGOL item (the Windsor StoryMap and Firestone layer are town-owned AGOL items with null `licenseInfo`).

## Corrections the test suggests to the ground truth (not applied)

- X26 Agilent: the ground truth has no street address; the permit layer gives 7051 Eagle Blvd (parcel 131326401001, also addressed as 12100 Andrews Dr) with the Endeavor construction trailer on the neighbouring 7400 Eagle Blvd lot (parcel 131326403001). The 2023-02-16 groundbreaking milestone is consistent with the permit series (grading 2023-01-30, foundation 2023-03-08).
- X26 Agilent: the project name in town records is "Project Endeavor" (and "Agilent Endeavor" on the site plan); adding it to the row would make text matching exact. The earlier 2021 permits name "Project Synergy", a separate Agilent fit-out, which the ground truth does not mention.
- C35 Hirsh Precision: needs a street address before any permit or planning source can be back-tested; the Frederick layer carries no applicant field to find it.

## Not finished

- Rank 11 Windsor PDFs: nothing downloaded or parsed (blocked, see above), so no X27 test on permits and no monthly industrial and commercial counts.
- Rank 10 Firestone archive: only the current PDF; no biweekly history to count against.
- Rank 26: two packets of 35; no Planning Commission packet streamed.
- Rank 3: Hirsh could not be tied without a street address.
