# Identity Resolution — Stage 1

## Source corpus

The project now uses the user's fixed hadith corpus to resolve **occurrences**, not merely strings. This is necessary because a short form such as `سفيان` can refer to different people in different isnads.

## Core rijal sources available in the source warehouse

The working archive contains:

- تهذيب الكمال في أسماء الرجال
- تهذيب التهذيب
- تقريب التهذيب
- التاريخ الكبير للبخاري
- الجرح والتعديل لابن أبي حاتم
- الكاشف في معرفة من له رواية في الكتب الستة
- ميزان الاعتدال
- الإصابة في تمييز الصحابة

The first identity pass deliberately uses **Tahdhib al-Kamal** as the teacher/student biography anchor and **Taqrib al-Tahdhib** as the convenient Ibn Hajar summary layer.

## Current results

- Tahdhib al-Kamal extracted entry blocks: **8,174**
- Entries with useful teacher and/or student lists: **7,159**
- Conservative full-name identity anchors in the fixed hadith corpus: **2,481**
- Full-name occurrences attached to those anchors: **36,865**
- Strong two-sided context resolutions in the first pass: **549**
- Stage-1 narrator cards currently assembled: **2,862**
- Cards uniquely matched to a Taqrib entry: **2,518**

Two-sided context means the candidate is supported by both sides of the actual sanad: the preceding narrator appears among the candidate's students and the following narrator appears among the candidate's teachers. One-sided matches are not automatically promoted.

Examples already separated correctly include occurrences of `سفيان` into Sufyan al-Thawri vs Sufyan ibn Uyaynah according to the surrounding chain, and `يحيى بن سعيد` into the appropriate narrator according to context.

## Card contents at this stage

Each card can already retain:

- canonical name
- full Tahdhib al-Kamal biography
- raw teacher list
- raw student list
- exact source locator
- Ibn Hajar's full Taqrib summary when uniquely matched
- death/date wording found in that Taqrib summary

The date field remains **evidence text**, not a normalized numeric date, until the date parser is separately audited.

## Next

1. Convert teacher/student raw lists to stable narrator-ID edges.
2. Resolve more short-name occurrences using strong neighboring identities.
3. Add Tahdhib al-Tahdhib / al-Kashif / al-Jarh wa al-Ta'dil evidence.
4. Extract individual critic judgments without collapsing disagreement.
5. Add structured death/birth/travel/ikhtilat/tadlis events.
6. Match/import Shamela narrator IDs when the 18,989-record seed is available.
