"""
JPC Monthly Report extractor.

Reads the JPC "Monthly Report - <month> <year>.pdf" files and writes one
consolidated Excel workbook containing:

  * producer-wise production of crude steel / hot metal / pig iron /
    sponge iron / pellets / finished steel (month + April-to-date)
  * producer x category production matrix (Ch.5, crude to finished equivalent)
  * producer x category downstream / value added production (Ch.5)
  * category-wise "Consumed For Downstream Processing" (Ch.5)
  * a derived producer-wise downstream view (JPC does not publish this
    directly - see the README sheet)
  * a tidy long-format master sheet

Usage:
    python jpc_extract.py
    python jpc_extract.py --input . --output jpc_consolidated.xlsx
    python jpc_extract.py --pattern "Monthly Report*Aug*.pdf"
"""

import argparse
import glob
import os
import re
import sys

import pymupdf
import pandas as pd

MONTH_NAMES = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
               "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
MONTH_NO = {m: i + 1 for i, m in enumerate(MONTH_NAMES)}
MONTH_RE = "|".join(MONTH_NAMES)

# order of the producer columns in every Chapter 5 matrix
PRODUCER_COLS = ["SAIL", "RINL", "NSL", "TSL Group", "AM/NS (ESSAR)",
                 "JSL(JSPL)", "JSW Group", "The Remaining Producers", "All India"]

# row labels we accept in the Chapter 2 summary tables, keyed by a squashed form
CH2_ROWS = {
    "sail": "SAIL",
    "rinl": "RINL",
    "nsl": "NSL",
    "tslgroup": "TSL Group",
    "am/ns(essar)": "AM/NS (ESSAR)",
    "amns(essar)": "AM/NS (ESSAR)",
    "jsl(jspl)": "JSL(JSPL)",
    "jswgroup": "JSW Group",
    "theremainingproducers": "The Remaining Producers",
    "totalproduction": "All India",
    "totalpsuproduction": "Total PSU",
    "%shareofpsu": "% Share of PSU",
}

CH2_TABLES = ["CRUDE STEEL PRODUCTION", "HOT METAL PRODUCTION",
              "PIG IRON PRODUCTION", "SPONGE IRON PRODUCTION",
              "PELLETS PRODUCTION", "FINISHED STEEL PRODUCTION"]

# 9 value columns of a Chapter 2 summary table, in printed order
CH2_FIELDS = ["month", "month_prev_year", "pct_yoy", "month_dup",
              "prev_month", "pct_mom", "cumulative", "cumulative_prev_year",
              "pct_cply"]

# 11 value columns of the downstream consumption table
DS_FIELDS = ["production", "consumed_for_downstream", "import", "export",
             "availability", "stock_opening", "stock_closing",
             "stock_variation", "consumption", "consumption_prev_year",
             "consumption_var_pct"]

NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")

# tables we could not read, surfaced on the console and on the README sheet
NOTES = []

# set by --ocr; some JPC issues ship their tables as flat images
USE_OCR = False


def note(message):
    NOTES.append(message)
    print("   ! " + message, file=sys.stderr)


def is_number(tok):
    return bool(NUMERIC.match(tok.replace(",", "").replace("%", "")))


def to_number(tok):
    return float(tok.replace(",", "").replace("%", ""))


def is_image_page(page):
    """True when the table on this page is a picture rather than real text.

    A real JPC table page carries dozens of figures; a scanned one keeps only
    its running header and page number as text.
    """
    words = page.get_text("words")
    figures = sum(1 for w in words if is_number(w[4]))
    return figures < 20 and bool(page.get_images())


def page_words(page):
    words = page.get_text("words")
    if USE_OCR and is_image_page(page):
        try:
            tp = page.get_textpage_ocr(dpi=300, full=True)
            words = page.get_text("words", textpage=tp)
        except Exception as exc:                      # tesseract missing/broken
            note("OCR failed on page %d: %s" % (page.number + 1, exc))
    return words


def page_lines(page):
    """Group the page words into visual lines, left to right."""
    words = page_words(page)
    words.sort(key=lambda w: (round(w[3], 1), w[0]))
    lines, current, base = [], [], None
    for w in words:
        if base is None or abs(w[3] - base) > 3:
            if current:
                lines.append(current)
            current, base = [], w[3]
        current.append(w)
    if current:
        lines.append(current)
    return lines


