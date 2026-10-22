# Step 5: analysis notes, Denver County

Run 2026-10-10 from the Step 4 files in `step4-scrape\` on Matthew's computer. Companion files: `denver_ranked_accounts.csv` (359 rows), `denver_evidence.csv` (1,300 source rows), `accela_lookup_list.csv` (25 lookups).

## Assumptions (read first)

1. **Candidates come only from rows Step 4 flagged.** A company with no flagged row in any source cannot enter the ranking, however many unflagged rows it has. Unflagged rows are used only as supporting evidence for a company found through a flag. This is the main reason the ground-truth check is poor (see below).
2. **Denver zip list:** the Census Bureau 2020 ZCTA to county relationship file (`tab20_zcta520_county20_natl.txt`). 19 zips are wholly in Denver County (99% or more of land area): 80202 to 80207, 80209 to 80211, 80218 to 80220, 80223, 80237, 80238, 80249, 80264, 80290, 80293, 80294 (plus 80266). 22 more are split with Adams, Arapahoe or Jefferson, including the main industrial zips 80216 (72% Denver) and 80239 (80%).
3. **Split zips were checked address by address with the Census geocoder** (a web lookup, used only to settle the county). 94 addresses were checked: 60 Denver, 18 Adams, 7 Jefferson, 5 Arapahoe, 4 no match. The geocoder interpolates along street ranges, so it is good evidence but not an assessor record. Addresses it places outside Denver, or cannot place, stay in the separate section with `county_basis` starting "Denver mailing address, county unconfirmed". Rows with a zip under 10% Denver and a mailing city other than Denver (Englewood 80110, Lakewood, Aurora) were left out; that removes several Englewood machine shops that are almost certainly Arapahoe County.
4. **A join by street address alone is "possible", and scores half.** Denver permits and site plans carry no tenant, so every permit attached to a named company is possible unless a suite number matches or a Step 3 document ties them. Exact name plus address is confirmed. Same name at a different address is possible.
5. **A state permit names the operator of an address.** Where exactly one air-permit applicant or water-permit facility sits at a permit address, that company is used as the row's name, and the Denver permit rows stay possible.
6. **Registered-agent and virtual-office suites are not sites.** An address and suite with 10 or more 2024-26 registrations is treated as an agent address. 121 flagged registrations were cut for this, and one flagged UCC debtor (a distillery) turned out to be in Longmont.
7. **Home addresses.** The UCC and registration files can hold a home used as a business address. A street address is shown only if it has a suite or unit, appears in a site-based source (permits, site plans, air, water, press), is shared by two or more business names, or was confirmed on the web. Otherwise the ranking shows "withheld" and keeps the zip: 58 rows, 9 of them in the top 60, including real machine shops (R B Machine, Big Metal Additive, Never Summer). The address is in the Step 4 source row under the `record_id`. In the evidence file, UCC and registration addresses are shown only where they are the company's confirmed site.
8. **Air permit dates are received dates.** A row received in 2021 to 2023 is in the feed because it was processed in the last six months, but it earns no recency points.
9. **The run date for recency is 2026-10-10.**
10. **Step 3 ground-truth corrections are not applied.** Those that affect the check are listed in that section.
11. **No Atlas Copco data, no contacts, no people's names, no agency or company was contacted, nothing was re-scraped.**

## Points table

Possible matches score half. Within one source only the best signal counts, plus 3 points for each further month with a strong signal in that source (maximum 9).

| Part | Points |
|---|---|
| **Signal: UCC filing naming an air compressor or compressed-air system** | 30 |
| Signal: UCC filing naming production machinery (CNC, machining centre, lathe, press brake, laser, injection moulding, packaging or bottling line, robot and similar) | 25 |
| Signal: air permit application, modification or approval for process units | 25 |
| Signal: Denver permit, new building or addition, industrial parcel or zoning (+3 if $1M or more) | 22 |
| Signal: construction stormwater permit with a manufacturing SIC or company-named facility | 20 (none survived the cuts in Denver) |
| Signal: Denver permit, alteration or tenant finish, industrial parcel or zoning (+3 if $1M or more) | 18 |
| Signal: air permit APEN-only or exempt row; new industrial stormwater or no-exposure certification; concept or site plan on heavy industrial zoning (I-A, I-B) | 12 |
| Signal: UCC filing with a flagged word but no production machinery (process chiller, small boiler, kitchen gear); towable construction compressor; press story naming the company | 8 |
| Signal: flagged Colorado registration; concept or site plan on industrial mixed-use zoning; unflagged permit at the company's address | 6 |
| Signal: press story naming only the address; OEDIT code-name approval | 5 |
| Support: generic or blanket UCC lien, other site plan at the address | 4 |
| Support: unflagged registration 3; air or water row cut as noise 2; 2024 stormwater renewal row 0 | 0 to 3 |
| **Independent sources** | +8 for each source beyond the first with a signal of 5 or more (maximum 24); +3 for each source with support only (maximum 6) |
| **Recency** (latest row worth 4 points or more) | +15 within 12 months; +8 within 24 months; 0 older |
| **Stage** | buying equipment +12; fit-out +12; under construction +8; operating and expanding +8; planned +4; unknown 0 |
| **Compressed-air fit** | strong +15; moderate +6; unknown 0; weak -15 |

Each row's `top_evidence` ends with its own points breakdown.

**Stage rules.** Buying equipment: a compressor or production-machinery UCC filing in the last 12 months. Fit-out: an alteration or tenant-finish permit not finaled, or finaled in the last 6 months. Under construction: a new-building permit not finaled. Operating and expanding: an air permit action, a new stormwater certification, an older equipment filing or a closed permit. Planned: only a concept or site plan, or an OEDIT approval.

**Fit rules, in order.** A web check where one was done; a manufacturing SIC (2000 to 3999) on a water permit; production machinery named in a UCC filing; a manufacturing word in the name (labelled "not confirmed"); process units on an air permit; then trade words (auto, tyre, concrete, print) as moderate; office, energy, software, housing and logistics words as weak. For an unattached address the assessor parcel class is used: food processing or factory is strong, warehouse is unknown.

## Result

- **359 rows ranked:** 318 in Denver County (177 companies, 141 unattached addresses), 28 with a Denver mailing address and county unconfirmed, 13 OEDIT code names that mention Denver.
- **The list is top-heavy.** 62 Denver rows score 50 or more. Below that it is a long tail: 100 are a concept or site plan and nothing else, and 97 are a flagged registration and nothing else.
- Sources per Denver row: one source 210, two 67, three 29, four or more 12.
- Fit: strong 68, moderate 12, unknown 164, weak 74.

### Top 25

| Rank | Company or address | Site | Stage | Score | Sources |
|---|---|---|---|---|---|
| 1 | PepsiCo Beverages North America (CB Manufacturing Company, Inc.), High Point plant | 19300 E 72ND AVE | fit-out | 122.0 | 3 |
| 2 | CONAGRA FOODS PACKAGED FOODS, LLC | 4735 FLORENCE STREET | fit-out | 96.0 | 4 |
| 3 | KING SOOPERS, INC. | 60 YUMA ST | operating and expanding | 92.0 | 5 |
| 4 | QUALITY LININGS & PAINTING, INC | 8250 E 40TH AVE | operating and expanding | 89.0 | 4 |
| 5 | DAWN FOOD PRODUCTS, INC | 4500 LIPAN ST | operating and expanding | 83.0 | 2 |
| 6 | NESTLE PURINA PETCARE COMPANY (FORMERLY RALSTON PURINA CO.) | 4555 YORK STREET | fit-out | 82.0 | 3 |
| 7 | Safeway milk plant (occupier named in a Step 3 Accela record, not in the scraped files) | 4301 N Forest ST | under construction | 79.0 | 2 |
| 8 | CARGILL, INC. | 4545 MADISON ST | operating and expanding | 78.0 | 3 |
| 9 | Colorado Truckwashing, LLC | 5150 Brighton Blvd | buying equipment | 77.0 | 2 |
| 10 | Titan Fittings LLC | 11795 E 45th Ave | buying equipment (repeat buyer; operating and expanding) | 76.0 | 1 |
| 11 | Frito Lay Inc | 11645 E 37th AVE | fit-out | 71.5 | 3 |
| 12 | Amcor Rigid Packaging | 4990 N Ironton ST | under construction | 70.5 | 2 |
| 13 | CO-Innovate, LLC | withheld (not confirmed as a business premises; see source record) | buying equipment | 70.0 | 1 |
| 14 | Unattached address (no company attached) | 95 S Tejon ST | fit-out | 68.0 | 2 |
| 15 | Unattached address (no company attached) | 4460 N Madison ST | under construction | 68.0 | 2 |
| 16 | Unattached address (no company attached) | 3100 N Brighton BLVD 1200 | fit-out | 67.5 | 3 |
| 17 | Pacific Air Incorporated | 2550 W 2nd Ave Unit 110 | buying equipment | 67.0 | 1 |
| 18 | Blazy Susan LLC | 10660 East 51st Avenue | buying equipment (repeat buyer; operating and expanding) | 67.0 | 2 |
| 19 | R B MACHINE, INC. | withheld (not confirmed as a business premises; see source record) | buying equipment | 67.0 | 1 |
| 20 | Custom Stone LLC | 4398 Broadway, Unit A | buying equipment | 67.0 | 1 |
| 21 | Big Metal Additive LLC | withheld (not confirmed as a business premises; see source record) | buying equipment | 67.0 | 1 |
| 22 | Native Foods LLC | 4823 Lima St | buying equipment | 67.0 | 1 |
| 23 | INTERTECH PLASTICS, LLC | 12850 E. 40th Ave | buying equipment | 67.0 | 1 |
| 24 | Starko Gear LLC | withheld (not confirmed as a business premises; see source record) | buying equipment | 67.0 | 1 |
| 25 | NEVER SUMMER INDUSTRIES, INC. | withheld (not confirmed as a business premises; see source record) | buying equipment | 67.0 | 1 |

Read the top with these cautions:

- **PepsiCo (rank 1)** is first partly because of two changes made after the ground-truth check (see that section). The web check could not confirm whether the plant is operating; the newest permit ($9.3M new building) was issued 2025-07-09 and is not finaled.
- **King Soopers bakery (rank 3)** rests on a 2023 air permit still in process, a withdrawn concept review joined by address, and a press mention by name. It is an existing plant; treat the score as generous.
- **Colorado Truckwashing (rank 9)** sits at 5150 Brighton Blvd, the site SRM Concrete bought for a batch plant. The June 2026 concept review at this address is very likely SRM's, not the truck wash's. The join is by address and is labelled possible.
- **Ranks 17 to 26 are ties at 67:** single-source UCC machinery buyers. Order within the tie is by latest filing date and means little.
- **Three food plants (Conagra, Nestle Purina, Frito-Lay) and the Safeway milk plant** have open building permits joined by address. The permit layer has no description, so whether the work adds process equipment is not known. These are on the Accela list.

## Method

1. **Scope.** County from the source where it has one (water permit county, AIRS prefix 031, the two Denver layers). Otherwise zip, then the geocoder for split zips (assumptions 2 and 3).
2. **Noise cuts** on the flagged rows, in the table below.
3. **Signals.** Each surviving flagged row becomes one signal with a type and points.
4. **Resolution.** Names are upper-cased, stripped of punctuation, "The", entity words (Inc, LLC, Corp, Co, Ltd, LP) and status suffixes, and single letters are joined ("R B MACHINE" becomes "RB MACHINE"). Addresses are reduced to house number, S, W or E prefix, and street name; N prefixes, street types and units are dropped from the key, and the unit is kept separately. Raw values stay in the evidence file. Records merge when the name key is identical; when two names share an address and a leading word (Titan Fittings and Titan Advanced Manufacturing); when they are co-debtors on one UCC filing; and when a water permit names one as the facility and the other as the operator (Pepsi Beverages North America and CB Manufacturing).
5. **Address-only records** (Denver permits, site plans, press rows with an address) join a company found at the same address. Where no company is found the address is its own row, "Unattached address". Names found at the address in the UCC or registration files are listed as possible occupiers, never promoted to the account. Contractors are never used as the account.
6. **Reach into the full files.** For every candidate, all rows in all eight files with the same name key or the same address: 352 further UCC rows, plus registrations, cut air and water rows, unflagged permits and press mentions.
7. **Score and rank**, then the sensitivity runs.
8. **Web checks** (below), then one re-run with the results.

### Noise cuts and counts

"ADDED" marks a cut that was not in the handoff list. Counts are rows removed at that step unless the text says otherwise.

| Source | Step | Rows |
|---|---|---|
| Colorado UCC filings | flagged rows statewide | 901 |
| Colorado UCC filings | outside Denver scope (zip and mailing city) | 789 |
| Colorado UCC filings | debtor name has no business word (may be an individual) | 10 |
| Colorado UCC filings | SBA continuation filings (none are flagged; flags sit on initial filings only) | 0 |
| Colorado UCC filings | forklifts and other lift or earthmoving equipment (Doosan, 'pneumatic' tyre) | 7 |
| Colorado UCC filings | paving and road-milling equipment ('pneumatic' rollers, Wirtgen milling machines) | 3 |
| Colorado UCC filings | dry-cleaner and laundry boilers | 2 |
| Colorado UCC filings | 'bottling' only in a debtor's own name (one blanket lien, 10 debtor rows) | 7 |
| Colorado UCC filings | ADDED: pharmacy and copier blanket liens where the flag word sits in boilerplate (Cardinal Health, Canon) | 5 |
| Colorado UCC filings | ADDED: restaurant, commissary-kitchen and survey equipment (kept below as a weak tier, not dropped) | 7 |
| Colorado UCC filings | ADDED: towable construction compressors (kept below as a weak tier, not dropped) | 8 |
| Colorado UCC filings | rows kept as signals | 78 |
| Colorado business registrations | flagged rows statewide | 2,211 |
| Colorado business registrations | no Colorado address (foreign entity showing an out-of-state head office); kept for name matching only | 1,707 |
| Colorado business registrations | Colorado address outside Denver scope | 269 |
| Colorado business registrations | February 2026 bulk filings through Colorado Registered Agents Inc | 4 |
| Colorado business registrations | ADDED: registered-agent or virtual-office address (10 or more 2024-26 registrations at the same address and suite) | 121 |
| Colorado business registrations | ADDED: entity since withdrawn, dissolved, converted or merged | 6 |
| Colorado business registrations | rows kept as signals | 104 |
| Denver commercial construction permits | flagged rows | 509 |
| Denver commercial construction permits | zero-valuation permits in the full layer (never flagged; listed for the record) | 1,713 |
| Denver commercial construction permits | flagged rows in the DIA neighborhood (all) | 200 |
| Denver commercial construction permits | DIA neighborhood on airport zoning or Pena Blvd (terminal and concourse tenant work). CHANGED after the ground-truth check: DIA-neighborhood permits on other zoning are now kept, because the blanket cut removed the PepsiCo plant permits at 19301 E 70th Ave | 145 |
| Denver commercial construction permits | ADDED: special events and change-of-contractor records | 24 |
| Denver commercial construction permits | ADDED: assessor parcel class is not industrial (office, retail, housing, restaurant, hotel, stadium and similar), or no industrial zoning and no industrial parcel class | 257 |
| Denver commercial construction permits | flagged rows received in the last 90 days (kept at full weight; the layer undercounts this window) | 3 |
| Denver commercial construction permits | rows kept as signals | 83 |
| Denver concept and site plans | flagged rows (every row is flagged) | 1,348 |
| Denver concept and site plans | ADDED: not industrially zoned (housing and mixed use dominate); kept as supporting evidence by address | 1,184 |
| Denver concept and site plans | ADDED: no usable street address | 3 |
| Denver concept and site plans | rows kept as signals | 161 |
| State water permits (WQCD) | flagged rows statewide | 1,867 |
| State water permits (WQCD) | flagged rows with county Denver | 161 |
| State water permits (WQCD) | flagged rows with a Denver mailing city but another county in the source (left out: the source states the county) | 38 |
| State water permits (WQCD) | ADDED: industrial stormwater general-permit renewal wave, May to July 2024 (existing plants re-applying; kept as identity and SIC evidence, zero growth points) | 70 |
| State water permits (WQCD) | renewals (received more than a year after issue) | 22 |
| State water permits (WQCD) | wastewater plants, hauling and detention or water-quality facilities | 6 |
| State water permits (WQCD) | ADDED: airport construction and airline facilities at DEN (same reason as the DIA permit cut) | 18 |
| State water permits (WQCD) | ADDED: portable plants with no fixed site | 0 |
| State water permits (WQCD) | ADDED: flagged on acreage alone (no manufacturing SIC, no company-named facility): schools, parks, housing, roads, pipelines | 20 |
| State water permits (WQCD) | ADDED: transit, public works, retail and contractor-coded sites with no manufacturing SIC | 9 |
| State water permits (WQCD) | rows kept as signals | 16 |
| APCD air permit status | flagged rows statewide (not oil and gas) | 1,064 |
| APCD air permit status | rows whose county column says Denver but AIRS prefix is not 031 (left out; office address in place of the site) | 4 |
| APCD air permit status | flagged rows with AIRS prefix 031 (Denver) | 90 |
| APCD air permit status | ADDED: fuel stations and bulk fuel | 19 |
| APCD air permit status | ADDED: emergency generators and fire pumps only (data centres, telecom, hotels, city buildings) | 32 |
| APCD air permit status | ADDED: hospitals, crematories, prisons, utilities, airport and city facilities, data centres, land development | 17 |
| APCD air permit status | ADDED: no street address for the site | 1 |
| APCD air permit status | rows kept as signals | 21 |
| Mile High CRE | flagged rows statewide (industrial category) | 160 |
| Mile High CRE | flagged rows with city Denver | 54 |
| Mile High CRE | no single street address (market reports, portfolio sales, round-ups); read by eye for occupier names | 35 |
| Mile High CRE | rows kept as address signals | 19 |
| Mile High CRE | no-address rows kept because the headline names an occupier (read by eye) | 1 |
| OEDIT EDC approvals | flagged rows (every row is flagged) | 139 |
| OEDIT EDC approvals | rows from minutes (mostly non-industrial) | 39 |
| OEDIT EDC approvals | no Denver County or Metro Denver reference | 87 |
| OEDIT EDC approvals | rows kept as code-name candidates | 13 |

Notes on the cuts:

- **SBA continuations:** none of the 901 flagged UCC rows is a continuation, so the cut removed nothing. They do appear as supporting amendment rows at zero points.
- **The last 90 days of permits:** the three flagged permits received after 2026-07-12 are kept at full weight. The undercount cannot be fixed by cutting; it means recent fit-outs are missing, not that the ones present are wrong.
- **Zero valuation:** 1,713 permits in the layer have zero valuation and none can flag. Some are real: Maybell Quantum's 2024 build-out is recorded at $1.
- **Water renewal wave:** 70 Denver industrial stormwater rows received May to July 2024 are existing plants re-applying under the renewed general permit. They score zero but supply the SIC code for the fit judgment.
- **OEDIT:** 13 code-named approvals mention Denver County as a wage benchmark or "Metro Denver under consideration". No code name was decoded. None could be matched to a registration or permit on county, industry and timing with any confidence, so no match is claimed, not even a possible one. They are listed at the bottom of the ranking as code names.
- **Mile High CRE:** of 54 flagged Denver posts, 35 had no single address. Read by eye, one named an occupier (Bron Tapes), and the web check showed its new site is in Centennial, so it was dropped.

### Rows checked on the web

- **County:** 94 addresses through the Census geocoder (every flagged UCC, registration and press address in a split zip or with a Denver mailing city outside a Denver zip).
- **What the company makes:** 52 names. Denver section, named rows at ranks 1 to 51 as they stood before the re-run (42 names), the top nine of the unconfirmed section, and Bron Tapes. Search returned titles only, so only about 22 could be confirmed. Confirmed and used in the fit column: PepsiCo (plant confirmed, operating status not), Conagra, King Soopers bakery, Quality Linings, Dawn Food Products, Nestle Purina, Cargill, Titan Fittings, Vasquez Ready Mix, Frito-Lay, Amcor (company level), Kokopelli Outdoor (office and retail only, moved to weak), Blazy Susan, Intertech Plastics, Never Summer, Big Metal Additive, Colorado Prefare Foods, 303 Auto Care, Guy's Floor Service, Electric Equipment & Engineering, Dencol Supply, CNC Pros Colorado (a distributor, moved to weak), Vexor.
- **Dropped after the web check:** Valor Peak Distillery (Longmont) and Bron Tapes Holdings (Centennial).
- **Not confirmed** (fit rests on the records alone): Colorado Truckwashing, CO-Innovate, Pacific Air, R B Machine, Custom Stone, Native Foods, Starko Gear, Skyline Motors, Lakin Tire, American Building Supply, Manny's Welding, Lemon Powers, B & B Machine (a listing gives a different Denver address), 2401 W 6th Ave LLC, Arclin, Accu-Tube (site refused the fetch), Holcim, RC Services, 1395 South Acoma, ADM, Nauhaus, and the unconfirmed-section machine shops.

## Check against the ground truth

**2 of 17 Denver projects appear in the ranking.**

| Project | Rank |
|---|---|
| D01 PepsiCo | 1, 113 |
| D02 Swire Coca-Cola (cancelled) | not ranked |
| D03 4 Noses Brewing | not ranked |
| D04 Wilding Brands Canworks | not ranked |
| D06 Full Frame Beer | not ranked |
| D07 BrewDog Denver | not ranked |
| D08 Monolith Brewing | not ranked |
| D09 Cheetah Coalition | not ranked |
| D10 Rebel Bread | not ranked |
| D11 Elemental Bakery | not ranked |
| D12 Azure Printed Homes | not ranked |
| D13 Vinyl Me Please plant | not ranked |
| D14 SRM Concrete | 9 |
| D15 Maybell Quantum | not ranked |
| X06 NextRun hub (Direct Polymers) | not ranked |
| X12 Crazy Shirts | not ranked |
| X13 Sara Gabriel | not ranked |

- **PepsiCo** is rank 1 (the new plant) and rank 113 (the old Brighton Blvd bottling plant, a 2024 stormwater row).
- **SRM Concrete** appears only through its site: the concept review at 5150 Brighton Blvd is attached, as possible, to Colorado Truckwashing at rank 9. SRM's name is nowhere in the Denver rows.

**Scoring was not tuned to the 17. Two things were changed after seeing the first result, and both moved PepsiCo:**

1. The first run had PepsiCo at rank 6 on its air and water permits alone. Its six plant permits at 19301 E 70th Ave ($72M, $9.3M, $7.1M and three smaller) had been removed by the DIA neighborhood cut. The cut now applies only to airport zoning or Pena Blvd addresses. That restored six permits, all at the PepsiCo address.
2. Those permits were then merged into the PepsiCo row as confirmed, on the strength of the Step 3 finding that the plant's permits are filed under 19301 E 70th Ave.

Without those two changes the count is still 2 of 17, with PepsiCo at rank 6.

**Why the other 15 were missed:**

| Reason | Projects |
|---|---|
| Milestones fall before the 2024 scrape window, and nothing flagged since | 4 Noses (opened 2023), Monolith (2023), BrewDog (permits 2023 to 2024, zero valuation), Crazy Shirts (2023), Sara Gabriel (2023), Vinyl Me Please (2023) |
| In the files, but only as blanket liens or unflagged rows | Rebel Bread (five UCC rows, all blanket; two permits under $250k in a shopping-centre parcel), Elemental Bakery (blanket lien), Wilding Canworks (Denver Beer Co Production continuation only), Cheetah Coalition (GoldSpot blanket lien; two 2025 domestic registrations), Sara Gabriel (2026 account lien), Maybell Quantum (permits of $1 and $32k at 3821 N Steele St units 1411 and 1302) |
| Flag word list too narrow | Direct Polymers (NextRun): five UCC filings 2024 to 2025, one naming a granulator; "granulator" is not a flag word, and two say "See Exhibit A" |
| Restart of an existing space, no record anywhere | Full Frame Beer (a 2024 domestic registration only; domestic entities are never flagged) |
| No Denver address in any source | Azure Printed Homes (registered and financed at its Los Angeles address) |
| Cancelled | Swire Coca-Cola (only the old York St plant's stormwater renewal) |

What this says: the ranking finds companies that financed named machinery, hold state permits, or pulled a permit of $250k or more on industrial land since 2024. It does not find small food and drink start-ups, tenants whose loans are blanket liens, or anything that opened before 2024. Thirteen of the 17 ground-truth projects are of those kinds.

**Step 3 corrections that affect this check (not applied):**

- D16 Metro Water Recovery, D17 Vartega and D05 Craft Beverage Warehouse are not in the 17 (best guess Adams). The APCD row for Vartega confirms Adams. Nothing here changes that.
- D15 Maybell: the 2024 production site may be 7100 Broadway, which is north of the Denver line. Its Denver rows are the York Street Yards suites only.
- D13 Vinyl Me Please: the likely plant is Vinyl Media Pressing LLC at 4201 N Brighton Blvd. One zero-valuation 2024 permit exists at that address; no name ties it.
- D01 PepsiCo aliases (CB Manufacturing, 19301 E 70th Ave, 7190 N Tower Rd) were used. This is the only correction the result depends on.
- D04: the Canworks address 4455 Jason St came from general knowledge in Step 3; the UCC file does show "Denver Beer Co Production, LLC" there.
- X12 and X13 have only unverified press dates. That does not affect whether they surface.

## Sensitivity of the top 25

Base top 25 compared with four re-weightings (Denver section only).

- **Recency doubled:** 1 of 25 change. In: Skyline Motors LLC (2050 W 7th Ave). Out: Starko Gear LLC (5032 N Raleigh St).
- **Recency removed:** 5 of 25 change. In: Unattached address (possible occupier: AFFORDABLE CLASSICS LLC) (890 N Navajo ST); Mannys Welding Shop Group Co (4881 Washington St); US MIX CO. (112 S SANTA FE DR); ACME MANUFACTURING COMPANY (4650 LEYDEN STREET); NR PARENTCO, LLC (4990 DAHLIA STREET). Out: R B MACHINE, INC. (1100 W LOUISIANA AVE); Custom Stone LLC (4398 Broadway, Unit A); Big Metal Additive LLC (3891 Paris St.); INTERTECH PLASTICS, LLC (12850 E. 40th Ave); Starko Gear LLC (5032 N Raleigh St).
- **Source bonus doubled:** 7 of 25 change. In: Lakin Tire West LLC (3750 N Nome ST); Unattached address (possible occupier: AFFORDABLE CLASSICS LLC) (890 N Navajo ST); ABS-American Building Supply (5025 Florence St, #D); VASQUEZ READY MIX, LLC (7555 E. 41ST AVENUE); Unattached address (no company attached) (5150 N Colorado BLVD); 2401 W 6th Ave LLC (2401 W 6th Ave); Unattached address (no company attached) (9400 E 46th 100). Out: Pacific Air Incorporated (2550 W 2nd Ave Unit 11); R B MACHINE, INC. (1100 W LOUISIANA AVE); Custom Stone LLC (4398 Broadway, Unit A); Big Metal Additive LLC (3891 Paris St.); Native Foods LLC (4823 Lima St); INTERTECH PLASTICS, LLC (12850 E. 40th Ave); NEVER SUMMER INDUSTRIES, INC. (3838 EUDORA WY).
- **Source bonus removed:** 5 of 25 change. In: Skyline Motors LLC (2050 W 7th Ave); Mannys Welding Shop Group Co (4881 Washington St); B & B MACHINE & GRINDING SERVICE CORP. (4382 Grape Street); Unattached address (no company attached) (1630 35th ST); 303 Auto Care LLC (4240 W 1st Ave). Out: Frito Lay Inc (11645 E 37th AVE); Amcor Rigid Packaging (4990 N Ironton ST); Unattached address (no company attached) (95 S Tejon ST); Unattached address (no company attached) (4460 N Madison ST); Unattached address (no company attached) (3100 N Brighton BLVD 1).

Reading: the top 10 (PepsiCo, the multi-source food plants, the Safeway site, Titan) hold in every run. Ranks 11 to 25 are a contest between two kinds of row: single-source UCC machinery buyers, which need the recency points, and multi-source rows built on address joins, which need the source bonus. Doubling the source bonus swaps seven of the 25. If Matthew trusts a named machine in a lien more than a permit joined by address, the base weighting already leans his way.

## What the data could not show

- **Who is behind a Denver permit.** 141 of 318 Denver rows are addresses with no company. 21 more carry only a possible occupier from a registration or lien at the address.
- **What a permit is for.** No description, so a $4.9M alteration at a snack plant may be a new line or a new roof.
- **Compressed air itself.** Six flagged filings in scope name a compressor: a truck wash, an oil-change shop, a tyre and welding shop, a woodworking shop, and in the unconfirmed section a tyre shop and a body shop (marked dissolved) whose filing lists air dryers and piping bought from a compressed-air dealer. Eight more rows are towable construction units. No plant-scale compressor purchase is visible in Denver.
- **Blanket liens.** Most equipment loans to small food and drink makers read "all assets", so they never flag.
- **Anything after 2026-08-07 in water permits,** and air permit applications that left the six-month window before 2026-10-10.
- **Whether a registered company operates in Denver at all.** 121 flagged Denver registrations sit at agent suites.
- **Dissolution dates.** The registration file gives none. One debtor (Nav Auto 1, unconfirmed section) carries a dissolved note inside its name.
- **Parcel owners** were not retrieved, so no owner name backs any permit row.
- **Plant status.** PepsiCo's opening could not be confirmed from the web in the time allowed.

## How to re-run statewide

The work is four scripts, kept in the Step 5 cloud workspace and not yet saved to the folder (say if you want them there): `signals.py` (scope and cuts), `resolve.py` (matching and reach), `score.py`, `build.py`.

1. **Scope:** replace the Denver test with the county wanted. Water permits and APCD carry county (use the AIRS prefix for APCD). For UCC and registrations, build the zip list for each county from the same Census file and geocode split zips. The geocoder took about one second an address; statewide flagged UCC and registration rows with a Colorado address number about 1,300.
2. **The two Denver layers have no equivalent elsewhere.** Outside Denver the address-only tier disappears and the ranking rests on UCC, APCD, water permits, registrations, OEDIT and press. Expect fewer "fit-out" rows and no unattached addresses.
3. **Construction stormwater will matter more outside Denver.** No Denver row survived the cuts, but Step 3 found it the best construction signal statewide. The cut for acreage-only rows should stay.
4. **Keep the cuts as they are, except** the DIA and airport cuts (Denver only) and the virtual-office rule (works anywhere).
5. **Widen the UCC flag words first.** Granulator, pelletizer, grinder, mixer, filler, oven, kiln, dryer and compressor brand names would have caught Direct Polymers. That is a Step 4 change.
6. **Oil and gas** stays out through the Step 4 operator list; statewide it is half the APCD feed.

## Decisions for Matthew

1. **Addresses withheld under the home-address rule** (58 rows). Say whether UCC debtor addresses of companies with production machinery can be shown as business addresses.
2. **The Accela lookups.** 25 are listed, eight named plants first. The first eight are the ones that would change what you do this month.
3. **Whether to widen the Step 4 flags** (UCC words; a lower permit threshold on industrial parcels) and re-run, before or instead of going statewide.
4. **Whether the unconfirmed section belongs to this territory.** 28 rows have Denver mailing addresses that the geocoder places in Adams, Jefferson or Arapahoe, including five machine shops along Washington St and E 69th to 70th Ave.
5. **Parcel owner names** would put an owner on most of the 141 unattached addresses. Still open from Step 4.
