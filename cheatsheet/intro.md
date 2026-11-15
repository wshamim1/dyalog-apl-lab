# APL glyph cheat sheet

Every Dyalog APL glyph on one page: what it's called, how to type it, what it
does, and an example with its real result.

## What is a glyph?

A **glyph** is one of APL's special symbols, such as `⍳ ⍴ ⌽ ¨ ⍵`. Each one
is a complete instruction: where Python writes `range(5)` or `reversed(x)`,
APL writes `⍳5` and `⌽x`.

- **About 80 glyphs** make up the whole core language. Learning APL largely
  means learning these.
- **Most glyphs have two related meanings,** depending on how many
  arguments they get:
  - **monadic**, with one argument on the right: `⌽1 2 3` reverses → `3 2 1`
  - **dyadic**, with arguments on both sides: `1⌽1 2 3` rotates → `2 3 1`
- **There are three kinds:**
  - **functions** work on data (`+ ⍴ ⌽`)
  - **operators** modify functions (`/ ¨ ∘`): `+/` means "sum", `≢¨` means "length of each"
  - **syntax** is the punctuation (`← ⋄ ⍝ ⍺ ⍵`)
- **They're ordinary Unicode characters,** so they work in any modern
  editor, terminal, web page or git diff.
- **The shapes are mnemonic:** `⌽` is a circle flipped across a vertical
  line (reverse), `⊖` across a horizontal one (flip rows), and `⍉` across a
  diagonal (transpose). `⌈` and `⌊` point up and down (ceiling and floor).

Reading tip: APL runs **right to left** with no precedence, so `2×3+4` is
`2×(3+4)` = 14.

## How to type them

| Where | How |
| --- | --- |
| **RIDE** | press the prefix key **`` ` ``** (backtick), then a key: `` ` `` `r` → `⍴`, `` ` `` `i` → `⍳`. Shifted keys give a second glyph: `` ` `` Shift+`e` → `⍷` |
| **RIDE, by name** | type two backticks and a name, e.g. ``` ``rho ``` or ``` ``reverse ```, then choose from the list |
| **RIDE language bar** | the row of glyphs at the top. Hover over one to see its name and key, click to insert |
| **Any app** | install the Dyalog keyboard layout: <https://www.dyalog.com/apl-font-keyboard.htm> |
| **Anywhere** | copy and paste from this page |

The **RIDE key** column below uses RIDE's US layout. `+ - = < > | ! ? * , / \ . ' ~`
are on a normal keyboard, so type them directly.

## How to read the tables

`` ` `` `r` means *press backtick, then r*. In the examples, `→` shows the
result Dyalog printed. Matrices are written row by row inside `[ ]`, with
`⋄` between rows: `[1 2 ⋄ 3 4]` is a 2×2 matrix. A **—** means that form
doesn't exist.
