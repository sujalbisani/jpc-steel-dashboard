import pymupdf, re, json, sys
D = sys.argv[1]; OUT = sys.argv[2]
MONTHS = ["April","May","June","July","August"]
num = re.compile(r'^-?\d+\.\d+$')
def lines(page): return [l.strip() for l in page.get_text().split('\n') if l.strip()]
def rows(ls):
    """rows = [(name, [floats])] from SL | NAME | values... streams"""
    out=[]; i=0
    while i < len(ls):
        if re.fullmatch(r'\d+', ls[i]) and i+1 < len(ls) and re.search('[A-Za-z]', ls[i+1]) and not num.match(ls[i+1]):
            name=ls[i+1]; j=i+2; vals=[]
            while j<len(ls) and num.match(ls[j]): vals.append(float(ls[j])); j+=1
            if vals: out.append((name,vals))
            i=j
        elif ls[i]=='TOTAL':
            j=i+1; vals=[]
            while j<len(ls) and num.match(ls[j]): vals.append(float(ls[j])); j+=1
            if vals: out.append(('TOTAL',vals))
            i=j
        else: i+=1
    return out
PROD_IMP=["Bars & Rods","Structurals","Rly Materials","Plates","HR Sheets","HR Coil/Strip","CR Coil/Sheets","GP/GC (incl. Galvalume)","Elec Sheets","TMBP","Tin Plates","Tin Free Steel","Pipes","Total Finished (Non-Alloy)","Alloy/Stainless","Grand Total"]
PROD_EXP=[p for p in PROD_IMP if p!="TMBP"]
SEMI=["Finished Steel","Non-Alloy Semis","Alloy/SS Semis","Fittings","Melting Scrap","Pig Iron","Sponge Iron","Ferro Alloys","Misc","Grand Total"]
res={"country":{}, "monthly":{}}
for m in MONTHS:
    d=pymupdf.open(f"{D}/Trade Report - {m} 2026.pdf")
    for flow in ("import","export"):
        res["country"].setdefault(m,{}).setdefault(flow,{"prod":{},"semi":{}})
    for pi in range(len(d)):
        ls=lines(d[pi]); head=' '.join(ls[:25])
        if 'Country' not in head and 'Country-Wise' not in ' '.join(ls): continue
        if 'Quantity' not in head and 'Quantity' not in ' '.join(ls[:40]): continue
        flow='import' if 'Import Reports' in head else 'export' if 'Export Reports' in head else None
        if not flow: continue
        for name,vals in rows(ls):
            n=len(vals)
            cols=PROD_IMP if flow=='import' else PROD_EXP
            if n==len(cols): res["country"][m][flow]["prod"][name]=dict(zip(cols,vals))
            elif n==len(SEMI): res["country"][m][flow]["semi"][name]=dict(zip(SEMI,vals))
    # monthwise product table (Aug has Apr-Aug); take from each report: last-5 numbers rows
    d_idx=None
    for pi in range(len(d)):
        t=d[pi].get_text()
        for flow,key in (("import","Monthwise IMPORTS"),("export","Month wise EXPORTS")):
            if key in t:
                res["monthly"].setdefault(m,{})[flow]=[l.strip() for l in t.split('\n') if l.strip()]
json.dump(res,open(OUT,'w'))
for m in MONTHS:
    for f in ("import","export"):
        c=res["country"][m][f]; print(m,f,len(c["prod"]),len(c["semi"]), 'TOTAL' in c["prod"])
