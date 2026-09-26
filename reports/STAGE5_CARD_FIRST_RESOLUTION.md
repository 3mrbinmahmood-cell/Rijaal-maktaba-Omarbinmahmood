# Stage 5 — Resolve to cards before deduplication

## Locked method

Stage 5 implements the rule: **resolve each sanad occurrence to a source-backed narrator card first; deduplicate cards only later**.

Raw names are never deduplicated into people merely because their spelling matches.

## Source-card universe

Taqrib al-Tahdhib was parsed as a complete card seed:

- Taqrib source cards: **8,827**
- card aliases after name-prefix, kunyah, embedded-kunyah and patronymic extraction: **110,673**
- Taqrib cards linked to existing anchored identities: **2,584**
- Taqrib cards linked to a unique Tahdhib al-Tahdhib entry: **6,862**
- cards with usable teacher/student text from Tahdhib al-Tahdhib: **6,569**
- cards with both teacher and student sections: **6,119**

The teacher/student parser was corrected to recognize `وعنه:` / `وعنها:`, not only `روى عنه:`.

## Card-first occurrence resolution

Previously unresolved occurrences resolved to a Taqrib source card using the exact sanad context:

- source-card resolutions: **12,201**
- resolutions to an already anchored card: **7,142**
- resolutions to a provisional source-backed card: **5,059**
- distinct new provisional source cards: **813**

After integrating one additional strict kinship resolution, provisional-card occurrences are **5,060**.

Current resolved narrator occurrences:

- existing anchored cards: **47,568**
- provisional source-backed cards: **5,060**
- **total resolved to a card: 52,628**

Current unresolved narrator/relational occurrences: **148,532**.

These are occurrence counts, not unique-person counts.

## Provisional card contents

Each provisional card retains:

- its own stable provisional card ID
- Taqrib entry number and exact Taqrib text
- source identity text
- convenience grade category without replacing the exact wording
- tabaqah when parsed
- Tahdhib al-Tahdhib biography when uniquely linked
- raw teachers
- raw students
- number of corpus occurrences currently attached

Current provisional-card convenience grades:

- thiqa: 237
- saduq: 166
- acceptable: 93
- unknown: 55
- weak: 38
- companion: 38
- rejected: 10
- very weak: 2
- not yet normalized: 57

## High-frequency improvements

The card-first pass resolved many occurrences that were previously blocked by short names or kunyahs, including occurrences of:

- Shu'bah
- Abu Hurayrah
- Ibn Abbas
- al-Zuhri / Ibn Shihab
- Qatadah
- Ma'mar
- Malik
- al-A'mash
- al-Awza'i
- Ibn al-Mubarak
- Abd al-Rahman ibn Mahdi
- Abu Usamah
- Abu Awanah
- Abu Nu'aym
- Abu Kurayb
- Ibn Jurayj
- Ibn Wahb

No short form is assigned globally; each occurrence is evaluated in its own chain.

## Card-first sanad graph

The graph can now use either an existing anchor ID or a provisional card ID as a node.

- resolved adjacent links: **24,533**
- relationship-supported links: **24,223**
- links still needing relationship evidence: **232**
- chronology-conflict flags for review: **78**
- fully card-resolved sanad branches: **1,715**

These are analyzer inputs, not final hadith rulings.

## Kinship safety

A new card-level `أبيه` resolver was tested. An early version was rejected because one-word fathers such as `أسلم` were not specific enough and compound names such as `عبد الله` could be split incorrectly.

The accepted rule now:

1. resolve the governing narrator card first;
2. derive the father using lineage segments separated by `بن`, preserving compound names;
3. require at least father + grandfather lineage;
4. require a unique source-card match;
5. require teacher/student context;
6. otherwise leave `أبيه` unresolved.

This intentionally resolves fewer kinship cases rather than risk mixing two fathers.