def split_line(line):
    """Return (label, [(right_edge, value), ...]) for one visual line."""
    label_parts, numbers = [], []
    for x0, y0, x1, y1, text, *_ in line:
        if is_number(text):
            numbers.append((x1, to_number(text)))
        else:
            label_parts.append(text)
    return " ".join(label_parts).strip(), numbers


def column_centres(rows, expected):
    """Derive column positions by clustering the right edges of the numbers.

    JPC right-aligns every figure, so the right edges form tight clusters.
    Only rows that carry the full set of figures are used to seed them.
    """
    edges = sorted(x for _, nums in rows if len(nums) == expected for x, _ in nums)
    if not edges:
        edges = sorted(x for _, nums in rows for x, _ in nums)
    clusters, group = [], [edges[0]]
    for e in edges[1:]:
        if e - group[-1] > 12:
            clusters.append(sum(group) / len(group))
            group = []
        group.append(e)
    clusters.append(sum(group) / len(group))
    return clusters


def place(numbers, centres):
    """Drop each figure into the column whose centre it sits closest to."""
    slots = [None] * len(centres)
    for x, value in numbers:
        idx = min(range(len(centres)), key=lambda i: abs(centres[i] - x))
        if slots[idx] is None:
            slots[idx] = value
    return slots


def squash(label):
    if not label:
        return ""
    # rows are printed with a serial letter, e.g. "E AM / NS (ESSAR)"
    label = re.sub(r"^[A-H][.)]?\s+", "", label.strip())
    return re.sub(r"\s+", "", label).lower()


def report_month(doc):
    """Report month/year from the running header, e.g. 'Monthly Report -AUGUST 2026'."""
    for i in range(min(20, doc.page_count)):
        text = " ".join(doc[i].get_text().split())
        m = re.search(r"Report\s*.?\s*(%s)\s+(\d{4})" % MONTH_RE, text, re.I)
        if m:
            return m.group(1).upper(), int(m.group(2))
    raise ValueError("could not determine report month")


def table_period(text):
    """Period a Chapter 5 table covers: ('cumulative'|'month', label, fy_start)."""
    flat = " ".join(text.split())
    m = re.search(r"April\s*.{0,3}\s*(%s)\s*(\d{4})-(\d{2})" % MONTH_RE, flat, re.I)
    if m:
        end_month, start_year = m.group(1).upper(), int(m.group(2))
        return ("cumulative",
                "April-%s %d-%s" % (end_month.title(), start_year, m.group(3)),
                start_year)
    m = re.search(r"\b(%s)\s+(\d{4})\s*\(Prov" % MONTH_RE, flat, re.I)
    if m:
        name, yr = m.group(1).upper(), int(m.group(2))
        label = "%s %d" % (name.title(), yr)
        # April opens the financial year, so the April issue prints a single
        # month where later issues print April-to-date. They are the same thing.
        if name == "APRIL":
            return "cumulative", label + " (= April to date)", yr
        return "month", label, yr
    return None, None, None


def find_pages(doc, predicate):
    for i in range(doc.page_count):
        text = " ".join(doc[i].get_text().split())
        if predicate(text):
            yield i, text


# --------------------------------------------------------------------------
# Chapter 2 - producer-wise summary production tables
# --------------------------------------------------------------------------

def parse_ch2(doc, month, year):
    records = []
    for title in CH2_TABLES:
        pages = [i for i, t in find_pages(
            doc, lambda t, ti=title: ti in t and "Chapter 2" in t)]
        if not pages:
            note("%s %d: '%s' page not found" % (month.title(), year, title))
            continue
        page = doc[pages[0]]
        rows = []
        for line in page_lines(page):
            label, numbers = split_line(line)
            key = squash(label)
            if key in CH2_ROWS and len(numbers) >= 4:
                rows.append((CH2_ROWS[key], numbers))
        if not rows:
            why = "table is an image, needs --ocr" if is_image_page(page) \
                else "no rows recognised"
            note("%s %d: '%s' on page %d - %s"
                 % (month.title(), year, title, pages[0] + 1, why))
            continue
        centres = column_centres(rows, len(CH2_FIELDS))
        for producer, numbers in rows:
            values = dict(zip(CH2_FIELDS, place(numbers, centres)))
            values.pop("month_dup", None)
            records.append({
                "report_month": "%s %d" % (month.title(), year),
                "month_no": MONTH_NO[month],
                "year": year,
                "metric": title.replace(" PRODUCTION", "").title(),
                "producer": producer,
                **values,
            })
    return records


