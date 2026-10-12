# Word Tells

Word, phrase, and character tells live in one file, and this skill reads it in place. Do not copy its lists here; a second list drifts from the first.

| Source | Use it for |
|---|---|
| [`rules/writing-standard.md`](../../../rules/writing-standard.md), "Mechanical tiers" and "Exemptions" | Each family in plain words, its tier, its fix, example phrases, and the regions no rule judges |

To add or change a word tell, edit `rules/writing-standard.md` (its header gives the order), never this file.

## Block tier

Block-tier tells are never correct in prose: the em dash, chatbot residue, curly quotes, and summary labels. Fix every one.

- **edit:** fix every one outside the exempt regions, using the family's fix.
- **detect:** report every one.
- Inside a quotation, leave the words alone (see [voice-and-quotes.md](voice-and-quotes.md)); straighten only the curly quote marks that delimit it.

## Advise tier

Advise-tier tells are usually filler and sometimes the right word: hedges, intensifiers, AI vocabulary, throat-clearing, fixed binary-contrast phrases, en dashes, prose arrows, and the spaced double hyphen.

Judge each hit in its sentence before changing it:

- **Term of art:** `robust` in "robust regression", `leverage` in finance, `elevate` with privileges, `landscape` as a page orientation. Keep.
- **Carries meaning:** a hedge that marks real uncertainty, or an intensifier the sentence needs to stay true. Keep one plain form.
- **Quoted or named:** an error message, a UI string, a title, or the word discussed as a word. Keep.
- **Arrow with structure:** two or more arrows on one line, a table row, a diagram. Keep.
- **Range:** an en dash between numbers or numbered ids. Keep.
- **Otherwise:** apply the family's fix, preferring the cut.

In `detect`, report advise-tier hits that are filler and skip the ones the list above keeps.

## Beyond the patterns

The listed phrases are examples. Read for the family, not only the listed phrase: an inflected form, a synonym in the same role, or a phrase split across a line break counts as the same tell. Report it under the family name.
