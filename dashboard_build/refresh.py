"""Rebuild jpc_dashboard.html. Run from this folder:  python refresh.py
Needs: pymupdf, pandas, openpyxl. Reads the Trade Report PDFs and jpc_consolidated.xlsx one level up.
Add new months to MONTHS / CUM / MON in trade_extract.py and build.py first."""
import subprocess, sys
subprocess.run([sys.executable, "trade_extract.py", "..", "trade.json"], check=True)
subprocess.run([sys.executable, "build.py"], check=True)
t = open("template_do_not_open.txt", encoding="utf-8").read().replace("/*__FLOW__*/", open("flow_ui.js", encoding="utf-8").read()).replace("__DATA__", open("data.json").read())
open("../jpc_dashboard.html", "w", encoding="utf-8").write(t)
print("jpc_dashboard.html updated")
