#!/usr/bin/env python3
"""Validate QuestPath translation files against lang/english.json.

Usage:
  python validate.py lang/english.json lang/german.json   # validate one file
  python validate.py                                       # validate every
                                                             # *.json in lang/
                                                             # against
                                                             # lang/english.json

Checks:
  - JSON parses                                          -> error
  - placeholder (%s/%d/...) mismatch vs. the English key  -> error
  - missing keys (not translated yet)                     -> warning
  - extra keys (no longer in english.json)                -> warning

Every finding points at the exact line (and, for placeholder mismatches,
the exact column) in the source file so it can be opened straight from the
terminal. Placeholders are highlighted in the printed line when the
terminal supports ANSI colors.

Exit code is non-zero only if at least one error was found (warnings never
fail the run) so CI can gate on real breakage without blocking partial
translations.
"""
import json
import os
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"%[sd%]")
# Matches a top-level `"key":` at the start of a line in a flat JSON object.
KEY_LINE_RE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:')


def _enable_windows_ansi():
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # VT processing
    except Exception:
        pass


_enable_windows_ansi()
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _color(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def red(t): return _color("31", t)
def yellow(t): return _color("33", t)
def green(t): return _color("32", t)
def cyan(t): return _color("36", t)
def bold(t): return _color("1", t)
def dim(t): return _color("2", t)


def load_json(path: Path):
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, None, f"could not read file: {e}"
    try:
        return json.loads(raw), raw, None
    except json.JSONDecodeError as e:
        return None, raw, f"invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"


def build_line_map(raw: str):
    """key -> (1-based line number, raw line text)"""
    line_map = {}
    for lineno, line in enumerate(raw.splitlines(), start=1):
        m = KEY_LINE_RE.match(line)
        if m:
            line_map[m.group(1)] = (lineno, line.rstrip("\n"))
    return line_map


def placeholders(value: str):
    return PLACEHOLDER_RE.findall(value)


def highlighted_line(lineno: int, line: str, color=red) -> str:
    """Print a source line with a caret line under every placeholder."""
    out = [f"      {dim(f'{lineno:>5} |')} {line}"]
    carets = []
    last_end = 0
    for m in PLACEHOLDER_RE.finditer(line):
        carets.append(" " * (m.start() - last_end) + color("^" * (m.end() - m.start())))
        last_end = m.end()
    if carets:
        prefix = " " * (len(f"      {lineno:>5} | "))
        out.append(prefix + "".join(carets))
    return "\n".join(out)


def plain_line(lineno: int, line: str) -> str:
    return f"      {dim(f'{lineno:>5} |')} {line}"


def validate_file(english: dict, english_lines: dict, path: Path) -> bool:
    """Returns True if no errors (warnings are printed but don't fail)."""
    data, raw, err = load_json(path)
    if err:
        print(f"[{red('ERROR')}] {bold(path.name)}: {err}")
        return False

    if not isinstance(data, dict):
        print(f"[{red('ERROR')}] {bold(path.name)}: top-level JSON value must be an object")
        return False

    tr_lines = build_line_map(raw)

    ok = True
    english_keys = set(english.keys())
    file_keys = set(data.keys())

    missing = sorted(english_keys - file_keys)
    extra = sorted(file_keys - english_keys)

    if missing:
        print(f"[{yellow('WARN')}] {bold(path.name)}: {len(missing)} key(s) not translated yet "
              f"(falls back to English):")
        for key in missing:
            lineno, line = english_lines.get(key, (None, None))
            loc = f"english.json:{lineno}" if lineno else "english.json:?"
            print(f"    - {cyan(key)}  ({loc})")
            if line is not None:
                print(plain_line(lineno, line))
    if extra:
        print(f"[{yellow('WARN')}] {bold(path.name)}: {len(extra)} key(s) not in english.json "
              f"(stale?):")
        for key in extra:
            lineno, line = tr_lines.get(key, (None, None))
            loc = f"{path.name}:{lineno}" if lineno else f"{path.name}:?"
            print(f"    - {cyan(key)}  ({loc})")
            if line is not None:
                print(plain_line(lineno, line))

    for key in sorted(english_keys & file_keys):
        en_value = english[key]
        tr_value = data[key]
        tr_lineno, tr_line = tr_lines.get(key, (None, None))
        loc = f"{path.name}:{tr_lineno}" if tr_lineno else path.name

        if not isinstance(tr_value, str):
            print(f"[{red('ERROR')}] {loc}: key '{cyan(key)}' value is not a string "
                  f"(got {type(tr_value).__name__})")
            if tr_line is not None:
                print(plain_line(tr_lineno, tr_line))
            ok = False
            continue

        en_ph = placeholders(en_value)
        tr_ph = placeholders(tr_value)
        if en_ph != tr_ph:
            en_lineno, en_line = english_lines.get(key, (None, None))
            print(f"[{red('ERROR')}] {loc}: key '{cyan(key)}' placeholder mismatch "
                  f"(english has {en_ph or '[]'}, translation has {tr_ph or '[]'})")
            if en_line is not None:
                print(f"    {dim('english:')}")
                print(highlighted_line(en_lineno, en_line, color=green))
            if tr_line is not None:
                print(f"    {dim('translation:')}")
                print(highlighted_line(tr_lineno, tr_line, color=red))
            ok = False

    if ok and not missing and not extra:
        print(f"[{green('OK')}] {path.name}: fully in sync with english.json")
    elif ok:
        print(f"[{green('OK')}] {path.name}: no errors (see warnings above)")

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
        lang_dir = root / "lang"
        english_path = lang_dir / "english.json"
        targets = sorted(
            p for p in lang_dir.glob("*.json") if p.name != "english.json"
        )
        if not targets:
            print("No translation files found in lang/ next to english.json.")
            sys.exit(0)

    english, english_raw, err = load_json(english_path)
    if err:
        print(f"[{red('ERROR')}] {english_path.name}: {err}")
        sys.exit(1)
    english_lines = build_line_map(english_raw)

    all_ok = True
    for target in targets:
        if not validate_file(english, english_lines, target):
            all_ok = False
        print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
