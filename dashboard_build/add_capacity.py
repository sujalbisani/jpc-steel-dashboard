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

 const NJ='JSW Group',NT='TSL Group',NS='SAIL',NA='AM/NS (ESSAR)',NO='Others';
 /* owner group, owner in 2026, plant, CR, galvanised (HDG), colour coated (PPGI), galvalume (GL), galvannealed (GA); Mt/yr, capacity chart (2021) */
 const PL=[[NJ,'JSW Steel','Bellary (Vijayanagar)',3.18,0,0,0,.40],[NJ,'JSW Steel','Kalmeshwar',.90,.66,.22,.24,0],[NJ,'JSW Steel','Vasind',.50,.16,.28,.24,0],[NJ,'JSW Steel','Tarapur',.42,.16,.24,.24,0],
  [NJ,'BPSL (JSW since 2021)','Odisha',.72,.06,.12,.36,0],[NJ,'BPSL (JSW since 2021)','Chandigarh',.14,0,0,0,0],[NJ,'BPSL (JSW since 2021)','Kolkata',.24,.11,0,0,0],
  [NT,'Tata Steel / BSL','Dhenkanal',.60,0,.30,.18,0],[NT,'Tata Steel / BSL','Sahibabad',.96,.30,.18,.14,0],[NT,'Tata Steel / BSL','Khopoli',.48,.18,.10,.29,0],[NT,'Tata Steel / BSL','Jamshedpur',2.20,.56,0,.24,.17],
  [NS,'SAIL','Rourkela',1.40,.17,0,0,0],[NS,'SAIL','Bokaro',1.20,.53,0,0,0],[NS,'SAIL','Salem',.43,0,0,0,0],
  [NA,'AM/NS India','Hazira',1.44,.90,0,0,0],[NA,'AM/NS India','Pune',.60,.50,.40,0,0],[NA,'AM/NS India (ex Uttam Galva, 2022)','Khopoli',.72,.60,.18,0,0],[NA,'AM/NS India (ex Indian Steel Corp, 2023)','Gandhidham',.54,.36,.12,0,0],
  [NO,'POSCO','Pune',2.28,.45,0,0,0],[NO,'Uttam Galva','Wardha',.30,.12,0,0,0],[NO,'ACCIL','Khopoli',.42,.30,.10,0,0],[NO,'ACCIL','Bawal',.30,.24,.06,0,0],[NO,'NSAIL','Indore',.34,.22,.10,.14,0],
  [NO,'Vardhman (chart: Vardhman/JSW)','Ludhiana',.12,.10,.05,0,0],[NO,'Tata BlueScope (joint venture)','Jamshedpur',0,0,.14,.24,0],[NO,'STI','Shahjahanpur',.04,.11,0,0,0],[NO,'JIL','Kolkata',.22,.24,0,.15,0],[NO,'Stelco','Ludhiana',.18,.10,0,0,0],
  [NO,'Jai Corp','Nanded',.10,.10,0,0,0],[NO,'Assam Asbestos','Guwahati',.12,.18,0,0,0],[NO,'Assam Asbestos','Meghalaya',0,0,.06,0,0],[NO,'Manaksia','Kolkata',0,.06,.04,0,0],[NO,'Manaksia','Gandhidham',0,0,.04,0,0],
  [NO,'Steelco Gujarat','Vadodara',.12,.10,.06,0,0],[NO,'Goodluck','Ghaziabad',.12,.05,0,0,0],[NO,'Ruchi Strips','Indore',.06,0,0,0,0],[NO,'Hero Cycle','Ludhiana',.17,0,0,0,0],[NO,'Avery','Ludhiana',.07,0,0,0,0],
  [NO,'ITW','Hyderabad',.06,0,0,0,0],[NO,'Pennar','Hyderabad',.12,0,0,0,0],[NO,'Other narrow cold reducers','',.60,0,0,0,0],[NO,'CRIL','Khopoli',0,0,.06,0,0],[NO,'Color Shine','Nellore',0,0,.12,0,0],[NO,'SriSol','Silvassa',0,0,.10,0,0],
  [NO,'Ralco','Vizag',0,0,.06,0,0],[NO,'Steel Center','Ludhiana',0,0,.09,0,0],[NO,'Latim','Umbergaon',0,0,.10,.10,0],[NO,'Prabhat','Khopoli',0,0,.06,0,0],
  [NO,'Not itemised in the photo (chart total minus rows read)','',.52,2.69,0,0,0]];
 /* additions since the chart, counted only in the 2026 view */
 const AD=[[NA,'AM/NS India','Hazira pickling line and tandem cold mill',2.0,0,0,0,0,'Inaugurated 30 April 2026'],[NT,'Tata Steel','Kalinganagar cold rolling mill',1.5,0,0,0,0,'Listed as under commissioning on the chart; first galvanising line running since August 2025'],
  [NJ,'JSW Steel','Vasind',1.0,0,0,0,0,'Listed as under commissioning on the chart; start not confirmed'],[NJ,'JSW Steel','Tarapur',1.0,0,0,0,0,'Listed as under commissioning on the chart; start not confirmed'],
  [NO,'Shyam Metalics','Jamuria galvanising / galvalume line',0,0,0,.15,0,'Commercial production from 16 April 2026'],[NO,'Jindal (India)','Ranihati colour coating line',0,0,.275,0,0,'First coil 18 May 2026']];
 const u=st.capu==='uc',fam=r=>[r[3],r[4]+r[6]+r[7],r[5]],ents=[NJ,NT,NS,NA,NO],en={[NJ]:'JSW (incl. BPSL)',[NT]:'Tata Steel / BSL',[NS]:'SAIL',[NA]:'AM/NS (incl. Uttam Khopoli, ISC)',[NO]:'All other producers'};
 const rowsAll=[...PL,...(u?AD:[])],cap={};ents.forEach(e=>cap[e]=[0,0,0]);rowsAll.forEach(r=>{fam(r).forEach((x,i)=>cap[r[0]][i]+=x)});
 const jo=(e,i)=>{const v=F.v[e][p];return an([v.cr,v.gpgc,v.cc][i]||0)};
 const out={};[NJ,NT,NS,NA].forEach(e=>out[e]=[0,1,2].map(i=>jo(e,i)));const on=['cr','gpgc','cc'].map(k=>an(g(k)));out[NO]=[0,1,2].map(i=>on[i]-[NJ,NT,NS,NA].reduce((s,e)=>s+out[e][i],0));
 const ct=[0,1,2].map(i=>ents.reduce((s,e)=>s+cap[e][i],0));
 const cell=(c,o)=>`<td>${c.toFixed(2)}</td><td>${o.toFixed(1)}</td><td>${c>0?pcI(o,c):'–'}</td>`;
 const ctab=`<div class="scroll"><table><thead><tr><th rowspan="2">Producer</th><th colspan="3">Cold rolled (CR)</th><th colspan="3">Galvanised / galvalume (GP/GC)</th><th colspan="3">Colour coated</th></tr><tr><th>Capacity</th><th>Output</th><th>Util.</th><th>Capacity</th><th>Output</th><th>Util.</th><th>Capacity</th><th>Output</th><th>Util.</th></tr></thead><tbody>`
  +ents.map(e=>`<tr><td>${en[e]}</td>${cell(cap[e][0],out[e][0])}${cell(cap[e][1],out[e][1])}${cell(cap[e][2],out[e][2])}</tr>`).join('')
  +`<tr class="grp"><td>All India</td>${cell(ct[0],on[0])}${cell(ct[1],on[1])}${cell(ct[2],on[2])}</tr></tbody></table></div>`;
 const f2c=x=>x?x.toFixed(2):'–';
 const ptab=`<details class="mini" style="margin-top:12px"><summary>Plant-wise capacity (${rowsAll.length} rows)</summary><div class="scroll"><table><thead><tr><th>Owner in 2026</th><th>Plant</th><th>CR</th><th>Galvanised</th><th>Colour coated</th><th>Galvalume</th><th>Galvannealed</th><th>Status</th></tr></thead><tbody>`
  +rowsAll.map(r=>`<tr><td>${r[1]}</td><td>${r[2]}</td><td>${f2c(r[3])}</td><td>${f2c(r[4])}</td><td>${f2c(r[5])}</td><td>${f2c(r[6])}</td><td>${f2c(r[7])}</td><td>${r[8]||'2021 chart'}</td></tr>`).join('')+`</tbody></table></div></details>`;
 const cpanel=`<div class="panel"><h2>Cold-rolled and coated lines</h2><p class="note">Plant capacity from the mills' capacity chart (Mt a year, <b>2021 data</b>), grouped by who owns each plant in 2026, against JPC output annualised from ${PERL[p]}. Over 100% means the mill has added capacity since 2021 or buys in coil. Galvanised / galvalume capacity is the HDG, GL and GA lines together; colour coated is the PPGI column.</p>
  <div class="bar">${seg('capu',[['2021','2021 chart'],['uc','2026 view (known additions)']],st.capu||'2021')}</div>${ctab}${ptab}
  <p class="note" style="margin-top:10px"><b>Ownership changes applied:</b> Bhushan Power &amp; Steel is JSW (since 2021); Uttam Galva’s Khopoli plant and Indian Steel Corporation are AM/NS (since 2022 and 2023); Uttam’s Wardha plant stays with other producers. <b>The 2026 view adds</b> the six lines marked with a date or status in the plant table. <b>Not added, because not confirmed running:</b> Tata’s Tarapur galvanising line (0.7 Mt, planned), AM/NS Hazira galvanising lines, Manaksia Haldia colour coating, and the JSW Khopoli, Toranagallu and Rajpura lines due in 2028. Every other plant is still its 2021 figure; I could not find reliable 2026 line capacity for them. Photo figures are read by eye, so check before quoting them.</p></div>`;
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
