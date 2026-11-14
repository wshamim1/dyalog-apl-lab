# 11 · Traditional functions and control structures

Dfns are great for short functions. For longer, step-by-step code, Dyalog
also has **traditional functions** ("tradfns"), with familiar control
structures: `:If`, `:For`, `:While` and so on.


## Anatomy of a tradfn

The first line is the **header**. It names the result, the function and the
arguments. Local names come after `;`:

```apl
 r←Stats v;n
⍝ Mean, minimum and maximum of a numeric vector.
 n←≢v
 r←((+/v)÷n),(⌊/v),⌈/v
```

| Header | Kind |
| --- | --- |
| `Foo` | no arguments, no result |
| `r←Foo y` | monadic, with result |
| `r←x Foo y` | dyadic, with result |
| `r←{x} Foo y` | `x` optional (ambivalent) |
| `r←Foo y;a;b` | `a` and `b` are local |

> **Unlike dfns, names in tradfns are global unless you list them after
> `;`.** Always localise your temporary names.

The example files are in this folder. Load them all at once:

```apl
      ]load /app/tutorials/11-tradfns-and-control/*.aplf
┌───────┬────────┬─────┬───────┬─────┐
│Collatz│FizzBuzz│Grade│SafeDiv│Stats│
└───────┴────────┴─────┴───────┴─────┘
      Stats 4 8 15 16 23 42
18 4 42
```

To create or edit one interactively, type `)ed Name` in RIDE.

## `:If` / `:ElseIf` / `:Else`

See [Grade.aplf](Grade.aplf):

```apl
      Grade 95
A
      Grade 72
C
      Grade¨55 85 91
FBA
```

## `:While`

See [Collatz.aplf](Collatz.aplf):

```apl
      Collatz 6
8
      Collatz¨⍳10
0 1 7 2 5 8 16 3 19 6
```

## `:For` and `:Select`

See [FizzBuzz.aplf](FizzBuzz.aplf):

```apl
      FizzBuzz 15
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
```

`:For i :In list` loops over items, and `:Select` compares a value against
each `:Case`.

## Error handling with `:Trap`

See [SafeDiv.aplf](SafeDiv.aplf):

```apl
      10 SafeDiv 2
5
      10 SafeDiv 0
0
```

Dfns have their own error guard, `errnum::result`:

```apl
      {11::0 ⋄ ⍺÷⍵}/10 0
0
```

## Other control words

| Structure | Use |
| --- | --- |
| `:Repeat` … `:Until cond` | loop at least once |
| `:Continue`, `:Leave` | next iteration / exit the loop |
| `:Return` | leave the function now |
| `:Hold`, `:With`, `:Namespace` | advanced, see the docs |

## Loops vs. arrays

A loop is often a sign there's an array solution. Compare:

```apl
      Collatz¨⍳10
0 1 7 2 5 8 16 3 19 6
      {(0=3|⍵)∧0=5|⍵}⍳15
0 0 0 0 0 0 0 0 0 0 0 0 0 0 1
```

The second line checks FizzBuzz "divisible by both" for every number at
once. Use control structures for real control flow (I/O, error handling,
state machines), and arrays for data.

## Exercises

1. Write a tradfn `r←Max3 v` that returns the 3 largest numbers of `v`.
2. Write a tradfn that uses `:Repeat` to count how many times you can
   halve a number before it's below 1.
3. Rewrite `Grade` as a one-line array expression using interval index `⍸`
   (tutorial 09).

<details><summary>Solutions</summary>

Put these in files and `]load` them, or define them with `)ed`:

```apl
 r←Max3 v
 r←3↑v[⍒v]

 r←Halvings n
 r←0
 :Repeat
     n←n÷2
     r+←1
 :Until n<1
```

The array version of `Grade`:

```apl
      'FCBA'[0 70 80 90⍸55 85 91 72]
FBAC
```

</details>

## Where next?

- [Dyalog documentation](https://docs.dyalog.com)
- [APL Problem Solving Competition](https://www.dyalogaplcompetition.com):
  great practice problems
- [APL Cart](https://aplcart.info): a searchable library of idioms
- [APL Wiki](https://aplwiki.com)

**Back to:** [Tutorials index](../README.md)
