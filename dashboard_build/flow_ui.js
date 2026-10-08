/* ---------- Steel flow tab: flowchart + waterfalls ---------- */
const F=D.flow;
const f2=n=>n==null?'–':(n/1000).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
const sg=n=>Math.abs(n)<5?'0.00':(n<0?'−':'+')+f2(Math.abs(n));
const kr=(a,b)=>b>0&&a<=b*1.0005?pc(a,b):(b>0?'>100%':'–');
const pc=(a,b)=>b>0?(a/b*100).toLocaleString('en-IN',{maximumFractionDigits:1,minimumFractionDigits:1})+'%':'–';
const PERL=Object.fromEntries(F.periods.map(p=>[p[0],p[1]]));
const CLS={tot:'Stage total',sub:'Carried to the next stage',out:'Leaves the chain as a product / sold as is',loss:'Loss or not converted',in:'Added from outside the chain'};
const COL={tot:'--imp',sub:'--sub',out:'--exp',loss:'--bad',in:'--good'};
function steps(route){
 const e=st.fent,p=st.fper,V=F.v[e][p],g=k=>V[k]||0,pub=e==='All India'?F.pub[p]:null,S=[];let run=0;
 const lvl=(label,v,cls,bal)=>{const d=v-run;
  if(S.length&&bal&&Math.abs(d)>3)S.push({label:d<0?bal[0]:bal[1],cls:d<0?'loss':'in',a:run,b:v,v:d,bal:true});
  S.push({label,cls,a:0,b:v,v});run=v};
 const stp=(label,d,cls)=>{S.push({label,cls:cls||(d<0?'out':'in'),a:run,b:run+d,v:d});run+=d};
 const trans=(lo,hi,d)=>d<=0?lo:hi;
 lvl('Crude steel',g('crude'),'tot');
 lvl('Finished steel (all grades)',g('fin'),'tot',['Yield loss, semis sold, stock change','Bought-in semis / stock draw']);
 if(route==='flat'){
  stp('Long products',-g('nonflat'));
  stp('Alloy & stainless flat',-(g('alloy_flat')+g('ss_flat')));
  stp('Plate-mill plates',-g('pm'));
  lvl('HR coil / strip',g('hr'),'tot',['Other flat not in HR coil','Other flat, unallocated']);
  const hf=pub&&pub.hrfeed!=null?pub.hrfeed:g('hrs')+g('hsm')+g('pipes')+g('cr');
  stp(trans('HR sold as HR / not processed','Bought-in HR (not own production)',hf-g('hr')),hf-g('hr'));
  lvl('HR fed to downstream',hf,'sub');
  stp('HR sheets',-g('hrs'));stp('HSM plates',-g('hsm'));stp('Large-dia pipes',-g('pipes'));
  lvl('CR coil / sheets',g('cr'),'tot',['Processing loss / unaccounted','Bought-in HR / stock draw']);
  const cf=pub&&pub.crfeed!=null?pub.crfeed:g('gpgc')+g('elec')+g('tin')+g('tfs')+g('tmbp');
  stp(trans('CR sold as CR / not processed','Bought-in CR',cf-g('cr')),cf-g('cr'));
  lvl('CR fed to downstream',cf,'sub');
  stp('Electrical steel',-g('elec'));stp('Tin plate, TFS & TMBP',-(g('tin')+g('tfs')+g('tmbp')));
  lvl('GP / GC incl. galvalume (BGL)',g('gpgc'),'tot',['Processing loss / unaccounted','Bought-in CR, imports / stock draw']);
  const gf=pub&&pub.gpfeed!=null?pub.gpfeed:g('cc');
  stp(trans('GP / GC / BGL sold as is','Bought-in GP / GC',gf-g('gpgc')),gf-g('gpgc'));
  lvl('Fed to colour coating',gf,'sub');
  lvl('Colour coated (PPGI / PPGL)',g('cc'),'tot',['Processing loss','Bought-in colour coated']);
 }else{
  stp('Flat products',-g('flat'));
  lvl('Long products',g('nonflat'),'tot',['Other','Other']);
  stp('Alloy long',-g('alloy_nf'));stp('Stainless long',-g('ss_nf'));
  lvl('Non-alloy long',g('bars')+g('struct')+g('rly'),'sub',['Unallocated','Unallocated']);
  stp('Angles, channels, beams (structurals)',-g('struct'));stp('Railway materials',-g('rly'));
  lvl('Bars & rods',g('bars'),'tot',['Unallocated','Unallocated']);
  stp('Wire rods',-g('wire'));stp('Plain rounds',-g('plain'));stp('Other bars',-g('others_b'));
  lvl('Rebars (TMT)',g('rebar'),'tot',['Unallocated','Unallocated']);
 }
 return S}
