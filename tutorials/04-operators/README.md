# 04 · Operators

An **operator** takes a function and produces a new function. This is
where APL gets its power.


## Reduce `/`

`f/` puts `f` between every item:

```apl
      +/1 2 3 4
10
      ×/1 2 3 4
24
      ⌈/3 9 2 7
9
      ⌊/3 9 2 7
2
```

`+/1 2 3 4` is `1+2+3+4`. Like everything in APL, it's evaluated right to
left, which matters for `-`:

```apl
      -/1 2 3 4
¯2
```

That's `1-(2-(3-4))`.

On a matrix, `/` reduces each row and `⌿` reduces each column:

```apl
      m←3 4⍴⍳12
      m
1  2  3  4
5  6  7  8
9 10 11 12
      +/m
10 26 42
      +⌿m
15 18 21 24
```

## Scan `\`

Like reduce, but keeps every intermediate result:

```apl
      +\1 2 3 4 5
1 3 6 10 15
      ⌈\3 1 4 1 5 9 2 6
3 3 4 4 5 9 9 9
      ×\1 2 3 4 5
1 2 6 24 120
```

## Each `¨`

Applies a function to each item separately:

```apl
      ⍳¨1 2 3
┌─┬───┬─────┐
│1│1 2│1 2 3│
└─┴───┴─────┘
      ≢¨'apple' 'fig' 'banana'
5 3 6
```

## Outer product `∘.`

`x∘.f y` applies `f` to every combination of items. It builds a table:

```apl
      1 2 3∘.×1 2 3 4
1 2 3  4
2 4 6  8
3 6 9 12
      (⍳4)∘.=⍳4
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
```

`(⍳4)∘.=⍳4` is the identity matrix.

## Commute `⍨`

`⍨` swaps the arguments, or with one argument, uses it on both sides:

```apl
      2-⍨10
8
      +⍨5
10
      ×⍨1 2 3
1 4 9
```

`2-⍨10` is `10-2`. `×⍨` means "times itself", so squaring.

## Compose `∘` and bind

`f∘g` applies `g` first, then `f`. Binding a value with `∘` makes a
one-argument function:

```apl
      2∘×1 2 3
2 4 6
      *∘2 ⊢1 2 3 4
1 4 9 16
```

`2∘×` is "double". `*∘2` is "square". `⊢` (right tack) just returns its
argument. It separates `2` from `1 2 3 4`, so they aren't read as one vector.

## Power `⍣`

`f⍣n` applies `f` n times:

```apl
      (2∘×)⍣5⊢1
32
```

`f⍣≡` keeps applying until the result stops changing (a *fixpoint*):

```apl
      {1+÷⍵}⍣≡ 1
1.618033989
```

That's the golden ratio.

## Rank `⍤`

`f⍤1` applies `f` to each row (each rank-1 piece) of an array:

```apl
      m
1  2  3  4
5  6  7  8
9 10 11 12
      {+/⍵}⍤1⊢m
10 26 42
      ⌽⍤1⊢m
 4  3  2 1
 8  7  6 5
12 11 10 9
```

## Key `⌸`

Groups items by key and applies a function to each group:

```apl
      {⍺,≢⍵}⌸'mississippi'
m 1
i 4
s 4
p 2
```

Each row is a letter and how often it appears.

## Exercises

1. Sum the numbers from 1 to 100.
2. Make a 9×9 multiplication table.
3. Running total of `5 3 8 1`.
4. The length of each word in `'the' 'quick' 'brown' 'fox'`.
5. The product 1×2×…×10 (compare with `!10`).

<details><summary>Solutions</summary>

```apl
      +/⍳100
5050
      (⍳9)∘.×⍳9
1  2  3  4  5  6  7  8  9
2  4  6  8 10 12 14 16 18
3  6  9 12 15 18 21 24 27
4  8 12 16 20 24 28 32 36
5 10 15 20 25 30 35 40 45
6 12 18 24 30 36 42 48 54
7 14 21 28 35 42 49 56 63
8 16 24 32 40 48 56 64 72
9 18 27 36 45 54 63 72 81
      +\5 3 8 1
5 8 16 17
      ≢¨'the' 'quick' 'brown' 'fox'
3 5 5 3
      ×/⍳10
3628800
      !10
3628800
```

</details>

**Next:** [05 · Booleans and selection](../05-boolean-selection/README.md)
