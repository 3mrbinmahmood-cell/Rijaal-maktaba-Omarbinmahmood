# Stage 4 — Secondary rijal sources and preliminary sanad graph

## Secondary entry boundaries

This stage replaces unsafe page-level name hits with discrete source-entry matching.

Parsed usable entries:
- Tahdhib al-Tahdhib (al-Risala): 10,030
- al-Tarikh al-Kabir (al-Bukhari): 13,011
- al-Isaba fi Tamyiz al-Sahaba: 11,973
- al-Kashif: 6,826
- Mizan al-I'tidal: 816 currently parsed; this parser is incomplete and Mizan is therefore supplementary only at this stage.

## Coverage of current 2,969 narrator identities

Unique entry matches:
- Tahdhib al-Tahdhib: 2,757 cards
- al-Kashif: 2,512 cards
- al-Tarikh al-Kabir: 1,288 cards
- al-Isaba: 530 cards
- Mizan al-I'tidal: 294 cards

At least one secondary source entry is attached to **2,917 / 2,969** current narrator identities.

New evidence extracted:
- attributed critic statements: **9,308**
- dated-event evidence rows: **858**
- source-specific compact grade evidence: **1,072**

All evidence remains source-specific. It does not overwrite Ibn Hajar, Tahdhib al-Kamal, or another critic.

## Preliminary sanad analyzer graph

This is evidence for the future analyzer, **not a final hadith grading**.

Resolved adjacent narrator links: **9,108**

Preliminary statuses:
- supported by reported teacher/student relation + observed corpus transmission: **6,524**
- repeated corpus transmission but reported-source relation still needed: **419**
- observed-only, needs review: **1,482**
- reported relation but possible tadlis/an'anah review: **185**
- tadlis review without reported relation: **466**
- chronology conflict: **32**

Additional warnings:
- links touching a weak/very-weak/rejected/unknown convenience grade: **637**
- possible tadlis/an'anah warnings: **652**

Sanad branches represented: **41,551**
Fully identity-resolved end-to-end branches: **266**

The low fully-resolved count is intentional: unresolved names are not forced merely to produce a complete chain.

## Rules

1. Relational tokens such as abihi / jaddihi / ammihi remain occurrence-specific relationship pointers.
2. Automated link analysis is derived data and may be rebuilt without altering source evidence.
3. A reported teacher/student relationship, actual observed transmission, chronology, tadlis, and narrator criticism are separate evidence dimensions.
4. Existing named-scholar hadith grades remain separate from automated sanad analysis.
5. The Shamela 18,989-card seed remains a primary identity source and external-ID layer when imported.
