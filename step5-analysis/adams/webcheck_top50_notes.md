# Adams County top 50 web check notes

Web check 2026-10-30. Input: `webcheck_input_top50.json`. Output: `webcheck_top50.json`.
Method: at most two WebSearch calls per company, with WebFetch of result pages where a search surfaced a usable page. Only what a page says is recorded. No Atlas Copco data, no contact with any company.

## Counts by fit level

| Fit | Count | Companies (rank) |
| --- | --- | --- |
| strong | 17 | Ardent Mills (2), Forge Nano (3), TruStile Doors (4), D-A Packaging (5), S & W Precision Machining (7), Quikrete Denver (8), Pretred (10), Coblaco Services (16), H&H Metals (24), Carlisle EPS / Insulfoam (25), McCallin Steel Storage Systems (27), Veolia ES Technical Solutions (28), Protocast (31), Swarco Colorado Paint (37), Sashco (38), Mill Rock Packaging / All Packaging (48), Vexor Custom Woodworking Tools (50) |
| moderate | 6 | Claremont Foods (11), Western Industrial Contractors (12), Denver Machine Shop (20), Rush Enterprises (33), Marini Diesel (41), Intertape Polymer (45) |
| weak | 8 | City of Westminster (6), Cando Rail & Terminals (14), CNC Pros Colorado (21), Allied Demolition (35), Metro Water Recovery (39), Bennett Creek Ranch (40), Kelley Trucking (42), Agfinity (43) |
| not confirmed | 19 | Kairus (1), Valhalla Industries (9), Ward Precision Manufacturing (13), Ginzel Enterprises (15), Duralux Finish (17), Genesee Wester (18), Imperial Machining (19), DG Metal (22), Skyline Motors (23), AGOV Underground (26), Durango Tire Shop (29), Flashfill Services (30), Cryoshield Industrial Services (32), MT Underground (34), Holcim - WCR (36), Cherry Creek Recycling (44), Quattro Machining Services (46), MechFi Designs (47), Harrelson (49) |

"Not confirmed" means the web returned nothing usable about the company at that site. It does not override the pipeline's own evidence (air permit descriptions such as "wood prefinishing", "asphalt plant", "fly ash silos", or UCC collateral such as machining centers). Those records remain the basis for the pipeline fit line; the web check simply adds nothing for these 19.

## Searches per company

| Rank | Company | Searches | Outcome |
| --- | --- | --- | --- |
| 1 | Kairus | 2 | not confirmed |
| 2 | Ardent Mills | 1 | company site, press |
| 3 | Forge Nano | 1 | trade press |
| 4 | TruStile Doors | 1 | trade directory |
| 5 | D-A Packaging | 1 | trade press |
| 6 | City of Westminster | 1 | city website |
| 7 | S & W Precision Machining | 2 | trade directory (company site fetch was blocked by the proxy; not retried) |
| 8 | Quikrete Denver | 2 | trade directory |
| 9 | Valhalla Industries | 2 | not confirmed |
| 10 | Pretred | 1 | local EDC press |
| 11 | Claremont Foods | 2 | trade blog, 2012 local press |
| 12 | Western Industrial Contractors | 1 | business directory |
| 13 | Ward Precision Manufacturing | 2 | not confirmed |
| 14 | Cando Rail & Terminals | 1 | rail services directory |
| 15 | Ginzel Enterprises | 3 | not confirmed (one search over the limit; nothing came back) |
| 16 | Coblaco Services | 2 | business directory |
| 17 | Duralux Finish | 2 | not confirmed |
| 18 | Genesee Wester | 1 | not confirmed (only hit was an unrelated firm) |
| 19 | Imperial Machining | 3 | not confirmed (one search over the limit; nothing came back) |
| 20 | Denver Machine Shop | 2 | training directory (address only) |
| 21 | CNC Pros Colorado | 2 | trade press |
| 22 | DG Metal | 2 | not confirmed |
| 23 | Skyline Motors | 2 | not confirmed (Brighton hits were car dealers under a similar name) |
| 24 | H&H Metals | 1 | company site |
| 25 | Carlisle EPS / Insulfoam | 1 | trade directory |
| 26 | AGOV Underground | 2 | not confirmed |
| 27 | McCallin Steel Storage Systems | 1 | trade press |
| 28 | Veolia ES Technical Solutions | 1 | company site |
| 29 | Durango Tire Shop | 2 | not confirmed |
| 30 | Flashfill Services | 2 | not confirmed (trademark and CDOT pages empty or failed) |
| 31 | Protocast | 1 | business directory |
| 32 | Cryoshield Industrial Services | 2 | not confirmed |
| 33 | Rush Enterprises | 1 | company site |
| 34 | MT Underground | 2 | not confirmed |
| 35 | Allied Demolition | 1 | waste directory |
| 36 | Holcim - WCR | 2 | not confirmed |
| 37 | Swarco Colorado Paint | 1 | company site |
| 38 | Sashco | 1 | trade directory |
| 39 | Metro Water Recovery | 1 | industry directory |
| 40 | Bennett Creek Ranch | 1 | county permit filing |
| 41 | Marini Diesel | 1 | trade press |
| 42 | Kelley Trucking | 1 | industry directory |
| 43 | Agfinity | 2 | job listing, local press |
| 44 | Cherry Creek Recycling | 2 | not confirmed |
| 45 | Intertape Polymer | 2 | company site (location list only) |
| 46 | Quattro Machining Services | 2 | not confirmed |
| 47 | MechFi Designs | 1 | not confirmed |
| 48 | Mill Rock Packaging | 1 | trade press |
| 49 | Harrelson | 2 | not confirmed |
| 50 | Vexor Custom Woodworking Tools | 1 | trade press |

