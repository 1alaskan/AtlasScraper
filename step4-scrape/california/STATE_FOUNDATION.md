# California state foundation

Written 2026-11-10. County runs read this and skip the foundation section of the `california-county-runner` skill, but must work through the open items below as they become possible.

## Part 1: state source verdicts (all `spot-checked only`; no ground truth exists)

| Source | Verdict | In the v3 build |
|---|---|---|
| SMARTS industrial stormwater | build | scored (`water_new`, 12) |
| SMARTS construction stormwater | build | scored when industrial and company-named (`water_construction`, 20) |
| California Competes awards | build | scored when every named city is in the county (`incentive_named`, 20; Matthew 2026-11-10) |
| CAEATFA STE awards | build | same |
| CEQAnet | build, pulled per county | not scored (no decision yet; rows have no company name and mostly no street address) |
| ABC manufacturer licences | park | not scored (no application date in the export; needs daily snapshots) |

Details: `step3-validation/california/validation_california_state_notes.md` and `scrape_notes_california.md`.

## Part 2: statewide pulls

`scrape_smarts_industrial.csv`, `scrape_smarts_construction.csv`, `scrape_calcompetes_awards.csv`, `scrape_caeatfa_ste_awards.csv`, `scrape_abc_manufacturer_licences.csv`, pulled 2026-11-10, records from 2024-01-01. Rerun steps are in `scrape_notes_california.md`.

## Part 3: how a California county runs through v3

The scripts were not rewritten. Two pieces make them work:

1. `scripts/build_v3_inputs.py <County> <slug> "<CITY|CITY|...>"` reshapes the state pulls into the files `build_v3.py` reads and writes them to `v3_inputs/<slug>/`, with header-only files for the Colorado sources that have no California counterpart.
2. `step5-analysis/v3/scripts/county_configs/ca_<slug>.py` sets the California labels and wording through four hooks added on 2026-11-10, all of which default to the Colorado behaviour: `SOURCE_LABELS`, `WAT_DATE_WORD`, `INCENTIVE_WORDING`, `INCENTIVE_CITY_ONLY_OK`. `build_zip_share.py` takes `--state=06`.

```
python3 step4-scrape/california/scripts/build_v3_inputs.py Alameda alameda "ALAMEDA|...|SUNOL"
cd step5-analysis/v3/scripts
python3 build_zip_share.py ca_alameda 001 --state=06
python3 build_v3.py ../../../step4-scrape/california/v3_inputs/alameda ../../california/alameda --county ca_alameda --out ../../california/alameda
python3 verify_v3.py ../../california/alameda
```

Checked after the last script edit: Denver, Adams and Weld (run 5) rebuild byte for byte, and `verify_v3.py` reports 0 problems on all four counties.

When a county gets city permit or planning pulls, point `LOCAL_PERMIT_FILES` and `LOCAL_PLAN_FILES` at them as in Adams and Weld. The paths are relative to the `v3_inputs/<slug>/` folder, so copy or link the county files there.

## Air districts

| District | Verdict | Note |
|---|---|---|
| Bay Area AQMD | manual lookup | Publishes every application received for two years, but robots.txt disallows the table's query URLs. Use by hand for top-ranked sites; a CPRA extract request has not been drafted. |

## Open items

- **Blocked on Matthew:** a bizfile login to read the UCC and business entity bulk order (contents, price, refresh). Until then California has no machinery-lien or registration signal.
- **Decisions not yet taken:** whether CEQA filings, Employment Training Panel contracts, ABC pending applications and pressure vessel records score anything; whether an award's industry text may feed the fit rule.
- **Not pulled:** Employment Training Panel agendas and packets (10-second crawl delay, about 30 PDFs); the 2026-09-15 CAEATFA applications and 2026-12-02 California Competes recommendations (neither confirmed approved when checked); EDD WARN; CEC awards; IBank; Regulated Site Portal.
- **Not read:** Cal/OSHA pressure vessel database conditions of use. No lookups have been made.
- **Found on the way:** four Weld rows known only from an incentive agreement (ranks 65, 66, 146, 147 in run 5) carry the county basis "Weld permit layer (Weld only)", which is the wrong wording for them. The stored Weld output was left as it is.
