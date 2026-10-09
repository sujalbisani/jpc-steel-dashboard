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
 const hf=F.pub[p]&&F.pub[p].hrfeed!=null?F.pub[p].hrfeed:0;
 const chk=[['HR coil production',`${an(g('hr')).toFixed(1)} Mt`,`Deck FY26E ${DECK.prod[0]} · FY27P ${DECK.prod[1]} Mt`,`Within ${Math.abs(Math.round((an(g('hr'))/DECK.prod[0]-1)*100))}% of the deck's FY26E. The deck's FY27P assumes growth from here.`],
  ['Plate production',`${an(g('pm')).toFixed(1)} Mt`,`Deck FY26E ${DECK.plate[0]} · FY27P ${DECK.plate[1]} Mt`,'Plate-mill plates match the deck closely.'],
  ['CR coil output (≈ captive HR)',`${an(g('cr')).toFixed(1)} Mt`,`Deck "captive" FY26E ${DECK.captive[0]} · FY27P ${DECK.captive[1]} Mt`,'The deck’s captive HR is almost exactly India’s CR output. So "captive" means HR turned into CR by the same company.'],
  ['JPC "HR fed to downstream"',hf?`${an(hf).toFixed(1)} Mt`:'–','Not the same thing as the deck’s captive',`Larger because JPC also counts HR going into pipes (${an(g('pipes')).toFixed(1)} Mt), HR sheets and HSM plates.`]];
 return `<h2 style="font:600 22px var(--fc);margin:0 0 4px">Capacity &amp; utilisation</h2>
 <p class="note" style="margin-bottom:10px">HR coil production by producer (JPC actuals, annualised) against mill capacity from the HR Strategy deck. Capacity and the comparison figures are JSW estimates from its HR Strategy deck (ABP FY27), not JPC data. ${PERL[p]}${F.periods.find(q=>q[0]===p)[2]==='cum'?' (April to date)':' (single month)'} × ${k.toFixed(2)}.</p>
 <div class="bar ctl"><label class="lab">Period</label>${per('fpa',['c8','c7','c6','c5'])}${per('fpb',['m8','m7','m6'])}</div>
 <div class="panel"><h2>Utilisation by producer (against FY27P capacity)</h2><p class="note">Grey is capacity, blue is annualised HR coil output. Figures are Mt per year.</p>${rows.map(bar).join('')}
  <p class="note" style="margin-top:10px"><b>Reading it:</b> AM/NS is measured against 10.1 Mt, which includes the new Hazira capacity still ramping up. Against 7.1 Mt (FY26) it runs near full. JSPL is low because JPC reports most of its Angul output as plate, not HR coil. "Others" is above 100% because the deck’s 6.0 Mt looks too small for all remaining mills.</p>${tbl}</div>
 <div class="panel"><h2>Does the deck agree with JPC?</h2><div class="kpis">${chk.map(c=>`<div class="kpi"><span>${c[0]}</span><b>${c[1]}</b><span>${c[2]}</span><span style="margin-top:6px;color:var(--ink)">${c[3]}</span></div>`).join('')}</div>
  <p class="note" style="margin-top:10px">All India HR coil is ${pcI(an(g('hr')),DECK.tot[1])} of FY27P capacity, against ${DECK.util[1]}% in the deck. JPC counts non-alloy HR coil only, and April–August includes the monsoon dip, so the full year may come out higher.</p></div>`}
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
rep(" if(st.sel==='flow'){wire('fpa'", " if(st.sel==='cap'){wire('fpa',k=>st.fper=k);wire('fpb',k=>st.fper=k)}else if(st.sel==='flow'){wire('fpa'")
rep("</style>", CSS)
out = os.path.join(here, "..", "jpc_dashboard.html")
open(out, "w", encoding="utf-8").write(h)
print("written", out)
