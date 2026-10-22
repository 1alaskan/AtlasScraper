import csv,re,sys,os,json,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import reflag_step4b as R
csv.field_size_limit(10**9)
OUT=sys.argv[1]; BASE=sys.argv[2]
def nk(s):
    s=s.upper(); s=re.sub(r"[^A-Z0-9 ]"," ",s); s=re.sub(r"\b(THE|INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLP)\b"," ",s); return re.sub(r"\s+"," ",s).strip()
# aliases: from step5 analysis_notes.md and step3 ground_truth_projects*.csv. Used ONLY for this check, never for flagging.
P={
'D01 PepsiCo':(['PEPSI','CB MANUFACTURING'],['19300 E 72','19301 E 70','7190 TOWER','6972 ARGONNE','3801 BRIGHTON']),
'D02 Swire Coca-Cola (cancelled)':(['SWIRE','COCA COLA'],['3825 YORK']),
'D03 4 Noses Brewing':(['4 NOSES','FOUR NOSES','4NB HOLDINGS'],['4040 DAHLIA']),
'D04 Wilding Brands Canworks':(['WILDING BRANDS','DENVER BEER'],['4455 JASON']),
'D06 Full Frame Beer':(['FULL FRAME BEER'],['1139 20']),
'D07 BrewDog Denver':(['BREWDOG'],['3950 WYNKOOP']),
'D08 Monolith Brewing':(['MONOLITH BREW'],['1290 S BROADWAY']),
'D09 Cheetah Coalition':(['CHEETAH COALITION','GOLDSPOT','GOLD SPOT BREW','FLOWER SHOP BEER','NEON BUZZ'],['4970 LOWELL']),
'D10 Rebel Bread':(['REBEL BREAD'],['675 S BROADWAY']),
'D11 Elemental Bakery':(['ELEMENTAL BAKERY'],['3875 STEELE']),
'D12 Azure Printed Homes':(['AZURE PRINTED'],[]),
'D13 Vinyl Me Please plant':(['VINYL ME PLEASE','VINYL MEDIA PRESSING'],['4201 BRIGHTON']),
'D14 SRM Concrete':(['SRM CONCRETE','SMYRNA READY MIX'],['5150 BRIGHTON','1145 QUIVAS']),
'D15 Maybell Quantum':(['MAYBELL'],['3821 STEELE']),
'X06 NextRun hub (Direct Polymers)':(['DIRECT POLYMERS','NEXTRUN','NEXT RUN'],['3600 E 45']),
'X12 Crazy Shirts':(['CRAZY SHIRTS'],['4747 IVY']),
'X13 Sara Gabriel':(['SARA GABRIEL'],['1325 S INCA','1575 BOULDER']),
}
files=[('ucc',os.path.join(OUT,'scrape_ucc_filings','scrape_ucc_filings_v2.csv')),('reg',os.path.join(OUT,'scrape_business_registrations','scrape_business_registrations_v2.csv')),('permits',os.path.join(OUT,'scrape_denver_commercial_permits_v2.csv'))]
for n in ['scrape_denver_site_plans.csv','scrape_state_water_permits.csv','scrape_apcd_permit_status.csv','scrape_mile_high_cre.csv','scrape_oedit_approvals.csv']:
    files.append((n[7:-4],os.path.join(BASE,n)))
hits=collections.defaultdict(list)
for src,f in files:
    for r in csv.DictReader(open(f,newline='',encoding='utf-8-sig')):
        name=nk(r['company_name']+' '+r.get('facility_name','')+' '+r.get('permittee','')+' '+r.get('owner','')) ; ak=R.addr_key(r['site_address'])
        txt=nk(r.get('description','')) if src in('mile_high_cre',) else ''
        for p,(names,addrs) in P.items():
            how=None
            if any(n in name for n in names): how='name'
            elif any(n in txt for n in names): how='name in text'
            if any(ak==a or ak.startswith(a+' ') or (ak.startswith(a) and len(ak)>len(a) and not ak[len(a)].isdigit() and a[-1].isdigit()==False) for a in addrs):
                how=(how+'+address') if how else 'address only'
            if how:
                tier=r.get('flag_tier', 'A' if r['flag']=='Y' else '')
                hits[p].append(dict(src=src,how=how,tier=tier,flag=r['flag'],date=r['record_date'],id=r['record_id'],name=r['company_name'][:40],addr=r['site_address'][:40]+' '+r.get('location_detail',''),city=r['city'],rule=r.get('flag_rule_v2') or r['flag_rule'],extra=(r.get('valuation','')+' '+r.get('class','')+' '+r.get('parcel_class','')+' '+r.get('zone_district','')+' | '+r.get('description','')[:90]+' | '+r.get('secured_party','')[:40]+' | '+r.get('entity_status','')+' '+r.get('transaction_type',''))))
json.dump(hits,open(os.path.join(OUT,'gt_hits.json'),'w'),indent=1)
for p in P:
    h=hits.get(p,[])
    print('\n##',p,len(h))
    for x in sorted(h,key=lambda x:(x['tier']=='' ,x['src'],x['date'])):
        if x['tier'] or len(h)<25:
            print(f"  [{x['tier'] or '-'}] {x['src']:8} {x['how']:14} {x['date']} {x['name'][:30]:30} | {x['addr'][:34]:34} | {x['rule'][:70]} || {x['extra'][:150]}")
    print('  untiered rows:',sum(1 for x in h if not x['tier']))
