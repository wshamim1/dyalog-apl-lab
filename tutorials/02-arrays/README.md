# 02 · Arrays

In APL, everything is an array: a single number, a list, a table, or more
dimensions.


## Vectors

Numbers separated by spaces form a *vector* (a list):

```apl
      3 1 4 1 5
3 1 4 1 5
```

## Index generator `⍳`

`⍳n` gives the first `n` integers:

```apl
      ⍳5
1 2 3 4 5
      ⍳0
```

`⍳0` is an empty vector, so it prints a blank line.

## Shape `⍴` and tally `≢`

Monadic `⍴` gives the **shape**, and `≢` gives the **number of items**:

```apl
      v←10 20 30 40
      ⍴v
4
      ≢v
4
      ⍴5
```

A scalar like `5` has an empty shape, so `⍴5` prints a blank line.

## Reshape: `shape ⍴ data`

Dyadic `⍴` builds an array of the given shape, recycling the data as
needed:

```apl
      2 3⍴⍳6
1 2 3
4 5 6
      3 4⍴0
0 0 0 0
0 0 0 0
0 0 0 0
      2 2⍴'ab'
ab
ab
      6⍴1 2
1 2 1 2 1 2
```

A two-dimensional array is a *matrix*:

```apl
      m←3 4⍴⍳12
      m
1  2  3  4
5  6  7  8
9 10 11 12
      ⍴m
3 4
      ≢m
3
```

`≢` counts the **rows** (the first axis).

## Indexing

Use square brackets. Indexing starts at **1**:

```apl
      v←10 20 30 40 50
      v[2]
20
      v[1 3 5]
10 30 50
      v[5 4 3 2 1]
50 40 30 20 10
```

For a matrix, use `[rows;cols]`. Leave a part empty to mean "all":

```apl
      m[2;3]
7
      m[2;]
5 6 7 8
      m[;1]
1 5 9
      m[1 3;2 4]
 2  4
10 12
```

You can also assign through an index:

```apl
      v[2]←99
      v
10 99 30 40 50
```

## Take `↑` and drop `↓`

```apl
      3↑v
10 99 30
      ¯2↑v
40 50
      2↓v
30 40 50
      ¯1↓v
10 99 30 40
      7↑1 2 3
1 2 3 0 0 0 0
```

Taking more than you have pads with zeros (or spaces, for text).

## Catenate `,` and ravel

Dyadic `,` joins arrays. Monadic `,` flattens an array to a vector:

```apl
      1 2 3,4 5
1 2 3 4 5
      0,v
0 10 99 30 40 50
      ,m
1 2 3 4 5 6 7 8 9 10 11 12
```

`⍪` joins along the first axis, adding rows:

```apl
      m⍪100 200 300 400
  1   2   3   4
  5   6   7   8
  9  10  11  12
100 200 300 400
```

## Reverse, rotate, transpose

```apl
      ⌽1 2 3 4 5
5 4 3 2 1
      2⌽1 2 3 4 5
3 4 5 1 2
      ⌽m
 4  3  2 1
 8  7  6 5
12 11 10 9
      ⊖m
9 10 11 12
5  6  7  8
1  2  3  4
      ⍉m
1 5  9
2 6 10
3 7 11
4 8 12
```

`⌽` works along the last axis (reverses each row), and `⊖` along the
first (flips the rows). `⍉` swaps rows and columns.

## Scalar functions work element-wise

Arithmetic applies to whole matrices too:

```apl
      m×10
10  20  30  40
50  60  70  80
90 100 110 120
      m+m
 2  4  6  8
10 12 14 16
18 20 22 24
```

## Exercises

1. Make a 4×4 matrix of the numbers 1 to 16.
2. Take its last column.
3. Get the numbers 10 to 20 using `⍳` (hint: drop, or add).
4. Reverse the order of the rows of your matrix.

<details><summary>Solutions</summary>

```apl
      x←4 4⍴⍳16
      x
 1  2  3  4
 5  6  7  8
 9 10 11 12
13 14 15 16
      x[;4]
4 8 12 16
      9+⍳11
10 11 12 13 14 15 16 17 18 19 20
      9↓⍳20
10 11 12 13 14 15 16 17 18 19 20
      ⊖x
13 14 15 16
 9 10 11 12
 5  6  7  8
 1  2  3  4
```

</details>

**Next:** [03 · Functions](../03-functions/README.md)
