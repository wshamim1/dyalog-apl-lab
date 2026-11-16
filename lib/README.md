# Shared APL library

`Lib` is a small set of helpers that any APL code in this repo can use,
instead of each script writing its own `Mean`, `Trim` or "environment
variable or a default". Each part is its own file, and
[Lib.apln](Lib.apln) loads them all:

| Part | File | For |
| --- | --- | --- |
| [`Lib.Str`](#libstr) | [Str.apln](Str.apln) | text: trim, split, join, case, replace |
| [`Lib.Stats`](#libstats) | [Stats.apln](Stats.apln) | mean, median, mode, SD, rounding, percentages |
| [`Lib.Data`](#libdata) | [Data.apln](Data.apln) | namespaces as records, JSON |
| [`Lib.Sys`](#libsys) | [Sys.apln](Sys.apln) | environment variables, script arguments, files, timestamps |
| [`Lib.Fmt`](#libfmt) | [Fmt.apln](Fmt.apln) | report formatting: decimals, commas, money, sizes, durations, padding |
| [`Lib.Err`](#liberr) | [Err.apln](Err.apln) | raising errors with messages, assertions, try-with-default |
| [`Lib.Date`](#libdate) | [Date.apln](Date.apln) | parse, format, add days, days between, weekday, month |
| [`Lib.Log`](#liblog) | [Log.apln](Log.apln) | timestamped log lines with levels, to the screen and/or a file |

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

[Lib.apln](Lib.apln) is only a loader: when it's fixed, it fixes every other
`.apln` file in its folder inside `Lib`, so `Str.apln` becomes `Lib.Str`. Fix
it again to reload after you edit a part. `Lib.Parts` lists what was loaded.

Give the parts you use short names: `S←Lib.Str ⋄ S.Trim '  x '`.

You can also load one part on its own, `⎕FIX'file:///apl-lib/Fmt.apln'`, and
call `Fmt.Money 12`. `Date` and `Log` use `Str` and `Sys`, so load those
alongside them, or simply load `Lib.apln`.

See [sample-scripts/11-using-lib.apls](../sample-scripts/11-using-lib.apls)
for a complete script.

## What's in it

### Lib.Str

Text.

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

### Lib.Stats

Numbers.

| Function | Does | Example → result |
| --- | --- | --- |
| `Mean v`, `Median v` | average, middle value | `Median 4 1 3 2` → `2.5` |
| `Mode v` | most frequent value (the first, on a tie) | `Mode 1 2 2 3` → `2` |
| `SD v` | population standard deviation | `SD 2 4 4 4 5 5 7 9` → `2` |
| `Range v` | largest minus smallest | `Range 3 9 4` → `6` |
| `[places] Round v` | round half up (default 0 places) | `2 Round 3.14159` → `3.14` |
| `[places] Percent v` | each item as a % of the total (default 1 place) | `Percent 1 3` → `25 75` |

### Lib.Data

Namespaces as records, and JSON.

| Function | Does | Example → result |
| --- | --- | --- |
| `names Record values` | make a namespace | `'name' 'age' Record 'Ann' 41` |
| `Fields ns` | its variable names, sorted | `Fields r` → `'age' 'name'` |
| `[default] Get ns name` | a field, or the default if missing | `0 Get r 'city'` → `0` |
| `[pretty] ToJSON x` | export as JSON (`1 ToJSON` indents it) | `ToJSON r` → `'{"age":41,"name":"Ann"}'` |
| `FromJSON s` | import JSON | `(FromJSON '{"a":1}').a` → `1` |

### Lib.Sys

Environment, command line, files, time.

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

### Lib.Fmt

Numbers and text for reports. Each takes a number, or a
vector (then you get one string per item). Negative numbers get a plain `-`.

| Function | Does | Example → result |
| --- | --- | --- |
| `[places] Fixed n` | fixed decimals (default 2) | `2 Fixed 3.5` → `'3.50'` |
| `[places] Commas n` | thousands separators (default 0 places) | `Commas 1234567` → `'1,234,567'` |
| `[symbol] Money n` | 2 places, commas, currency (default `$`) | `Money ¯1234.5` → `'-$1,234.50'` |
| `[places] Pct n` | a fraction as a percentage (default 1 place) | `Pct 0.256` → `'25.6%'` |
| `Bytes n` | a size in B, KB, MB… | `Bytes 1536` → `'1.5 KB'` |
| `Duration ms` | milliseconds, readably | `Duration 185000` → `'3m 05s'` |
| `w PadL x` / `w PadR x` | right- / left-align to width `w` (never cuts) | `6 PadL 42` → `'    42'` |
| `w Center x` | center in width `w` | `7 Center 'abc'` → `'  abc  '` |
| `n Plural word` | a count with the right word | `3 Plural 'order'` → `'3 orders'`, `2 Plural 'child' 'children'` |

### Lib.Err

Raising and catching errors with useful messages.

| Function | Does | Example |
| --- | --- | --- |
| `[context] Fail msg` | raise DOMAIN ERROR (11) with a message | `'MySQLExec' Fail 'lost connection'` |
| `en Signal msg` | raise any error number with a message | `5 Signal 'lengths differ'` |
| `msg Assert bool` | raise DOMAIN ERROR unless all 1s | `'qty must be > 0' Assert qty>0` |
| `[default] (Fn Try) x` | `Fn x`, or the default (`⍬`) on any error | `0 ({÷⍵} Try) 0` → `0` |
| `Text ⍬` | the last error as text, for logs | `'DOMAIN ERROR: qty must be > 0'` |

The messages show up where the error stops your program, so a failed
`Fail` reads `DOMAIN ERROR: MySQLExec: lost connection` instead of just
`DOMAIN ERROR`. In `:Trap` or `0::`, use `Text ⍬` to get them.

### Lib.Date

Dates as `'YYYY-MM-DD'` text, or `⎕TS`-style numbers
(`2026 11 16`). Every function takes either.

| Function | Does | Example → result |
| --- | --- | --- |
| `Parse d` | text → numbers; DOMAIN ERROR if not a real date | `Parse '2026-11-16 09:05'` → `2026 11 16 9 5 0` |
| `Format d` | numbers → text | `Format 2026 1 5` → `'2026-01-05'` |
| `IsValid d` | 1 if a real date | `IsValid '2026-02-29'` → `0` |
| `Today ⍬` | today's date | `'2026-11-16'` |
| `n AddDays d` | `n` days later (or earlier, if negative) | `7 AddDays '2026-11-16'` → `'2026-11-23'` |
| `a DaysBetween b` | days from `a` to `b` | `'2026-11-01' DaysBetween '2026-11-16'` → `15` |
| `Weekday d` | the day's name | `Weekday '2026-11-16'` → `'Monday'` |
| `Month d` | year and month, for grouping with `⌸` | `Month '2026-11-16'` → `'2026-11'` |
| `IsLeap d`, `DaysInMonth d` | leap year? days in that month | `DaysInMonth '2024-02-01'` → `29` |
| `Day d` / `FromDay n` | to and from a day number (days since 1899-12-31) | |

Group sales by month: `(Lib.Date.Month¨dates){⍺,+/⍵}⌸amounts`.

### Lib.Log

Timestamped log lines.

```apl
      Lib.Log.Info 'pipeline started'
2026-11-16 09:05:03 INFO  pipeline started
      'kafka' Lib.Log.Warn 'slow poll: ',Lib.Fmt.Duration 4200
2026-11-16 09:05:07 WARN  [kafka] slow poll: 4.2 s
```

| Function / setting | Does |
| --- | --- |
| `[context] Debug msg`, `Info`, `Warn`, `Error` | log a line at that level; `msg` can be any array (it is formatted with `⍕`). Returns the line (shy), or `''` if dropped |
| `Level` | lowest level shown: `Lib.Log.Level←'DEBUG'`. If empty, `$LOG_LEVEL` is used, else `INFO` |
| `File` | also append each line to this file: `Lib.Log.File←'/app/run.log'` |
| `Console` | `0` stops printing to the screen (file only) |

`LOG_LEVEL=DEBUG dyalog my-script.apls` works: the `dyalog` command passes
`LOG_LEVEL` into the container. Times are the container's clock, which is
usually UTC.

## Adding to it

1. Add the function to the matching part (`Str.apln`, `Fmt.apln`, …), with
   a one-line `⍝` comment saying what it does. Keep it general: something two
   or more places in the repo would use.
2. Add checks to the matching file in [tests/](tests), then run
   `dyalog test lib`.
3. Add a row to the tables above.

**A new part** is a new file, say `Csv.apln`, holding `:Namespace Csv`. Start
it with `⎕IO←1 ⋄ ⎕ML←1`, and reach other parts as `##.Str.Trim`. The loader
picks it up as `Lib.Csv` with no other change; add `Csv_test.aplf` to
[tests/](tests) and add it to the list in [Lib_test.aplf](tests/Lib_test.aplf).
