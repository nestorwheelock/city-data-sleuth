# How to write a public-records request that is hard to dodge

Most requests fail not because the law is weak but because they ask for the wrong thing,
in the wrong form, from the wrong custodian — and leave the agency room to hand back a
thin, flattened subset. This is the method behind the case study on this site. It is
general; swap in your own state's open-records statute (examples cite the Missouri Sunshine
Law, Chapter 610 RSMo).

## Four principles

1. **Ask for records, not answers.** Open-records laws compel existing records and database
   fields — not new analysis. Never ask the agency to "calculate the average" or "tell me
   why." Ask for the rows; you do the math. Asking for analysis invites a lawful "we don't
   create records" refusal.
2. **Keep it neutral — don't show your hand.** The request should read as a records request
   about records, never as your theory of the case. Stating a grievance or an accusation
   tells the agency what to be defensive about and what to route to its lawyers. Describe
   the records; let them speak.
3. **Name the hidden layers.** The public-facing screen is the tip. Below it sit the
   database, the audit log, and the metadata — and that is where the real timeline lives.
   You have to name them specifically, because an agency answers what you asked, not what
   you meant.
4. **Close the exits.** Specify custodians, systems, identifiers, date ranges, format, and
   a withholding log. Every exit you leave open is one the record can slip through.

## The three layers to request

### A. The data behind the screen
- The **underlying database record**, not a screenshot or PDF of the web view — every field
  the system stores for each record, **including fields not displayed publicly**.
- The **data dictionary / schema / field list** (table layout, column names and
  definitions, and any lookup/code tables). *Request this explicitly — once you have the
  field list, the agency cannot claim a field "doesn't exist."*
- The **mapping between the public form/portal fields and the database columns** (which
  on-screen label corresponds to which stored field).
- The **audit / history / workflow log**: the row-level event trail — for each record,
  every status change with its **timestamp, the actor, the action, and old → new value**,
  plus **assignment and reassignment** events (who it was routed to, and when).

### B. The communications
- **Email** — with **full headers**, in native format (`.eml`/`.msg`), including messages
  **among** staff and **across departments**, not just the agency's replies to you.
- **Text / SMS messages** about the public business — including those on **personal
  devices** where the business was conducted there (in many states these are public
  records regardless of device).
- **Chat / instant messaging** (Teams, Slack, etc.), **voicemail**, and **call logs**.
- **Inter-office memos, routing slips, and transmittal records.**
- **Calendars and meeting records** — invitations, agendas, minutes, or notes of any
  meeting where the matter was discussed.

### C. The metadata most people never ask for
- **Native file formats with metadata intact** — spreadsheets as **CSV/XLSX**, not PDF;
  documents in their original format. *Explicitly forbid "flattening" to PDF or printouts*,
  which strips dates, authorship, and structure.
- **System-generated metadata**: created/modified timestamps, author/editor, document
  properties; image **EXIF**; email routing headers.
- **The list of systems/applications** the agency uses for this process (the permitting
  system and its vendor, the email system, chat, phone/SMS). You need this to know which
  custodian and system to name.
- **The records-retention schedule and records-management policy** for these records — this
  tells you what **must** exist, so a "no records" answer can be tested against the
  agency's own retention rules.

## Closing the exits (what makes it hard to wiggle out of)

- **Name the custodians and systems to search** — each department and each application by
  name, not "the City."
- **Give exact identifiers and search terms** — case numbers, addresses, parcel/locator
  IDs, and names — so the search is defined, not left to interpretation.
- **Set explicit date ranges** for each category.
- **Demand native electronic format with metadata**, and state that PDF printouts are not
  an acceptable substitute for data that exists in a database.
- **Require a withholding log**: for anything redacted or withheld, the specific record,
  the field, and the **statutory basis**, item by item (not a blanket citation).
- **Ask them to state their search methodology** — which systems were searched and with
  what terms. This converts a thin response into a documented one you can challenge.
- **Request the data dictionary alongside the data**, so field-level completeness is
  checkable.
- **Fees**: request an **itemized estimate in advance**, and a **fee waiver** where the use
  is in the public interest and non-commercial (discretionary in many states — make the
  case).
- **Cite the statute and the response deadline** (Missouri: three business days under
  610.023; if more time is needed they must say when and why).
- **Ask for rolling production** — records that can be produced now, produced now; the rest
  to follow — so nothing waits on the slowest item.

## Then do the analysis properly

- **Verify completeness** against an independent public source (e.g., published board
  minutes or agendas) — if the agency's export is missing cases the minutes show, you know
  the response is incomplete.
- **Load the native data** into a spreadsheet or a small script; never eyeball a PDF.
- **Compute the distribution** (median, quartiles, range) and **compare like-to-like** —
  same record type, same stage — before calling anything an outlier.
- **Preserve provenance**: keep the originals and a checksum (e.g., SHA-256) so you can
  prove later that nothing was altered.

## A neutral request skeleton

> Under [your state's open-records statute], I request the following existing records. I am
> requesting records and database fields, not asking you to create any new analysis. Where
> records exist electronically, provide them in native electronic format with metadata
> intact (CSV for tabular data; original messages with full headers) — not PDF printouts.
>
> 1. For [record type] from [date] to [date]: every field stored for each record, including
>    fields not displayed publicly; the data dictionary/field list; and the complete
>    audit/history log (timestamp, actor, action, old→new value; assignment/reassignment).
> 2. Communications concerning [identifiers] among [named custodians], [date] to [date]:
>    email (full headers), text/SMS (including personal devices used for this business),
>    chat, voicemail, call logs, routing slips, and meeting/calendar records.
> 3. The list of systems used for this process and the applicable records-retention
>    schedule.
>
> Search terms: [case #, address, parcel ID, names]. Custodians: [departments/offices].
> For anything withheld, identify the record and field and cite the statutory basis. Please
> state which systems you searched and with what terms. Provide an itemized fee estimate in
> advance; I request a fee waiver as the use is in the public interest and non-commercial.

Keep the tone administrative throughout. The strongest request asks only for records — and
lets the records tell the story.

*This is general guidance, not legal advice. For a specific dispute, consult a lawyer in
your jurisdiction.*