function wfSvg(S,aria){
 const W=920,L=265,R=64,rh=27,top=8,n=S.length,H=top+n*rh+26,crude=S[0].v;
 const mx=Math.max(...S.map(s=>Math.max(s.a,s.b)),1),mn=Math.min(0,...S.map(s=>Math.min(s.a,s.b)));
 const x=v=>L+(v-mn)/(mx-mn)*(W-L-R);
 const raw=(mx-mn)/5,e=Math.pow(10,Math.floor(Math.log10(raw))),tk=[1,2,2.5,5,10].map(k=>k*e).find(v=>v>=raw);
 let s=`<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${aria}" style="min-width:640px;display:block">`;
 for(let v=Math.ceil(mn/tk)*tk;v<=mx+1e-6;v+=tk)s+=`<line x1="${x(v)}" x2="${x(v)}" y1="${top}" y2="${H-22}" stroke="var(--grid)"/><text x="${x(v)}" y="${H-8}" text-anchor="middle">${f2(v)}</text>`;
 S.forEach((r,i)=>{const y=top+i*rh+4,h=rh-8,x1=x(Math.min(r.a,r.b)),w=Math.max(x(Math.max(r.a,r.b))-x1,1.5),isT=r.cls==='tot'||r.cls==='sub';
  const tip=isT?`${r.label}: ${f2(r.v)} Mt · ${pc(r.v,crude)} of crude steel`:`${r.label}: ${sg(r.v)} Mt · ${pc(Math.abs(r.v),Math.abs(r.a))} of the level before · ${pc(Math.abs(r.v),crude)} of crude steel`;
  if(i>0){const pv=S[i-1];s+=`<line x1="${x(pv.b)}" x2="${x(pv.b)}" y1="${top+(i-1)*rh+4+h}" y2="${y}" stroke="var(--ink3)" stroke-dasharray="2 2"/>`}
  s+=`<g data-tip="${tip}"><rect x="0" y="${y-4}" width="${W}" height="${rh}" fill="transparent"/>`
   +`<text x="${L-8}" y="${y+h/2+4}" text-anchor="end" ${isT?'class="v"':''}>${isT?'':'↳ '}${r.label}</text>`
   +`<rect x="${x1}" y="${y}" width="${w}" height="${h}" rx="3" fill="var(${COL[r.cls]})" ${r.bal?'fill-opacity=".75"':''}/>`
   +`<text class="v" x="${x(Math.max(r.a,r.b))+6}" y="${y+h/2+4}">${isT?f2(r.v):sg(r.v)}</text></g>`});
 return s+'</svg>'}
function wfTable(S){const crude=S[0].v;
 return `<details><summary>Show as table</summary><div class="scroll"><table><thead><tr><th>Step</th><th>Type</th><th>Mt</th><th>'000 t</th><th>% of crude</th></tr></thead><tbody>`
 +S.map(r=>{const t=r.cls==='tot'||r.cls==='sub';return `<tr><td>${t?'':'↳ '}${r.label}</td><td>${CLS[r.cls]}</td><td>${t?f2(r.v):sg(r.v)}</td><td>${Math.round(r.v).toLocaleString('en-IN')}</td><td>${pc(Math.abs(r.v),crude)}</td></tr>`}).join('')+`</tbody></table></div></details>`}
