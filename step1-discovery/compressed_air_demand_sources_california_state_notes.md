# California state-tier data sources for early facility-level compressed air demand: notes

Companion to `compressed_air_demand_sources_california_state.csv` (31 rows, ranked). Verification date: 2026-11-10. Same column layout as the Colorado state file, including `application_received_date_exposed` and `automation_notes`.

**Question:** which California facilities are about to add compressed air demand. Unit of observation: facility (company-site). Required lead time: months ahead of the equipment purchase.

**Assumed:** "run state sources for California" means a Step 1 discovery pass at state tier, the same job as the Colorado state run. Atlas Copco first-party data is excluded, as in every earlier run.

## How this pass differs from the Colorado one (read this first)

1. **It is smaller.** Colorado was seven parallel research agents and produced 82 rows. This was one pass from a phone session: 31 rows, about 60 searches and page fetches. The top of the list is solid. The long tail (minor licences, associations, water, bonds, labor) is thinner, and the "Leads not chased" section at the bottom is longer than Colorado's as a result.
2. 12 rows are `yes`, 19 are `partial`. `partial` nearly always means the landing page was fetched but the live table, file or query behind it was not opened. `verification_notes` says which.
3. Anything marked "from prior knowledge" in the CSV was not confirmed by a fetch. There are four such statements: the number of air districts (35), that SCAQMD F.I.N.D. lists permit applications, ABC licence type 23, and that CalCompetes agreements carry annual milestones.
4. Regional sources (air districts, regional business press) are in the CSV with `tier = regional`, because in California the air-permit link of the chain does not exist at state level at all.

## Tier 1 (ranks 1 to 13): the working set

**Incentive stage, named companies (0 to 60 months out)**

1. **CAEATFA Sales and Use Tax Exclusion agendas.** The best single source found. A manufacturer applies to buy equipment free of sales tax, and the State Treasurer's board agenda prints the company, city, county and the dollar value of equipment it plans to buy. September 2026 had 15 applicants, from Bosch Semiconductor in Roseville ($176.5M) to Pyka in Alameda ($2.9M). Each gets its own staff report. This is an equipment-purchase list, which is closer to the compressor order than a jobs credit is.
2. **California Competes agendas.** Three rounds a year. Every recommended business is named with city, net new jobs, investment and credit. December 2, 2026 agenda: Castelion and K2 Space in Torrance, Swift Solar in Oakland ($528M), Nextpower in Fremont, Joseph Gallo Cheese in Atwater, Redwood Beverage in West Sacramento. Colorado hides names behind code words for about 8 months. California does not.
3. **CAEATFA awards workbook.** The running list of every award with "STE used to date" and percent used. An award that is 20% used is a plant still buying.
12. **CalCompetes awardee list and agreements.** The decode and enrichment layer for rank 2.

**Installed base (coincident, but unique)**

4. **Cal/OSHA Pressure Vessel Registration Database.** California requires a Permit to Operate for air tanks and publishes the database: company, street address, year built, MAWP, diameter, manufacturer, location in plant, inspection date, permit expiry. This is the answer to the question left open in Colorado (whether the boiler program tracks air receivers). Here it does, publicly. It is not a leading signal, but it is a site-by-site map of who has receivers, how many, how big and how old. State numbers issued after 2018 start with the year (A18-...), so new registrations may be listable by year. Nobody has run a query yet, and the conditions of use are unread.

**Permit and land-use stage (0 to 48 months out)**

5. **SMARTS stormwater files on data.ca.gov.** Weekly CSVs, "No Restrictions on Public Use". The industrial file is every Industrial General Permit enrolment (a new one is a new industrial site by SIC code). The construction file is every site over an acre breaking ground. Column headers still need opening.
6. **CEQAnet.** Every CEQA document filed with the State Clearinghouse, with received date, full project description, parcel, development type and CSV export. Nothing like it exists in Colorado. Long lead (1 to 4 years) and noisy (spec warehouses, housing).
9, 10. **South Coast AQMD and Bay Area AQMD.** Regional air permit lookups and notices. BAAQMD's November 2026 list includes Tesla Fremont furnace applications.

**Hiring and financing**

7. **Employment Training Panel packets.** Monthly, named, with California sites and a narrative on why the company is training (new contracts, new lines). Colorado's equivalent is unpublished.
8. **ABC daily export.** Pending and active alcohol licences, refreshed every business day, including a daily new-applications report. A true pending-application feed for breweries, wineries and distilleries.
11. **California UCC.** Exists, searchable free, bulk orders through a bizfile account. Whether the bulk file carries collateral text, what it costs and how often it refreshes are all unconfirmed. This was Colorado's best feed, so it is the most important open question here.

**Press**

13. **The Registry** for the Fremont, Newark and San Jose manufacturing belt (Quanta, Vander-Bend items on November 9).

## Local air permitting authority: the structural difference

Colorado has one air permitting agency. California has none at state level: stationary-source permits are issued by local air districts (35 of them, from prior knowledge; the CARB page listing them would not load). That means no California equivalent of the APCD Permit Status tracker or the Environmental Justice Summary dashboard. The air-permit link has to be built district by district. Priority order by industrial weight (my judgement): South Coast (LA, Orange, Riverside, San Bernardino), San Joaquin Valley (eight counties, food and oilfield), Bay Area, San Diego, Sacramento Metro, then Ventura, Mojave Desert and Imperial. Only South Coast and Bay Area were checked. San Joaquin Valley's site rejected the fetch tool on both URLs tried.

