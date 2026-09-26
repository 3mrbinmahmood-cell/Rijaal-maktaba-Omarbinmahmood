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
