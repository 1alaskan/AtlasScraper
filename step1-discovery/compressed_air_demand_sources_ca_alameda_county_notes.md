# Alameda County, California: local-tier discovery notes (PARTIAL)

Run 2026-11-10 as part of the first California county run. **Second pass added 2026-11-10 (same day): 14 sources are now listed; 7 are fully verified.** The machine-readable routes have been tried for Fremont, Hayward, Oakland, Berkeley, San Leandro and Alameda city; see `step3-validation/california/alameda/validation_alameda_notes.md` for verdicts. Still unexplored: Newark, Union City, Livermore, Pleasanton, Dublin, Emeryville, Albany, Piedmont, county planning, utilities, wastewater agencies, the port, assessor and recorder, local press. A Colorado county run found 50 or more local sources. Most of this session went to the state foundation.

## Jurisdiction map (from prior knowledge, to be confirmed city by city)

- Incorporated cities: Alameda, Albany, Berkeley, Dublin, Emeryville, Fremont, Hayward, Livermore, Newark, Oakland, Piedmont, Pleasanton, San Leandro, Union City. Each runs its own building and planning function.
- Unincorporated (county Planning and Public Works): Castro Valley, San Lorenzo, Ashland, Cherryland, Fairview, Sunol.
- Industrial weight, judged from the state pulls (new manufacturing stormwater enrolments since 2024): Fremont 24, San Leandro 22, Hayward 18, Oakland 11, Alameda 9, Emeryville 6, Livermore 6, Berkeley 5. Newark and Union City are smaller in count but hold large sites.
- Air district: Bay Area AQMD (whole county).
- Not yet mapped: the hazardous materials agencies (CUPAs), wastewater agencies with industrial pretreatment programs, electric providers, Port of Oakland.

## What was checked

- BAAQMD publishes every permit application received for the last two years. This is the nearest thing to Colorado's air permit tracker and it covers nine counties. The table is drawn by script, and the district's robots.txt disallows the grid's query URLs, so it is a manual lookup source unless the district provides an extract.
- Fremont publishes a Development Activity Table as Excel and runs AgencyCounter, a permit activity map with daily summaries. fremont.gov refuses the cloud shell (403), so nothing was pulled.
- Oakland's open data portal has no permit dataset (catalog searched for permit, business licence and planning: nothing current). Oakland permits are Accela, browser-only.
- Berkeley publishes business licences on Socrata, refreshed daily.
- San Leandro and Livermore city sites also returned 403 to the shell. Hayward's site was reachable but not explored.
- The county open data portal (data.acgov.org) returned nothing for permit searches through the Socrata catalog; not explored further (its robots.txt asks for a 60-second crawl delay).

## Rejected

- data.oaklandca.gov for permits: datasets are from 2013 to 2021 and none is a permit feed.
- Third-party meeting and permit aggregators seen in search (GatherGov, Boardwalk, Levelset): not primary publishers.

## Real recent industrial examples seen (proof the signal exists)

- 1111 Aladdin Avenue Manufacturing Project, San Leandro: CEQA mitigated negative declaration received 2026-06-08, 142,645 sq ft.
- Tesla Fremont furnace permit applications on BAAQMD public notice, November 2026.
- Teledyne ETM, 35451 Dumbarton Court, Newark: new industrial stormwater enrolment processed 2026-09-28 (state source).

## Not done (pick up here)

Hayward, San Leandro, Livermore, Union City, Pleasanton, Dublin, Emeryville, Alameda city, Albany, Piedmont and county planning and permit portals. City council and planning commission agenda systems. Fremont file URLs and AgencyCounter terms. Port of Oakland board items. EBMUD, Union Sanitary District, Oro Loma, Livermore and Dublin San Ramon pretreatment lists. Alameda Municipal Power board items. City business licence registers other than Berkeley. Assessor and recorder. CUPAs. Local EDO pages (East Bay EDA, city economic development pages) and local press. CPRA drafts (first candidate: BAAQMD applications-received extract).

## Surprising

- Three of the larger city websites (Fremont, San Leandro, Livermore) refuse the cloud shell outright. In Colorado most city sites were reachable. Expect more manual or fetch-tool work here.
- The air district's applications list is public and two years deep, but fenced off from automated reading.
