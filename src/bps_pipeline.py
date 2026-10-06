#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nestor Wheelock.  Licensed under the GNU GPL v3 or later.
"""
bps_pipeline.py — reproducible analysis of St. Louis Board of Public Service (BPS)
"Parcel and Survey" permits, built entirely from public records.

Stages (run as subcommands):
    fetch     download the weekly BPS meeting-minutes PDFs + SHA-256 manifest
    extract   parse the minutes text -> parcel/survey roster (CSV)
    analyze   roster -> cadence counts + turnaround distribution (reads a documented sample)
    verify    compare a fresh extract against a reviewed roster (reproducibility check)
    site      render a self-contained static HTML page from roster + analysis
    all       extract + analyze + site

Data sources (both public):
  - BPS weekly board-meeting minutes (PDFs published by the City)
  - the City case-check system (per-case review dates), used only for the turnaround
    sample and only where a page is already public.

Dependencies: Python 3.9+ stdlib, plus the `pdftotext` binary (poppler-utils) for `fetch`.
Nothing here requires network except `fetch`.
"""
from __future__ import annotations
import argparse, csv, datetime, glob, hashlib, html, os, re, statistics, subprocess, sys
from collections import Counter

# --------------------------------------------------------------------------- config
MONTHS = ["January","February","March","April","May","June","July","August",
          "September","October","November","December"]
BASE_URL = ("https://www.stlouis-mo.gov/government/departments/public-service/"
            "documents/upload")

# Palette (dataviz reference instance): single blue for magnitude; reserved red for the
# one highlighted case, always accompanied by a text label (never color alone).
PAL = dict(surface="#fcfcfb", page="#f9f9f7", ink="#0b0b0b", ink2="#52514e",
           muted="#898781", grid="#e1e0d9", base="#c3c2b7", series="#2a78d6",
           crit="#d03b3b")

# A property-boundary-change (parcel/survey) matter. Phrase-based, not bare words:
# "boundary"/"property line" must appear in an ADJUSTMENT context, so geographic uses
# ("trash receptacles within the CID boundary", "fence along the property line") don't match.
PARCEL_RE = re.compile(r"""
      consolidat
    | subdivi | re-?subdivi
    | \blot\s+split\b | \bparcel\s+split\b
    | (?:divide|split)\s+the\s+existing\s+(?:lot|parcel)
    | into\s+\w+\s+new\s+(?:parcels|lots)
    | boundary\s+adjustment | adjust\w*\s+the\s+boundary | boundary/property\s*line
    | property\s*line\s+adjustment | adjust\w*\s+the\s+property\s*line
    | fee\s+simple
    | \bplat\b
""", re.I | re.X)

ITEM_RE = re.compile(r"\b(30[6-9]\d{3})\b")                 # 6-digit board item number
BPS_RE  = re.compile(r"\b(BPS\d{2}-\d{4})\b")               # case number
CB_RE   = re.compile(r"C\.?\s*B\.?\s*"
                     r"([0-9]{1,4}(?:[-–][0-9A-Za-z]+)?"
                     r"(?:\s*(?:&|and|,|E\.?|W\.?)\s*[0-9A-Za-z\-]+)*)")
APPLICANT_RE = re.compile(r"(?:Request\s+(?:submitted\s+)?by|submitted\s+by)\s+(.+?)"
                          r"\s+(?:to\b|for\b|requesting\b)", re.I)
HEADER_RE = re.compile(r"^[ \t]*[A-Z][A-Z &/,\.]{6,}$")

TYPE_RULES = [  # (regex, canonical label)  -- order matters, first match wins
    (r"re-?subdivi", "re-subdivision"),
    (r"consolidat", "consolidation"),
    (r"divide\s+the\s+existing\s+lot|into\s+\w+\s+new\s+lots", "subdivision"),
    (r"split\s+the\s+existing\s+parcel|\bparcel\s+split\b|into\s+\w+\s+new\s+parcels", "parcel split"),
    (r"subdivi", "subdivision"),
    (r"\blot\s+split\b", "lot split"),
    (r"boundary\s+adjustment|adjust\w*\s+the\s+boundary|boundary/property", "boundary adjustment"),
    (r"property\s*line\s+adjustment|adjust\w*\s+the\s+property", "property line adjustment"),
    (r"fee\s+simple", "subdivision"),
    (r"\bplat\b", "plat"),
]

