"""Builds the 'Steel flow' data block (crude steel -> HR -> CR -> GP/GC -> colour coated, plus the long-product split)
from the sheets of jpc_consolidated.xlsx. All figures in '000 tonnes. Called from build.py."""
import pandas as pd

PR = ["SAIL", "RINL", "NSL", "TSL Group", "AM/NS (ESSAR)", "JSL(JSPL)", "JSW Group", "The Remaining Producers"]
ENT = ["All India"] + PR
RMS = ["May 2026", "June 2026", "July 2026", "August 2026"]          # reports that carry the producer x category tables
PERIODS = [("c8", "Apr–Aug", "cum", 3), ("c7", "Apr–Jul", "cum", 2), ("c6", "Apr–Jun", "cum", 1), ("c5", "Apr–May", "cum", 0),
           ("m8", "Aug", "mon", 3), ("m7", "Jul", "mon", 2), ("m6", "Jun", "mon", 1)]   # (key, label, kind, index into RMS)

PBC = {"crude": ("Semis", "Semis"), "fin": ("All Grades", "Total Finished Steel"), "flat": ("All Grades", "Total(Flat)"),
       "nonflat": ("All Grades", "Total(Non-Flat)"), "alloy_flat": ("Alloy", "Flat"), "ss_flat": ("Stainless", "Flat"),
       "alloy_nf": ("Alloy", "Non-Flat"), "ss_nf": ("Stainless", "Non-Flat"), "hr": ("Non-Alloy", "Hr Coil/Strip"),
       "pm": ("Non-Alloy", "Pm Plates"), "bars": ("Non-Alloy", "Bars & Rods"), "struct": ("Non-Alloy", "Structurals"),
       "rly": ("Non-Alloy", "Rly. Materials")}
DS = {"cr": "Cr Coil/Sheets", "hrs": "Hr Sheets", "hsm": "Hsm Plates", "pipes": "Pipes (Large Dia.)", "gpgc": "Gp/Gc Sheets/Coil",
      "cc": "Color Coated Coils/Sheet", "elec": "Electrical Coils/Sheets", "tin": "Tin Plates (Incl Ww)", "tfs": "Tin Free Steel", "tmbp": "Tmbp"}
SUM = {"hotmetal": "Hot Metal", "sponge": "Sponge Iron", "pig": "Pig Iron", "pellets": "Pellets"}


def load_book(src="../jpc_consolidated.xlsx"):
    """Read the workbook; if Excel has it locked, read a copy made with the shell (which shares the file), or the path in JPC_XLSX."""
    import os, subprocess, tempfile
    if os.environ.get("JPC_XLSX"): return pd.read_excel(os.environ["JPC_XLSX"], sheet_name=None)
    try: return pd.read_excel(src, sheet_name=None)
    except PermissionError:
        t = os.path.join(tempfile.gettempdir(), "jc_copy.xlsx")
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Copy-Item -LiteralPath '{os.path.abspath(src)}' -Destination '{t}' -Force"], check=True)
        return pd.read_excel(t, sheet_name=None)


def bars_nonalloy(b):
    """Rebars / wire rods / plain rounds / others for NON-ALLOY bars. The bifurcation sheet repeats these names for alloy,
    non-alloy and stainless, so pick the block that sits next to 'Total Bars & Rods (Non - Alloy)' (file order: Others, Plain Rounds,
    Rebars, Total, Wire Rods)."""
    out = {}
    for rm in RMS:
        d = b[b.report_month == rm].reset_index(drop=True)
        groups, prev = [], None
        for i, c in enumerate(d.category):
            if c != prev:
                groups.append([c, i]); prev = c
        names = [g[0] for g in groups]
        j = names.index("Total Bars & Rods (Non - Alloy)")
        want = {"others_b": (j - 3, "Others"), "plain": (j - 2, "Plain Rounds"), "rebar": (j - 1, "Rebars"), "wire": (j + 1, "Wire Rods")}
        res = {}
        for k, (gi, nm) in want.items():
            assert names[gi] == nm, (rm, k, names[gi])
            s = groups[gi][1]
            blk = d.iloc[s:s + 9]
            res[k] = dict(zip(blk.producer, blk.value))
        blk = d.iloc[groups[j][1]:groups[j][1] + 9]
        tot = dict(zip(blk.producer, blk.value))
        for p in ENT:   # the four parts must add back to the published non-alloy total
            assert abs(sum(res[k].get(p, 0) for k in res) - tot[p]) <= 3, (rm, p)
        out[rm] = res
    return out


