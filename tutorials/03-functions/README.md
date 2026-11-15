# 03 · Functions (dfns)

Write your own functions with braces `{ }`. These are called **dfns**
("dee-funs").


## `⍵` and `⍺`

Inside braces, `⍵` is the right argument and `⍺` is the left argument:

```apl
      {⍵×2} 5
10
      {⍵×2} 1 2 3
2 4 6
      3 {⍺+⍵} 4
7
```

Give a function a name by assigning it:

```apl
      Double←{⍵×2}
      Double 21
42
      Plus←{⍺+⍵}
      10 Plus 5
15
```

The same function can be called with one argument (monadic) or two
(dyadic). `⍺←value` sets a default for when there's no left argument:

```apl
      Pow←{⍺←2 ⋄ ⍵*⍺}
      Pow 5
25
      3 Pow 5
125
```

## A function that works on arrays

Functions built from array operations automatically work on arrays:

```apl
      Mean←{(+/⍵)÷≢⍵}
      Mean 1 2 3 4 10
4
```

`+/` means "sum". It's the reduce operator, covered in
[tutorial 04](../04-operators/README.md).

## Guards `cond: result`

A *guard* returns early when its condition is true (1). Separate
statements with `⋄`, or put them on new lines in a file:

```apl
      Sign←{⍵>0:'positive' ⋄ ⍵<0:'negative' ⋄ 'zero'}
      Sign 5
positive
      Sign ¯2
negative
      Sign 0
zero
```

## Recursion with `∇`

`∇` refers to the function itself:

```apl
      {⍵≤1:1 ⋄ ⍵×∇ ⍵-1} 5
120
      Fib←{⍵≤1:⍵ ⋄ (∇ ⍵-1)+∇ ⍵-2}
      Fib 10
55
```

## Local variables

Names assigned inside a dfn are **local**. They don't leak out:

```apl
      sq←'outside'
      {sq←⍵*2 ⋄ sq+1} 4
17
      sq
outside
```

## Functions in files

Multi-line functions are easiest to write in a file. This folder has three
example files:

- [Fact.aplf](Fact.aplf)
- [Hyp.aplf](Hyp.aplf)
- [Mean.aplf](Mean.aplf)

Load one with `]load`. The container mounts the repo at `/app`:

```apl
      ]load /app/tutorials/03-functions/Fact.aplf
Fact
      Fact 6
720
      ]load /app/tutorials/03-functions/Hyp.aplf
Hyp
      3 Hyp 4
5
      Hyp 1
1.414213562
```

On the native Mac app, use the real path instead, for example
`]load ~/Desktop/GITRepo/learn-apl-dyalog/tutorials/03-functions/Fact.aplf`.

To edit a function in RIDE, type `)ed Fact` (or press Shift+Enter on the
name), edit it, then press Esc to save and close.

## Applying a function to each item

A dfn applied to a vector gets the *whole vector* as `⍵`. To apply it to
each item separately, use `¨` (each):

```apl
      {⍵>3:'big' ⋄ 'small'}¨1 5 2 8
┌─────┬───┬─────┬───┐
│small│big│small│big│
└─────┴───┴─────┴───┘
```

## Exercises

1. Write `Sq` that squares its argument. Try `Sq ⍳5`.
2. Write `Avg3` that takes `⍺` and `⍵` and returns their average.
3. Write `Clamp` that limits `⍵` to the range 0–10 (hint: `⌈` and `⌊`).
4. Write a recursive `Sum` that adds the numbers from 1 to `⍵`.

<details><summary>Solutions</summary>

```apl
      Sq←{⍵*2}
      Sq ⍳5
1 4 9 16 25
      Avg3←{(⍺+⍵)÷2}
      4 Avg3 10
7
      Clamp←{0⌈10⌊⍵}
      Clamp ¯5 3 12
0 3 10
      Sum←{⍵=0:0 ⋄ ⍵+∇ ⍵-1}
      Sum 100
5050
```

</details>

**Next:** [04 · Operators](../04-operators/README.md)

## Tests

The functions in this folder have tests in [tests/](tests). Run them with
`dyalog test tutorials/03-functions` (see [testing](../../testing/README.md)).
