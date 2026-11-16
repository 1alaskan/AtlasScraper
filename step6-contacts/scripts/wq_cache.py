"""Step 6: turn the WQCD sheet into a slim JSON cache with NO personal fields.
Keeps permit, facility, permittee and, per contact block, only organisation, title, city, state.
Usage: python3 -I wq_cache.py active_permits.xlsx wq_cache.json"""
import sys, json, warnings, datetime as dt
warnings.simplefilter("ignore")
import openpyxl
ws = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True).worksheets[0]
it = ws.iter_rows(values_only=True)
header = [str(h).strip() if h is not None else "" for h in next(it)]
H = {h: i for i, h in enumerate(header)}
blocks = [h[:-len("Organization")] for h in header if h.endswith("Organization")]
def t(v):
    if v is None: return ""
    if isinstance(v, (dt.datetime, dt.date)): return v.strftime("%Y-%m-%d")
    return str(v).strip()
KEEP = ["PermitID","GeneralPermitType","PermitStatus","ApplicationReceivedDate","IssuedDate","TerminationDate","Permittee","FacilityName","FacilityAddress1","FacilityCity","FacilityZip","FacilityCounty","FacilitySICCode","SWConstructionActivity","SWConstructionDisturbedAcres"]
out = []
for r in it:
    if r is None or r[H["PermitID"]] is None: continue
    g = lambda c: t(r[H[c]]) if c in H and H[c] < len(r) else ""
    rec = {k: g(k) for k in KEEP}
    cs = []
    if g("LegalTitle") or g("LegalLName"):
        cs.append(["Legal", rec["Permittee"], g("LegalTitle"), g("LegalCity"), g("LegalState")])
    for b in blocks:
        if g(b + "Organization") or g(b + "Title") or g(b + "LName"):
            cs.append([b, g(b + "Organization"), g(b + "Title"), g(b + "City"), g(b + "State")])
    rec["c"] = cs
    out.append(rec)
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "rows cached")