# --------------------------------------------------------------------------- helpers
def tuesdays(year: int):
    """Every Tuesday of `year` as (MonthName, day)."""
    d = datetime.date(year, 1, 1)
    d += datetime.timedelta(days=(1 - d.weekday()) % 7)      # first Tuesday
    while d.year == year:
        yield MONTHS[d.month - 1], d.day
        d += datetime.timedelta(days=7)

def classify(block: str):
    """Return a roster dict for a minutes item block, or None if not parcel/survey."""
    if not PARCEL_RE.search(block):
        return None
    mitem, mbps = ITEM_RE.search(block), BPS_RE.search(block)
    if not (mitem and mbps):
        return None
    excerpt = re.sub(r"\s+", " ", block).strip()
    mapp = APPLICANT_RE.search(excerpt)
    applicant = mapp.group(1).strip().rstrip(",") if mapp else ""
    mcb = CB_RE.search(excerpt)
    typ = next((lab for pat, lab in TYPE_RULES if re.search(pat, excerpt, re.I)), "parcel/survey")
    maddr = re.search(r"\b(?:at|located at)\s+(.+?)(?:,?\s+in\s+C\.?\s*B\.?|\.\s*$|$)",
                      excerpt, re.I)
    address = maddr.group(1).strip().rstrip(".") if maddr else ""
    return dict(item_no=mitem.group(1), bps_no=mbps.group(1), applicant=applicant,
                address=address, city_block=(mcb.group(1).strip().rstrip(".") if mcb else ""),
                type=typ, excerpt=excerpt)

def iter_item_blocks(text: str):
    """Split a minutes text into (item_no, block) spans at each board item number."""
    starts = [(m.start(), m.group(1)) for m in ITEM_RE.finditer(text)]
    for i, (pos, item) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        yield item, text[pos:end]

def date_from_filename(path: str):
    m = re.search(r"BPS-Minutes-([A-Za-z]+)-(\d{1,2})-(\d{4})", os.path.basename(path))
    if not m:
        return ""
    mon = MONTHS.index(m.group(1)) + 1
    return f"{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}"

def version_from_filename(path: str):
    return "Preliminary" if "Preliminary" in path else "Approved"

# --------------------------------------------------------------------------- stages
def fetch(minutes_dir: str, year: int):
    """Download minutes PDFs (Approved, else Preliminary), text, and a SHA-256 manifest."""
    import urllib.request, urllib.error
    os.makedirs(minutes_dir, exist_ok=True)
    got = missing = 0
    for mon, day in tuesdays(year):
        stem = f"BPS-Minutes-{mon}-{day}-{year}"
        if glob.glob(os.path.join(minutes_dir, f"{stem}-*.pdf")):
            got += 1; continue
        ok = None
        for ver in ("Approved", "Preliminary"):
            url, out = f"{BASE_URL}/{stem}-{ver}.pdf", os.path.join(minutes_dir, f"{stem}-{ver}.pdf")
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = r.read()
                if data[:4] == b"%PDF":
                    open(out, "wb").write(data); ok = ver; break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                pass
        print(f"{'GOT ' if ok else 'MISS'} {stem}{f' [{ok}]' if ok else ''}")
        got += bool(ok); missing += (not ok)
    for pdf in glob.glob(os.path.join(minutes_dir, "*.pdf")):          # text sidecars
        txt = pdf[:-4] + ".txt"
        if not os.path.exists(txt):
            subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
    manifest = os.path.join(minutes_dir, "MANIFEST.sha256")            # integrity
    with open(manifest, "w") as mf:
        for pdf in sorted(glob.glob(os.path.join(minutes_dir, "*.pdf"))):
            h = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
            mf.write(f"{h}  {os.path.basename(pdf)}\n")
    print(f"--- have {got}, missing {missing}; manifest -> {manifest}")

def extract(minutes_dir: str, out_csv: str):
    """Parse every minutes .txt into a parcel/survey roster CSV."""
    rows = []
    for txt in sorted(glob.glob(os.path.join(minutes_dir, "*.txt"))):
        date, ver, body = date_from_filename(txt), version_from_filename(txt), open(txt, encoding="utf-8", errors="replace").read()
        for _item, block in iter_item_blocks(body):
            rec = classify(block)
            if rec:
                rec["meeting_date"], rec["minutes_version"] = date, ver
                rows.append(rec)
    rows = dedupe(rows)
    cols = ["meeting_date","item_no","bps_no","applicant","address","city_block",
            "type","minutes_version","excerpt"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"extracted {len(rows)} parcel/survey matters -> {out_csv}")
    return rows