def build_flow(x):
    pc = x["Prod_by_Category"]; pc = pc[~pc.prior_year_table]
    dn = x["Downstream_by_Producer"]; dn = dn[~dn.prior_year_table]
    sm = x["Summary_Production"]
    b = x["Bifurcation_GPGC_Bars"]
    dc = x["Downstream_Consumption"]; dc = dc[~dc.prior_year_table]
    cum = {}          # cum[item][rm][entity]
    def put(item, rm, ent, v):
        cum.setdefault(item, {}).setdefault(rm, {})[ent] = None if pd.isna(v) else float(v)
    for k, (seg, cat) in PBC.items():
        for _, r in pc[(pc.segment == seg) & (pc.category == cat)].iterrows():
            put(k, r.report_month, r.producer, r.value)
    for k, cat in DS.items():
        for _, r in dn[(dn.segment == "Non-Alloy") & (dn.category == cat)].iterrows():
            put(k, r.report_month, r.producer, r.value)
    for _, r in b[b.category == "Galvalume"].iterrows():
        put("galv", r.report_month, r.producer, r.value)
    for k, name in SUM.items():
        for _, r in sm[sm.metric == name].drop_duplicates(["report_month", "producer"]).iterrows():
            put(k, r.report_month, r.producer, r.cumulative)
    for rm, res in bars_nonalloy(b).items():
        for k, d in res.items():
            for p, v in d.items():
                put(k, rm, p, v)
    def val(item, e, per):
        _, _, kind, i = per
        a = cum.get(item, {}).get(RMS[i], {}).get(e)
        if a is None: return None
        if kind == "cum": return a
        p = cum.get(item, {}).get(RMS[i - 1], {}).get(e)
        return None if p is None else a - p
    v = {e: {pk: {it: val(it, e, (pk, lab, kind, i)) for it in cum} for pk, lab, kind, i in PERIODS} for e in ENT}
    # JPC's own 'consumed for downstream' (published for All India only, cumulative)
    pubcat = {"hrfeed": "HR Coils/Strips (feedstock)", "crfeed": "Cr Coil/Sheets", "gpfeed": "Gp/Gc Sheets/Coils & Galvalume"}
    pcum = {k: {r.report_month: float(r.consumed_for_downstream) for _, r in dc[(dc.segment == "Non-Alloy") & (dc.category == c)].iterrows()}
            for k, c in pubcat.items()}
    pub = {}
    for pk, lab, kind, i in PERIODS:
        pub[pk] = {}
        for k in pcum:
            a = pcum[k].get(RMS[i]); p = pcum[k].get(RMS[i - 1]) if kind == "mon" else 0
            pub[pk][k] = None if a is None or p is None else a - p
    return {"periods": [[k, l, kind] for k, l, kind, _ in PERIODS], "entities": ENT, "v": v, "pub": pub}


if __name__ == "__main__":
    import os, shutil, tempfile, json
    x = load_book()
    f = build_flow(x)
    a = f["v"]["All India"]["c8"]; print({k: a[k] for k in ("crude", "fin", "flat", "hr", "cr", "gpgc", "cc", "rebar", "wire", "plain", "others_b")}); print(f["pub"]["c8"], f["pub"]["m8"])
