import json,re,pandas as pd
r=json.load(open('trade.json'))
num=re.compile(r'^-?\d+\.\d+$')
def monthly(lines):
    out={}; buf=[]; i=0
    while i<len(lines):
        if num.match(lines[i]):
            j=i; v=[]
            while j<len(lines) and num.match(lines[j]): v.append(float(lines[j])); j+=1
            if len(v)==6:
                lab=' '.join(buf).upper(); buf=[]
                out[lab]=v
            else: buf=[]
            i=j
        else:
            if lines[i] not in('CATEGORY',) and not re.match(r'^(Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|TOTAL|26|27)[- ]?',lines[i]) : buf.append(lines[i])
            i+=1
    return out
M={}
for f in('import','export'):
    M[f]=monthly(r['monthly']['August'][f])
    print(f,list(M[f]))

def pick(f,key):
    for k,v in M[f].items():
        if key in k: return v[:5]
    raise KeyError(key)
MON=["Apr","May","Jun","Jul","Aug"]
# product -> (monthly key, country-table column, kind)
P=[("HRC","H.R.COILS","HR Coil/Strip","prod","Flat"),
   ("HR Sheet","H.R.SHEETS","HR Sheets","prod","Flat"),
   ("HR Plate","4. PLATES","Plates","prod","Flat"),
   ("CR Coil","C.R.SHEETS","CR Coil/Sheets","prod","Flat"),
   ("GP/GC (incl. BGL)","8. GP & GC","GP/GC (incl. Galvalume)","prod","Coated"),
   ("PPGL/PPGI","COLOR COATED","GP/GC (incl. Galvalume)","prod","Coated"),
   ("TMT / Bars & Rods","1. BARS","Bars & Rods","prod","Long"),
   ("Angles & Structurals","2. STRUCTURALS","Structurals","prod","Long"),
   ("Railway Materials","3. RLY","Rly Materials","prod","Long"),
   ("Pig Iron","PIG IRON","Pig Iron","semi","Long"),
   ("Billets / Semis","BILLETS","Non-Alloy Semis","semi","Long"),
   ("Pipes","13. PIPES","Pipes","prod","Flat"),
   ("Electrical Sheets","10. ELEC","Elec Sheets","prod","Flat"),
   ("Tin Plate","11. TINPLATE","Tin Plates","prod","Flat"),
   ("Alloy & SS Non-Flat","ALLOY & SS NON","Alloy/Stainless","none","Long"),
]
CUM=["April","May","June","July","August"]
def countries(flow,col,kind):
    # monthly = diff of cumulative
    names=[n for n in r['country']['August'][flow][kind] if n not in('TOTAL',)]
    res={}
    for n in names:
        cum=[r['country'][m][flow][kind].get(n,{}).get(col,0.0) for m in CUM]
        mon=[round(cum[0],1)]+[round(cum[i]-cum[i-1],1) for i in range(1,5)]
        res[n.title() if n not in('UAE','USA','U.K.') else n]=mon
    return res
out={"months":MON,"products":[]}
for name,key,col,kind,grp in P:
    e={"name":name,"group":grp}
    for f in('import','export'):
        e[f]=pick(f,key)
        if kind!='none':
            e[f+"_countries"]=countries(f,col,kind)
    out["products"].append(e)
# NB: PPGL/PPGI uses combined GP/GC+colour-coated country table
for e in out["products"]:
    if e["name"]=="PPGL/PPGI":
        e["country_note"]="JPC reports countries only for GP/GC and Colour Coated combined"
        e["import_countries"]=[p for p in out["products"] if p["name"].startswith("GP/GC")][0]["import_countries"]
        e["export_countries"]=[p for p in out["products"] if p["name"].startswith("GP/GC")][0]["export_countries"]
    if e["name"].startswith("GP/GC"): e["country_note"]="Country split covers GP/GC + colour coated together (JPC does not split galvalume or PPGL by country)"
    if e["name"]=="Billets / Semis": e["country_note"]="Country split is for all non-alloy semis (billets, slabs, re-rollables)"
    if e["name"]=="TMT / Bars & Rods": e["country_note"]="JPC reports Bars & Rods in total; TMT is not split out"
