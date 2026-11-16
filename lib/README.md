# Shared APL library

`Lib` is a small set of helpers that any APL code in this repo can use,
instead of each script writing its own `Mean`, `Trim` or "environment
variable or a default". Everything is in one file, [Lib.apln](Lib.apln).

```apl
      ⎕FIX'file:///apl-lib/Lib.apln'
      Lib.Str.Trim '  hello  '
hello
      Lib.Stats.Mean 3 4 8
5
      ', ' Lib.Str.Join 'a' 'b' 'c'
a, b, c
```

## Loading it

| Where your code runs | What to do |
| --- | --- |
| `dyalog` (session or script), any folder | `⎕FIX'file:///apl-lib/Lib.apln'`: the command mounts `lib/` at `/apl-lib`, read-only |
| `dyalog test` | nothing: `Lib` is already loaded for the code under test |
| Dyalog app, RIDE, or your own container | `⎕FIX'file://<path to repo>/lib/Lib.apln'`, or set `APL_LIB` to that path for `Tester` |

Give the parts you use short names: `S←Lib.Str ⋄ S.Trim '  x '`.

See [sample-scripts/11-using-lib.apls](../sample-scripts/11-using-lib.apls)
for a complete script.

## What's in it

**`Lib.Str`**: text

| Function | Does | Example → result |
| --- | --- | --- |
| `IsText s` | 1 if a character scalar or vector | `IsText 'abc'` → `1` |
| `Trim s` | drop leading and trailing blanks | `Trim '  hi  '` → `'hi'` |
| `[seps] Split s` | split on separators (default blank); empty pieces dropped | `',' Split 'a,b,,c'` → `'a' 'b' 'c'` |
| `[sep] Join items` | join with a separator (default blank); numbers are formatted | `'-' Join 1 2 3` → `'1-2-3'` |
| `Words s` | runs of letters | `Words 'Hi, you!'` → `'Hi' 'you'` |
| `Lower s` / `Upper s` | change case | `Upper 'abc'` → `'ABC'` |
| `n Clip s` | cut to `n` characters, ending in `…` | `5 Clip 'abcdefgh'` → `'abcd…'` |
| `(old new) Replace s` | replace text (plain, not a regex) | `('.' '+') Replace 'a.b'` → `'a+b'` |
| `p StartsWith s` / `p EndsWith s` | prefix / suffix test | `'.csv' EndsWith 'x.csv'` → `1` |

**`Lib.Stats`**: numbers

| Function | Does | Example → result |
| --- | --- | --- |
| `Mean v`, `Median v` | average, middle value | `Median 4 1 3 2` → `2.5` |
| `Mode v` | most frequent value (the first, on a tie) | `Mode 1 2 2 3` → `2` |
| `SD v` | population standard deviation | `SD 2 4 4 4 5 5 7 9` → `2` |
| `Range v` | largest minus smallest | `Range 3 9 4` → `6` |
| `[places] Round v` | round half up (default 0 places) | `2 Round 3.14159` → `3.14` |
| `[places] Percent v` | each item as a % of the total (default 1 place) | `Percent 1 3` → `25 75` |

**`Lib.Data`**: namespaces as records, and JSON

| Function | Does | Example → result |
| --- | --- | --- |
| `names Record values` | make a namespace | `'name' 'age' Record 'Ann' 41` |
| `Fields ns` | its variable names, sorted | `Fields r` → `'age' 'name'` |
| `[default] Get ns name` | a field, or the default if missing | `0 Get r 'city'` → `0` |
| `[pretty] ToJSON x` | export as JSON (`1 ToJSON` indents it) | `ToJSON r` → `'{"age":41,"name":"Ann"}'` |
| `FromJSON s` | import JSON | `(FromJSON '{"a":1}').a` → `1` |

**`Lib.Sys`**: environment, command line, files, time

| Function | Does | Example → result |
| --- | --- | --- |
| `[default] Env name` | an environment variable, or the default if unset/empty | `'localhost' Env 'DB_HOST'` |
| `Args ⍬` | the script's arguments (without the script path) | `dyalog x.apls a b` → `'a' 'b'` |
| `ScriptDir ⍬` | folder of the running script, ending in `/` | `(ScriptDir ⍬),'data.csv'` |
| `Exists path` | 1 if the file or folder exists | |
| `ReadText path` / `ReadLines path` | whole file as one string / as lines | |
| `text WriteText path` | write a file (overwrites) | |
| `Now ⍬`, `ISO ⎕TS` | timestamp as `'2026-11-16 09:05:03'` | |
| `(Fn Time) arg` | run `Fn arg`, print how long it took, return its result | `(Fn Time) 1e6` |

Note the parentheses in `(ScriptDir ⍬),'data.csv'`: without them, APL reads
`ScriptDir ⍬,'data.csv'` as `ScriptDir (⍬,'data.csv')`.

## Adding to it

1. Add the function to the right namespace in [Lib.apln](Lib.apln), with a
   one-line `⍝` comment saying what it does. Keep it general: something two
   or more places in the repo would use.
2. Add checks to the matching file in [tests/](tests), then run
   `dyalog test lib`.
3. Add a row to the tables above.