Total: 78 searches. Two companies (Ginzel, Imperial Machining) got a third search by mistake; neither returned anything.

## County check

- 34 marked Adams. Where a page did not name the county, the mark rests on the city or zip: Commerce City, Henderson, Thornton, Brighton, Bennett and Westminster (13150 Huron) are Adams; Aurora addresses in 80011 and 80019 (Moncrieff Pl, E 33rd Ave, Walden St, E 48th Ave, Denali St) are the Adams part of Aurora; Denver mailing addresses in 80229 and 80221 (E 71st Ave, E 69th Ave, E 70th Ave, W 64th Ave, York St) are Adams-only ZCTAs.
- 12 "not checked": address withheld in the input.
- 4 "not confirmed": Claremont Foods (11751 Huron St, Westminster; the only press found placed its 2012 plant near Niwot, Boulder County, and no page ties production to the Westminster address), Duralux Finish and CNC Pros Colorado (80216 split zip, Denver mailing address, no page confirming county), Harrelson (80221 split zip, no page found).

## Sites outside Adams County

None confirmed. No company gets a drop reason.

Two to watch:
- Claremont Foods (11): production site not tied to the Westminster address by any page; the 2012 plant was in Boulder County. Keep but treat the Adams location as unverified.
- Kelley Trucking (42): headquarters is in Golden (Jefferson County); the Adams record is the Sand Creek gravel mine near Byers, which is a pit, not a plant.

## Obvious non-manufacturers in the top 20

- City of Westminster (6): municipal wastewater treatment plant.
- Cando Rail & Terminals (14): rail transload and tank car cleaning terminal.
- Western Industrial Contractors (12): construction contractor that installs systems in other companies' plants; any in-house fabrication is unconfirmed.
- Valhalla Industries (9): web found nothing; the input's own UCC collateral (trailer-mounted compressors, Vermeer directional drill, tractor with boring attachment) reads as a mobile utility contractor, not a plant.

## Fit changes versus the input fit line (for the analyst)

- Downgrades from "strong": City of Westminster, Cando Rail, CNC Pros Colorado (machine tool dealer), Allied Demolition, Metro Water Recovery, Bennett Creek Ranch, Kelley Trucking, Agfinity (all weak); Western Industrial Contractors, Rush Enterprises, Marini Diesel, Intertape Polymer, Claremont Foods, Denver Machine Shop (moderate).
- Upgrades from "unknown" or "name only": none confirmed; AGOV Underground, Cryoshield, MT Underground, Mill Rock Packaging. Mill Rock Packaging is now strong (folding carton plant in Aurora). The other three stay unconfirmed.
- Confirmed strong by web: 17 listed above.
