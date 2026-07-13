# QuestPath — Translations

Community translation files for **QuestPath**, an in-game quest tracker
overlay for ELDEN RING (see your started quests, completed steps, and what to
do next). Mod page: https://www.nexusmods.com/eldenring/mods/10363

This repo holds only the translation files (`*.json`), no mod source code.

## How translation works

QuestPath falls back to English automatically for any key a translation file
doesn't have — a partial or slightly outdated translation never breaks
anything, it just shows English for the untranslated bits. So don't worry
about finishing 100% in one go.

## How to translate

1. Copy [`english.json`](english.json) and rename it to `<language>.json`
   using one of the exact names below (these match Steam's UI language names,
   not ISO codes — the mod won't recognize `de.json` or `deutsch.json`).
2. Translate the **values** only. Never change the **keys** (the part before
   `:`).
3. Keep any `%s` / `%d` placeholders exactly as they are, in the same order —
   they get replaced with numbers/names at runtime. If a line has `%d / %d
   steps`, your translation must still have exactly two `%d`.
4. Save as valid UTF-8 JSON (use any text editor that supports UTF-8, e.g.
   VS Code or Notepad++; avoid old Notepad on Windows 7/8 for non-Latin
   scripts).

### Accepted file names

| File name | Language |
|---|---|
| `german.json` | German |
| `french.json` | French |
| `italian.json` | Italian |
| `spanish.json` | Spanish (Spain) |
| `latam.json` | Spanish (Latin America) |
| `brazilian.json` | Portuguese (Brazil) |
| `russian.json` | Russian |
| `japanese.json` | Japanese |
| `koreana.json` | Korean |
| `turkish.json` | Turkish |
| `vietnamese.json` | Vietnamese |
| `polish.json` | Polish |
| `schinese.json` | Chinese (Simplified) |
| `tchinese.json` | Chinese (Traditional) |

Don't see your language? Open an Issue and ask — the mod can support any
name, this is just the current list.

## How to test your translation in-game

1. Drop your `<language>.json` into the `lang/` folder next to
   `QuestPath.dll`.
2. In `QuestPath.ini`, set `language = <language>` (e.g. `language = german`).
3. Launch the game and check the overlay.

## How to submit your translation

Pick whichever is easier for you:

- **Pull Request** (if you're comfortable with Git/GitHub): fork this repo,
  add or update your `<language>.json` at the root, open a PR. A CI check
  (`validate.py`) runs automatically and reports missing keys or broken
  `%s`/`%d` placeholders.
- **Issue**: open a new Issue and attach your `<language>.json` file. It'll
  be added manually.

## Validating locally (optional)

```
python validate.py english.json german.json
```

Reports missing/extra keys (warnings — not blocking) and placeholder
mismatches (errors — these do break in-game text formatting).
