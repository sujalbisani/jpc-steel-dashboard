# JPC steel dashboard

Single-file dashboard built from JPC Trade and Monthly Reports (FY 2026-27): import/export by product and country, producer-wise production, and a crude-steel-to-downstream waterfall.

- `jpc_dashboard.html` is the finished page. GitHub Actions publishes it as the site index on every push to `main`.
- `dashboard_build/` rebuilds it: `python refresh.py` (needs pymupdf, pandas, openpyxl, and the JPC PDFs, which are not in this repo).
- `jpc_consolidated.xlsx` holds the extracted tables; `JPC_gist_Sep2026.xlsx` is the one-file gist.

To update: rebuild locally, then commit and push `jpc_dashboard.html`.