## Considered and rejected or downgraded

- **CPUC Rule 30 large-load filings:** aggregates only. PG&E signs NDAs with large-load customers and applies the 15/15 aggregation rule. Individual customers appear only when a special contract goes to the Commission (STACK, Microsoft, both data centers). Scored 1.
- **CDPH Processed Food Registration:** the registration exists, no public list. CPRA candidate.
- **CARB PERP:** no public registrant list found.
- **GO-Biz newsroom:** five releases on the page, newest February 2026. Not a feed.
- **CMTA, Roadmap 4 Innovation (cmtc.com redirects there):** channels, not data.
- **lab.data.ca.gov SMARTS mirror:** stale at 2019. Use data.ca.gov.
- **CERS:** login-only for regulators and businesses. The Regulated Site Portal is the public face.
- **Sales tax and property tax records** (CDTFA partial manufacturing exemption claims, Form 571-L business property statements): confidential by statute, from prior knowledge. Not fetched.
- **CTCAC and CDLAC agendas** surfaced in search: housing tax credits, wrong buyer.
- **Third-party aggregators** seen in search (cpo.soar.com meeting summaries, california-warn.pages.dev, an Apify bizfile scraper): not primary publishers. The scraper in particular is the route to avoid.

## Gaps: chain links with no good California state source

1. **Air permit applications statewide.** Covered above. District by district only.
2. **Utility requests.** Same wall as Colorado. Customer identity is confidential. Possible proxy not yet checked: the utilities' annual Grid Needs Assessment filings, which list circuits with load growth.
3. **UCC collateral text.** Unknown until someone logs into bizfile and looks at the bulk order.
4. **Building, mechanical and electrical permits.** No statewide feed. City and county level (many large California cities run open-data permit feeds; none checked this pass).
5. **Food manufacturing registrations.** Unpublished (CDPH). ABC covers only alcohol.
6. **Announcements.** No state press flow comparable to OEDIT. The CCTC and CAEATFA agendas are the announcement feed.
7. **Small and mid private manufacturers outside incentives.** CCTC and CAEATFA skew large. ETP, UCC, SMARTS and the pressure vessel database are the ones that reach small plants.

## Could a Public Records Act request unlock anything?

From prior knowledge, not fetched this pass: the California Public Records Act (Government Code 7920.000 and following) gives agencies 10 days to respond and lets them charge only direct duplication costs, plus programming cost where a custom data extract is needed. Check each agency's own page before sending anything.

Ranked candidates:

1. Cal/OSHA Pressure Vessel Unit: air tank permits first issued since January 2025 (company, address, year built, size, inspection date). The inspection request form has a "New Installation" box, so the unit can tell new from renewal.
2. Secretary of State: the UCC bulk file specification, if the bizfile help pages do not answer it.
3. CDPH Food and Drug Branch: Processed Food Registrations first issued since January 2025.
4. South Coast AQMD and San Joaquin Valley APCD: permit applications received by date, with equipment description.
5. CARB: PERP registrations for portable compressors by owner.

The Colorado caution applies: a records request is itself a public record, and one from an Atlas Copco address shows what you are building. Decide whether legal or your manager should see them first. No drafts written this pass.

## Surprising

- California names incentive recipients at approval, with city, jobs and investment. The eight-month code-name problem from Colorado does not exist here.
- The State Treasurer publishes, per manufacturer, the dollar value of equipment it plans to buy and later how much of that it has actually bought.
- Air receivers are publicly registered with street addresses.
- There is no statewide air permit tracker of any kind.
- ABC publishes pending applications daily. No Colorado licensing agency publishes anything pending.
- CEQAnet moved hosts (opr.ca.gov to lci.ca.gov) after the Office of Planning and Research was renamed. Old links redirect for now.
- CAEATFA cancelled six of its 2026 monthly meetings, including October and November. Awards arrive in bursts.
- cmtc.com, the old California MEP center site, now redirects to a differently named nonprofit.

## Leads not chased (hand to the next pass)

Open the SMARTS facility CSV headers. Run one query on the pressure vessel database and read DIR's conditions of use. Log into bizfile and read the bulk order spec. Open the CAEATFA awards workbook and one staff report. Open one CalCompetes agreement. San Joaquin Valley APCD, San Diego APCD, Sacramento Metro AQMD notices and permit lookups. SCAQMD F.I.N.D. application listing by date. BAAQMD Public Data Center. CEC NOPA result tables and FPIP status. IBank and CDLAC 2026 board agendas. CAEATFA "500+ Employee Applicants" PDF. Utility Grid Needs Assessment filings. DWR well completion reports and State Water Board water rights (eWRIMS). Department of Cannabis Control licence search. CDFA milk products plant and meat processor lists. CDPH drug and medical device manufacturing licences. HCD factory-built housing manufacturers. Division of Mine Reclamation (SMARA) mines. HWTS report list. CalRecycle SWIS and grant awards. CNPA public notices user agreement. CalJOBS. Division of Apprenticeship Standards sponsors. Caltrans encroachment permits. State Lands Commission leases. Regional press not checked: Los Angeles, Orange County, San Diego, Sacramento, San Francisco and Silicon Valley business journals, Central Valley Business Journal (Stockton/Modesto), Inland Empire outlets, North Bay Business Journal. City and county tier: nothing run yet; Alameda and Santa Clara counties (Fremont, Newark, San Jose) would be the natural first county run from Fremont.
