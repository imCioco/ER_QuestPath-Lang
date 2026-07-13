#!/usr/bin/env python3
"""Validate QuestPath translation files against english.json.

Usage:
  python validate.py english.json german.json   # validate one file
  python validate.py                             # validate every *.json
                                                   # in this folder against
                                                   # english.json

Checks:
  - JSON parses                                          -> error
  - placeholder (%s/%d/...) mismatch vs. the English key  -> error
  - missing keys (not translated yet)                     -> warning
  - extra keys (no longer in english.json)                -> warning

Exit code is non-zero only if at least one error was found (warnings never
fail the run) so CI can gate on real breakage without blocking partial
translations.
"""
import json
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"%[sd%]")


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"invalid JSON: {e}"


def placeholders(value: str):
    return PLACEHOLDER_RE.findall(value)


def validate_file(english: dict, path: Path) -> bool:
    """Returns True if no errors (warnings are printed but don't fail)."""
    data, err = load_json(path)
    if err:
        print(f"[ERROR] {path.name}: {err}")
        return False

    ok = True
    english_keys = set(english.keys())
    file_keys = set(data.keys())

    missing = sorted(english_keys - file_keys)
    extra = sorted(file_keys - english_keys)

    if missing:
        print(f"[WARN] {path.name}: {len(missing)} key(s) not translated yet "
              f"(falls back to English): {', '.join(missing[:10])}"
              f"{' ...' if len(missing) > 10 else ''}")
    if extra:
        print(f"[WARN] {path.name}: {len(extra)} key(s) not in english.json "
              f"(stale?): {', '.join(extra[:10])}"
              f"{' ...' if len(extra) > 10 else ''}")

    for key in sorted(english_keys & file_keys):
        en_value = english[key]
        tr_value = data[key]
        if not isinstance(tr_value, str):
            print(f"[ERROR] {path.name}: key '{key}' value is not a string")
            ok = False
            continue
        en_ph = placeholders(en_value)
        tr_ph = placeholders(tr_value)
        if en_ph != tr_ph:
            print(f"[ERROR] {path.name}: key '{key}' placeholder mismatch: "
                  f"english has {en_ph or '[]'}, translation has {tr_ph or '[]'}")
            ok = False

    if ok and not missing and not extra:
        print(f"[OK] {path.name}: fully in sync with english.json")
    elif ok:
        print(f"[OK] {path.name}: no errors (see warnings above)")

    return ok


def main():
    args = sys.argv[1:]
    root = Path(__file__).resolve().parent

    if args:
        english_path = Path(args[0])
        targets = [Path(a) for a in args[1:]]
        if not targets:
            print("usage: validate.py english.json <translation.json> [more.json ...]")
            sys.exit(2)
    else:
        english_path = root / "english.json"
        targets = sorted(
            p for p in root.glob("*.json") if p.name != "english.json"
        )
        if not targets:
            print("No translation files found next to english.json.")
            sys.exit(0)

    english, err = load_json(english_path)
    if err:
        print(f"[ERROR] {english_path.name}: {err}")
        sys.exit(1)

    all_ok = True
    for target in targets:
        if not validate_file(english, target):
            all_ok = False
        print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
