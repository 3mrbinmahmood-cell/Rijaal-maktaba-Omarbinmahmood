# Stage 6 — Card-first expansion and extraction audit

Stage 6 continues the locked rule: **resolve occurrences to source-backed cards before card deduplication**.

## Resolution checkpoint

Identity-bearing narrator/relational occurrences in the current raw layer: **201,160**

Resolved to a card:
- **66,352 occurrences (33.0%)**
- existing anchored-card occurrences: current map retains the previously anchored identities plus new contextual resolutions
- provisional source-card occurrences are retained separately and are not deduplicated

Unresolved:
- **134,808 occurrences (67.0%)**

Distinct cards currently used by resolved occurrences:
- existing anchored cards: **2,860**
- provisional source-backed cards: **1,617**
- **total used cards before deduplication: 4,477**

## Stage-6 seed rule

A previously unresolved name is allowed to attach without neighboring context only when:
1. it contains at least three normalized tokens; and
2. that exact prefix belongs to exactly one card across the complete **8,827-card Taqrib universe**.

This produced **9,571 direct source-card seeds**.

Two-token or one-token forms are never resolved by this rule.

## Context resolver safety

Shorter names are resolved occurrence-by-occurrence using the exact sanad context.

Teacher/student corroboration now uses **specific identity keys**, not generic names:
- full identity;
- person + father;
- person + father + grandfather;
- sufficiently specific kunyah forms.

Generic keys such as `عبد الله`, `سفيان`, or `أبو سلمة` are not accepted as relationship proof.

This tightening was introduced after auditing false-positive candidate experiments. Those experimental matches were discarded before the Stage-6 checkpoint.

## Kinship

`أبيه` remains a relationship pointer, never a narrator name.

The strict father resolver:
1. resolves the governing narrator card;
2. derives father + grandfather from that card's lineage;
3. requires exactly one source-card candidate;
4. requires corroboration from the next resolved narrator;
5. otherwise leaves the occurrence unresolved.

The current strict pass resolves only the cases that survive all guards.

## Prophet-terminal extraction repair

The earlier raw parser labeled every occurrence containing `النبي` or `رسول الله` as a Prophet terminal. Stage 6 separates:

- **4,736 pure Prophet terminals**
- **759 narrator + Prophet-terminal expressions**
- **1,159 narrator descriptions containing Prophet wording but not themselves Prophet terminals**

Examples of the latter include `ثوبان مولى رسول الله` and `عائشة زوج النبي`.

This repair is stored as a derived layer; original raw text is preserved.

## Analyzer-facing graph

With the Stage-6 card map:
- resolved adjacent narrator-card links: **30,148**
- supported by the audited existing anchor graph: **15,324**
- supported bilaterally from source teacher/student lists: **2,233**
- supported from one source direction: **6,936**
- still needing relationship evidence: **5,655**

The graph is evidence for the future sanad analyzer, not a final hadith grade.

## Next

1. resolve more high-frequency short names using source cards plus specific lineage context;
2. resolve repaired hidden terminal narrators;
3. import the 18,989 Shamela S1 cards/IDs when the seed is available;
4. only after occurrence resolution is much higher, deduplicate cards representing the same historical person.


## Final audited Stage-6 breakdown

Compared with the Stage-5 card map, Stage 6 adds **13,727 resolved narrator occurrences**:

- unique 3+ token source-card prefix seeds: **9,571**
- specific teacher/student-context resolutions: **4,114**
- strict contextual father (`أبيه` / `أبي`) resolutions: **28**
- repeated two-sided sanad-signature propagation: **14**

Final identity occurrence count: **66,352 / 201,160 = 33.0%**.

Remaining unresolved: **134,808**.

The current resolved occurrences use **4,477 distinct cards before deduplication**:
- 2,860 existing anchored cards
- 1,617 provisional source-backed cards

### Relationship-evidence tightening

During audit, generic relationship keys were rejected. A teacher/student list match may not rely on a common form such as `عبد الله`, `سفيان`, or a bare `أبو سلمة`. The Stage-6 resolver now requires a sufficiently specific identity key such as person+father, person+father+grandfather, or a longer kunyah/nasab form.

Experimental one-sided nisba matches (for example a bare `الزهري`) were discarded rather than integrated.

### Terminal repair

Of 6,654 raw occurrences previously tagged as Prophet terminals:
- 4,736 are pure Prophet terminals
- 759 contain a narrator followed by an actual Prophet terminal
- 1,159 are narrator descriptions containing Prophet wording but are not Prophet terminals themselves

A conservative first repair pass resolves **92 hidden narrator nodes** to existing/provisional cards. These are stored separately and are not added to the 201,160 denominator until the raw chain-node model is rebuilt.
