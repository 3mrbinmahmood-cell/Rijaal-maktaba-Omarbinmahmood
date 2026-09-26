# Data model for narrator cards and the sanad analyzer

The database separates **source evidence**, **identity resolution**, and **automated analysis**.

## Narrator card

A card is assembled from:

- `narrators`: canonical identity and convenient summary grade.
- `narrator_aliases`: names, kunyah, nisbah, short forms, lineage variants.
- `narrator_biography_evidence`: sourced biography passages.
- `narrator_judgments`: each critic's exact judgment; disagreement is preserved.
- `narrator_events`: birth, death, travel, meeting/hearing dates and other dated events.
- `narrator_traits`: tadlis, ikhtilat and other time-sensitive traits.
- `narrator_relationships`: student→teacher links.
- `relationship_evidence`: why a teacher/student link exists.

## Relationship evidence

Teacher/student lists must distinguish:

1. **reported_biography** — a rijal source says X narrated from Y / Y narrated from X.
2. **observed_isnad** — an actual chain in our fixed corpus has X→Y.
3. **explicit_samaa** — the chain/source explicitly uses سمعت / حدثني / حدثنا or equivalent.
4. **legacy_warehouse** — evidence inherited from the older large extraction and awaiting verification.

A relationship is never considered proven merely because two names look similar.

## Sanad visualization

Every chain is stored as a branch of ordered nodes and links:

`sanad_branches → sanad_nodes → sanad_edges`

The reader can therefore render the entire chain visually. Each node can display narrator status; each edge can display continuity evidence.

## Analyzer

The analyzer is deliberately stored separately from evidence.

For each link it can evaluate:

- identity resolution
- chronological compatibility
- teacher/student evidence
- actual corpus occurrences
- explicit samaa
- documented meeting
- geographic compatibility
- tadlis / an'anah concerns
- continuity or break
- weakness caused by the link

For each narrator it can display:

- summary grade
- individual critic judgments
- ikhtilat
- tadlis
- identity uncertainty

The final branch summary can show breaks, weak narrators, uncertain links, and existing scholarly gradings. Automated analysis must remain clearly distinct from a named scholar's grading.


## Identity-source priority (locked)

The reverse-engineered Shamela narrator dataset (~18,989 S1 narrator cards) is a **primary identity seed**, not an optional later add-on.

Identity workflow:

1. Extract every narrator occurrence from the fixed hadith corpus.
2. Search the Shamela 18,989-card set by short name, long name, aliases/metadata and death year.
3. Never merge merely because a short name matches.
4. Verify each candidate at the occurrence level using the narrator immediately before and after it in the sanad.
5. Cross-check teacher/student relationships against Tahdhib al-Kamal and actual observed isnads.
6. Use dates, tabaqah, kunyah, lineage, place, travel, and other rijal evidence to reject impossible candidates.
7. Assign our own stable `narrator_id` only after resolution; retain `shamela_id` permanently as an external cross-reference.
8. If a corpus narrator is absent from the 18,989 Shamela set, build a new card from the core rijal sources rather than forcing a Shamela match.

The Shamela card seed and the classical-source extraction are complementary:
- **Shamela S1**: fast candidate universe and stable external IDs.
- **Fixed corpus**: determines which person a name means in each actual sanad.
- **Tahdhib al-Kamal / other rijal books**: evidence, teachers/students, judgments, dates and conflict resolution.
