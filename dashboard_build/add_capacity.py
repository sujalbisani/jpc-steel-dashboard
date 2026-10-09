"""Adds the 'Capacity & utilisation' tab to ../jpc_dashboard.html (run by refresh.py after the main build). Capacity figures: JSW HR Strategy deck (ABP FY27), JSW estimates."""
import os
here = os.path.dirname(os.path.abspath(__file__))
h = open(os.path.join(here, "..", "jpc_dashboard.html"), encoding="utf-8").read()

def rep(a, b):
    global h
    assert a in h, a
    h = h.replace(a, b, 1)

CAP_JS = r'''
/* ---------- PRIVATE: capacity & utilisation (deck: HR Strategy Meet ABP FY27, JSW estimates, Mt) ---------- */
const DECK={cap:{'JSW Group':[25.3,25.3],'TSL Group':[18.6,18.6],'SAIL':[7.2,7.2],'JSL(JSPL)':[5.0,5.0],'AM/NS (ESSAR)':[7.1,10.1],'NSL':[3.0,3.0],'The Remaining Producers':[6.0,6.0]},
 name:{'JSW Group':'JSW','TSL Group':'Tata Steel','SAIL':'SAIL','JSL(JSPL)':'JSPL (Angul)','AM/NS (ESSAR)':'AM/NS','NSL':'NMDC Steel (Nagarnar)','The Remaining Producers':'Others (incl. RINL)'},
 tot:[72.2,75.2],prod:[64.4,69.2],captive:[25.1,27.4],plate:[5.5,6.8],plateCap:[8.1,9.1],util:[89,92]};
const AF={c8:12/5,c7:12/4,c6:12/3,c5:12/2,m8:12,m7:12,m6:12};
const pcI=(a,b)=>b>0?Math.round(a/b*100)+'%':'–';
function capView(){const p=st.fper,k=AF[p],A=F.v['All India'][p],g=x=>A[x]||0,an=v=>v/1000*k;
 const per=(ids,list)=>seg(ids,list.map(q=>[q,PERL[q]]),st.fper);
 const rows=Object.keys(DECK.cap).map(e=>{const v=an(F.v[e][p].hr||0),c=DECK.cap[e];return {e,v,c26:c[0],c27:c[1]}});
 const sum=rows.reduce((s,r)=>s+r.v,0)+an(F.v['RINL'][p].hr||0),mx=Math.max(...rows.map(r=>Math.max(r.v,r.c27)));
 const bar=r=>`<div class="cr" data-tip="${DECK.name[r.e]}: ${r.v.toFixed(1)} Mt annualised of ${r.c27.toFixed(1)} Mt capacity (FY27P)"><span class="l">${DECK.name[r.e]}</span><div class="ct"><div class="cc" style="width:${r.c27/mx*100}%"></div><div class="cf" style="width:${Math.min(r.v,mx)/mx*100}%"></div></div><span class="v">${r.v.toFixed(1)} / ${r.c27.toFixed(1)}</span><b class="${r.v/r.c27>1.02?'bad':''}">${pcI(r.v,r.c27)}</b></div>`;
 const tbl=`<div class="scroll"><table><thead><tr><th>Producer</th><th>HR coil Apr–Aug (Mt)</th><th>Annualised (Mt)</th><th>Capacity FY26</th><th>Capacity FY27P</th><th>Util. vs FY26</th><th>Util. vs FY27P</th></tr></thead><tbody>`
  +rows.map(r=>{const raw=(F.v[r.e][p].hr||0)/1000;return `<tr><td>${DECK.name[r.e]}</td><td>${raw.toFixed(2)}</td><td>${r.v.toFixed(1)}</td><td>${r.c26.toFixed(1)}</td><td>${r.c27.toFixed(1)}</td><td>${pcI(r.v,r.c26)}</td><td>${pcI(r.v,r.c27)}</td></tr>`}).join('')
  +`<tr class="grp"><td>All India</td><td>${(g('hr')/1000).toFixed(2)}</td><td>${an(g('hr')).toFixed(1)}</td><td>${DECK.tot[0]}</td><td>${DECK.tot[1]}</td><td>${pcI(an(g('hr')),DECK.tot[0])}</td><td>${pcI(an(g('hr')),DECK.tot[1])}</td></tr></tbody></table></div>`;

 const CC={rows:[['JSW Group','JSW (incl. BPSL)',[6.10,1.15,0.90,1.48]],['TSL Group','Tata Steel / BSL',[4.24,0.98,0.58,1.02]],['SAIL','SAIL',[3.03,0.70,0,0]],['AM/NS (ESSAR)','AM/NS (incl. Uttam Khopoli, ISC)',[3.30,2.36,0.70,0]]],tot:[22.93,10.25,3.42,2.79],uc:{'JSW Group':[2.0,0,0,0],'TSL Group':[1.5,0,0,0]}};
 const u=st.capu==='uc',ad=e=>u&&CC.uc[e]?CC.uc[e]:[0,0,0,0];
 const jo=(e,i)=>{const v=F.v[e][p];return an([v.cr,v.gpgc,v.cc][i]||0)};
 const cpr=CC.rows.map(([e,n,c])=>{const cap=c.map((x,i)=>x+ad(e)[i]);return {n,cap,o:[jo(e,0),jo(e,1)||0,jo(e,2)]}});
 const ct=CC.tot.map((x,i)=>x+(u?Object.values(CC.uc).reduce((s,a)=>s+a[i],0):0)),on=['cr','gpgc','cc'].map(k=>an(g(k)));
 const nm=cpr.reduce((s,r)=>s.map((x,i)=>x+r.cap[i]),[0,0,0,0]),no=cpr.reduce((s,r)=>s.map((x,i)=>x+r.o[i]),[0,0,0]);
 const ot=[on[0]-no[0],on[1]-no[1],on[2]-no[2]],oc=[ct[0]-nm[0],ct[1]-nm[1],ct[2]-nm[2],ct[3]-nm[3]];
 const cu=(o,c)=>c>0?`<td>${pcI(o,c)}</td>`:`<td>–</td>`,cell=(r,c,o)=>`<td>${c.toFixed(2)}</td><td>${o.toFixed(1)}</td>${cu(o,c)}`;
 const rr=[...cpr.map(r=>[r.n,r.cap,r.o]),['All other producers',oc,ot]],ctab=`<div class="scroll"><table><thead><tr><th rowspan="2">Producer</th><th colspan="3">Cold rolled (CR)</th><th colspan="3">Galvanised / galvalume (GP/GC)</th><th colspan="3">Colour coated</th></tr><tr><th>Capacity</th><th>Output</th><th>Util.</th><th>Capacity</th><th>Output</th><th>Util.</th><th>Capacity</th><th>Output</th><th>Util.</th></tr></thead><tbody>`
  +rr.map(([n,c,o])=>`<tr><td>${n}</td>${cell(n,c[0],o[0])}${cell(n,c[1]+c[3],o[1])}${cell(n,c[2],o[2])}</tr>`).join('')
  +`<tr class="grp"><td>All India</td>${cell('',ct[0],on[0])}${cell('',ct[1]+ct[3],on[1])}${cell('',ct[2],on[2])}</tr></tbody></table></div>`;
 const cpanel=`<div class="panel"><h2>Cold-rolled and coated lines</h2><p class="note">Line capacity from the mills' capacity chart (Mt a year, <b>2021 data</b>) against JPC output annualised from ${PERL[p]}. Over 100% means the mill has added capacity since 2021 or buys in coil. Galvanised / galvalume capacity is the HDG, GL and GA lines together; colour coated is the PPGI column.</p>
  <div class="bar">${seg('capu',[['2021','2021 chart'],['uc','Add units then under commissioning']],st.capu||'2021')}</div>${ctab}
  <p class="note" style="margin-top:10px">Units then under commissioning, added in the second view: JSW Vasind and Tarapur (2.0 Mt CR) and Tata Kalinganagar (1.5 Mt CR). AM/NS includes Hazira and Pune plus two plants it has bought since: Uttam Galva’s Khopoli (0.72 CR, 0.60 galvanised, 0.18 colour coated) and Indian Steel Corporation, Gandhidham (0.54, 0.36, 0.12). Uttam’s Wardha plant stays under other producers. Other changes since 2021 are not in the chart. Photo figures are read by eye and a few were hard to read, so check before quoting them.</p></div>`;
 return `<h2 style="font:600 22px var(--fc);margin:0 0 4px">Capacity &amp; utilisation</h2>
 <p class="note" style="margin-bottom:10px">HR coil production by producer (JPC actuals, annualised) against mill capacity from the HR Strategy deck. Capacity and the comparison figures are JSW estimates from its HR Strategy deck (ABP FY27), not JPC data. ${PERL[p]}${F.periods.find(q=>q[0]===p)[2]==='cum'?' (April to date)':' (single month)'} × ${k.toFixed(2)}.</p>
 <div class="bar ctl"><label class="lab">Period</label>${per('fpa',['c8','c7','c6','c5'])}${per('fpb',['m8','m7','m6'])}</div>
 <div class="panel"><h2>Utilisation by producer (against FY27P capacity)</h2><p class="note">Grey is capacity, blue is annualised HR coil output. Figures are Mt per year.</p>${rows.map(bar).join('')}
  <p class="note" style="margin-top:10px"><b>Reading it:</b> AM/NS is measured against 10.1 Mt, which includes the new Hazira capacity still ramping up. Against 7.1 Mt (FY26) it runs near full. JSPL is low because JPC reports most of its Angul output as plate, not HR coil. "Others" is above 100% because the deck’s 6.0 Mt looks too small for all remaining mills.</p>${tbl}</div>${cpanel}`}
'''
CSS = '''.cr{display:grid;grid-template-columns:150px minmax(0,1fr) 92px 44px;gap:10px;align-items:center;padding:5px 0}.cr .l{font-size:13px}.cr .v{font-size:12px;color:var(--ink2);text-align:right}.cr b{font:600 13px var(--fc);text-align:right}.cr b.bad{color:var(--bad)}
.ct{position:relative;height:14px}.cc{position:absolute;inset:0 auto 0 0;background:var(--grid);border-radius:3px}.cf{position:absolute;inset:3px auto 3px 0;background:var(--imp);border-radius:2px}
.priv{font:600 11px var(--f);border:1px solid var(--bad);color:var(--bad);border-radius:4px;padding:1px 6px;margin-left:6px;vertical-align:middle}
@media(max-width:700px){.cr{grid-template-columns:100px minmax(0,1fr) 40px}.cr .v{display:none}}
</style>'''
rep("function render(){chrome();nav();", CAP_JS + "function render(){chrome();nav();")
rep("""<button data-p="" aria-current="${cur(null)}">Import / export overview</button>""",
    """<button data-p="" aria-current="${cur(null)}">Import / export overview</button><button data-p="cap" aria-current="${cur('cap')}">Capacity &amp; utilisation</button>""")
rep("b.dataset.p==='flow'?'flow':+b.dataset.p", "isNaN(+b.dataset.p)?b.dataset.p:+b.dataset.p")
rep("$('#crumb').textContent=st.sel==='flow'?'Steel flow':", "$('#crumb').textContent=st.sel==='cap'?'Capacity & utilisation':st.sel==='flow'?'Steel flow':")
rep("$('#main').innerHTML=st.sel==='flow'?flowView():", "$('#main').innerHTML=st.sel==='cap'?capView():st.sel==='flow'?flowView():")
rep(" if(st.sel==='flow'){wire('fpa'", " if(st.sel==='cap'){wire('fpa',k=>st.fper=k);wire('fpb',k=>st.fper=k);wire('capu',k=>st.capu=k)}else if(st.sel==='flow'){wire('fpa'")
rep("</style>", CSS)
out = os.path.join(here, "..", "jpc_dashboard.html")
open(out, "w", encoding="utf-8").write(h)
print("written", out)
