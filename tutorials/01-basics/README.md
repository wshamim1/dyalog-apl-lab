# 01 · Basics

Arithmetic, the right-to-left rule, and variables.


## Arithmetic

```apl
      2+3
5
      10-4
6
      6×7
42
      22÷7
3.142857143
      2*10
1024
```

`×` is multiply, `÷` is divide, and `*` is power.

## Negative numbers use the high minus `¯`

`¯` is part of the number, while `-` is a function:

```apl
      ¯5
¯5
      3-8
¯5
      ¯3+1
¯2
```

## Every function works on whole arrays

No loops are needed. A function applies to every element:

```apl
      1 2 3+10 20 30
11 22 33
      2×1 2 3 4
2 4 6 8
      1 2 3 4*2
1 4 9 16
```

A single number (a *scalar*) is extended to match the other argument.

## Right to left. No precedence.

APL has **no operator precedence**. Every function takes as its right
argument *everything to its right*:

```apl
      2×3+4
14
```

This is `2×(3+4)`, not `(2×3)+4`. Use parentheses when you want something
else:

```apl
      (2×3)+4
10
```

It feels odd for a day, then it's simpler than remembering precedence rules.

## Monadic and dyadic

Most glyphs mean two related things:

- **dyadic** (two arguments: `x f y`)
- **monadic** (one argument: `f y`)

| Glyph | Monadic `f y` | Dyadic `x f y` |
| --- | --- | --- |
| `-` | negate | subtract |
| `×` | sign (¯1, 0, 1) | multiply |
| `÷` | reciprocal | divide |
| `⌈` | ceiling | maximum |
| `⌊` | floor | minimum |
| `\|` | absolute value | residue (mod) |
| `*` | e to the power | power |
| `!` | factorial | binomial |

```apl
      -5
¯5
      ×¯7 0 3
¯1 0 1
      ÷4
0.25
      ⌈3.2
4
      5⌈9
9
      ⌊3.7
3
      5⌊9
5
      |¯6
6
      3|10
1
      !5
120
```

Note that `3|10` is **10 mod 3**: the divisor goes on the left.

## Variables

`←` assigns. Names are case-sensitive.

```apl
      price←4.5
      qty←3
      price×qty
13.5
      total←price×qty
      total
13.5
```

An assignment doesn't print anything. Type the name to see its value. To
assign *and* display, use `⎕←`:

```apl
      ⎕←tax←total×0.2
2.7
```

You can assign several names at once:

```apl
      (a b c)←1 2 3
      b
2
```

## Exercises

1. Compute `(5+3)×2` without parentheses (reorder it).
2. What is 17 mod 5?
3. Convert 100 °F to °C: `(F-32)×5÷9`.
4. Make a variable `r←2` and compute the area of a circle. `○1` is π.

<details><summary>Solutions</summary>

```apl
      2×5+3
16
      5|17
2
      F←100
      (F-32)×5÷9
37.77777778
      r←2
      ○1
3.141592654
      (○1)×r*2
12.56637061
      ○r*2
12.56637061
```

`○r*2` works because `○x` means π×x.

</details>

**Next:** [02 · Arrays](../02-arrays/README.md)
