# County configs

One file per county. `build_v3.py --county adams` loads `county_configs/adams.py`. `denver.py` is the working example; `_template.py` is the starting point.

Before the first run of a new county you need:

1. `<county>_zip_share.json` in the scripts folder. One command makes it: `python3 build_zip_share.py <county>` (downloads the Census 2020 ZCTA-to-county relationship file once into `census_cache/`, git-ignored; share = ZCTA land area inside the county / total ZCTA land area, the same formula as `denver_zip_share.json`; `python3 build_zip_share.py denver --check` proves it). The build exits with a message if the file is missing.
2. The AIRS prefix (county FIPS code). Confirm it against the APCD file.
3. `LOCAL_LAYERS`. Denver's own permit and site plan layers are read when it is True and `LOCAL_PERMIT_FILES` is None. For another county set it True and name the Step 3 county files (relative to the step 4 folder): `LOCAL_PERMIT_FILES` (permit files, read as the permit layer) and `LOCAL_PLAN_FILES` (planning, development and site-plan files, read as the planning layer), plus `LOCAL_PERMIT_LABEL` and `LOCAL_PLAN_LABEL` for the sources column. `v3_local.py` maps the shared 17-column rows onto the fields the Denver code expects (its docstring gives the mapping); the points table does not change. Added for Adams on 2026-10-31.
4. Mailing cities. A county that is not also a city needs `MAIL_CITIES` (mailing cities wholly inside the county) and `SPLIT_CITIES` (cities that straddle the line, placed by zip share and geocoder only). Denver needs neither.
5. `PERSON_NAMED`: name keys of registered entities named after private individuals that Matthew has decided to leave out of every listing. Optional.
6. `STEP3_OCCUPIERS` and `KNOWN_TIES` carry occupiers and entity ties that Step 2 or Step 3 documented (an incentive agreement, a permit description naming the tenant). Only ones backed by a document.

After any edit to the scripts, rerun `--county denver` and compare with the committed Denver output. It must match.