# --------------------------------------------------------------------------
# Chapter 5 - producer x category matrices
# --------------------------------------------------------------------------

SECTION = re.compile(r"(?i)finished\s+steel\s*\((.+)\)")


def section_name(label):
    """'FINISHED STEEL (Non-Alloy + Alloy + Stainless)' -> 'All Grades'."""
    m = SECTION.search(label)
    if not m:
        return None
    inner = m.group(1).strip()
    return "All Grades" if "+" in inner else inner.title()


def clean_label(label):
    """Tidy a row label; some issues print '(incl ww)' as '(incl w w )'."""
    label = re.sub(r"\s+", " ", label).strip()
    label = re.sub(r"\(\s+", "(", label)
    label = re.sub(r"\s+\)", ")", label)
    label = re.sub(r"(?i)\bw\s+w\b", "ww", label)
    return label.title()


def parse_matrix(page, min_numbers=8):
    """Rows of a producer x category matrix, tagged with their section header.

    The section headers ('FINISHED STEEL (Alloy)' etc.) sit in their own
    visual line above the rows they cover, which is what keeps the repeated
    'Flat' / 'Non-Flat' / 'Total(...)' labels apart.
    """
    rows, segment = [], ""
    for line in page_lines(page):
        label, numbers = split_line(line)
        if not label:
            continue
        if not numbers:
            found = section_name(label)
            if found:
                segment = found
            continue
        if len(numbers) < min_numbers:
            continue
        if re.search(r"(?i)report|chapter|quantity|tonnes", label):
            continue
        rows.append((segment, label, numbers))
    if not rows:
        return []
    centres = column_centres([(l, n) for _, l, n in rows], len(PRODUCER_COLS))
    return [(segment, label, dict(zip(PRODUCER_COLS, place(numbers, centres))))
            for segment, label, numbers in rows]


# the three Chapter 5 bifurcation tables, keyed by their page title
BIFURCATIONS = [
    ("PRODUCTION OF BARS & RODS", "Bars & Rods"),
    ("PRODUCTION OF GP / GC & COLOR COATED PRODUCTS", "GP/GC & Color Coated"),
    ("PRODUCTION OF FINISHED STEEL (ALLOY & STAINLESS)", "Alloy & Stainless"),
]

# column headings and producer names that must never be read as a section
NOT_A_SECTION = re.compile(
    r"(?i)\b(sail|rinl|nsl|jsl|jspl|jsw|essar|producers|products|group|"
    r"bifurcation|quantity|qunatity|report|chapter|prov|tonnes)\b|am\s*/\s*ns")


def parse_bifurcation(page):
    """Rows of a Chapter 5 bifurcation table.

    These pages differ from the other matrices in two ways: the section
    headings are plain ('ALLOY STEEL', not 'FINISHED STEEL (Alloy)'), and a
    long row label such as 'TOTAL GP / GC & COLOR COATED PRODUCTS' wraps onto
    its own line with the figures printed on the next one.
    """
    rows, segment, pending = [], "", ""
    for line in page_lines(page):
        label, numbers = split_line(line)
        if not numbers:
            if not label or NOT_A_SECTION.search(label) or len(label) < 4:
                continue
            # headings sit in the middle of the page, row labels on the left
            if line[0][0] >= 250:
                segment = clean_label(label)
            else:
                pending = label
            continue
        if len(numbers) < 8:
            continue
        if not label:
            label, pending = pending, ""
        if not label or NOT_A_SECTION.search(label):
            continue
        rows.append((segment, label, numbers))
    if not rows:
        return []
    centres = column_centres([(l, n) for _, l, n in rows], len(PRODUCER_COLS))
    return [(segment, label, dict(zip(PRODUCER_COLS, place(numbers, centres))))
            for segment, label, numbers in rows]