# producer data
import flow_build as fb
x=fb.load_book()
PR=["SAIL","RINL","NSL","TSL Group","AM/NS (ESSAR)","JSL(JSPL)","JSW Group","The Remaining Producers"]
prod={}
pc=x['Prod_by_Category']; pc=pc[(~pc.prior_year_table)]
dn=x['Downstream_by_Producer']; dn=dn[~dn.prior_year_table]
def series(df,cat,seg):
    d=df[(df.category==cat)&(df.segment==seg)]
    o={}
    for rm,g in d.groupby('report_month'):
        o[rm]={"cum":{p:float(g[g.producer==p].value.sum()) for p in PR+["All India"]},
               "mon":{p:(None if g[g.producer==p].value_month.isna().all() else float(g[g.producer==p].value_month.sum())) for p in PR+["All India"]}}
    return o
prod["HRC"]=series(pc,'Hr Coil/Strip','Non-Alloy')
prod["HR Plate (plate mill)"]=series(pc,'Pm Plates','Non-Alloy')
prod["HR Plate (HSM)"]=series(dn,'Hsm Plates','Non-Alloy')
prod["HR Sheet"]=series(dn,'Hr Sheets','Non-Alloy')
prod["CR Coil"]=series(dn,'Cr Coil/Sheets','Non-Alloy')
prod["GP/GC (incl. BGL)"]=series(dn,'Gp/Gc Sheets/Coil','Non-Alloy')
prod["PPGL/PPGI"]=series(dn,'Color Coated Coils/Sheet','Non-Alloy')
prod["TMT / Bars & Rods"]=series(pc,'Bars & Rods','Non-Alloy')
prod["Angles & Structurals"]=series(pc,'Structurals','Non-Alloy')
prod["Railway Materials"]=series(pc,'Rly. Materials','Non-Alloy')
prod["Pipes"]=series(dn,'Pipes (Large Dia.)','Non-Alloy')
b=x['Bifurcation_GPGC_Bars']
def bser(cat):
    d=b[b.category==cat]; o={}
    for rm,g in d.groupby('report_month'):
        o[rm]={"cum":{p:float(g[g.producer==p].value.sum()) for p in PR+["All India"]},
               "mon":{p:(None if g[g.producer==p].value_month.isna().all() else float(g[g.producer==p].value_month.sum())) for p in PR+["All India"]}}
    return o
prod["Galvalume (BGL)"]=bser('Galvalume')
# the sheet repeats Rebars / Wire Rods / Plain Rounds for alloy, non-alloy and stainless blocks: take the non-alloy block only
def bnon(key):
    nb=fb.bars_nonalloy(b); o={}
    for i,rm in enumerate(fb.RMS):
        cum={p:float(nb[rm][key].get(p,0)) for p in PR+["All India"]}
        mon=None if i==0 else {p:cum[p]-float(nb[fb.RMS[i-1]][key].get(p,0)) for p in cum}
        o[rm]={"cum":cum,"mon":mon if mon else {p:None for p in cum}}
    return o
prod["Rebars (TMT)"]=bnon("rebar"); prod["Wire Rods"]=bnon("wire"); prod["Plain Rounds"]=bnon("plain")
out["production"]=prod; out["producers"]=PR
json.dump(out,open('data.json','w'))
e=out["products"][2]; print(e['name'],e['import'],e['export']); print(list(e['export_countries'].items())[:3])
for k in("Galvalume (BGL)","HR Plate (HSM)"):
    print(k, {rm:(v['cum']['All India'],v['mon']['All India']) for rm,v in prod[k].items()})
print(len(json.dumps(out)))

s=x['Summary_Production']
def sser(metric):
    d=s[s.metric==metric]; o={}
    for rm,g in d.groupby('report_month'):
        o[rm]={"cum":{p:float(g[g.producer==p].cumulative.sum()) for p in PR+["All India"]},
               "mon":{p:(None if g[g.producer==p].month.isna().all() else float(g[g.producer==p].month.sum())) for p in PR+["All India"]}}
    return o
out["production"]["Pig Iron"]=sser('Pig Iron')
out["production"]["Billets / Semis"]=series(pc,'Semis','Semis')
json.dump(out,open('data.json','w'))
print({rm:(v['cum']['All India'],v['mon']['All India']) for rm,v in out["production"]["Pig Iron"].items()})
print({rm:(v['cum']['All India'],v['mon']['All India']) for rm,v in out["production"]["Billets / Semis"].items()})
print({rm:(v['cum']['All India'],v['mon']['All India']) for rm,v in out["production"]["HRC"].items()})

out['flow']=fb.build_flow(x,out['products'])
json.dump(out,open('data.json','w'))
print('flow added',len(json.dumps(out['flow'])))
print('Rebars All India cum Aug',out['production']['Rebars (TMT)']['August 2026']['cum']['All India'])
