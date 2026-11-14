# 10 · Workspaces, files and system names

How to save your work, load code from files, read and write text files,
and use the most common system functions (`⎕` names).


## Workspaces

Everything you define lives in the **workspace**. You can save it and load
it again:

```apl
      )save /app/mywork      ⍝ writes mywork.dws
      )load /app/mywork
      )wsid                  ⍝ current workspace name
      )clear                 ⍝ empty workspace
```

> In the container, only `/app` (this repo) is kept after you exit, so save
> there.

Workspaces are binary files, so they're not ideal for git. For code you
want to keep, use **text source files** instead (next section).

## Source files: `]load` and `⎕FIX`

Put one function per file with the `.aplf` extension, like the files in
[`../03-functions`](../03-functions):

```apl
      ]load /app/tutorials/03-functions/Mean.aplf
Mean
      Mean 2 4 9
5
```

`2 ⎕FIX` does the same from code. The `2` is needed for single-function
files. Plain `⎕FIX` is for script files that define a whole namespace or
class:

```apl
      2 ⎕FIX 'file:///app/tutorials/03-functions/Fact.aplf'
      Fact 5
120
```

`]load` also accepts a wildcard, such as
`]load /app/tutorials/03-functions/*.aplf`. For larger projects, look at
**Link** (`]link.create`), which keeps a namespace and a folder in sync as
you edit.

## Reading and writing text files

`⎕NPUT` writes text and `⎕NGET` reads it:

```apl
      (⊂'line one' 'line two' 'line three') ⎕NPUT '/tmp/demo.txt' 1
      ⊃⎕NGET '/tmp/demo.txt' 1
┌────────┬────────┬──────────┐
│line one│line two│line three│
└────────┴────────┴──────────┘
      ≢⊃⎕NGET '/tmp/demo.txt' 1
3
```

- The `1` on the right of `⎕NPUT` means "overwrite if it exists".
- The `1` on the right of `⎕NGET` means "split into lines". Without it,
  you get one string.

Other useful file functions:

```apl
      ⎕NEXISTS '/tmp/demo.txt'
1
      ⎕NDELETE '/tmp/demo.txt'
      ⎕NEXISTS '/tmp/demo.txt'
0
```

## CSV: `⎕CSV`

```apl
      (⊂'name,age' 'ann,31' 'bob,25') ⎕NPUT '/tmp/people.csv' 1
      ⎕CSV '/tmp/people.csv'
┌────┬───┐
│name│age│
├────┼───┤
│ann │31 │
├────┼───┤
│bob │25 │
└────┴───┘
      csv←⎕CSV '/tmp/people.csv' '' 4
      csv
┌────┬───┐
│name│age│
├────┼───┤
│ann │31 │
├────┼───┤
│bob │25 │
└────┴───┘
      +/1↓csv[;2]
56
```

The `4` asks `⎕CSV` to convert number columns to numbers where possible.
That's why the ages can be summed.

## JSON: `⎕JSON`

```apl
      d←⎕JSON '{"name":"ann","langs":["apl","k"]}'
      d.name
ann
      d.langs
┌───┬─┐
│apl│k│
└───┴─┘
      ⎕JSON d
{"langs":["apl","k"],"name":"ann"}
```

## Useful system names

| Name | What it is |
| --- | --- |
| `⎕IO` | index origin (1 by default; set to 0 to count from 0) |
| `⎕A` | the alphabet `'ABC…Z'` |
| `⎕D` | the digits `'0123456789'` |
| `⎕TS` | timestamp: year month day h m s ms |
| `⎕PP` | print precision (digits shown) |
| `⎕NL` | name list (`⎕NL 3` lists functions) |
| `⎕EX` | erase a name |
| `⎕DL` | delay (sleep) in seconds |
| `?` | random numbers: `?6` rolls a die, `5?10` deals 5 from 10 |

```apl
      ⎕A
ABCDEFGHIJKLMNOPQRSTUVWXYZ
      ⎕D
0123456789
      ⍳3
1 2 3
      ⎕IO←0
      ⍳3
0 1 2
      ⎕IO←1
      ⎕PP←4
      ○1
3.142
      ⎕PP←10
      ⍴⎕TS
7
```

## Timing code

Use `]runtime` to see how long an expression takes. It's handy when you
compare two solutions.

```apl
      ]runtime +/⍳1e6
```

## Exercises

1. Write three lines of text to `/tmp/notes.txt`, then read them back.
2. Count the lines that contain the letter `a`.
3. Load `Mean.aplf` with `2 ⎕FIX` and take the mean of `⍳10`.

<details><summary>Solutions</summary>

```apl
      (⊂'apple' 'kiwi' 'banana') ⎕NPUT '/tmp/notes.txt' 1
      lines←⊃⎕NGET '/tmp/notes.txt' 1
      lines
┌─────┬────┬──────┐
│apple│kiwi│banana│
└─────┴────┴──────┘
      +/'a'∊¨lines
2
      2 ⎕FIX 'file:///app/tutorials/03-functions/Mean.aplf'
      Mean ⍳10
5.5
```

</details>

**Next:** [11 · Traditional functions and control structures](../11-tradfns-and-control/README.md)
