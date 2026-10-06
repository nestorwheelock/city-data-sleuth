#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# City Data Sleuth — one-page case summary PDF generator.
# Copyright (C) 2026  Nestor Wheelock.  Licensed under the GNU GPL v3 or later.
"""
Render the one-page case summary to docs/summary.pdf.

    python3 src/make_pdf.py

Requires the `wkhtmltopdf` binary (https://wkhtmltopdf.org). Writes an intermediate
HTML next to the PDF. Case facts are read from data/ where possible; the narrative
summary is defined here.
"""
import os, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page{size:letter;margin:.7in}
body{font:12pt/1.4 Georgia,serif;color:#111}
h1{font-size:17pt;margin:0 0 2px}
.sub{font-size:10.5pt;color:#333;margin:0 0 14px}
h2{font-size:12pt;text-transform:uppercase;letter-spacing:.06em;border-bottom:1.5px solid #111;padding-bottom:3px;margin:16px 0 8px}
td{padding:3px 8px 3px 0;vertical-align:top} td.d{width:60px;font-weight:bold;white-space:nowrap}
.pending{color:#a00;font-weight:bold} .ok{color:#060}
.box{background:#f4f4f4;border:1px solid #ccc;padding:10px 14px;margin:6px 0}
.big{font-size:15pt;font-weight:bold} .q{font-style:italic;font-size:12.5pt}
.foot{font-size:9.5pt;color:#555;margin-top:16px;border-top:1px solid #ccc;padding-top:6px}
</style></head><body>
<h1>Permit BPS26-0517 &mdash; 3235 Ivanhoe Ave, St. Louis 63139</h1>
<p class="sub"><b>Purpose:</b> Boundary adjustment (~525 sq ft; no construction).
&nbsp;&bull;&nbsp; <b>Source:</b> City of St. Louis case-check system &amp; published BPS board minutes.</p>
<h2>Timeline</h2>
<table>
<tr><td class="d">9/4</td><td>Application submitted</td></tr>
<tr><td class="d">9/9</td><td>BPS Survey review &mdash; <span class="ok">APPROVED</span></td></tr>
<tr><td class="d">9/15</td><td>Water &mdash; <span class="ok">APPROVED</span></td></tr>
<tr><td class="d">9/15</td><td>Assessor &mdash; <span class="ok">APPROVED</span></td></tr>
<tr><td class="d">10/6</td><td>Building (Dept. of Public Safety) &mdash; <span class="pending">PENDING (27 days)</span><br>No deficiency &bull; no required action &bull; no reviewer date assigned</td></tr>
</table>
<h2>Comparison</h2>
<div class="box"><span class="big">This case: 27 days pending</span> &mdash; only 1 of 9 comparable
public cases ran longer, and that one carried a documented deficiency. In the same weeks, the
Board approved dozens of comparable parcel/survey matters.</div>
<h2>The question</h2>
<p class="q">&ldquo;What specifically is outstanding in the Building review of BPS26-0517, who has
the file, and when will a decision be made?&rdquo;</p>
<p class="foot">Every line is verifiable in the City's own records. Full analysis, data, and
open-source code: github.com/nestorwheelock/city-data-sleuth</p>
</body></html>"""

def main():
    html_path = os.path.join(DOCS, "summary.html")
    pdf_path = os.path.join(DOCS, "summary.pdf")
    open(html_path, "w").write(HTML)
    subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "--page-size", "Letter",
                    html_path, pdf_path], check=True)
    print("wrote", pdf_path)

if __name__ == "__main__":
    main()