def dedupe(rows):
    seen, out = set(), []
    for r in sorted(rows, key=lambda x: (x["meeting_date"], x["item_no"])):
        if r["item_no"] in seen: continue
        seen.add(r["item_no"]); out.append(r)
    return out

def analyze(roster_csv: str, sample_csv: str | None = None):
    rows = list(csv.DictReader(open(roster_csv, newline="")))
    cadence = Counter(r["meeting_date"][:7] for r in rows)
    out = {"total": len(rows), "cadence": dict(sorted(cadence.items()))}
    if sample_csv and os.path.exists(sample_csv):
        srows = list(csv.DictReader(open(sample_csv, newline="")))
        days = sorted(int(s["days"]) for s in srows if s.get("pending") != "1")
        clean = sorted(int(s["days"]) for s in srows
                       if s.get("pending") != "1" and s.get("deficiency") != "1")
        out["turnaround"] = dict(
            n=len(days), values=days, min=min(days), median=statistics.median(days),
            max=max(days), mean=round(statistics.mean(days), 1),
            clean_values=clean)
    return out, rows

def verify(minutes_dir: str, reference_csv: str, tmp_csv: str):
    """Reproducibility check: re-extract and diff case-number sets vs a reviewed roster."""
    fresh = {r["bps_no"] for r in extract(minutes_dir, tmp_csv)}
    ref = {r["bps_no"] for r in csv.DictReader(open(reference_csv, newline=""))}
    only_fresh, only_ref = sorted(fresh - ref), sorted(ref - fresh)
    print(f"reference cases: {len(ref)} | extracted cases: {len(fresh)} | "
          f"in both: {len(fresh & ref)}")
    if only_ref:   print("  only in reference (extractor missed):", ", ".join(only_ref))
    if only_fresh: print("  only in extract (reference missed):  ", ", ".join(only_fresh))
    if not (only_ref or only_fresh): print("  EXACT MATCH on case numbers.")
    return not (only_ref or only_fresh)

