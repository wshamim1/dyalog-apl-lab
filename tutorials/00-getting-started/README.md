# 00 · Getting started

How the APL session works, how to type the symbols, and the handful of
commands you'll use every day.

## Start a session

```sh
install/dyalog/podman.sh run     # or docker.sh run / mac.sh run
```

The cursor is indented 6 spaces. That's the prompt. Type an expression,
press Enter, and the result is printed at the left margin:

```apl
      2+3
5
```

All examples in these tutorials look like that: the indented line is what
you type, and the lines below it are what APL prints.

## Typing the symbols

APL uses special symbols (glyphs) such as `⍳ ⍴ ← ⍵`.

- **In RIDE:** press the prefix key `` ` `` (backtick), then a normal key.
  Hover over the language bar at the top to see every glyph and its key.
- **In the terminal (container):** there's no prefix key. Copy and paste
  from these notes, or install the Dyalog keyboard layout from
  <https://www.dyalog.com/apl-font-keyboard.htm>.

For every glyph, with its meaning and an example, see the
[glyph cheat sheet](../../cheatsheet/README.md). The ones you'll use most often:

| Glyph | Name | RIDE keys | | Glyph | Name | RIDE keys |
| --- | --- | --- | --- | --- | --- | --- |
| `←` | assign | `` ` `` `[` | | `⍵` | right argument | `` ` `` `w` |
| `×` | times | `` ` `` `-` | | `⍺` | left argument | `` ` `` `a` |
| `÷` | divide | `` ` `` `=` | | `⍝` | comment | `` ` `` `,` |
| `⍳` | iota | `` ` `` `i` | | `¯` | high minus | `` ` `` `2` |
| `⍴` | rho | `` ` `` `r` | | `¨` | each | `` ` `` `1` |
| `⌈` | max / ceiling | `` ` `` `s` | | `∊` | member | `` ` `` `e` |
| `⌊` | min / floor | `` ` `` `d` | | `⎕` | quad | `` ` `` `l` |
| `≠` | not equal | `` ` `` `8` | | `⋄` | diamond | `` ` `` `` ` `` |

## Comments

Everything after `⍝` is ignored:

```apl
      10×4   ⍝ ten times four
40
```

## Several statements on one line

`⋄` (diamond) separates statements:

```apl
      a←3 ⋄ b←4 ⋄ a×b
12
```

## Display nested arrays with boxes

Turn on boxed display. It makes nested arrays (tutorial 07) much easier to
read:

```apl
      ]box on
Was OFF
      (1 2)(3 4 5)
┌───┬─────┐
│1 2│3 4 5│
└───┴─────┘
```

All later tutorials assume `]box on`.

## System commands

Commands that start with `)` talk to the session, not the language:

```apl
      )clear          ⍝ start with an empty workspace
      )vars           ⍝ list your variables
      )fns            ⍝ list your functions
      )erase a        ⍝ delete the name a
      )save myws      ⍝ save the workspace to a file
      )load myws      ⍝ load it again
      )off            ⍝ quit
```

Commands that start with `]` are *user commands* (tools):

```apl
      ]help           ⍝ list user commands
      ]box on         ⍝ boxed display
      ]rows on        ⍝ cut long output to the window width instead of wrapping
```

## Getting help

- In RIDE, put the cursor on a glyph and press **F1** to open its documentation.
- Docs: <https://docs.dyalog.com>
- A quick reference for every glyph: <https://aplwiki.com/wiki/List_of_language_elements>

## When things go wrong

A mistake prints an error, and APL keeps going:

```apl
      1 2+1 2 3
LENGTH ERROR: Mismatched left and right argument shapes
      1 2+1 2 3
         ∧
```

The caret `∧` points to where the problem is. If an error happens inside a
function, the function is *suspended*. Type `→` on its own line to clear
the stack, or `)reset` to clear everything.

## Exercises

1. Start a session, compute `123×456`, then quit with `)off`.
2. Turn on boxing and display `(1 2)(3 4)`.
3. Assign `x←7`, then list your variables with `)vars`.

<details><summary>Solution</summary>

```apl
      123×456
56088
      (1 2)(3 4)
┌───┬───┐
│1 2│3 4│
└───┴───┘
```

`)vars` lists `x` (and any other variables you made).

</details>

**Next:** [01 · Basics](../01-basics/README.md)