def parse_ch5_bifurcation(doc, month, year):
    records = []
    for title, table_name in BIFURCATIONS:
        pages = [i for i, t in find_pages(doc, lambda t, ti=title: ti in t)]
        if not pages:
            note("%s %d: '%s' page not found" % (month.title(), year, title))
            continue
        for idx in pages:
            kind, period, fy = table_period(" ".join(doc[idx].get_text().split()))
            rows = parse_bifurcation(doc[idx])
            if not rows:
                why = "table is an image, needs --ocr" if is_image_page(doc[idx]) \
                    else "no rows recognised"
                note("%s %d: bifurcation of %s on page %d - %s"
                     % (month.title(), year, table_name, idx + 1, why))
                continue
            for segment, label, values in rows:
                for producer, value in values.items():
                    records.append({
                        "report_month": "%s %d" % (month.title(), year),
                        "month_no": MONTH_NO[month],
                        "year": year,
                        "table": table_name,
                        "period_type": kind,
                        "period": period,
                        "prior_year_table": fy is not None and fy < year,
                        "segment": segment,
                        "category": clean_label(label),
                        "producer": producer,
                        "value": value,
                    })
    return records


def parse_ch5_matrices(doc, month, year):
    """Production matrix (crude->finished equivalent) and downstream matrix."""
    prod, down = [], []

    def collect(predicate, bucket, table_name):
        for idx, text in find_pages(doc, predicate):
            kind, period, fy = table_period(text)
            if kind is None:
                continue
            # the second copy of each table is last year's comparison
            is_prev_year = fy is not None and fy < year
            matrix = parse_matrix(doc[idx])
            if not matrix:
                why = "table is an image, needs --ocr" if is_image_page(doc[idx]) \
                    else "no rows recognised"
                note("%s %d: '%s' on page %d - %s"
                     % (month.title(), year, table_name, idx + 1, why))
            for segment, label, values in matrix:
                for producer, value in values.items():
                    bucket.append({
                        "report_month": "%s %d" % (month.title(), year),
                        "month_no": MONTH_NO[month],
                        "year": year,
                        "table": table_name,
                        "period_type": kind,
                        "period": period,
                        "prior_year_table": is_prev_year,
                        "segment": segment,
                        "category": clean_label(label),
                        "producer": producer,
                        "value": value,
                    })

    collect(lambda t: "CRUDE STEEL TO FINISHED STEEL EQUIVALENT" in t,
            prod, "Production by Category")
    collect(lambda t: "DOWNSTREAM" in t and "VALUE ADDED PRODUCTION" in t
            and "IMPORT" not in t, down, "Downstream / Value Added Production")
    return prod, down


# --------------------------------------------------------------------------
# Chapter 5 - category-wise downstream consumption
# --------------------------------------------------------------------------

def parse_downstream_consumption(doc, month, year):
    records = []

    def predicate(t):
        return "DOWNSTREAM" in t and "VALUE ADDED PRODUCTION, IMPORT" in t

    for idx, text in find_pages(doc, predicate):
        kind, period, fy = table_period(text)
        if kind is None:
            continue
        is_prev_year = fy is not None and fy < year
        rows, hr_feed, segment = [], None, ""
        for line in page_lines(doc[idx]):
            label, numbers = split_line(line)
            if not label or re.search(r"(?i)report|chapter|quantity|tonnes|as on", label):
                continue
            if not numbers:
                found = section_name(label)
                if found:
                    segment = found
                continue
            if re.match(r"(?i)^hr coils?/strips", label) and len(numbers) == 1:
                hr_feed = numbers[0][1]
                continue
            if len(numbers) >= 8:
                rows.append((segment, label, numbers))
        if not rows:
            why = "table is an image, needs --ocr" if is_image_page(doc[idx]) \
                else "no rows recognised"
            note("%s %d: downstream consumption on page %d - %s"
                 % (month.title(), year, idx + 1, why))
            continue
        centres = column_centres([(l, n) for _, l, n in rows], len(DS_FIELDS))
        stamp = {
            "report_month": "%s %d" % (month.title(), year),
            "month_no": MONTH_NO[month], "year": year,
            "period_type": kind, "period": period,
            "prior_year_table": is_prev_year,
        }
        if hr_feed is not None:
            records.append(dict(stamp, segment="Non-Alloy",
                                category="HR Coils/Strips (feedstock)",
                                consumed_for_downstream=hr_feed))
        for segment, label, numbers in rows:
            values = dict(zip(DS_FIELDS, place(numbers, centres)))
            records.append(dict(stamp, segment=segment,
                                category=clean_label(label), **values))
    return records


