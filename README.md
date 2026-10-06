# City Data Sleuth

**Connect the dots in local government, using only public records.**

A reusable toolkit — and a worked case study — for measuring how a city process actually
performs, built entirely from public data with every step scripted, tested, and checkable.
The case study examines St. Louis **parcel/survey permits** (property-boundary changes) and
one application, BPS26-0517, that stalled while comparable cases moved.

Live site: build it with `make_site.py` (below) and publish `docs/` to GitHub Pages.

## Why

An anecdote is "my permit is stuck." Evidence is "here is the whole year of comparable
cases, from the City's own minutes, with a reproducible pipeline anyone can re-run." This
project turns the first into the second.

## Repository layout

```
src/   bps_pipeline.py    fetch · extract · analyze · verify · site (the analysis)
       make_site.py       multi-page static-site generator
       make_pdf.py        one-page case summary PDF
       test_bps_pipeline.py   parser unit tests
data/  parcel-survey-roster.csv   extracted roster (output of `extract`)
       turnaround-sample.csv      documented public case-check sample
content/   markdown for the narrative pages (edit these)
docs/      the generated site (GitHub Pages root)
```

## Requirements

- Python 3.9+ (standard library only)
- `pdftotext` (poppler-utils) for `fetch`
- `wkhtmltopdf` for the summary PDF

## Run it

```bash
python3 src/bps_pipeline.py fetch   --minutes-dir ./minutes-2026 --year 2026
python3 src/bps_pipeline.py extract --minutes-dir ./minutes-2026 --out ./data/parcel-survey-roster.csv
python3 src/bps_pipeline.py verify  --minutes-dir ./minutes-2026 --reference ./data/parcel-survey-roster.csv
python3 src/bps_pipeline.py analyze --roster ./data/parcel-survey-roster.csv --sample ./data/turnaround-sample.csv
python3 -m unittest discover -s src -p 'test_*.py'      # or: python3 src/test_bps_pipeline.py
python3 src/make_site.py                                  # builds docs/
python3 src/make_pdf.py                                   # builds docs/summary.pdf
```

## Reproducibility

- `verify` re-derives the roster from the minutes text and diffs case numbers against a
  reviewed reference — a clean run prints **"EXACT MATCH on case numbers."**
- `fetch` writes `MANIFEST.sha256`; `sha256sum -c` proves the archived PDFs are unaltered.
- The parsers ship with unit tests.

## The ethical boundary (also the credibility)

Only public surfaces are used: what the government publishes (minutes, agendas) and the
formal records process. Access controls are never bypassed and other people's access keys
are never reused. Where the public surface runs out, file a public-records request — see
`content/records-request-guide.md`.

## Use it in your town

Change the source URLs and the keyword rules in `src/bps_pipeline.py`, then re-run. The
method is general; see the "Use it yourself" page.

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later). See `LICENSE`.
Copyright (C) 2026 Nestor Wheelock.

*Not legal advice.*
