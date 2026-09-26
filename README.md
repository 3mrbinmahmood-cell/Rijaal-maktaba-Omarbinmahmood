# Rijaal Maktaba Omar bin Mahmood

This repository is the source corpus and structured database project for the rebuilt hadith reader, rijal search, takhrij layer, and full sanad analyzer.

## Current phase
Phase 1: normalize and identify the fixed hadith corpus.

### File naming convention
`<book name> - المجلد NN.htm`

Introductions use:
`<book name> - المقدمة.htm`

Supplements use:
`<book name> - ملحق N.htm`

The original HTML contents are preserved unchanged; only filenames are normalized.

## Next
1. Extract every sanad from the fixed corpus.
2. Extract every narrator occurrence.
3. Resolve unique narrator identities conservatively.
4. Match against Shamela narrator IDs where possible.
5. Enrich narrator cards with names, grades, biography, dates, teachers, students, and sourced critic statements.
6. Build the complete sanad graph and analyzer for continuity, breaks, weak/criticized narrators, and strength of each link.


## Phase 1 status

Phase 1A and the raw occurrence layer are now implemented.

- 74 unique source HTML files inventoried.
- 54,572 numbered body segments retained in the raw extraction database.
- 40,334 primary-body sanad candidates identified.
- 25,569 footnote blocks preserved separately for later takhrij-route extraction.
- 197,493 raw narrator mentions extracted from current sanad candidates.
- 27,402 distinct normalized **name strings** before identity resolution. This is intentionally not a narrator count.

The next stage is identity resolution: clean raw mention phrases, preserve relational forms such as `أبيه`, match strong candidates against Shamela narrator IDs, and use surrounding teachers/students to resolve ambiguous short names.


## Stage 3 checkpoint — kinship-safe identity resolution

- Current anchored narrator identities: **2,969**
- Strong/provisional resolved sanad occurrences: **39,578**
- Contextually resolved kinship occurrences: **1,907**
- New identities exposed by kinship expressions: **107**

Kinship tokens such as `أبيه`, `جده`, `عمه`, `أخيه`, and `أمه` are resolved per occurrence from the governing narrator, lineage, biography, and sanad context. They are never treated as names or globally deduplicated.

The core Tahdhib al-Kamal parser has also been corrected for vocalized/unvocalized `روى عن` forms and optional punctuation while preserving existing IDs.
