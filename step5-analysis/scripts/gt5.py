import csv,sys,re,collections,json
sys.path.insert(0,'.'); import rerank_step5b as X
R=X.R; csv.field_size_limit(10**9)
P={
'D01 PepsiCo':(['PEPSI','CB MANUFACTURING'],['19300 E 72','19301 E 70','7190 TOWER','6972 ARGONNE','3801 BRIGHTON']),
'D02 Swire Coca-Cola (cancelled)':(['SWIRE COCA','COCA COLA'],['3825 YORK']),
'D03 4 Noses Brewing':(['4 NOSES','FOUR NOSES','4NB HOLDINGS'],['4040 DAHLIA']),
'D04 Wilding Brands Canworks':(['WILDING BRANDS','DENVER BEER'],['4455 JASON']),
'D06 Full Frame Beer':(['FULL FRAME BEER'],['1139 20']),
'D07 BrewDog Denver':(['BREWDOG'],['3950 WYNKOOP']),
'D08 Monolith Brewing':(['MONOLITH BREW'],['1290 S BROADWAY']),
'D09 Cheetah Coalition':(['CHEETAH COALITION','GOLDSPOT','FLOWER SHOP BEER','NEON BUZZ'],['4970 LOWELL']),
'D10 Rebel Bread':(['REBEL BREAD'],['675 S BROADWAY']),
'D11 Elemental Bakery':(['ELEMENTAL BAKERY'],['3875 STEELE']),
'D12 Azure Printed Homes':(['AZURE PRINTED'],[]),
'D13 Vinyl Me Please plant':(['VINYL ME PLEASE','VINYL MEDIA PRESSING'],['4201 BRIGHTON']),
'D14 SRM Concrete':(['SRM CONCRETE','SMYRNA READY MIX'],['5150 BRIGHTON','1145 QUIVAS']),
'D15 Maybell Quantum':(['MAYBELL QUANTUM'],['3821 STEELE']),
'X06 NextRun hub (Direct Polymers)':(['DIRECT POLYMERS','NEXTRUN'],['3600 E 45','3601 E 44']),
'X12 Crazy Shirts':(['CRAZY SHIRTS'],['4747 IVY']),
'X13 Sara Gabriel':(['SARA GABRIEL'],['1325 S INCA']),
}
def run(d,verbose=True):
    rk=list(csv.DictReader(open(d+'/denver_ranked_accounts_v2.csv',newline='',encoding='utf-8')))
    ev=list(csv.DictReader(open(d+'/denver_evidence_v2.csv',newline='',encoding='utf-8')))
    evby=collections.defaultdict(list)
    for e in ev: evby[e['rank']].append(e)
    res={}
    for p,(names,addrs) in P.items():
        hits=[]
        for x in rk:
            nm=X.nk(x['company_name']+' '+x['name_variants'])
            how=None
            if any(n in nm for n in names): how='name'
            keys={R.addr_key(x['site_address'])}|{R.addr_key(e['site_address']) for e in evby[str(x['rank'])] if e['added_in']=='step5b' or e['match_class']=='confirmed'}
            if any(k==a for k in keys for a in addrs): how=(how+'+address') if how else 'address only'
            if how: hits.append((int(x['rank']),how,x['company_name'][:50],x['site_address'][:28],x['score'],x['tier'],x['rank_before']))
        res[p]=hits
        if verbose:
            print(p,'->',hits if hits else 'not ranked')
    return res,rk
res,rk=run('out')
json.dump({p:[list(h) for h in v] for p,v in res.items()},open('out/gt5.json','w'))
old=set(x['company_name']+'|'+x['site_address'] for x in rk if x['rank_before'] and int(x['rank_before'])<=25)
def top(d,n=25):
    r=list(csv.DictReader(open(d+'/denver_ranked_accounts_v2.csv',newline='',encoding='utf-8')))[:n]
    return [x['company_name'][:40]+' @ '+x['site_address'][:22] for x in r]
b=top('out'); h=top('out_half'); dd=top('out_dbl')
o=[x['company_name'][:40]+' @ '+x['site_address'][:22] for x in sorted([x for x in rk if x['rank_before']],key=lambda x:int(x['rank_before']))[:25]]
print('\nTOP25 vs Step 5: in',[x for x in b if x not in o],'\n out',[x for x in o if x not in b])
print('half B pts: in',[x for x in h if x not in b],' out',[x for x in b if x not in h])
print('double B pts: in',[x for x in dd if x not in b],' out',[x for x in b if x not in dd])
r2=list(csv.DictReader(open('out/denver_ranked_accounts_v2.csv',newline='',encoding='utf-8')))
den=[x for x in r2 if not x['county_basis'].startswith(('Denver mailing','OEDIT'))]
print(len(r2),len(den),sum(1 for x in den if float(x['score'])>=50), collections.Counter(x['tier'] for x in den), sum(1 for x in den if x['company_name'].startswith('Unattached')))
print(collections.Counter(x['tier'] for x in r2[:100]))