function chips(arr){return arr.map(([n,v,base])=>`<div class="chip" data-tip="${n}: ${f2(v)} Mt${base?' · '+pc(v,base)+' of crude steel':''}"><span>${n}</span><b>${f2(v)}</b>${base?`<i>${pc(v,base)}</i>`:''}</div>`).join('<span class="arr">→</span>')}
function flowView(){
 const e=st.fent,p=st.fper,V=F.v[e][p],g=k=>V[k]||0,pub=e==='All India'?F.pub[p]:null,cr=g('crude');
 const hf=pub&&pub.hrfeed!=null?pub.hrfeed:g('hrs')+g('hsm')+g('pipes')+g('cr'),cf=pub&&pub.crfeed!=null?pub.crfeed:g('gpgc')+g('elec')+g('tin')+g('tfs')+g('tmbp'),gf=pub&&pub.gpfeed!=null?pub.gpfeed:g('cc');
 const est=pub?'':' (est.)';
 const kp=[['Crude steel → HR coil',kr(g('hr'),cr),`${f2(g('hr'))} of ${f2(cr)} Mt`],['HR fed to downstream'+est,kr(hf,g('hr')),`${f2(hf)} of ${f2(g('hr'))} Mt HR coil`],['CR fed to downstream'+est,kr(cf,g('cr')),`${f2(cf)} of ${f2(g('cr'))} Mt CR`],['GP/GC painted into PPGI/PPGL'+est,kr(gf,g('gpgc')),`${f2(gf)} of ${f2(g('gpgc'))} Mt GP/GC`]];
 const per=(ids,list)=>seg(ids,list.map(k=>[k,PERL[k]]),st.fper);
 const opts=F.entities.map(n=>`<option${n===e?' selected':''}>${n}</option>`).join('');
 const lg=Object.keys(CLS).map(k=>`<span><i style="background:var(${COL[k]})"></i>${CLS[k]}</span>`).join('');
 const SF=steps('flat'),SL=steps('long');
 return `<h2 style="font:600 22px var(--fc);margin:0 0 4px">Steel flow – from crude steel to downstream</h2>
 <p class="note" style="margin-bottom:10px">Where the steel goes, stage by stage, in million tonnes. ${e} · ${PERL[p]}${F.periods.find(q=>q[0]===p)[2]==='cum'?' (April to date)':' (single month)'}</p>
 <div class="bar"><label class="lab">Period</label>${per('fpa',['c8','c7','c6','c5'])}${per('fpb',['m8','m7','m6'])}<label class="lab" style="margin-left:8px" for="fe">Producer</label><select id="fe">${opts}</select></div>
 <div class="kpis">${kp.map(k=>`<div class="kpi"><span>${k[0]}</span><b>${k[1]}</b><span>${k[2]}</span></div>`).join('')}</div>
 <div class="panel"><h2>Process flow</h2><p class="note">Boxes show the selected period in Mt; the % is the share of crude steel. Inputs are alternative routes, so they do not add up to crude steel.</p>
  <div class="frow"><div class="fl">Iron-making and steel-making</div><div class="chips"><div class="grp4">${[['Pellets',g('pellets')],['Sponge iron (DRI)',g('sponge')],['Hot metal (BF)',g('hotmetal')],['Pig iron',g('pig')]].map(([n,v])=>`<div class="chip mini" data-tip="${n}: ${f2(v)} Mt"><span>${n}</span><b>${f2(v)}</b></div>`).join('')}</div><span class="arr">→</span>${chips([['Crude steel',g('crude'),cr],['Finished steel',g('fin'),cr]])}</div></div>
  <div class="frow"><div class="fl">Flat route</div><div class="chips">${chips([['Flat finished',g('flat'),cr],['HR coil / strip',g('hr'),cr],['CR coil / sheets',g('cr'),cr],['GP / GC / BGL',g('gpgc'),cr],['PPGI / PPGL',g('cc'),cr]])}</div></div>
  <div class="frow"><div class="fl">Long route</div><div class="chips">${chips([['Long finished',g('nonflat'),cr],['Non-alloy long',g('bars')+g('struct')+g('rly'),cr],['Bars & rods',g('bars'),cr],['Rebars (TMT)',g('rebar'),cr]])}</div></div></div>
 <div class="panel"><h2>Flat products waterfall</h2><p class="note">Crude steel down to HR coil, then each downstream stage. Blue bars are what each stage produced, teal is what moved on to the next stage, the rest are exits.</p>
  <div class="leg">${lg}</div><div class="scroll">${wfSvg(SF,'Waterfall of flat steel from crude steel to colour coated')}</div>${wfTable(SF)}</div>
 <div class="panel"><h2>Long products waterfall</h2><p class="note">Crude steel down to rebars. Angles and structurals, rails, wire rods and the rest are grouped as long products.</p>
  <div class="leg">${lg}</div><div class="scroll">${wfSvg(SL,'Waterfall of long steel from crude steel to rebars')}</div>${wfTable(SL)}</div>
 <div class="panel"><h2>How to read this</h2><ul class="notes">
  <li><b>All India:</b> “HR / CR / GP-GC fed to downstream” are JPC’s own <i>consumed for downstream</i> figures (Chapter 5). For a single producer JPC publishes no such number, so it is estimated as the output of the next stage taken 1:1 (no yield loss).</li>
  <li><b>“&gt;100%”</b> in a box above means the producer processes more than it makes at the stage before, so it buys coil.</li>
  <li><b>Balancing bars</b> (red or green) make each stage tie to the reported production. Red is yield loss, stock build or unaccounted material. Green is material that came from outside the chain, such as imports, bought-in coil or stock draw. A producer with more downstream output than HR coil (for example JSL and “The remaining producers”) shows a large green bar: it buys coil.</li>
  <li><b>Colour coated:</b> JPC’s GP/GC-consumed-for-downstream equals colour-coated output exactly, so that step has no loss. JPC does not split PPGL from PPGI, or GP/GC from galvalume sales.</li>
  <li><b>Alloy and stainless flat</b> come out before HR coil because JPC’s HR coil line is non-alloy only; their own downstream is not tracked here.</li>
  <li><b>Periods:</b> April-only and May-only figures are not available because JPC prints the April category tables as images. Single months are the difference between consecutive April-to-date reports, so JPC’s later revisions are already included.</li></ul></div>`}
