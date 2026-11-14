# 09 · Sorting and searching

APL doesn't sort directly. It gives you the *order* (a permutation), and
you index with it. That turns out to be more flexible.


## Grade up `⍋` and grade down `⍒`

`⍋` returns the indices that would sort the array ascending:

```apl
      v←30 10 50 20 40
      ⍋v
2 4 1 5 3
      v[⍋v]
10 20 30 40 50
      v[⍒v]
50 40 30 20 10
```

A sort function is one line:

```apl
      sort←{⍵[⍋⍵]}
      sort 3 1 4 1 5 9 2 6
1 1 2 3 4 5 6 9
      sort 'banana'
aaabnn
```

`⍋` works on numbers, text, and even nested arrays such as lists of words.

## Sort one thing by another

The order is a separate value, so you can use it to sort *other* data:

```apl
      names←'cy' 'ann' 'bob'
      ages←40 31 25
      names[⍋ages]
┌───┬───┬──┐
│bob│ann│cy│
└───┴───┴──┘
      names[⍋names]
┌───┬───┬──┐
│ann│bob│cy│
└───┴───┴──┘
      ages[⍋names]
31 25 40
```

## Sort the rows of a matrix

`⍋` on a matrix grades its rows:

```apl
      m←4 2⍴3 1 1 9 2 2 1 4
      m
3 1
1 9
2 2
1 4
      m[⍋m;]
1 4
1 9
2 2
3 1
```

## Top n

```apl
      scores←72 95 61 88 79 90
      3↑scores[⍒scores]
95 90 88
```

## Searching recap

| Expression | Meaning |
| --- | --- |
| `y⍳x` | position of the first `x` in `y` |
| `x∊y` | is `x` in `y`? |
| `⍸mask` | positions where the mask is 1 |
| `x⍷y` | where substring `x` starts in `y` |

```apl
      fruits←'apple' 'kiwi' 'fig'
      fruits⍳⊂'kiwi'
2
      (⊂'fig')∊fruits
1
```

Note the `⊂`. A word is a vector, so you enclose it to search for it as
**one** item.

## Interval index `⍸` (dyadic)

`bins⍸values` finds which interval each value falls into. Grading scores is
a classic use:

```apl
      cutoffs←0 60 70 80 90
      cutoffs⍸55 65 85 92 70
1 2 4 5 3
      'FDCBA'[cutoffs⍸55 65 85 92 70]
FDBAC
```

## Frequency counts with key `⌸`

```apl
      w←'the' 'cat' 'the' 'dog' 'the' 'cat'
      {⍺,≢⍵}⌸w
┌───┬─┐
│the│3│
├───┼─┤
│cat│2│
├───┼─┤
│dog│1│
└───┴─┘
```

Sort that by count, descending:

```apl
      t←{⍺,≢⍵}⌸w
      t[⍒t[;2];]
┌───┬─┐
│the│3│
├───┼─┤
│cat│2│
├───┼─┤
│dog│1│
└───┴─┘
```

## Unique, and removing duplicates

```apl
      ∪w
┌───┬───┬───┐
│the│cat│dog│
└───┴───┴───┘
      ≠w
1 1 0 1 0 0
```

`≠` (unique mask) marks the first time each item appears.

## Exercises

1. Sort `5 2 8 1 9` descending.
2. Find the second-largest number in `4 11 7 9 2`.
3. Sort the words `'pear' 'apple' 'fig'` alphabetically.
4. Count how many times each letter appears in `'hello'`.

<details><summary>Solutions</summary>

```apl
      x←5 2 8 1 9
      x[⍒x]
9 8 5 2 1
      y←4 11 7 9 2
      2⊃y[⍒y]
9
      w←'pear' 'apple' 'fig'
      w[⍋w]
┌─────┬───┬────┐
│apple│fig│pear│
└─────┴───┴────┘
      {⍺,≢⍵}⌸'hello'
h 1
e 1
l 2
o 1
```

</details>

**Next:** [10 · Workspaces and files](../10-workspaces-files/README.md)