# --------------------------------------------------------------------------
# derivations
# --------------------------------------------------------------------------

FY_ORDER = {MONTH_NO[m]: i for i, m in enumerate(
    ["APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER",
     "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"])}


def backfill_from_next_report(ch2):
    """Recover a missing month from the next report's 'previous month' column.

    Every Chapter 2 table prints the preceding month beside the current one,
    so a month whose own report is unreadable (the April 2026 issue ships its
    tables as images) can still be filled in from the month after it. April is
    the start of the financial year, so its April-to-date figure equals its
    month figure.
    """
    if ch2.empty:
        return ch2
    ch2 = ch2.copy()
    ch2["source"] = "report"
    have = set(ch2["month_no"])
    pos_to_month = {p: m for m, p in FY_ORDER.items()}
    added = []
    for month_no in sorted(have):
        pos = FY_ORDER[month_no]
        if pos == 0:
            continue
        prev_no = pos_to_month[pos - 1]
        if prev_no in have:
            continue
        for _, row in ch2[ch2["month_no"] == month_no].iterrows():
            if pd.isna(row["prev_month"]):
                continue
            prev_year = row["year"] - 1 if month_no == 1 else row["year"]
            added.append({
                "report_month": "%s %d" % (MONTH_NAMES[prev_no - 1].title(), prev_year),
                "month_no": prev_no,
                "year": prev_year,
                "metric": row["metric"],
                "producer": row["producer"],
                "month": row["prev_month"],
                # April opens the financial year, so April-to-date == April
                "cumulative": row["prev_month"] if pos - 1 == 0 else None,
                "source": "prev-month column of the %s report" % row["report_month"],
            })
    if not added:
        return ch2
    months = sorted({r["report_month"] for r in added})
    note("%s had no readable tables of its own - filled from the following "
         "month's previous-month column" % ", ".join(months))
    return pd.concat([ch2, pd.DataFrame(added)], ignore_index=True)


def add_implied_month(ch2):
    """Month figures implied by differencing the April-to-date series.

    JPC revises earlier months in later issues but only reprints the
    April-to-date totals, so the months as first published do not always add
    up to the latest cumulative figure. This column always does.
    """
    if ch2.empty:
        return ch2
    ch2 = ch2.copy()
    ch2["fy_pos"] = ch2["month_no"].map(FY_ORDER)
    ch2 = ch2.sort_values(["metric", "producer", "fy_pos"])
    keys = ["metric", "producer"]
    prev = ch2.groupby(keys, dropna=False)["cumulative"].shift(1)
    prev_pos = ch2.groupby(keys, dropna=False)["fy_pos"].shift(1)
    implied = ch2["cumulative"] - prev.fillna(0)
    ok = (prev_pos.isna() & (ch2["fy_pos"] == 0)) | (ch2["fy_pos"] - prev_pos == 1)
    # a percentage share is not additive, so differencing it means nothing
    ok = ok & ~ch2["producer"].str.startswith("%")
    ch2["month_from_cumulative"] = implied.where(ok)
    return ch2.drop(columns=["fy_pos"])


def add_monthly_from_cumulative(df, keys, value_col="value"):
    """Chapter 5 tables are April-to-date only; difference them into months."""
    if df.empty:
        df["value_month"] = []
        return df
    df = df.copy()
    df["fy_pos"] = df["month_no"].map(FY_ORDER)
    df = df.sort_values(keys + ["fy_pos"])
    prev = df.groupby(keys, dropna=False)[value_col].shift(1)
    prev_pos = df.groupby(keys, dropna=False)["fy_pos"].shift(1)
    monthly = df[value_col] - prev.fillna(0)
    # only trust the difference when the previous report is the adjacent month
    ok = (prev_pos.isna() & (df["fy_pos"] == 0)) | (df["fy_pos"] - prev_pos == 1)
    # a table already printed as a single month needs no differencing
    ok = ok | (df["period_type"] == "month")
    monthly = monthly.where(df["period_type"] != "month", df[value_col])
    df["value_month"] = monthly.where(ok)
    return df.drop(columns=["fy_pos"])


DOWNSTREAM_FLAT = ["Hsm Plates", "Hr Sheets", "Cr Coil/Sheets",
                   "Gp/Gc Sheets/Coil", "Color Coated Coils/Sheet",
                   "Electrical Coils/Sheets", "Tin Plates (Incl Ww)",
                   "Pipes (Large Dia.)", "Tmbp", "Tin Free Steel"]


