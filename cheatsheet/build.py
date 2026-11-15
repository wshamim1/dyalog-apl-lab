#!/usr/bin/env python3
"""Build cheatsheet/README.md: every Dyalog APL glyph with its name, RIDE key,
meanings and a worked example. Example results come from running them in
Dyalog (via the repo's `dyalog` command), so they're always real.

    python3 cheatsheet/build.py
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# RIDE's US keyboard layout (from Dyalog/ride src/kbds.js, en_US). Row 1 is the
# normal keys and row 2 the shifted keys; rows 3 and 4 are the glyphs you get
# by pressing the prefix key ` first.
LAYOUT = [
    " `1234567890-=   qwertyuiop[]\\ asdfghjkl;'    zxcvbnm,./  ",
    " ~!@#$%^&*()_+   QWERTYUIOP{}| ASDFGHJKL:\"    ZXCVBNM<>?  ",
    " ⋄¨¯<≤=≥>≠∨∧×÷   ?⍵∊⍴~↑↓⍳○*←→⊢ ⍺⌈⌊_∇∆∘'⎕⍎⍕    ⊂⊃∩∪⊥⊤|⍝⍀⌿  ",
    " ⌺⌶⍫⍒⍋⌽⍉⊖⍟⍱⍲!⌹     ⍷ ⍨  ⍸⍥⍣⍞⍬⊣    ⍛  ⍤⌸⌷≡≢    ⊆      ⍪⍙⍠  ",
]
NATIVE = set("+-=<>|!?*,/\\.'~_@")   # on a normal keyboard; prefer typing these directly


def ride_key(g: str) -> str:
    """How to type glyph g in RIDE: the prefix ` then a key."""
    if g in NATIVE:
        return "on keyboard"
    for row_glyphs, row_keys, shift in ((LAYOUT[2], LAYOUT[0], False), (LAYOUT[3], LAYOUT[1], True)):
        i = row_glyphs.find(g)
        if i >= 0 and row_keys[i] != " ":
            k = row_keys[i]
            if shift:
                base = LAYOUT[0][i]
                return f"`` ` `` Shift+`{base}`" if base.isalpha() else f"`` ` `` `{k}`"
            return "`` ` `` `` ` ``" if k == "`" else f"`` ` `` `{k}`"
    return "—"


# (glyph, name, one-argument meaning, example, two-argument meaning, example)
# An empty meaning means that form doesn't exist.
SECTIONS: list[tuple[str, str, list[tuple[str, ...]]]] = [
    ("Arithmetic", "Scalar functions: they work element by element on whole arrays.", [
        ("+", "plus", "conjugate (same number, for reals)", "+¯3.5", "add", "2+3 4"),
        ("-", "minus", "negate", "-3 ¯4", "subtract", "10-3"),
        ("×", "times", "sign (¯1, 0 or 1)", "×¯5 0 7", "multiply", "3×4"),
        ("÷", "divide", "reciprocal", "÷4", "divide", "10÷4"),
        ("*", "star", "e to the power", "*1", "power", "2*10"),
        ("⍟", "log", "natural logarithm", "⍟*2", "logarithm (base ⍺)", "10⍟1000"),
        ("|", "stile", "absolute value", "|¯7 3", "remainder (⍵ mod ⍺)", "3|10"),
        ("⌈", "upstile", "ceiling", "⌈2.3", "maximum", "3⌈7"),
        ("⌊", "downstile", "floor", "⌊2.7", "minimum", "3⌊7"),
        ("!", "exclamation", "factorial", "!5", "binomial (⍺ from ⍵)", "2!5"),
        ("○", "circle", "π times", "○1", "trig function ⍺ (1 sin, 2 cos, 3 tan)", "2○0"),
        ("?", "question", "roll: random 1 to ⍵", "?6", "deal: ⍺ unique from ⍳⍵", "3?10"),
        ("⌹", "domino", "matrix inverse", "⌹2 2⍴4 7 2 6", "solve linear equations", "5 1⌹2 2⍴2 1 1 ¯1"),
    ]),
    ("Comparison and logic", "Results are booleans: 1 for true, 0 for false.", [
        ("=", "equal", "", "", "equal", "1 2 3=2"),
        ("≠", "not equal", "unique mask (first of each)", "≠1 2 2 3 1", "not equal", "1 2 3≠2"),
        ("<", "less than", "", "", "less than", "1 2 3<2"),
        ("≤", "less or equal", "", "", "less than or equal", "1 2 3≤2"),
        (">", "greater than", "", "", "greater than", "1 2 3>2"),
        ("≥", "greater or equal", "", "", "greater than or equal", "1 2 3≥2"),
        ("≡", "match", "depth (nesting level)", "≡(1 2)(3 4)", "match: identical arrays?", "1 2 3≡1 2 3"),
        ("≢", "not match", "tally: number of items", "≢'hello'", "not match", "1 2≢1 2"),
        ("∧", "and", "", "", "and (also lowest common multiple)", "1 0 1∧1 1 0"),
        ("∨", "or", "", "", "or (also greatest common divisor)", "1 0 1∨0 0 1"),
        ("⍲", "nand", "", "", "not and", "1 0⍲1 1"),
        ("⍱", "nor", "", "", "not or", "1 0⍱0 0"),
        ("~", "tilde", "not", "~1 0 1", "without: remove items", "1 2 3 4~2 4"),
    ]),
    ("Structure", "Build, reshape and take apart arrays.", [
        ("⍴", "rho", "shape", "⍴2 3⍴0", "reshape", "2 3⍴⍳6"),
        (",", "comma", "ravel: flatten", ",2 2⍴⍳4", "catenate", "1 2,3"),
        ("⍪", "comma bar", "table: make a column", "⍪1 2 3", "catenate rows", "(2 2⍴⍳4)⍪5 6"),
        ("⌽", "circle stile", "reverse", "⌽1 2 3", "rotate", "1⌽1 2 3 4"),
        ("⊖", "circle bar", "reverse rows (first axis)", "⊖2 2⍴⍳4", "rotate rows", "1⊖3 2⍴⍳6"),
        ("⍉", "transpose", "transpose", "⍉2 3⍴⍳6", "reorder axes (1 1⍉ is the diagonal)", "1 1⍉3 3⍴⍳9"),
        ("↑", "up arrow", "mix: list of lists → matrix", "↑(1 2)(3 4 5)", "take", "2↑5 6 7"),
        ("↓", "down arrow", "split: matrix → list of rows", "↓2 2⍴⍳4", "drop", "1↓5 6 7"),
        ("⊂", "left shoe", "enclose: treat as one item", "≢⊂1 2 3", "partitioned enclose: new piece at each 1", "1 0 1 0⊂'abcd'"),
        ("⊃", "right shoe", "first", "⊃'abc' 'de'", "pick", "2⊃'abc' 'de'"),
        ("⊆", "left shoe underbar", "nest (enclose if simple)", "≡⊆'abc'", "partition: keep runs under non-zeros", "1 1 0 1⊆'ab d'"),
        ("∊", "epsilon", "enlist: flatten nested", "∊(1 2)(3(4 5))", "member of", "2 5∊1 2 3"),
        ("⌷", "squad", "materialise", "⌷1 2 3", "index", "2⌷10 20 30"),
        ("⊣", "left tack", "same", "⊣5", "left argument", "1⊣2"),
        ("⊢", "right tack", "same", "⊢5", "right argument", "1⊢2"),
    ]),
    ("Search, select and sort", "Find things, keep things, order things.", [
        ("⍳", "iota", "index generator", "⍳5", "index of", "'abc'⍳'cb'"),
        ("⍸", "iota underbar", "where: indices of 1s", "⍸0 1 0 1", "interval index", "0 10 20⍸5 15 25"),
        ("⍷", "epsilon underbar", "", "", "find: where ⍺ starts in ⍵", "'an'⍷'banana'"),
        ("∪", "up shoe", "unique", "∪1 2 2 3 1", "union", "1 2∪2 3"),
        ("∩", "down shoe", "", "", "intersection", "1 2 3∩2 3 4"),
        ("⍋", "grade up", "indices that sort ascending", "⍋30 10 20", "grade by a collating sequence", "'cab'⍋'acb'"),
        ("⍒", "grade down", "indices that sort descending", "⍒30 10 20", "grade down by a collating sequence", "'cab'⍒'acb'"),
        ("/", "slash", "(operator: reduce, below)", "", "replicate / compress", "1 0 2/'abc'"),
        ("⌿", "slash bar", "(operator: reduce first axis)", "", "replicate along first axis", "1 0 1⌿3 2⍴⍳6"),
        ("\\", "backslash", "(operator: scan, below)", "", "expand: 0 inserts a blank", "1 0 1\\'ab'"),
        ("⍀", "backslash bar", "(operator: scan first axis)", "", "expand along first axis", "1 0 1⍀2 2⍴⍳4"),
    ]),
    ("Conversion", "Between numbers, text and number bases.", [
        ("⍕", "format", "format: number → text (⍴ shows 7 characters)", "⍴⍕3.14159", "format with width/decimals", "6 2⍕3.14159"),
        ("⍎", "execute", "execute text as APL", "⍎'2+3'", "", ""),
        ("⊥", "up tack", "", "", "decode: digits → number in base ⍺", "2⊥1 0 1"),
        ("⊤", "down tack", "", "", "encode: number → digits in base ⍺", "2 2 2⊤5"),
    ]),
    ("Operators", "An operator takes a function (its operand) and makes a new one.", [
        ("/", "reduce", "f/ puts f between items", "+/1 2 3 4", "n-wise reduce (windows of ⍺)", "2+/1 2 3 4"),
        ("\\", "scan", "f\\ keeps the running results", "+\\1 2 3 4", "", ""),
        ("⌿", "reduce first", "reduce down the columns", "+⌿2 3⍴⍳6", "", ""),
        ("¨", "each", "f¨ applies f to each item", "≢¨'ab' 'cde'", "pairwise each", "1 2,¨3 4"),
        ("⍨", "commute / selfie", "f⍨⍵ is ⍵ f ⍵", "×⍨3", "⍺ f⍨ ⍵ is ⍵ f ⍺", "2-⍨10"),
        ("∘", "jot", "bind (2∘×) or compose (f∘g)", "2∘×1 2 3", "outer product ∘.f: every pair", "1 2∘.×1 2 3"),
        (".", "dot", "", "", "inner product f.g (+.× is matrix product)", "1 2 3+.×4 5 6"),
        ("⍤", "jot diaeresis", "rank: f⍤1 applies to each row", "{+/⍵}⍤1⊢2 3⍴⍳6", "atop: f⍤g is f (⍺ g ⍵)", "2-⍤+3"),
        ("⍥", "circle diaeresis", "over: ⍺ f⍥g ⍵ is (g ⍺) f (g ⍵)", "", "compare after transforming", "'Ab'≡⍥⎕C'aB'"),
        ("⍣", "power", "f⍣n applies f n times; f⍣≡ until stable", "(2∘×)⍣3⊢1", "", ""),
        ("⌸", "key", "group by key: ⍺ is the key, ⍵ its positions", "{⍺,≢⍵}⌸'abca'", "group ⍵ by keys ⍺", "'abab'{⍺,+/⍵}⌸1 2 3 4"),
        ("⌺", "stencil", "f⌺n on each window (edges padded with 0)", "{+/,⍵}⌺3⊢1 2 3 4 5", "", ""),
        ("@", "at", "replace at positions", "0@2 4⊢1 2 3 4 5", "", ""),
        ("⍠", "variant", "set an option of a system function", "('a'⎕R'x'⍠'IC' 1)'Aa'", "", ""),
        ("⌶", "I-beam", "system services by number (739⌶ is the temp folder)", "(739⌶)0", "", ""),
    ]),
    ("Syntax and names", "Not functions: the punctuation of APL.", [
        ("←", "left arrow", "assign: x←5", "", "", ""),
        ("→", "right arrow", "branch / leave a function: →0", "", "", ""),
        ("⍺", "alpha", "left argument of a dfn", "3{⍺+⍵}4", "", ""),
        ("⍵", "omega", "right argument of a dfn", "{⍵×2}5", "", ""),
        ("∇", "del", "the dfn itself (recursion); also starts/ends a tradfn", "{⍵≤1:1 ⋄ ⍵×∇ ⍵-1}5", "", ""),
        ("⋄", "diamond", "statement separator", "{a←2 ⋄ a×3}0", "", ""),
        ("⍝", "lamp", "comment: the rest of the line is ignored, e.g. `x←5 ⍝ the price`", "", "", ""),
        ("⍬", "zilde", "empty numeric vector", "≢⍬", "", ""),
        ("¯", "high minus", "negative number sign (part of the number)", "¯3+1", "", ""),
        ("⎕", "quad", "system names (⎕IO, ⎕A…); ⎕← prints, ⎕ reads input", "⎕A", "", ""),
        ("⍞", "quote quad", "character input/output (no newline)", "", "", ""),
        ("'", "quote", "text: 'it''s' (double a quote to include one)", "'it''s'", "", ""),
        ("∆ ⍙", "delta, delta underbar", "allowed in names, like letters", "{∆x←1 ⋄ ∆x+1}0", "", ""),
        ("⍛", "jot underbar", "behind: (f⍛g)⍵ is (f ⍵) g ⍵ (Dyalog 20+)", "-⍛+5", "", ""),
    ]),
]


# --------------------------------------------------------------------- run
def run_examples(examples: list[str]) -> list[str]:
    """Run each example in Dyalog; return its output (or 'ERROR …')."""
    lines = ["⎕RL←42 1",           # fixed random seed so ? examples repeat
             # Show nested vectors in strand notation: (1 2) (3 4), 'ab' 'cd'
             "Item←{(0=10|⎕DR ⍵)∧1≥|≡⍵:'''',(,⍵),'''' ⋄ (1=≢,⍵)∧1≥|≡⍵:⍕⍵ ⋄ '(',(⍕⍵),')'}",
             "Fmt←{(1<|≡⍵)∧1=≢⍴⍵:¯1↓∊(Item¨⍵),¨' ' ⋄ ⍵}"]
    for i, ex in enumerate(examples):
        lines += [f"⎕←'@@{i}'", ":Trap 0", f"    ⎕←Fmt({ex})", ":Else",
                  "    ⎕←'!!ERROR ',⎕DMX.EM", ":EndTrap"]
    lines.append("⎕←'@@end'")
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        script = Path(tmp) / "examples.apls"
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out = subprocess.run(["dyalog", str(script)], capture_output=True,
                             text=True, cwd=HERE).stdout
    results: dict[int, list[str]] = {}
    cur = None
    for ln in out.split("\n"):
        m = re.fullmatch(r"@@(\d+|end)", ln.strip())
        if m:
            cur = None if m.group(1) == "end" else int(m.group(1))
            if cur is not None:
                results[cur] = []
        elif cur is not None:
            results[cur].append(ln.rstrip())
    missing = [examples[i] for i in range(len(examples)) if i not in results]
    if missing:
        raise SystemExit(f"no output for: {missing}\n--- output ---\n{out[-2000:]}")
    return [render(results[i]) for i in range(len(examples))]


def render(out: list[str]) -> str:
    """Show one result on one line: matrix rows are joined with ⋄ in []."""
    while out and not out[-1].strip():
        out.pop()
    if len(out) == 1:
        return out[0].strip()
    if not out:
        return "(empty)"
    return "[" + " ⋄ ".join(r.rstrip() for r in out) + "]"


def cell(meaning: str, example: str, result: str) -> str:
    if not meaning:
        return "—"
    if not example:
        return meaning
    result = result.replace("|", "\\|")
    ex = example.replace("|", "\\|")
    return f"{meaning}<br>`{ex}` → `{result}`" if result else f"{meaning}<br>`{ex}`"


# -------------------------------------------------------------------- build
def main() -> None:
    examples = [ex for _, _, rows in SECTIONS for r in rows for ex in (r[3], r[5]) if ex]
    got = dict(zip(examples, run_examples(examples)))
    errors = {e: r for e, r in got.items() if r.startswith("!!ERROR")}
    if errors:
        raise SystemExit("examples that failed:\n" + "\n".join(f"  {e}: {r}" for e, r in errors.items()))

    parts = [(HERE / "intro.md").read_text(encoding="utf-8").rstrip(), ""]
    parts.append("## Contents\n")
    parts += [f"- [{title}](#{title.lower().replace(' ', '-').replace(',', '')})" for title, _, _ in SECTIONS]
    for title, blurb, rows in SECTIONS:
        parts += ["", f"## {title}", "", blurb, "",
                  "| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |",
                  "| :---: | --- | --- | --- | --- |"]
        for g, name, m, mex, d, dex in rows:
            key = " / ".join(ride_key(c) for c in g.split()) if " " in g else ride_key(g)
            key = key.replace("|", "\\|")
            gl = "\\|" if g == "|" else g
            parts.append(f"| **{gl}** | {name} | {key} | {cell(m, mex, got.get(mex, ''))} "
                         f"| {cell(d, dex, got.get(dex, ''))} |")
    parts += ["", (HERE / "outro.md").read_text(encoding="utf-8").rstrip(), ""]
    (HERE / "README.md").write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {HERE / 'README.md'}: {len(examples)} examples, all run in Dyalog")


if __name__ == "__main__":
    main()
