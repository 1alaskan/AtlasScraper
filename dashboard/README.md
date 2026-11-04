# Streamlit site

`streamlit_app.py` (repo root) shows every finished county: ranked accounts, the evidence rows behind each account with source links, the run notes, and a cross-county view. It is deployed on Streamlit Community Cloud from the `main` branch and redeploys on every push.

## Register a county after its analysis step

Run from the repo root, pointing at the final build of the run (the one the notes describe):

```
python3 dashboard/register_county.py --slug {county} --name "{COUNTY} County" \
  --version v3 --run-date <YYYY-MM-DD of the build> \
  --ranked step5-analysis/{county}/{county}_ranked_accounts_v3.csv \
  --evidence step5-analysis/{county}/{county}_evidence_v3.csv \
  --notes step5-analysis/{county}/{county}_analysis_notes.md \
  --extra-notes step5-analysis/{county}/review_findings.md
```

Re-running with the same `--slug` replaces that county's entry in `dashboard/counties.json`.

The ranked file must keep the standard columns (`rank, company_name, name_variants, site_address, zip, county_basis, stage, score, sources_count, sources, first_signal_date, latest_signal_date, top_evidence, compressed_air_fit, match_confidence, in_ground_truth, next_step, tier`) and the evidence file the shared columns plus `rank` and `points`; the site filters on them.

Smoke-test before pushing (install with `pip install --break-system-packages -r requirements.txt` if needed):

```
python3 -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('streamlit_app.py', default_timeout=120).run(); assert not at.exception, at.exception; print('ok')"
```

Then `git add dashboard/counties.json` and push to `main`.

## Run it locally

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```
