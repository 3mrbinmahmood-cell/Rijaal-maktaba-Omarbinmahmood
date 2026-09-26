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
