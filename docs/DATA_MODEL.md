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


## Relational narrator expressions (hard rule)

Expressions such as `أبيه`, `أبيها`, `أمه`, `جده`, `عمه`, `أخيه` are **not narrator identities** and must never be globally deduplicated.

They are resolved per sanad occurrence:

1. Preserve the exact relational expression in the raw sanad node.
2. Determine the grammatically governing/immediately referenced narrator in that exact chain.
3. Resolve that governing narrator first.
4. Derive the claimed family relation from the governing narrator's full lineage/biography.
5. Generate candidate relative identities only from that context.
6. Verify the candidate against the surrounding sanad: previous/next narrator, reported teachers/students, actual corpus transmissions, dates/tabaqah, places, and biography evidence.
7. If more than one candidate remains, keep the node unresolved/ambiguous; never substitute a person merely because another `أبيه` occurrence elsewhere resolved to him.
8. Store both the original token (`أبيه`) and the resolved narrator ID, plus the derivation evidence.

Example:
`فلان بن محمد، عن أبيه، عن الزهري`
means: first resolve `فلان بن محمد`; then identify **his father** from that narrator's lineage; then test that father against the fact that he is narrating from al-Zuhri. It does not mean "look up a narrator named أبيه".

This relational-resolution step runs before final sanad continuity analysis.


## Resolve before identity deduplication (locked rule)

The project resolves narrator occurrences to **source-backed narrator cards before deduplicating identities**.

Order of operations:

1. Preserve every narrator occurrence exactly as it appears in its sanad.
2. Find one or more candidate cards from Shamela S1 and the classical rijal sources.
3. Create/retain a provisional card when a source biography exists, even if another card may later prove to be the same person.
4. Resolve the occurrence using the exact sanad context: previous narrator, next narrator, kinship wording, teachers/students, dates, tabaqah, kunyah, lineage, places, and source evidence.
5. Attach the occurrence to the best-supported card only when sufficiently resolved.
6. After cards have accumulated their own source evidence and sanad occurrences, run identity deduplication across the **cards**, not across raw names.
7. Merge two cards only when the combined evidence supports that they are the same historical person. Preserve all former card IDs as aliases/redirects and retain provenance.
8. If identity remains uncertain, keep separate cards linked as possible duplicates rather than merging them.

This prevents premature normalization of short names, kunyahs, relational expressions, and variant lineages from destroying evidence needed to identify the narrator.


## Reader scope decision — no card deduplication required

The reader project does **not** require a globally deduplicated narrator database.

### Primary goal

The reader serves the user's selected hadith library and helps a student understand **why a scholar may have graded a hadith sahih, hasan, or da'if** by exposing the evidence in the sanad visually.

The production priority is therefore:

1. preserve the user's selected hadith books;
2. preserve every sanad and its exact wording;
3. resolve each sanad occurrence to one or more source-backed rijal cards where possible;
4. display the entire chain visually;
5. display evidence on every narrator node and every narrator-to-narrator link;
6. show existing scholar gradings separately from automated evidence analysis;
7. leave unresolved or conflicting evidence visible rather than force a verdict.

### Card model

A narrator may have multiple cards from different source books.

For example, one historical narrator may have:
- a Shamela S1 card;
- a Tahdhib al-Kamal card;
- a Taqrib card;
- a Tahdhib al-Tahdhib card;
- an al-Kashif card;
- a Tarikh al-Kabir card;
- other source cards.

These cards may be linked as `possible_same_person`, `same_person_supported`, or by a shared external ID, but the reader does not need to physically merge them.

Each card retains:
- source book;
- source locator;
- exact name/identity wording;
- exact grading/judgment wording;
- biography;
- dates;
- teachers;
- students;
- tadlis / ikhtilat evidence;
- aliases;
- source provenance.

### Sanad node

A visual sanad node points to the best-supported card or card cluster for that exact occurrence. Expanding the node shows all linked source cards/evidence.

### Sanad edge

Every narrator-to-narrator edge may show:
- actual occurrence in the user's corpus;
- reported teacher/student relationship;
- explicit sama' / haddathana / akhbarana;
- an'anah;
- chronology;
- known meeting/hearing evidence;
- place/travel compatibility;
- tadlis warning;
- possible break;
- uncertainty.

### Scholar ruling vs analyzer

The UI must distinguish:

**Scholar's ruling**
- e.g. Sahih / Hasan / Da'if
- exact scholar/source
- exact wording when available

**Sanad evidence**
- narrator judgments
- continuity evidence
- weak/unknown narrator
- tadlis
- ikhtilat
- chronology
- break/uncertain link

**Automated explanation**
- explains which stored evidence supports or challenges continuity/strength
- does not replace the scholar's ruling
- does not claim certainty where the evidence is incomplete

### Storage policy

Duplicate source cards are acceptable. Storage optimization is secondary to provenance and correctness. A separate future project may deduplicate/merge narrator identities if desired, without blocking the reader.