# --------------------------------------------------------------------------- site
def _bar_v(vals, labels, w=620, h=240, pad=34):
    mx = max(vals) or 1; bw = (w - 2*pad)/len(vals); inner = h - 2*pad; s = []
    s.append(f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Approvals per month" '
             f'style="width:100%;height:auto;font:12px system-ui,sans-serif">')
    for gy in range(0, mx+1, max(1, mx//4)):
        y = h-pad-inner*gy/mx
        s.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{w-pad}" y2="{y:.1f}" stroke="{PAL["grid"]}"/>')
        s.append(f'<text x="{pad-6}" y="{y+4:.1f}" text-anchor="end" fill="{PAL["muted"]}">{gy}</text>')
    for i,(v,lb) in enumerate(zip(vals, labels)):
        bh = inner*v/mx; x = pad+i*bw+bw*0.18; bwid = bw*0.64; y = h-pad-bh
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bwid:.1f}" height="{bh:.1f}" rx="4" '
                 f'fill="{PAL["series"]}"><title>{lb}: {v}</title></rect>')
        s.append(f'<text x="{x+bwid/2:.1f}" y="{y-5:.1f}" text-anchor="middle" '
                 f'fill="{PAL["ink2"]}" font-weight="600">{v}</text>')
        s.append(f'<text x="{x+bwid/2:.1f}" y="{h-pad+15:.1f}" text-anchor="middle" '
                 f'fill="{PAL["muted"]}">{lb}</text>')
    s.append(f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="{PAL["base"]}"/></svg>')
    return "".join(s)

def build_site(roster_csv, analysis, rows, outdir, sample_rows=None):
    os.makedirs(outdir, exist_ok=True)
    e = lambda s: html.escape(s or "")
    cad = analysis["cadence"]
    mlbl = [m[5:] for m in cad]; mon_names = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    short = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
             "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
    labels = [short[m] for m in mlbl]; vals = list(cad.values())
    trows = "".join("<tr>"+"".join(f"<td>{e(r[k])}</td>" for k in
            ["meeting_date","bps_no","applicant","address","city_block","type"])+"</tr>"
            for r in sorted(rows, key=lambda x:(x["meeting_date"], x["bps_no"])))
    t = analysis.get("turnaround", {})
    turic = (f'median {t["median"]} days (n={t["n"]}; range {t["min"]}–{t["max"]})'
             if t else "sample pending")
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>St. Louis Parcel &amp; Survey Permits — methodology &amp; data</title>
<style>
body{{margin:0;background:{PAL['page']};color:{PAL['ink']};
font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:860px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:28px}} h2{{font-size:20px;border-bottom:2px solid {PAL['ink']};padding-bottom:4px;margin-top:1.8em}}
.note{{font-size:13px;color:{PAL['muted']}}}
table{{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:5px 8px;border-bottom:1px solid {PAL['grid']}}}
.wrap{{max-height:460px;overflow:auto;border:1px solid {PAL['grid']};border-radius:8px}}
a{{color:{PAL['series']}}} code{{background:#eee;padding:1px 4px;border-radius:3px}}
details{{margin:10px 0;border:1px solid {PAL['grid']};border-radius:8px;background:{PAL['surface']};padding:4px 10px}}
summary{{cursor:pointer;font-weight:600;font-family:ui-monospace,Menlo,Consolas,monospace}}
pre{{overflow:auto;background:#0b0b0b;color:#e6e6e6;padding:12px;border-radius:8px;
font:12px/1.45 ui-monospace,Menlo,Consolas,monospace;max-height:560px}}
pre code{{background:none;color:inherit;padding:0}}
</style></head><body><main>
<h1>St. Louis parcel &amp; survey permits — data &amp; method</h1>
<p class="note">Built from public records with an open-source Python pipeline. Reproducible: run it yourself.</p>
<h2>How many clear, and when</h2>
<p>{analysis['total']} parcel/survey matters in the {len(cad)} months covered. Turnaround sample: {turic}.</p>
{_bar_v(vals, labels)}
<h2>Method</h2>
<ol>
<li><b>Sources</b> — public BPS board minutes (PDFs) and the City case-check system.</li>
<li><b>fetch</b> — downloads each weekly minutes PDF, verifies it, extracts text, writes a SHA-256 manifest.</li>
<li><b>extract</b> — parses the minutes text for parcel/survey items (keyword + case-number match).</li>
<li><b>analyze</b> — monthly cadence; turnaround from a documented case-check sample.</li>
<li><b>verify</b> — re-extracts and diffs against the reviewed roster.</li>
</ol>
<p class="note">Limitation: the minutes give one date per case (board approval), not the per-step
review clock; the turnaround sample is small and non-random. The population distribution
requires the City's workflow data (requested under the Missouri Sunshine Law).
Code: <code>bps_pipeline.py</code>. Data: <a href="parcel-survey-roster.csv">roster CSV</a>.</p>
<h2>The data</h2>
<div class="wrap"><table><thead><tr><th>Board date</th><th>Case</th><th>Applicant</th>
<th>Property</th><th>City block</th><th>Type</th></tr></thead><tbody>{trows}</tbody></table></div>
</main></body></html>"""
    out = os.path.join(outdir, "index.html"); open(out, "w").write(doc)
    import shutil; shutil.copy(roster_csv, os.path.join(outdir, "parcel-survey-roster.csv"))
    print(f"site -> {out}")

# --------------------------------------------------------------------------- CLI
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("fetch");   sp.add_argument("--minutes-dir", required=True); sp.add_argument("--year", type=int, default=2026)
    sp = sub.add_parser("extract"); sp.add_argument("--minutes-dir", required=True); sp.add_argument("--out", required=True)
    sp = sub.add_parser("analyze"); sp.add_argument("--roster", required=True); sp.add_argument("--sample")
    sp = sub.add_parser("verify");  sp.add_argument("--minutes-dir", required=True); sp.add_argument("--reference", required=True); sp.add_argument("--tmp", default="/tmp/_bps_fresh.csv")
    sp = sub.add_parser("site");    sp.add_argument("--roster", required=True); sp.add_argument("--sample"); sp.add_argument("--outdir", required=True)
    a = p.parse_args(argv)
    if a.cmd == "fetch":    fetch(a.minutes_dir, a.year)
    elif a.cmd == "extract": extract(a.minutes_dir, a.out)
    elif a.cmd == "analyze":
        res, _ = analyze(a.roster, a.sample); import json; print(json.dumps(res, indent=2))
    elif a.cmd == "verify":  sys.exit(0 if verify(a.minutes_dir, a.reference, a.tmp) else 1)
    elif a.cmd == "site":
        res, rows = analyze(a.roster, a.sample); build_site(a.roster, res, rows, a.outdir)

if __name__ == "__main__":
    main()