def derive_producer_downstream(prod_df, down_df, bif_df=None):
    """Producer-wise feedstock vs downstream output. Derived, not published."""
    idx = ["report_month", "month_no", "year", "producer"]
    if prod_df.empty or down_df.empty:
        return pd.DataFrame(columns=idx)

    prod = prod_df[(~prod_df["prior_year_table"]) & (prod_df["segment"] == "Non-Alloy")]
    hr = prod[prod["category"].str.contains("Hr Coil", case=False, na=False)]
    hr = hr.groupby(idx, as_index=False)["value"].sum()
    hr = hr.rename(columns={"value": "hr_coil_production"})

    down = down_df[(~down_df["prior_year_table"]) & (down_df["segment"] == "Non-Alloy")]
    wide = down.pivot_table(index=idx, columns="category", values="value",
                            aggfunc="sum").reset_index()
    wide.columns.name = None
    for col in DOWNSTREAM_FLAT:
        if col not in wide.columns:
            wide[col] = 0.0
    wide["downstream_total"] = wide[DOWNSTREAM_FLAT].fillna(0).sum(axis=1)

    out = hr.merge(wide, on=idx, how="outer")
    out["downstream_pct_of_hr_coil"] = (
        out["downstream_total"] / out["hr_coil_production"].replace(0, float("nan")) * 100
    ).round(1)
    out["cr_pct_of_hr_coil"] = (
        out["Cr Coil/Sheets"] / out["hr_coil_production"].replace(0, float("nan")) * 100
    ).round(1)
    out["gpgc_pct_of_cr"] = (
        out["Gp/Gc Sheets/Coil"] / out["Cr Coil/Sheets"].replace(0, float("nan")) * 100
    ).round(1)

    # the downstream table lumps Galvalume into GP/GC; the bifurcation
    # table splits them, so carry both through
    if bif_df is not None and not bif_df.empty:
        gp = bif_df[(~bif_df["prior_year_table"]) &
                    (bif_df["table"] == "GP/GC & Color Coated")]
        gp = gp.pivot_table(index=idx, columns="category", values="value",
                            aggfunc="sum").reset_index()
        gp.columns.name = None
        rename = {"Gp / Gc Sheets / Coils": "GP/GC excl Galvalume",
                  "Galvalume": "Galvalume",
                  "Color Coated Sheets / Coils": "Color Coated (bifurcation)",
                  "Total Gp / Gc & Color Coated": "Total GP/GC & Color Coated"}
        gp = gp[[c for c in gp.columns if c in idx or c in rename]]
        out = out.merge(gp.rename(columns=rename), on=idx, how="left")
        if "Galvalume" in out.columns and "GP/GC excl Galvalume" in out.columns:
            out["galvalume_pct_of_gpgc"] = (
                out["Galvalume"] /
                (out["Galvalume"] + out["GP/GC excl Galvalume"]).replace(0, float("nan"))
                * 100).round(1)

    out["period"] = "April to date"
    front = idx + ["period", "hr_coil_production", "downstream_total",
                   "downstream_pct_of_hr_coil", "cr_pct_of_hr_coil",
                   "gpgc_pct_of_cr", "GP/GC excl Galvalume", "Galvalume",
                   "galvalume_pct_of_gpgc"]
    front = [c for c in front if c in out.columns]
    rest = [c for c in out.columns if c not in front]
    return out[front + rest].sort_values(["month_no", "producer"])


