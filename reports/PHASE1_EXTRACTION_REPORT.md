# Phase 1A extraction report

This is a **raw extraction layer**, not the final narrator database.

- Source HTML files: **74**
- Numbered body segments retained: **54,572**
- Primary-body sanad candidates: **40,334**
- Footnote blocks preserved separately: **25,569**

Important: `sanad_candidates` are deliberately conservative candidates. Ambiguous chain boundaries are flagged for later extension/identity review. Footnotes are not merged into primary isnads.

## By book

| Book | Files | Retained numbered segments | Hadith-like | Report-like | Other numbered | Sanad candidates |
|---|---:|---:|---:|---:|---:|---:|
| الجامع الكامل في الحديث الصحيح الشامل المرتب على أبواب الفقه | 12 | 889 | 35 | 106 | 748 | 33 |
| الجامع المسند الصحيح | 5 | 4,602 | 1,631 | 860 | 2,111 | 1,570 |
| الصحيح المسند مما ليس في الصحيحين | 2 | 1,685 | 1,655 | 23 | 7 | 1,657 |
| المنيحة بسلسلة الأحاديث الصحيحة | 2 | 939 | 1 | 7 | 931 | 1 |
| سلسلة الأحاديث الصحيحة وشيء من فقهها وفوائدها | 9 | 1,176 | 238 | 213 | 725 | 236 |
| سنن أبي داود - ت الأرنؤوط | 8 | 5,308 | 5,225 | 3 | 80 | 5,206 |
| سنن ابن ماجه - ت الأرنؤوط | 6 | 4,383 | 4,336 | 1 | 46 | 4,336 |
| سنن الترمذي - ت شاكر | 5 | 3,952 | 3,945 | 7 | 0 | 3,944 |
| سنن النسائي - ط الرسالة | 9 | 5,770 | 5,750 | 8 | 12 | 5,750 |
| صحيح البخاري - ت البغا | 7 | 7,139 | 7,092 | 31 | 16 | 7,091 |
| صحيح الكتب التسعة وزوائده | 1 | 8,940 | 828 | 4,470 | 3,642 | 753 |
| صحيح مسلم - ت عبد الباقي | 4 | 6,247 | 6,239 | 7 | 1 | 6,239 |
| مسند الدارمي - ت حسين أسد | 4 | 3,542 | 3,518 | 5 | 19 | 3,518 |

## Sanad boundary methods

- `reporter_boundary`: 28,883 candidates; 4,855 flagged for possible chain extension.
- `prophet_boundary`: 6,928 candidates; 0 flagged for possible chain extension.
- `open_ended`: 4,523 candidates; 4,523 flagged for possible chain extension.

## Data rules locked in

1. Original Arabic text is preserved.
2. Primary body and footnote/takhrij evidence remain separate.
3. No narrator identity is merged at this phase.
4. Stable hash-based IDs are used for source files, records, footnotes, and sanad candidates.
5. A candidate ending at a narrative boundary is not automatically treated as a complete isnad.
6. Cases that later contain expressions such as `سمعت رسول الله` are flagged for extension review.
7. The next phase creates raw narrator occurrences and route branches before Shamela-ID matching.
