"""Step 6: read contact ROLE (title) and ORGANISATION columns for chosen permits from the WQCD sheet.
Never reads out or writes first names, last names, phones, emails or mailing addresses."""
import sys, re, json, warnings, datetime as dt
warnings.simplefilter("ignore")
import openpyxl
xlsx = sys.argv[1]; out = sys.argv[2]
wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
ws = wb[wb.sheetnames[0]]
it = ws.iter_rows(values_only=True)
header = [str(h).strip() if h is not None else "" for h in next(it)]
H = {h: i for i, h in enumerate(header)}
if "--header" in sys.argv:
    print(len(header)); print(header); sys.exit()
blocks = [h[:-len("Organization")] for h in header if h.endswith("Organization")]
ADDR = re.compile(r"^(19300 E\.? 72|19301 E\.? 70|7190 N?\.? ?Tower|4301 N?\.? ?Forest|4735 N?\.? ?Florence|60 N?\.? ?Yuma|8250 E\.? 40|4555 N?\.? ?York|3939 N?\.? ?Kearney|4500 N?\.? ?Lipan|3750 N?\.? ?Nome|5150 N?\.? ?Brighton|11795 E|10660 E|4545 N?\.? ?Madison|4450 N?\.? ?Madison|4460 N?\.? ?Madison|2401 W\.? 6th|1925 S\.? Rosemary|11645 E\.? 37|95 S\.? Tejon|4990 N?\.? ?Ironton|3100 N?\.? ?Brighton|2550 W\.? 2nd|4398 N?\.? ?Broadway|4823 N?\.? ?Lima|12850 E\.? 40)", re.I)
NAME = re.compile(r"(pepsi|cb manufact|project mustang|high ?point|safeway milk|conagra|king soopers bak|quality lining|nestle|purina|adams mcclure|dawn food|lakin|truckwash|srm concrete|smyrna ready|titan fitt|titan adv|blazy|cargill|frito|amcor|steel house|pacific air|custom stone|native foods|intertech|big metal|never summer|r ?b machine|verde prickly|hearth baking|co-innovate|copeland ent|starko|lemon powers)", re.I)
def t(v):
    if v is None: return ""
    if isinstance(v, (dt.datetime, dt.date)): return v.strftime("%Y-%m-%d")
    return str(v).strip()
rows = []
for r in it:
    if r is None: continue
    g = lambda c: t(r[H[c]]) if c in H and H[c] < len(r) else ""
    fac, addr, city, county = g("FacilityName"), g("FacilityAddress1"), g("FacilityCity"), g("FacilityCounty")
    perm = g("Permittee")
    if not (ADDR.search(addr) or NAME.search(fac) or NAME.search(perm) or NAME.search(g("PropertyOwnerOrganization")) or NAME.search(g("OperatorOrganization"))):
        continue
    if not (city.upper() == "DENVER" or county.upper() == "DENVER"): continue
    rec = {k: g(k) for k in ["PermitID","GeneralPermitType","PermitSector","PermitStatus","ApplicationReceivedDate","IssuedDate","TerminationDate","Permittee","FacilityName","FacilityCity","FacilityCounty","FacilityZip","FacilitySICCode","SWConstructionActivity","SWConstructionDisturbedAcres","SWConstructionStartDate","SWConstructionEndDate","FacilityDescription","ActivityDescription"] if k in H}
    rec["FacilityAddress"] = addr
    rec["contacts"] = []
    lt=g("LegalTitle")
    if lt or g("LegalLName"):
        rec["contacts"].append({"block":"Legal","org":perm+" (permittee)","title":lt,"has_person":bool(g("LegalLName")),"city":g("LegalCity"),"state":g("LegalState")})
    for b in blocks:
        org = g(b + "Organization"); title = g(b + "Title") if (b + "Title") in H else ""
        has_person = bool(g(b + "FName") or g(b + "LName") or g(b+"FirstName") or g(b+"LastName"))
        if org or title or has_person:
            rec["contacts"].append({"block": b, "org": org, "title": title, "has_person": has_person, "city": g(b+"City"), "state": g(b+"State")})
    rows.append(rec)
json.dump(rows, open(out, "w"), indent=1)
print(len(rows), "rows; blocks:", blocks)
