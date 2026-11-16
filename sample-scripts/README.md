# Sample scripts

Small, runnable APL scripts (`.apls`), each showing one idea. Run any of them
with the [`dyalog` command](../install/dyalog/README.md#the-dyalog-command):

```sh
dyalog sample-scripts/04-primes.apls
```

| Script | Shows | Key glyphs |
| --- | --- | --- |
| [test.apls](test.apls) | the smallest possible script | `⎕←` |
| [01-basics.apls](01-basics.apls) | arithmetic, right-to-left order, variables | `× ÷ * ←` |
| [02-arrays.apls](02-arrays.apls) | reshape, indexing, take, rotate, transpose, row/column sums | `⍴ [;] ↑ ⌽ ⍉ / ⌿` |
| [03-fizzbuzz.apls](03-fizzbuzz.apls) | the same problem with array operations and with a loop | `\| ⊃ ¨` and `:For` / `:Select` |
| [04-primes.apls](04-primes.apls) | primes via a divisor table and via a recursive sieve; twin primes | `∘.\| ∇ 2-/` |
| [05-strings.apls](05-strings.apls) | reverse, upper case, split into words, palindromes, Caesar cipher | `⌽ ⎕C ⊆ ⍒ ∊` |
| [06-statistics.apls](06-statistics.apls) | mean, median, mode, standard deviation, text histogram | `⍋ ⌸ ∘.=` |
| [07-matrices.apls](07-matrices.apls) | tables, identity, matrix product, solving equations | `∘.× +.× ⌹` |
| [08-life.apls](08-life.apls) | Conway's Game of Life in one line (a glider moving) | `⊖ ⌽ ∨.∧` |
| [09-word-count.apls](09-word-count.apls) | word frequencies in [poem.txt](poem.txt), or any file you pass | `⎕NGET ⊆ ⌸` |
| [10-csv-report.apls](10-csv-report.apls) | revenue per region from [sales.csv](sales.csv) | `⎕CSV ⌸ ⍒` |
| [11-using-lib.apls](11-using-lib.apls) | using the [shared library](../lib/README.md) instead of rewriting helpers | `⎕FIX` |

All outputs were checked against the same calculations in Python.

**Component files:** [component-files/](component-files/README.md) has sample
`.dcf` data files and a working migration path: inventory, JSON export, load
into SQL, verify, and a data-access layer.

**Other file types:** [file-types/](file-types/README.md) has one example of each
Dyalog file type (`.aplf .aplo .apln .aplc .apli .apla .dyapp .dws`) and
shows how to run and load them.

## Example

```
$ dyalog sample-scripts/06-statistics.apls
data:   23 45 12 67 34 45 89 21 45 56 34 78
mean:   45.75
median: 45
mode:   45
sd:     22.38721733
range:  12 89
histogram:
  0- 19 │█
 20- 39 │████
 40- 59 │████
 60- 79 │██
 80- 99 │█
```

## Writing your own scripts

```apl
⍝ hello.apls
⎕←'hello'                 ⍝ only ⎕← lines print in a script
'this is not shown'       ⍝ evaluated, but not displayed
Avg←{(+/⍵)÷≢⍵}            ⍝ define functions as you go
⎕←Avg 3 1 4 1 5
```

- **Printing:** only `⎕←` output appears. A bare expression is evaluated
  but not displayed, unlike in the interactive session.
- **Errors** stop the script with the usual message, and `dyalog` exits
  with code 4. Use `⎕OFF n` to exit with your own code.
- **Files next to the script:** the script's own path is the first
  command-line item, so this finds its folder from anywhere:

  ```apl
  here←⊃1⎕NPARTS⊃2⎕NQ'.' 'GetCommandLineArgs'
  text←⊃⎕NGET here,'poem.txt'
  ```

- **Arguments:** `dyalog my.apls a b` puts `a b` after the script path, so
  `1↓2⎕NQ'.' 'GetCommandLineArgs'` gives `'a' 'b'`. See
  [09-word-count.apls](09-word-count.apls).
- **Functions vs scripts:** a file that *defines one function* is `.aplf`
  (`dyalog MyFn.aplf` loads it). A file of statements is a script, `.apls`.
