# 05 · Booleans and selection

Comparisons return 1 (true) or 0 (false). With those, you can count,
filter and search without writing loops.


## Comparison

```apl
      3<5
1
      1 2 3 4 5>2
0 0 1 1 1
      1 2 3 4 5=3 2 3 2 3
0 1 1 0 0
      'hello'='l'
0 0 1 1 0
```

| Glyph | Meaning |
| --- | --- |
| `= ≠` | equal, not equal |
| `< ≤ > ≥` | less, at most, greater, at least |
| `∧ ∨` | and, or |
| `~` | not |
| `≡ ≢` | match (whole arrays identical), not match |

```apl
      1 0 1∧1 1 0
1 0 0
      1 0 1∨0 0 1
1 0 1
      ~1 0 1
0 1 0
      1 2 3≡1 2 3
1
      1 2 3≡1 2 4
0
```

## Counting

A boolean vector summed gives a count:

```apl
      v←3 8 1 9 4 7 2
      v>5
0 1 0 1 0 1 0
      +/v>5
3
```

## Filtering with compress `/`

`mask/data` keeps the items where the mask is 1:

```apl
      1 0 1 0 1/'abcde'
ace
      (v>5)/v
8 9 7
      (0=2|v)/v
8 4 2
```

The second line is "items greater than 5". The third is "even items". A
dfn makes filters reusable:

```apl
      Evens←{(0=2|⍵)/⍵}
      Evens ⍳20
2 4 6 8 10 12 14 16 18 20
```

## Where `⍸`

`⍸` gives the **positions** of the 1s:

```apl
      ⍸v>5
2 4 6
      ⍸'banana'='a'
2 4 6
```

## Membership `∊`

`x∊y` asks "is each item of x found in y?":

```apl
      3 5 7∊1 2 3 4 5
1 1 0
      'hello world'∊'aeiou'
0 1 0 0 1 0 0 1 0 0 0
      +/'hello world'∊'aeiou'
3
```

The last line counts the vowels.

## Index of `⍳` (dyadic)

`y⍳x` gives the position of each `x` in `y`. Something not found gives
`1+≢y`:

```apl
      'abcde'⍳'dab'
4 1 2
      10 20 30⍳20 99
2 4
```

## Unique `∪`, intersection `∩`

```apl
      ∪3 1 3 2 1
3 1 2
      1 2 3 4∩3 4 5
3 4
      1 2 3∪3 4 5
1 2 3 4 5
```

## If-then-else without `if`

Choose between two values using a boolean as an index:

```apl
      'no' 'yes'[1+5>3]
┌───┐
│yes│
└───┘
```

Or apply a different result per element:

```apl
      x←¯3 5 ¯1 4
      x×x>0
0 5 0 4
```

That keeps the positive values and turns the negative ones into 0.

## Exercises

1. How many numbers from 1 to 100 are divisible by 7?
2. Keep only the odd numbers in `⍳15`.
3. Positions of the spaces in `'to be or not'`.
4. Remove the vowels from `'programming'`.
5. FizzBuzz check: which numbers from 1 to 30 are divisible by both 3 and 5?

<details><summary>Solutions</summary>

```apl
      +/0=7|⍳100
14
      (2|⍳15)/⍳15
1 3 5 7 9 11 13 15
      ⍸'to be or not'=' '
3 6 9
      s←'programming'
      (~s∊'aeiou')/s
prgrmmng
      n←⍳30
      ((0=3|n)∧0=5|n)/n
15 30
```

</details>

**Next:** [06 · Strings](../06-strings/README.md)
