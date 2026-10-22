# Step 5 v3 scripts

One command rebuilds the Denver County ranking from the Step 4 files:

```
python3 build_v3.py <step4-scrape folder> <step5-analysis folder>
```

On Matthew's computer, from this folder:

```
python3 build_v3.py "../../../step4-scrape" "../.."
```

Output goes to `<step5-analysis>/v3/` (change it with `--out <folder>`):

- `denver_ranked_accounts_v3.csv`
- `denver_evidence_v3.csv`
- `rank_changes_v3.csv` (rows that moved more than 10 places against the tier B run, with the cause)
- `v3_report.json` (cut counts, ground-truth check, sensitivity runs, rank changes)

Then, optionally:

```
python3 verify_v3.py <v3 output folder>      # recomputes every score from the evidence file; prints "problems: 0" when the two files agree
python3 report_v3.py <v3 output folder>      # prints the cut table, top 25, ground truth and sensitivity as Markdown
```

Standard library only (Python 3.8 or later). About 40 seconds.

## What it reads

- Step 4: `scrape_ucc_filings/scrape_ucc_filings_v2.csv`, `scrape_business_registrations/scrape_business_registrations_v2.csv`,
  `scrape_denver_commercial_permits_v2.csv`, `scrape_denver_site_plans.csv`, `scrape_state_water_permits.csv`,
  `scrape_apcd_permit_status.csv`, `scrape_mile_high_cre.csv`, `scrape_oedit_approvals.csv`,
  `scrape_ucc_filings/ucc_b1a_fulltext_hits.csv`.
- This folder: `denver_zip_share.json` (share of each zip inside Denver County, Census 2020 ZCTA file) and
  `geocode_cache.json` (151 addresses already looked up).
- Step 5: `denver_ranked_accounts.csv` and `denver_ranked_accounts_v2.csv`, only to fill `rank_step5` and `rank_step5b`
  and the rank-change report. The ranking itself does not use them. If they are missing the two columns are blank.

## The geocoder

The only web call is the Census geocoder, and only for addresses not in `geocode_cache.json`. With the cache shipped
here a Denver re-run makes no web call. After a new scrape there will be new addresses: the script looks them up at one
a second, saves as it goes, and stops after 150 seconds with exit code 3 and the message "Run the same command again to
continue". Run it again until it finishes. `--offline` skips the lookups and treats uncached addresses as "could not place".

## Files

| File | What it does |
|---|---|
| `build_v3.py` | The one command. Ranks, writes the CSVs and the report, runs the sensitivity re-weightings. |
| `v3_signals.py` | Scope test and noise cuts. Turns flagged rows into signals and counts every cut. |
| `v3_resolve.py` | Resolution: one account per company or unattached address, address joins, reach into the full files. |
| `v3_score.py` | Scoring, stage and fit rules. |
| `v3_lib.py` | Constants, the fixed points table, name and address normalisers, file readers. |
| `v3_config.py` | Word lists for the cuts and fit rules, the web checks, the two Step 3 ties, the 17 ground-truth projects. |
| `v3_geocode.py` | Cached, resumable Census geocoder lookups. |
| `verify_v3.py` | Self-check of the two output files. |
| `report_v3.py` | Prints the report as Markdown. |

## Another county

See "How to re-run for another county" in `analysis_notes_v3.md`. In short: replace `denver_zip_share.json`, the AIRS
prefix and county name in `v3_signals.py`, and drop the two Denver-only layers.
