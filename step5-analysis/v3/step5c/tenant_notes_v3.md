# Step 5c: tenant candidates for unattached addresses (score 40 or more)

Run 2026-10-11 against `denver_ranked_accounts_v3.csv`. Output: `tenant_candidates_v3.csv` (one row per candidate name, or one "no match" row per address). The ranking itself is unchanged.

## What was joined

- **EPA Facility Registry file** already in the project folder (`frs_filtered.csv`, built by `frs_filter.py`): 1,360 Colorado rows with a Denver county, city or 802 zip. It was filtered to chosen NAICS prefixes when it was built, so it is not every facility.
- **Denver "Active Business Licenses"** open data layer (`ODC_active_business_licenses`, same host and same use-constraints text as the permit layers). 56,483 rows pulled, matching the source count. 47,129 are residential rental licences and 2,113 short-term rentals; those, parking lots, pools, valet and pedal cabs were left out, leaving 6,746. The pull was used in memory and is not saved here, because the rental rows can name individuals. `pull_denver_business_licenses.py` re-pulls it in about 40 seconds.

Join: the v3 address key (house number, S/W/E prefix, street name) plus zip. A weaker tier lists EPA facilities within 75 m of the permit point at a different address.

## Assumptions

1. Every name is a **possible occupier**, not confirmed. A match is to the street address; only a unit match would confirm, and none occurred.
2. **The EPA file has no dates.** A facility listed there may have closed or moved. Example: A. R. Wilfley and Sons is listed at 2763 Blake St, but its current stormwater permit is in Commerce City.
3. Licences are current (status active), so a licence match is a present occupier of some part of the address.
4. The city licenses only certain trades (food, liquor, marijuana, auto repair and a few more). A general manufacturer or warehouse tenant has no city licence, so "no match" says little.
5. No people's names were kept; the candidate names are business or trade names as the sources give them.

## Result

See the chat summary of 2026-10-11 for the list. Counts are in the CSV: column `match` is "same street address", "same street address, different unit", "nearby, different address (weak)" or "no match".

## Re-run

`python3 pull_denver_business_licenses.py` then
`python3 join_tenants.py <v3 folder> <step4-scrape folder> <frs_filtered.csv> denver_business_licenses.csv [--min 40]`
