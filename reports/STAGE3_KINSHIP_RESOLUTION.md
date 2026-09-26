# Stage 3 — Contextual kinship resolution

The resolver now treats kinship expressions as relationship pointers, never names.

## Parser correction

Tahdhib al-Kamal uses both vocalized/unvocalized forms of `روى عن` and sometimes omits the colon. The core parser was corrected to recognize these forms without confusing `روى عن` with `روى عنه`. Existing narrator IDs are retained.

## Current results

- anchored narrator identities: **2,969**
- current strong/provisional resolved sanad occurrences: **39,578**
- narrator identities newly exposed through kinship context: **107**
- exact relational occurrences resolved: **1,815**
- prefixed/named relational occurrences resolved: **92**
- total contextually resolved kinship occurrences in this pass: **1,907**

Examples:
- `هشام بن عروة → أبيه` resolves to **عروة بن الزبير**.
- `عون بن أبي جحيفة → أبيه` resolves to **أبو جحيفة وهب بن عبد الله**, not to another biography that merely mentions Abu Juhayfa.
- `سهيل بن أبي صالح → أبيه` resolves to **أبو صالح ذكوان السمان**, not `صالح بن أبي صالح`.
- `بهز بن حكيم → أبيه → جده` resolves to **حكيم بن معاوية → معاوية بن حيدة**.

## Safety rules

1. `أبيه`, `جده`, `عمه`, etc. are never globally deduplicated.
2. The governing narrator in that exact sanad must resolve first.
3. Kunyah matching uses the narrator's own identity introduction, not incidental mentions elsewhere in a biography.
4. Direct lineage matches require a unique multi-token lineage.
5. Explicit relational names such as `جده رافع بن خديج` are preserved as relational evidence and matched separately.
6. If candidate evidence remains tied or weak, the occurrence stays unresolved.
7. Raw sanad wording is never overwritten.

## Shamela seed

The public Shamela 4 metadata directory currently exposes both `narrators.jsonl` (53 MB) and `narrators.parquet` (7.96 MB), representing 18,989 narrator records. The project remains designed to overlay those Shamela IDs on these identities; classical-source and actual-isnad evidence remain the final disambiguation guards.
