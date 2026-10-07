#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# City Data Sleuth — multi-page static site generator.
# Copyright (C) 2026  Nestor Wheelock.  Licensed under the GNU GPL v3 or later.
"""
Builds the public site from the analysis outputs and the content/ markdown.

    python3 src/make_site.py

Reads  : data/parcel-survey-roster.csv, data/turnaround-sample.csv, content/*.md,
         content/assets/* (optional), src/*.py (shown on the methods page)
Writes : docs/  (GitHub Pages root) — index, case, data, exhibits,
         records-request, methods, reuse
No third-party dependencies.
"""
from __future__ import annotations
import csv, html, os, re, shutil
import bps_pipeline as bp   # same dir; provides analyze()

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA    = os.path.join(ROOT, "data")
CONTENT = os.path.join(ROOT, "content")
SRC     = os.path.join(ROOT, "src")
DOCS    = os.path.join(ROOT, "docs")
REPO    = "https://github.com/nestorwheelock/city-data-sleuth"
BRAND   = "City Data Sleuth"
PAL     = bp.PAL

NAV = [("index.html","Story"), ("case.html","The case"), ("data.html","The data"),
       ("exhibits.html","Exhibits"),
       ("methods.html","Methods & code"), ("reuse.html","Use it yourself")]

def e(s): return html.escape(str(s if s is not None else ""))

# ----------------------------------------------------------------- minimal markdown
def md(text: str) -> str:
    out, i, lines = [], 0, text.split("\n")
    def inline(s):
        s = e(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
        return s
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        m = re.match(r"(#{1,4})\s+(.*)", ln)
        if m:
            lvl = len(m.group(1)); out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i += 1; continue
        if ln.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].lstrip()); i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf if b) + "</blockquote>"); continue
        if re.match(r"\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"\s*[-*]\s+", "", lines[i], count=1)); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>"); continue
        if re.match(r"\s*\d+\.\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"\s*\d+\.\s+", lines[i]):
                buf.append(re.sub(r"\s*\d+\.\s+", "", lines[i], count=1)); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>"); continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,4}\s|\s*[-*]\s|\s*\d+\.\s|>)", lines[i]):
            buf.append(lines[i]); i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)

def read_md(name):
    p = os.path.join(CONTENT, name)
    return md(open(p, encoding="utf-8").read()) if os.path.exists(p) else ""

