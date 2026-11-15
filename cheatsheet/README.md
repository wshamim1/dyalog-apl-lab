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

## Contents

- [Arithmetic](#arithmetic)
- [Comparison and logic](#comparison-and-logic)
- [Structure](#structure)
- [Search, select and sort](#search-select-and-sort)
- [Conversion](#conversion)
- [Operators](#operators)
- [Syntax and names](#syntax-and-names)

## Arithmetic

Scalar functions: they work element by element on whole arrays.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **+** | plus | on keyboard | conjugate (same number, for reals)<br>`+¯3.5` → `¯3.5` | add<br>`2+3 4` → `5 6` |
| **-** | minus | on keyboard | negate<br>`-3 ¯4` → `¯3 4` | subtract<br>`10-3` → `7` |
| **×** | times | `` ` `` `-` | sign (¯1, 0 or 1)<br>`×¯5 0 7` → `¯1 0 1` | multiply<br>`3×4` → `12` |
| **÷** | divide | `` ` `` `=` | reciprocal<br>`÷4` → `0.25` | divide<br>`10÷4` → `2.5` |
| ***** | star | on keyboard | e to the power<br>`*1` → `2.718281828` | power<br>`2*10` → `1024` |
| **⍟** | log | `` ` `` `*` | natural logarithm<br>`⍟*2` → `2` | logarithm (base ⍺)<br>`10⍟1000` → `3` |
| **\|** | stile | on keyboard | absolute value<br>`\|¯7 3` → `7 3` | remainder (⍵ mod ⍺)<br>`3\|10` → `1` |
| **⌈** | upstile | `` ` `` `s` | ceiling<br>`⌈2.3` → `3` | maximum<br>`3⌈7` → `7` |
| **⌊** | downstile | `` ` `` `d` | floor<br>`⌊2.7` → `2` | minimum<br>`3⌊7` → `3` |
| **!** | exclamation | on keyboard | factorial<br>`!5` → `120` | binomial (⍺ from ⍵)<br>`2!5` → `10` |
| **○** | circle | `` ` `` `o` | π times<br>`○1` → `3.141592654` | trig function ⍺ (1 sin, 2 cos, 3 tan)<br>`2○0` → `1` |
| **?** | question | on keyboard | roll: random 1 to ⍵<br>`?6` → `3` | deal: ⍺ unique from ⍳⍵<br>`3?10` → `3 9 1` |
| **⌹** | domino | `` ` `` `+` | matrix inverse<br>`⌹2 2⍴4 7 2 6` → `[ 0.6 ¯0.7 ⋄ ¯0.2  0.4]` | solve linear equations<br>`5 1⌹2 2⍴2 1 1 ¯1` → `2 1` |

## Comparison and logic

Results are booleans: 1 for true, 0 for false.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **=** | equal | on keyboard | — | equal<br>`1 2 3=2` → `0 1 0` |
| **≠** | not equal | `` ` `` `8` | unique mask (first of each)<br>`≠1 2 2 3 1` → `1 1 0 1 0` | not equal<br>`1 2 3≠2` → `1 0 1` |
| **<** | less than | on keyboard | — | less than<br>`1 2 3<2` → `1 0 0` |
| **≤** | less or equal | `` ` `` `4` | — | less than or equal<br>`1 2 3≤2` → `1 1 0` |
| **>** | greater than | on keyboard | — | greater than<br>`1 2 3>2` → `0 0 1` |
| **≥** | greater or equal | `` ` `` `6` | — | greater than or equal<br>`1 2 3≥2` → `0 1 1` |
| **≡** | match | `` ` `` `:` | depth (nesting level)<br>`≡(1 2)(3 4)` → `2` | match: identical arrays?<br>`1 2 3≡1 2 3` → `1` |
| **≢** | not match | `` ` `` `"` | tally: number of items<br>`≢'hello'` → `5` | not match<br>`1 2≢1 2` → `0` |
| **∧** | and | `` ` `` `0` | — | and (also lowest common multiple)<br>`1 0 1∧1 1 0` → `1 0 0` |
| **∨** | or | `` ` `` `9` | — | or (also greatest common divisor)<br>`1 0 1∨0 0 1` → `1 0 1` |
| **⍲** | nand | `` ` `` `)` | — | not and<br>`1 0⍲1 1` → `0 1` |
| **⍱** | nor | `` ` `` `(` | — | not or<br>`1 0⍱0 0` → `0 1` |
| **~** | tilde | on keyboard | not<br>`~1 0 1` → `0 1 0` | without: remove items<br>`1 2 3 4~2 4` → `1 3` |

## Structure

Build, reshape and take apart arrays.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **⍴** | rho | `` ` `` `r` | shape<br>`⍴2 3⍴0` → `2 3` | reshape<br>`2 3⍴⍳6` → `[1 2 3 ⋄ 4 5 6]` |
| **,** | comma | on keyboard | ravel: flatten<br>`,2 2⍴⍳4` → `1 2 3 4` | catenate<br>`1 2,3` → `1 2 3` |
| **⍪** | comma bar | `` ` `` `<` | table: make a column<br>`⍪1 2 3` → `[1 ⋄ 2 ⋄ 3]` | catenate rows<br>`(2 2⍴⍳4)⍪5 6` → `[1 2 ⋄ 3 4 ⋄ 5 6]` |
| **⌽** | circle stile | `` ` `` `%` | reverse<br>`⌽1 2 3` → `3 2 1` | rotate<br>`1⌽1 2 3 4` → `2 3 4 1` |
| **⊖** | circle bar | `` ` `` `&` | reverse rows (first axis)<br>`⊖2 2⍴⍳4` → `[3 4 ⋄ 1 2]` | rotate rows<br>`1⊖3 2⍴⍳6` → `[3 4 ⋄ 5 6 ⋄ 1 2]` |
| **⍉** | transpose | `` ` `` `^` | transpose<br>`⍉2 3⍴⍳6` → `[1 4 ⋄ 2 5 ⋄ 3 6]` | reorder axes (1 1⍉ is the diagonal)<br>`1 1⍉3 3⍴⍳9` → `1 5 9` |
| **↑** | up arrow | `` ` `` `y` | mix: list of lists → matrix<br>`↑(1 2)(3 4 5)` → `[1 2 0 ⋄ 3 4 5]` | take<br>`2↑5 6 7` → `5 6` |
| **↓** | down arrow | `` ` `` `u` | split: matrix → list of rows<br>`↓2 2⍴⍳4` → `(1 2) (3 4)` | drop<br>`1↓5 6 7` → `6 7` |
| **⊂** | left shoe | `` ` `` `z` | enclose: treat as one item<br>`≢⊂1 2 3` → `1` | partitioned enclose: new piece at each 1<br>`1 0 1 0⊂'abcd'` → `'ab' 'cd'` |
| **⊃** | right shoe | `` ` `` `x` | first<br>`⊃'abc' 'de'` → `abc` | pick<br>`2⊃'abc' 'de'` → `de` |
| **⊆** | left shoe underbar | `` ` `` Shift+`z` | nest (enclose if simple)<br>`≡⊆'abc'` → `2` | partition: keep runs under non-zeros<br>`1 1 0 1⊆'ab d'` → `'ab' 'd'` |
| **∊** | epsilon | `` ` `` `e` | enlist: flatten nested<br>`∊(1 2)(3(4 5))` → `1 2 3 4 5` | member of<br>`2 5∊1 2 3` → `1 0` |
| **⌷** | squad | `` ` `` Shift+`l` | materialise<br>`⌷1 2 3` → `1 2 3` | index<br>`2⌷10 20 30` → `20` |
| **⊣** | left tack | `` ` `` `\|` | same<br>`⊣5` → `5` | left argument<br>`1⊣2` → `1` |
| **⊢** | right tack | `` ` `` `\` | same<br>`⊢5` → `5` | right argument<br>`1⊢2` → `2` |

## Search, select and sort

Find things, keep things, order things.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **⍳** | iota | `` ` `` `i` | index generator<br>`⍳5` → `1 2 3 4 5` | index of<br>`'abc'⍳'cb'` → `3 2` |
| **⍸** | iota underbar | `` ` `` Shift+`i` | where: indices of 1s<br>`⍸0 1 0 1` → `2 4` | interval index<br>`0 10 20⍸5 15 25` → `1 2 3` |
| **⍷** | epsilon underbar | `` ` `` Shift+`e` | — | find: where ⍺ starts in ⍵<br>`'an'⍷'banana'` → `0 1 0 1 0 0` |
| **∪** | up shoe | `` ` `` `v` | unique<br>`∪1 2 2 3 1` → `1 2 3` | union<br>`1 2∪2 3` → `1 2 3` |
| **∩** | down shoe | `` ` `` `c` | — | intersection<br>`1 2 3∩2 3 4` → `2 3` |
| **⍋** | grade up | `` ` `` `$` | indices that sort ascending<br>`⍋30 10 20` → `2 3 1` | grade by a collating sequence<br>`'cab'⍋'acb'` → `2 1 3` |
| **⍒** | grade down | `` ` `` `#` | indices that sort descending<br>`⍒30 10 20` → `1 3 2` | grade down by a collating sequence<br>`'cab'⍒'acb'` → `3 1 2` |
| **/** | slash | on keyboard | (operator: reduce, below) | replicate / compress<br>`1 0 2/'abc'` → `acc` |
| **⌿** | slash bar | `` ` `` `/` | (operator: reduce first axis) | replicate along first axis<br>`1 0 1⌿3 2⍴⍳6` → `[1 2 ⋄ 5 6]` |
| **\** | backslash | on keyboard | (operator: scan, below) | expand: 0 inserts a blank<br>`1 0 1\'ab'` → `a b` |
| **⍀** | backslash bar | `` ` `` `.` | (operator: scan first axis) | expand along first axis<br>`1 0 1⍀2 2⍴⍳4` → `[1 2 ⋄ 0 0 ⋄ 3 4]` |

## Conversion

Between numbers, text and number bases.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **⍕** | format | `` ` `` `'` | format: number → text (⍴ shows 7 characters)<br>`⍴⍕3.14159` → `7` | format with width/decimals<br>`6 2⍕3.14159` → `3.14` |
| **⍎** | execute | `` ` `` `;` | execute text as APL<br>`⍎'2+3'` → `5` | — |
| **⊥** | up tack | `` ` `` `b` | — | decode: digits → number in base ⍺<br>`2⊥1 0 1` → `5` |
| **⊤** | down tack | `` ` `` `n` | — | encode: number → digits in base ⍺<br>`2 2 2⊤5` → `1 0 1` |

## Operators

An operator takes a function (its operand) and makes a new one.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **/** | reduce | on keyboard | f/ puts f between items<br>`+/1 2 3 4` → `10` | n-wise reduce (windows of ⍺)<br>`2+/1 2 3 4` → `3 5 7` |
| **\** | scan | on keyboard | f\ keeps the running results<br>`+\1 2 3 4` → `1 3 6 10` | — |
| **⌿** | reduce first | `` ` `` `/` | reduce down the columns<br>`+⌿2 3⍴⍳6` → `5 7 9` | — |
| **¨** | each | `` ` `` `1` | f¨ applies f to each item<br>`≢¨'ab' 'cde'` → `2 3` | pairwise each<br>`1 2,¨3 4` → `(1 3) (2 4)` |
| **⍨** | commute / selfie | `` ` `` Shift+`t` | f⍨⍵ is ⍵ f ⍵<br>`×⍨3` → `9` | ⍺ f⍨ ⍵ is ⍵ f ⍺<br>`2-⍨10` → `8` |
| **∘** | jot | `` ` `` `j` | bind (2∘×) or compose (f∘g)<br>`2∘×1 2 3` → `2 4 6` | outer product ∘.f: every pair<br>`1 2∘.×1 2 3` → `[1 2 3 ⋄ 2 4 6]` |
| **.** | dot | on keyboard | — | inner product f.g (+.× is matrix product)<br>`1 2 3+.×4 5 6` → `32` |
| **⍤** | jot diaeresis | `` ` `` Shift+`j` | rank: f⍤1 applies to each row<br>`{+/⍵}⍤1⊢2 3⍴⍳6` → `6 15` | atop: f⍤g is f (⍺ g ⍵)<br>`2-⍤+3` → `¯5` |
| **⍥** | circle diaeresis | `` ` `` Shift+`o` | over: ⍺ f⍥g ⍵ is (g ⍺) f (g ⍵) | compare after transforming<br>`'Ab'≡⍥⎕C'aB'` → `1` |
| **⍣** | power | `` ` `` Shift+`p` | f⍣n applies f n times; f⍣≡ until stable<br>`(2∘×)⍣3⊢1` → `8` | — |
| **⌸** | key | `` ` `` Shift+`k` | group by key: ⍺ is the key, ⍵ its positions<br>`{⍺,≢⍵}⌸'abca'` → `[a 2 ⋄ b 1 ⋄ c 1]` | group ⍵ by keys ⍺<br>`'abab'{⍺,+/⍵}⌸1 2 3 4` → `[a 4 ⋄ b 6]` |
| **⌺** | stencil | `` ` `` `~` | f⌺n on each window (edges padded with 0)<br>`{+/,⍵}⌺3⊢1 2 3 4 5` → `3 6 9 12 9` | — |
| **@** | at | on keyboard | replace at positions<br>`0@2 4⊢1 2 3 4 5` → `1 0 3 0 5` | — |
| **⍠** | variant | `` ` `` `?` | set an option of a system function<br>`('a'⎕R'x'⍠'IC' 1)'Aa'` → `xx` | — |
| **⌶** | I-beam | `` ` `` `!` | system services by number (739⌶ is the temp folder)<br>`(739⌶)0` → `/tmp` | — |

## Syntax and names

Not functions: the punctuation of APL.

| Glyph | Name | RIDE key | One argument (monadic) | Two arguments (dyadic) |
| :---: | --- | --- | --- | --- |
| **←** | left arrow | `` ` `` `[` | assign: x←5 | — |
| **→** | right arrow | `` ` `` `]` | branch / leave a function: →0 | — |
| **⍺** | alpha | `` ` `` `a` | left argument of a dfn<br>`3{⍺+⍵}4` → `7` | — |
| **⍵** | omega | `` ` `` `w` | right argument of a dfn<br>`{⍵×2}5` → `10` | — |
| **∇** | del | `` ` `` `g` | the dfn itself (recursion); also starts/ends a tradfn<br>`{⍵≤1:1 ⋄ ⍵×∇ ⍵-1}5` → `120` | — |
| **⋄** | diamond | `` ` `` `` ` `` | statement separator<br>`{a←2 ⋄ a×3}0` → `6` | — |
| **⍝** | lamp | `` ` `` `,` | comment: the rest of the line is ignored, e.g. `x←5 ⍝ the price` | — |
| **⍬** | zilde | `` ` `` `}` | empty numeric vector<br>`≢⍬` → `0` | — |
| **¯** | high minus | `` ` `` `2` | negative number sign (part of the number)<br>`¯3+1` → `¯2` | — |
| **⎕** | quad | `` ` `` `l` | system names (⎕IO, ⎕A…); ⎕← prints, ⎕ reads input<br>`⎕A` → `ABCDEFGHIJKLMNOPQRSTUVWXYZ` | — |
| **⍞** | quote quad | `` ` `` `{` | character input/output (no newline) | — |
| **'** | quote | on keyboard | text: 'it''s' (double a quote to include one)<br>`'it''s'` → `it's` | — |
| **∆ ⍙** | delta, delta underbar | `` ` `` `h` / `` ` `` `>` | allowed in names, like letters<br>`{∆x←1 ⋄ ∆x+1}0` → `2` | — |
| **⍛** | jot underbar | `` ` `` Shift+`f` | behind: (f⍛g)⍵ is (f ⍵) g ⍵ (Dyalog 20+)<br>`-⍛+5` → `0` | — |

## Learn them in this order

You don't need all 80 at once. These cover most everyday code:

1. **Arithmetic and arrays:** `+ - × ÷ ⍳ ⍴ ,` ([tutorial 01](../tutorials/01-basics/README.md), [02](../tutorials/02-arrays/README.md))
2. **Functions:** `{ } ⍺ ⍵ ←` ([tutorial 03](../tutorials/03-functions/README.md))
3. **Operators:** `/ \ ¨ ∘. ⍨` ([tutorial 04](../tutorials/04-operators/README.md))
4. **Selecting:** `= ≠ < > ∧ ∨ ~ ⍸ ∊` and `/` as compress ([tutorial 05](../tutorials/05-boolean-selection/README.md))
5. **Nesting and sorting:** `⊂ ⊃ ↑ ↓ ⍋ ⍒ ⌸` ([tutorials 07](../tutorials/07-nested-arrays/README.md), [09](../tutorials/09-sorting-searching/README.md))

## More

- In RIDE, put the cursor on a glyph and press **F1** for its documentation.
- [APL Wiki: list of language elements](https://aplwiki.com/wiki/List_of_language_elements)
- [Dyalog language reference](https://docs.dyalog.com)
- [APL Cart](https://aplcart.info): search for "how do I…" and get the idiom

---

*Generated by [build.py](build.py): every example above was run in Dyalog to
get its result. To change the sheet, edit the glyph list in `build.py`, then
run `python3 cheatsheet/build.py`.*
