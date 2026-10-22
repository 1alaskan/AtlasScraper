# County configs

One file per county. `build_v3.py --county adams` loads `county_configs/adams.py`. `denver.py` is the working example; `_template.py` is the starting point.

Before the first run of a new county you need:

1. `<county>_zip_share.json` in the scripts folder. One command makes it: `python3 build_zip_share.py <county>` (downloads the Census 2020 ZCTA-to-county relationship file once into `census_cache/`, git-ignored; share = ZCTA land area inside the county / total ZCTA land area, the same formula as `denver_zip_share.json`; `python3 build_zip_share.py denver --check` proves it). The build exits with a message if the file is missing.
2. The AIRS prefix (county FIPS code). Confirm it against the APCD file.
3. `LOCAL_LAYERS = False` until the county has permit or site plan loaders. The v3 code reads those layers only for Denver.

After any edit to the scripts, rerun `--county denver` and compare with the committed Denver output. It must match.
