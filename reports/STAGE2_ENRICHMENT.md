# Stage 2 — Card enrichment and identity candidate queue

## Structured card enrichment

Current anchored narrator cards: **2,862**

From Ibn Hajar's Taqrib summaries:
- cards with a structured grade category: **2,386**
- cards with parsed tabaqah: **2,138**
- flagged for tadlis in the summary: **30**
- flagged for ikhtilat: **16**
- flagged for late memory change: **12**

From Tahdhib al-Kamal date evidence:
- cards with a parsed birth year candidate: **154**
- cards with a parsed death year candidate: **1,080**

Grade-category counts:
- thiqa: **1,027**
- saduq: **604**
- acceptable/maqbul: **263**
- weak: **183**
- companion: **141**
- unknown/majhul: **118**
- rejected/matruk/kadhdhab: **49**
- very weak: **1**
- no structured Taqrib grade yet: **476**

The exact Ibn Hajar wording is always retained alongside the normalized convenience category.

## Individual critic statements

A conservative first pass over Tahdhib al-Kamal extracted **5,084** attributed critic statements across **1,913** narrator cards.

The database stores separately:
- final critic name
- full attribution chain when the statement is transmitted through another person
- exact judgment wording
- a convenience judgment category
- source title
- extraction confidence

No disagreement is collapsed into a single verdict.

## Unresolved occurrence candidate queue

The resolver remains occurrence-specific. It does not assume that one short name always means one narrator.

- unresolved occurrences with at least one current-card candidate: **53,507**
- total candidate rows retained: **503,939**
- ambiguous after scoring: **43,818**
- unique-candidate-high queue: **1,844**
- unique-top-review queue: **7,818**
- clearly separated strong top candidates: **27**

The 27 strong candidates are still a queue, not silently promoted identities. The Shamela 18,989-card overlay and further rijal evidence should be used before promotion.

## Shamela integration

The public Shamela 4 extraction documents:
- **18,989 narrator records**
- **35,526 isnad records**

The Shamela S1/reverse-engineered card set is locked as a primary identity seed. Our own stable narrator IDs remain canonical; Shamela IDs are retained as external cross-references.