def build_master(ch2, prod, down, cons, bif=None):
    cols = ["report_month", "month_no", "year", "table", "period_type",
            "producer", "segment", "category", "value"]
    frames = []

    if not ch2.empty:
        long = ch2.melt(id_vars=["report_month", "month_no", "year",
                                 "metric", "producer"],
                        value_vars=["month", "cumulative"],
                        var_name="period_type", value_name="value")
        long["table"] = "Summary Production"
        long["segment"] = ""
        long["category"] = long["metric"]
        frames.append(long[cols])

    sources = [(prod, "Production by Category"),
               (down, "Downstream / Value Added Production")]
    if bif is not None and not bif.empty:
        for name in bif["table"].unique():
            sources.append((bif[bif["table"] == name], "Bifurcation: " + name))
    for df, name in sources:
        if df.empty:
            continue
        sub = df[~df["prior_year_table"]].copy()
        sub["table"] = name
        frames.append(sub[cols])
        month_rows = sub.dropna(subset=["value_month"]).copy()
        month_rows = month_rows[month_rows["period_type"] == "cumulative"]
        month_rows["period_type"] = "month (derived)"
        month_rows["value"] = month_rows["value_month"]
        frames.append(month_rows[cols])

    if not cons.empty:
        sub = cons[~cons["prior_year_table"]].copy()
        keep = [c for c in DS_FIELDS if c in sub.columns]
        long = sub.melt(id_vars=["report_month", "month_no", "year",
                                 "period_type", "segment", "category"],
                        value_vars=keep, var_name="measure", value_name="value")
        long["table"] = "Downstream Consumption"
        long["producer"] = "All India"
        long["category"] = long["category"] + " | " + long["measure"]
        frames.append(long[cols])

    if not frames:
        return pd.DataFrame(columns=cols)
    master = pd.concat(frames, ignore_index=True).dropna(subset=["value"])
    return master.sort_values(["month_no", "table", "producer", "segment", "category"])


README = [
    ("Source", "JPC Monthly Report: Iron & Steel (PDF), Chapters 2 and 5."),
    ("Units", "All quantities in '000 tonnes unless the column name says pct/%."),
    ("Summary_Production", "Chapter 2 producer-wise tables. 'month' is the report "
     "month, 'cumulative' is April-to-date of the same financial year. The "
     "'source' column says whether a month came from its own report or was "
     "recovered from the next month's previous-month column."),
    ("month vs month_from_cumulative", "JPC revises earlier months in later "
     "issues but only reprints the April-to-date totals, so the months as first "
     "published need not add up to the latest cumulative figure. 'month' is as "
     "first published; 'month_from_cumulative' is backed out of the cumulative "
     "series and always reconciles to it. Use the latter for period totals."),
    ("Prod_by_Category", "Chapter 5 'Crude Steel to Finished Steel Equivalent'. "
     "Producer x category. Published April-to-date; value_month is the single "
     "month figure derived by differencing consecutive reports."),
    ("Downstream_by_Producer", "Chapter 5 'Downstream / Value Added Production'. "
     "Producer x category, including GP/GC Sheets/Coil. value_month derived as above."),
    ("Downstream_Consumption", "Chapter 5 'Downstream / Value Added Production, "
     "Import, Export & Consumption'. The column consumed_for_downstream is JPC's "
     "own figure for material fed into further processing instead of being sold. "
     "JPC publishes it as an All-India total per category only - there is no "
     "producer split for it anywhere in the report."),
    ("Downstream_vs_Production", "DERIVED, not published by JPC. Puts each "
     "producer's HR coil production next to its downstream output so you can see "
     "roughly how much of a producer's flat output moves into value-added lines. "
     "downstream_total sums the flat downstream categories, which are successive "
     "stages (HR -> CR -> GP/GC -> colour coated), so it double counts tonnage "
     "across stages - use the per-category columns and the ratio columns for "
     "anything precise."),
    ("Bifurcation_GPGC_Bars", "Chapter 5 bifurcation pages, producer x product: "
     "GP/GC & Colour Coated (which is where GALVALUME is reported separately), "
     "Bars & Rods, and Finished Steel (Alloy & Stainless)."),
    ("Galvalume", "The Downstream_by_Producer line 'GP/GC Sheets/Coil' INCLUDES "
     "Galvalume. The bifurcation sheet splits it: GP/GC sheets/coils plus "
     "Galvalume adds back exactly to that line, producer by producer "
     "(Apr-Aug 2026-27: 3,819 + 956 = 4,775). Downstream_vs_Production carries "
     "both as 'GP/GC excl Galvalume' and 'Galvalume'."),
    ("April Chapter 5 tables", "The April issue prints its Chapter 5 tables for "
     "the single month of April. April opens the financial year, so those "
     "figures are also the April-to-date figures and are stored as such."),
    ("MASTER_LONG", "Every figure in one tidy table for pivoting."),
    ("Prior year tables", "Chapter 5 prints a previous-year copy of each table. "
     "Those rows are kept with prior_year_table = True and are excluded from the "
     "derived sheets and from MASTER_LONG."),
]


