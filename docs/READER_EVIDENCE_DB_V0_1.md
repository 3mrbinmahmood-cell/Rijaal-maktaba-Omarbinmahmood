# Reader Evidence Database v0.1

This is the compact database intended for the reader application. It deliberately does **not** require global narrator-card deduplication.

## Current size and contents

Built from the audited Stage-6 research database:

- uncompressed SQLite: ~123 MB
- gzip-compressed: ~32 MB
- cards: 4,633
- attributed critic statements: 14,392
- sanad candidates: 40,334
- sanad nodes: 207,814
- analyzed narrator-to-narrator links: 30,148
- branch summaries: 41,551
- terminal-repair records: 6,654

The database passes SQLite `PRAGMA quick_check`.

## Reader model

The reader needs seven core tables:

- `cards` — source-backed narrator cards
- `critic_statements` — attributed jarh/ta'dil evidence
- `sanads` — original sanad text and book provenance
- `sanad_nodes` — every narrator occurrence in chain order
- `sanad_edges` — evidence on each narrator-to-narrator connection
- `branch_summary` — quick chain-level completeness/status
- `terminal_repairs` — separates real Prophet terminals from narrators whose descriptions mention the Prophet

A card is stored once. Thousands of hadith occurrences may point to that same card.

## Visual chain example

A fully card-resolved chain from Sunan al-Nasa'i no. 1701 currently renders conceptually as:

`Yahya b. Musa → Abd al-Aziz b. Khalid → Sa'id b. Abi Aruba → Qatada → Azra → Sa'id b. Abd al-Rahman b. Abza → أبيه = Abd al-Rahman b. Abza → Ubayy b. Ka'b`

The `أبيه` node is resolved contextually from the governing narrator, not by treating `أبيه` as a name.

Six of the seven current links have stored teacher/student support. The remaining link is shown as **needs relationship evidence** rather than being silently marked continuous.

## UI principle

For every narrator node show:
- name
- convenient grade
- exact source wording
- critic statements
- dates/tabaqah
- teachers/students
- tadlis/ikhtilat evidence when present

For every link show:
- transmission term
- actual occurrence in this sanad
- teacher/student support
- explicit hearing evidence when available
- chronology
- tadlis/an'anah warning
- continuity / break / uncertainty

Existing scholar rulings remain a separate layer from automated evidence analysis.
