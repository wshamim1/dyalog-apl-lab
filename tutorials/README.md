# APL tutorials

A hands-on path through Dyalog APL, from your first expression to
traditional functions. Work through them in order. Each one has examples to
type in and exercises with solutions.

| # | Tutorial | You'll learn |
| --- | --- | --- |
| 00 | [Getting started](00-getting-started/README.md) | the session, typing glyphs, `)` commands, `]box` |
| 01 | [Basics](01-basics/README.md) | arithmetic, right-to-left, monadic/dyadic, variables |
| 02 | [Arrays](02-arrays/README.md) | `⍳ ⍴ ≢`, reshape, indexing, take/drop, `⌽ ⊖ ⍉` |
| 03 | [Functions](03-functions/README.md) | dfns, `⍺ ⍵`, guards, recursion, `.aplf` files |
| 04 | [Operators](04-operators/README.md) | reduce `/`, scan `\`, each `¨`, outer `∘.`, `⍨ ∘ ⍣ ⍤ ⌸` |
| 05 | [Booleans and selection](05-boolean-selection/README.md) | comparisons, compress, `⍸ ∊ ⍳ ∪` |
| 06 | [Strings](06-strings/README.md) | text, `⎕C ⍕ ⍎ ⎕UCS`, split/join, `⍷ ⎕R` |
| 07 | [Nested arrays](07-nested-arrays/README.md) | `⊂ ⊃ ≡`, mix/split, partition, records |
| 08 | [Trains](08-trains/README.md) | tacit forks and atops |
| 09 | [Sorting and searching](09-sorting-searching/README.md) | `⍋ ⍒`, top n, interval index, frequency counts |
| 10 | [Workspaces and files](10-workspaces-files/README.md) | `)save`, `]load`, `⎕NGET ⎕NPUT ⎕CSV ⎕JSON`, `⎕IO` |
| 11 | [Tradfns and control](11-tradfns-and-control/README.md) | headers, `:If :For :While :Select :Trap` |

## How to use these

1. Start a session (see [install/dyalog](../install/dyalog/README.md)):

   ```sh
   install/dyalog/podman.sh run      # or docker.sh / mac.sh
   ```

2. Turn on boxed display: `]box on`.
3. Type the indented lines and compare with the output shown below them.
4. Try the exercises before you open the solutions.

All outputs were produced by Dyalog APL 21.0 with `]box on` and the default
`⎕IO←1`.

## Reading the examples

```apl
      2×3+4
14
```

- The **indented** line is what you type (the session prompt is 6 spaces).
- The lines below it are what APL prints.

## Function files

Tutorials [03](03-functions) and [11](11-tradfns-and-control) include
`.aplf` files you can load. The container mounts the repo at `/app`:

```apl
      ]load /app/tutorials/03-functions/Fact.aplf
Fact
      Fact 5
120
```