def write_workbook(path, ch2, prod, down, cons, bif, derived, master):
    readme = list(README) + [("Warning", n) for n in NOTES]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(readme, columns=["Sheet / Topic", "Note"]).to_excel(
            writer, sheet_name="README", index=False)
        ch2.to_excel(writer, sheet_name="Summary_Production", index=False)
        prod.to_excel(writer, sheet_name="Prod_by_Category", index=False)
        down.to_excel(writer, sheet_name="Downstream_by_Producer", index=False)
        cons.to_excel(writer, sheet_name="Downstream_Consumption", index=False)
        bif.to_excel(writer, sheet_name="Bifurcation_GPGC_Bars", index=False)
        derived.to_excel(writer, sheet_name="Downstream_vs_Production", index=False)
        master.to_excel(writer, sheet_name="MASTER_LONG", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            for column in sheet.columns:
                width = max((len(str(c.value)) for c in column[:60] if c.value),
                            default=10)
                sheet.column_dimensions[column[0].column_letter].width = \
                    min(max(width + 2, 10), 46)


def main():
    ap = argparse.ArgumentParser(description="Consolidate JPC monthly report PDFs.")
    ap.add_argument("--input", default=".", help="folder holding the PDFs")
    ap.add_argument("--pattern", default="Monthly Report*.pdf", help="file glob")
    ap.add_argument("--output", default="jpc_consolidated.xlsx", help="output .xlsx")
    ap.add_argument("--ocr", action="store_true",
                    help="OCR tables that are embedded as images (needs Tesseract)")
    args = ap.parse_args()

    global USE_OCR
    USE_OCR = args.ocr

    files = sorted(glob.glob(os.path.join(args.input, args.pattern)))
    files = [f for f in files if "highlight" not in os.path.basename(f).lower()]
    if not files:
        sys.exit("no PDFs matched %r in %s" % (args.pattern, args.input))

    ch2_rows, prod_rows, down_rows, cons_rows, bif_rows = [], [], [], [], []
    for path in files:
        doc = pymupdf.open(path)
        month, year = report_month(doc)
        print("reading %s  (%s %d)" % (os.path.basename(path), month.title(), year))
        ch2_rows += parse_ch2(doc, month, year)
        p, d = parse_ch5_matrices(doc, month, year)
        prod_rows += p
        down_rows += d
        cons_rows += parse_downstream_consumption(doc, month, year)
        bif_rows += parse_ch5_bifurcation(doc, month, year)
        doc.close()

    ch2 = add_implied_month(backfill_from_next_report(pd.DataFrame(ch2_rows)))
    prod = pd.DataFrame(prod_rows)
    down = pd.DataFrame(down_rows)
    cons = pd.DataFrame(cons_rows)
    bif = pd.DataFrame(bif_rows)

    if all(df.empty for df in (ch2, prod, down, cons, bif)):
        sys.exit("nothing readable in %d file(s) - see the warnings above; if the "
                 "tables are images, install Tesseract and rerun with --ocr"
                 % len(files))

    # rows printed above the first section header are the semis line
    for df in (prod, down, cons, bif):
        if "segment" in df.columns:
            df["segment"] = df["segment"].replace("", "Semis").fillna("Semis")

    keys = ["table", "period_type", "prior_year_table", "segment", "category",
            "producer"]
    prod = add_monthly_from_cumulative(prod, keys)
    down = add_monthly_from_cumulative(down, keys)
    bif = add_monthly_from_cumulative(bif, keys)

    derived = derive_producer_downstream(prod, down, bif)
    master = build_master(ch2, prod, down, cons, bif)

    for df in (ch2, prod, down, cons, bif):
        if "month_no" in df.columns:
            df.sort_values("month_no", inplace=True, kind="stable")

    out = args.output if os.path.isabs(args.output) else \
        os.path.join(args.input, args.output)
    write_workbook(out, ch2, prod, down, cons, bif, derived, master)
    print("\nwrote %s" % out)
    print("  summary %d | by-category %d | downstream %d | consumption %d | "
          "bifurcation %d | master %d"
          % (len(ch2), len(prod), len(down), len(cons), len(bif), len(master)))
    if NOTES:
        print("\n%d warning(s), also listed on the README sheet:" % len(NOTES))
        for n in NOTES:
            print("  - " + n)


if __name__ == "__main__":
    main()