# ----------------------------------------------------------------- charts (inline SVG)
def bar_v(cadence, w=640, h=260, pad=36):
    short = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
             "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
    labels = [short[k[5:]] for k in cadence]; vals = list(cadence.values())
    mx = max(vals) or 1; bw = (w-2*pad)/len(vals); inner = h-2*pad; s = []
    s.append(f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Approvals per month" class="chart">')
    for gy in range(0, mx+1, max(1, mx//4)):
        y = h-pad-inner*gy/mx
        s.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{w-pad}" y2="{y:.1f}" stroke="{PAL["grid"]}"/>')
        s.append(f'<text x="{pad-6}" y="{y+4:.1f}" text-anchor="end" fill="{PAL["muted"]}" font-size="11">{gy}</text>')
    for i,(v,lb) in enumerate(zip(vals, labels)):
        bh = inner*v/mx; x = pad+i*bw+bw*0.18; bwid = bw*0.64; y = h-pad-bh
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bwid:.1f}" height="{bh:.1f}" rx="4" fill="{PAL["series"]}"><title>{lb}: {v}</title></rect>')
        s.append(f'<text x="{x+bwid/2:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="{PAL["ink2"]}" font-size="12" font-weight="600">{v}</text>')
        s.append(f'<text x="{x+bwid/2:.1f}" y="{h-pad+16:.1f}" text-anchor="middle" fill="{PAL["muted"]}" font-size="11">{lb}</text>')
    s.append(f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="{PAL["base"]}"/></svg>')
    return "".join(s)

def bar_h(sample_rows, w=640, rowh=28, pad=118):
    items = sorted([r for r in sample_rows if r.get("pending") != "1"], key=lambda r:int(r["days"]))
    items += [r for r in sample_rows if r.get("pending") == "1"]
    mx = max(int(r["days"]) for r in items); plot = w-pad-150; h = rowh*len(items)+16; s = []
    s.append(f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Building-review days per case" class="chart">')
    for i, r in enumerate(items):
        v = int(r["days"]); pend = r.get("pending") == "1"; defic = r.get("deficiency") == "1"
        y = 8+i*rowh; bw = plot*v/mx; col = PAL["crit"] if pend else PAL["series"]
        s.append(f'<text x="{pad-8}" y="{y+14:.0f}" text-anchor="end" fill="{PAL["ink2"]}" font-size="12" style="font-variant-numeric:tabular-nums">{e(r["case"])}</text>')
        s.append(f'<rect x="{pad}" y="{y:.0f}" width="{bw:.1f}" height="{rowh-9}" rx="4" fill="{col}"><title>{e(r["case"])}: {v} days</title></rect>')
        tag = " — pending, no decision" if pend else (" — had a deficiency" if defic else "")
        s.append(f'<text x="{pad+bw+6:.1f}" y="{y+14:.0f}" fill="{PAL["crit"] if pend else PAL["ink2"]}" font-size="12" font-weight="{700 if pend else 400}">{v} days{tag}</text>')
    s.append("</svg>")
    return "".join(s)

# ----------------------------------------------------------------- page shell
CSS = r"""
*{box-sizing:border-box} html{scroll-behavior:smooth}
body{margin:0;background:var(--pg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--ser);text-decoration:none} a:hover{text-decoration:underline}
header.nav{position:sticky;top:0;z-index:5;background:rgba(252,252,251,.92);backdrop-filter:blur(8px);
 border-bottom:1px solid var(--grid)}
.nav-in{max-width:960px;margin:0 auto;display:flex;flex-wrap:wrap;align-items:center;gap:4px 18px;padding:12px 20px}
.brand{font-weight:800;letter-spacing:-.01em;margin-right:auto;font-size:18px;color:var(--ink);display:flex;align-items:center;gap:9px}
.logo{height:32px;width:32px;flex:none}
.brand span{color:var(--ser)}
.nav a{color:var(--ink2);font-size:14px;padding:4px 0} .nav a.on{color:var(--ink);font-weight:700;box-shadow:inset 0 -2px 0 var(--ser)}
main{max-width:860px;margin:0 auto;padding:30px 20px 80px}
.hero{max-width:960px;margin:0 auto;padding:54px 20px 20px}
h1{font-size:40px;line-height:1.08;letter-spacing:-.02em;margin:.1em 0}
h2{font-size:23px;margin:1.9em 0 .5em;letter-spacing:-.01em}
h3{font-size:18px;margin:1.4em 0 .4em}
.lede{font-size:20px;color:var(--ink2);max-width:40em}
.tiles{display:flex;flex-wrap:wrap;gap:14px;margin:26px 0}
.tile{flex:1 1 160px;background:var(--s);border:1px solid var(--grid);border-radius:12px;padding:16px 18px}
.tile .n{font-size:30px;font-weight:800;letter-spacing:-.02em} .tile .n.crit{color:var(--crit)}
.tile .l{font-size:13px;color:var(--ink2);margin-top:2px}
.card{background:var(--s);border:1px solid var(--grid);border-radius:12px;padding:18px 20px;margin:16px 0}
.chart{width:100%;height:auto;font-family:system-ui,sans-serif}
.step{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:14px;color:var(--ink2)}
.step b{background:var(--s);border:1px solid var(--grid);border-radius:999px;padding:5px 12px;color:var(--ink)}
.callout{border-left:4px solid var(--ser);background:var(--s);padding:12px 18px;border-radius:0 10px 10px 0;margin:16px 0}
.callout.crit{border-color:var(--crit)}
blockquote{border-left:3px solid var(--base);margin:12px 0;padding:6px 16px;color:var(--ink2);background:var(--s);border-radius:0 8px 8px 0}
ul,ol{padding-left:22px} li{margin:3px 0}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:6px 9px;border-bottom:1px solid var(--grid);vertical-align:top}
th{position:sticky;top:0;background:var(--s);cursor:pointer;white-space:nowrap}
.wrap{max-height:520px;overflow:auto;border:1px solid var(--grid);border-radius:10px}
.note{font-size:13px;color:var(--mut)}
.btn{display:inline-block;background:var(--ser);color:#fff;padding:9px 16px;border-radius:8px;font-weight:600;font-size:14px}
.btn:hover{text-decoration:none;filter:brightness(.95)}
input.filter{width:100%;padding:9px 12px;border:1px solid var(--grid);border-radius:8px;margin:0 0 10px;font-size:14px}
details{margin:10px 0;border:1px solid var(--grid);border-radius:10px;background:var(--s);padding:4px 12px}
summary{cursor:pointer;font-weight:600;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px}
pre{overflow:auto;background:#0b0b0b;color:#e6e6e6;padding:14px;border-radius:8px;
 font:12px/1.45 ui-monospace,Menlo,Consolas,monospace;max-height:620px}
pre code{background:none;color:inherit;padding:0}
code{background:#eee;padding:1px 5px;border-radius:4px;font-size:.92em}
footer{border-top:1px solid var(--grid);margin-top:50px}
.foot-in{max-width:960px;margin:0 auto;padding:22px 20px;color:var(--mut);font-size:13px;display:flex;flex-wrap:wrap;gap:6px 18px}
@media(max-width:560px){h1{font-size:30px}}
"""
VARS = (f":root{{--s:{PAL['surface']};--pg:{PAL['page']};--ink:{PAL['ink']};--ink2:{PAL['ink2']};"
        f"--mut:{PAL['muted']};--grid:{PAL['grid']};--base:{PAL['base']};--ser:{PAL['series']};--crit:{PAL['crit']};}}")

def shell(title, active, body, hero=None):
    nav = "".join(f'<a href="{h}" class="{"on" if h==active else ""}">{e(l)}</a>' for h,l in NAV)
    hero_html = f'<section class="hero">{hero}</section>' if hero else ""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} — {BRAND}</title>
<meta name="robots" content="noindex, nofollow">
<link rel="icon" type="image/svg+xml" href="assets/logo.svg">
<style>{VARS}{CSS}</style></head><body>
<header class="nav"><div class="nav-in"><a class="brand" href="index.html"><img class="logo" src="assets/logo.svg" alt="">City Data <span>Sleuth</span></a>{nav}</div></header>
{hero_html}<main>{body}</main>
<footer><div class="foot-in">
<span>Built from public records with open-source code.</span>
<span><a href="{REPO}">Source on GitHub</a></span>
<span>Licensed GNU GPL v3</span><span>Not legal advice.</span>
</div></footer></body></html>"""

# ----------------------------------------------------------------- build
def build():
    os.makedirs(DOCS, exist_ok=True)
    roster = os.path.join(DATA, "parcel-survey-roster.csv")
    sample = os.path.join(DATA, "turnaround-sample.csv")
    analysis, rows = bp.analyze(roster, sample)
    srows = list(csv.DictReader(open(sample, newline="")))
    t = analysis.get("turnaround", {})
    median = t.get("median", "–")

    # copy static assets (plat, review-flow chart, etc.) into docs/assets/
    adir, ddir = os.path.join(CONTENT, "assets"), os.path.join(DOCS, "assets")
    flow_imgs = []
    if os.path.isdir(adir):
        os.makedirs(ddir, exist_ok=True)
        for fn in sorted(os.listdir(adir)):
            shutil.copy(os.path.join(adir, fn), os.path.join(ddir, fn))
            if fn.startswith("review-flow") and fn.lower().endswith((".png",".jpg",".jpeg",".webp")):
                flow_imgs.append(fn)
    flow_fig = ""
    if flow_imgs:
        imgs = "".join(f'<img src="assets/{e(f)}" alt="BPS parcel/survey review-flow comparison" '
                       f'style="width:100%;border:1px solid var(--grid);border-radius:8px;margin:6px 0">'
                       for f in flow_imgs)
        flow_fig = (f'<figure style="margin:0">{imgs}<figcaption class="note">Per-department review '
                    f'flow — the subject case (BPS26-0517) against comparable cases, in calendar days '
                    f'from Department Reviews start. Source: City case-check pages.</figcaption></figure>')

    # ---- index / story
    hero = f"""<h1>A permit stalled. The City's own records show how unusual that is.</h1>
<p class="lede">Small property-line changes all run through the same St. Louis review. Using the
City's published board minutes and permit-status system, this is what that process looks
like across 2026 — and one application that simply stopped.</p>
<div class="tiles">
<div class="tile"><div class="n">{analysis['total']}</div><div class="l">parcel/survey matters charted (2026)</div></div>
<div class="tile"><div class="n">~{median} days</div><div class="l">median Building review (public sample)</div></div>
<div class="tile"><div class="n crit">27 days+</div><div class="l">case BPS26-0517, still pending</div></div>
</div>"""
    body = f"""
<h2>The process</h2>
<p>Every parcel/survey permit passes through these reviews before the Board approves it:</p>
<div class="card"><div class="step"><b>1 · BPS Survey</b>→<b>2 · Water</b>→<b>3 · Assessor</b>→
<b>4 · Building (Public Safety)</b>→<b>5 · Board approval</b></div></div>
<h2>How many clear, and when</h2>
<p>In 2026 the Board approved <strong>{analysis['total']}</strong> parcel/survey matters — a steady
flow every month. (Board-approval dates, from the public minutes.)</p>
<div class="card">{bar_v(analysis['cadence'])}</div>
<h2>How Building review compares</h2>
<p>For cases where both dates are public, Building review runs from a few days to about four
weeks. The one case that took as long as BPS26-0517 carried a documented deficiency — this one shows none.</p>
{f'<div class="card">{flow_fig}</div>' if flow_fig else ''}
<div class="card">{bar_h(srows)}</div>
<p class="note">Small, non-random sample (n={t.get('n','?')}); the population distribution needs the City's
workflow data, requested via public records. See <a href="methods.html">Methods</a>.</p>
<div class="callout crit"><strong>The case in one line:</strong> every other department cleared
BPS26-0517 by Sept 15; Building has sat with <strong>no date assigned</strong> and no stated
deficiency, while {analysis['total']} comparable matters moved through. <a href="case.html">See the case →</a></div>
"""
    write("index.html", shell("A permit stalled", "index.html", body, hero=hero))

    # ---- case
    case_body = f"""<h1>The case: BPS26-0517</h1>
{read_md("permit-description.md")}
<h2>Timeline</h2>
<div class="card"><table><tbody>
<tr><td><b>9/4</b></td><td>Application submitted</td></tr>
<tr><td><b>9/9</b></td><td>BPS Survey review — approved</td></tr>
<tr><td><b>9/15</b></td><td>Water — approved</td></tr>
<tr><td><b>9/15</b></td><td>Assessor — approved</td></tr>
<tr><td><b>10/6</b></td><td><span style="color:var(--crit);font-weight:700">Building — PENDING, no date assigned</span></td></tr>
</tbody></table></div>
<div class="callout crit"><span style="font-size:26px;font-weight:800;color:var(--crit)">27 days pending</span><br>
Building shows no deficiency and no assigned date, while every other department finished by Sept 15.</div>
{f'<h2>Compared to similar cases</h2><div class="card">{flow_fig}</div>' if flow_fig else ''}
<p><a class="btn" href="exhibits.html">See the exhibits →</a></p>"""
    write("case.html", shell("The case", "case.html", case_body))

    # ---- data
    trows = "".join("<tr>"+"".join(f"<td>{e(r[k])}</td>" for k in
            ["meeting_date","bps_no","applicant","address","city_block","type"])+"</tr>"
            for r in sorted(rows, key=lambda x:(x["meeting_date"], x["bps_no"])))
    data_body = f"""<h1>The data</h1>
<p>All {len(rows)} parcel/survey matters the Board approved in 2026, extracted from the published
minutes. <a class="btn" href="parcel-survey-roster.csv">Download CSV</a></p>
<input class="filter" id="f" placeholder="Filter — applicant, address, case, type…" onkeyup="flt()">
<div class="wrap"><table id="t"><thead><tr>
<th>Board date</th><th>Case</th><th>Applicant</th><th>Property</th><th>City block</th><th>Type</th>
</tr></thead><tbody>{trows}</tbody></table></div>
<p class="note">Source: City of St. Louis Board of Public Service meeting minutes. Reproducible via
the <a href="methods.html">open-source pipeline</a>.</p>
<script>
function flt(){{var q=document.getElementById('f').value.toLowerCase();
 document.querySelectorAll('#t tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none')}}
document.querySelectorAll('#t th').forEach((th,i)=>th.onclick=()=>{{var tb=th.closest('table').tBodies[0],
 rs=[...tb.rows],a=th.d=!th.d;rs.sort((x,y)=>(a?1:-1)*x.cells[i].innerText.localeCompare(y.cells[i].innerText,undefined,{{numeric:true}}));
 rs.forEach(r=>tb.appendChild(r))}});
</script>"""
    write("data.html", shell("The data", "data.html", data_body))
    shutil.copy(roster, os.path.join(DOCS, "parcel-survey-roster.csv"))

    # ---- exhibits
    plat = ""
    for ext in ("png","jpg","jpeg","webp"):
        if os.path.exists(os.path.join(CONTENT,"assets",f"plat.{ext}")):
            os.makedirs(os.path.join(DOCS,"assets"), exist_ok=True)
            shutil.copy(os.path.join(CONTENT,"assets",f"plat.{ext}"), os.path.join(DOCS,"assets",f"plat.{ext}"))
            plat = f'<img src="assets/plat.{ext}" alt="Survey plat for BPS26-0517" style="max-width:100%;border:1px solid var(--grid);border-radius:8px">'
            break
    if not plat:
        plat = ('<div class="note">The survey plat is a public exhibit on the City case page. '
                'To include it, drop the image at <code>content/assets/plat.png</code> and rebuild.</div>')
    ex_body = f"""<h1>Exhibits</h1>
<p class="note">Deliberately excluded: ownership records, deeds, purchase contracts, and other
private documents. This page shows the permit request and the public correspondence only.</p>
<section>{read_md("permit-description.md")}</section>
<section>{read_md("alderman-email-chain.md")}</section>
<h2>One-page summary</h2>
<p>A printable summary of the case and the comparison. <a class="btn" href="summary.pdf">Download PDF</a>
<span class="note">(generated by <code>src/make_pdf.py</code>)</span></p>"""
    write("exhibits.html", shell("Exhibits", "exhibits.html", ex_body))

    # records-request page intentionally not published

    # ---- reuse
    write("reuse.html", shell("Use it yourself", "reuse.html",
          f'<article>{read_md("reuse.md")}</article>'))

    # ---- methods + code
    code_files = ["bps_pipeline.py","make_site.py","make_pdf.py","test_bps_pipeline.py"]
    blocks = []
    for fn in code_files:
        p = os.path.join(SRC, fn)
        if os.path.exists(p):
            src = e(open(p, encoding="utf-8").read()); n = src.count("\n")+1
            blocks.append(f'<details><summary>src/{fn} — {n} lines</summary><pre><code>{src}</code></pre></details>')
    sp = os.path.join(DATA,"turnaround-sample.csv")
    if os.path.exists(sp):
        src = e(open(sp).read())
        blocks.append(f'<details><summary>data/turnaround-sample.csv</summary><pre><code>{src}</code></pre></details>')
    m_body = f"""<h1>Methods &amp; code</h1>
<p>Everything that produced this site, released under the GNU GPL v3. Copy it, run it, check it.</p>
<h2>Pipeline</h2>
<ol>
<li><b>fetch</b> — download each weekly minutes PDF, verify it, extract text, write a SHA-256 manifest.</li>
<li><b>extract</b> — parse the minutes text into a parcel/survey roster (keyword + case-number rules).</li>
<li><b>analyze</b> — monthly cadence; turnaround from a documented public sample.</li>
<li><b>verify</b> — re-extract and diff against the reviewed roster (last run: exact match).</li>
<li><b>site</b> — this generator renders the pages you're reading.</li>
</ol>
<h2>What the data can and cannot show</h2>
<p>The minutes give <b>one date per case</b> (board approval), not the per-step review clock. Turnaround
exists only on the public case pages; the sample here is small and non-random. The population-wide
distribution requires the City's workflow timestamps — requested via public records (see
the records-request process).</p>
<h2>The source code</h2>
{''.join(blocks)}
<p class="note">Reproducibility: unit tests ship with the parsers; <code>verify</code> re-derives the
roster from the minutes text and diffs it against the reviewed reference. Archived PDFs carry a
SHA-256 manifest. Full repo: <a href="{REPO}">{REPO}</a>.</p>"""
    write("methods.html", shell("Methods & code", "methods.html", m_body))
    print(f"built {len(NAV)} pages -> {DOCS}")

def write(name, content):
    open(os.path.join(DOCS, name), "w", encoding="utf-8").write(content)

if __name__ == "__main__":
    build()
