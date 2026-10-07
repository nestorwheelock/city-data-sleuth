# Use this in your town

This project is a **method**, not just one city's story. If your local government runs
permits, licenses, inspections, or cases through an online system and publishes board
agendas or minutes, you can do exactly what the case study here does.

## Who it's for
- **Residents** trying to understand why their own case is stuck, and whether it's unusual.
- **Journalists** looking for a documented, reproducible story instead of an anecdote.
- **Researchers and watchdogs** measuring how a public process actually performs.

## The pattern
1. **Find the public surfaces** — the status-lookup system and the published
   agendas/minutes. One gives you per-case detail; the other gives you the full universe.
2. **Archive the originals** with a checksum manifest, so the record is provably unaltered.
3. **Extract with tested parsers**, not by hand — so anyone can re-run and get the same table.
4. **Verify** the automated extract against the published record for completeness.
5. **Analyze** — compute the distribution, compare like-to-like, find the outliers.
6. **Request what's missing** — the per-step timestamps and communications usually live in a
   database you can only reach with a public-records request.

## The one rule
Stay on the public side. Read what the government actually publishes; use the records
process for the rest. Don't bypass access controls or reuse other people's keys — the
boundary is both the ethics and the credibility of the work.

## Make it yours
The code is general. To point it at a different city or record type, change the source URLs
and the keyword rules in the extractor, then re-run the pipeline. It's released under the
GNU GPL v3 — free to use, study, modify, and share.
