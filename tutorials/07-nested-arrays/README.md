# 07 · Nested arrays

An item of an array can itself be an array. That's how APL represents
lists of words, records, trees and so on.


## Making nested arrays

*Strand* notation (items next to each other) makes a nested vector:

```apl
      (1 2 3)(4 5)
┌─────┬───┐
│1 2 3│4 5│
└─────┴───┘
      'abc' 'de' 'f'
┌───┬──┬─┐
│abc│de│f│
└───┴──┴─┘
      1 (2 3) 'x' 'hello'
┌─┬───┬─┬─────┐
│1│2 3│x│hello│
└─┴───┴─┴─────┘
```

Each box is one item:

```apl
      ≢(1 2 3)(4 5)
2
      ≢¨(1 2 3)(4 5)
3 2
```

## Enclose `⊂` and disclose `⊃`

`⊂` wraps an array into a single scalar item. `⊃` (first) takes the first
item and opens it:

```apl
      ⊂1 2 3
┌─────┐
│1 2 3│
└─────┘
      ≢⊂1 2 3
1
      ⊃(1 2 3)(4 5)
1 2 3
```

Enclose is useful when you want to treat a whole array as **one** thing:

```apl
      (⊂'hello'),'world' 'apl'
┌─────┬─────┬───┐
│hello│world│apl│
└─────┴─────┴───┘
```

## Pick `⊃` (dyadic)

`n⊃array` picks item `n` and opens it. A nested path goes deeper:

```apl
      data←'alice' (30 'london')
      1⊃data
alice
      2⊃data
┌──┬──────┐
│30│london│
└──┴──────┘
      (2 2)⊃data
london
```

## Depth `≡`

Monadic `≡` tells you how deeply nested an array is:

```apl
      ≡5
0
      ≡1 2 3
1
      ≡(1 2)(3 4)
2
      ≡(1 (2 3))(4 5)
¯3
```

A negative depth means the nesting is uneven.

## Each `¨` is your main tool

Since every item is its own array, `¨` lets you work inside each one:

```apl
      names←'ann' 'bob' 'charlotte'
      ≢¨names
3 3 9
      ⌽¨names
┌───┬───┬─────────┐
│nna│bob│ettolrahc│
└───┴───┴─────────┘
      1↑¨names
┌─┬─┬─┐
│a│b│c│
└─┴─┴─┘
```

**A classic gotcha.** To put `'Hi '` in front of each name, you might
write `'Hi ',¨names`. But `'Hi '` is itself a 3-item vector, so `¨` pairs
`'H'`, `'i'` and `' '` with the three names, one each:

```apl
      'Hi ',¨names
┌────┬────┬──────────┐
│Hann│ibob│ charlotte│
└────┴────┴──────────┘
```

Enclose it, so it counts as **one** item that is reused for every name:

```apl
      (⊂'Hi '),¨names
┌──────┬──────┬────────────┐
│Hi ann│Hi bob│Hi charlotte│
└──────┴──────┴────────────┘
```

## Mix `↑` and split `↓`

`↑` turns a nested vector into a matrix, padding as needed. `↓` turns each
row of a matrix into an item:

```apl
      ↑(1 2 3)(4 5)(6)
1 2 3
4 5 0
6 0 0
      ↓3 3⍴⍳9
┌─────┬─────┬─────┐
│1 2 3│4 5 6│7 8 9│
└─────┴─────┴─────┘
```

## Enlist `∊`

`∊` flattens everything into one simple vector:

```apl
      ∊(1 2)(3 (4 5))
1 2 3 4 5
```

## Partition `⊆` and `⊂`

`mask⊆data` keeps the runs where the mask is non-zero, and drops the items
under a 0:

```apl
      1 1 0 1 1 1 0 1⊆'ab cde f'
┌──┬───┬─┐
│ab│cde│f│
└──┴───┴─┘
```

`mask⊂data` starts a new piece at every 1:

```apl
      1 0 0 1 0 1 0 0⊂'abcdefgh'
┌───┬──┬───┐
│abc│de│fgh│
└───┴──┴───┘
```

## Records as nested arrays

A simple "table" of people:

```apl
      people←('ann' 31)('bob' 25)('cy' 40)
      people
┌────────┬────────┬───────┐
│┌───┬──┐│┌───┬──┐│┌──┬──┐│
││ann│31│││bob│25│││cy│40││
│└───┴──┘│└───┴──┘│└──┴──┘│
└────────┴────────┴───────┘
      ⊃¨people
┌───┬───┬──┐
│ann│bob│cy│
└───┴───┴──┘
      2⊃¨people
31 25 40
      (+/2⊃¨people)÷≢people
32
```

That last line is the average age.

## Exercises

1. Make the nested vector `'red' 'green' 'blue'` and find the longest
   word's length.
2. Reverse the order of the words, then reverse each word.
3. From `scores←(90 80)(70 60 50)(100)`, compute each student's total.
4. Join `'a' 'b' 'c'` into the string `'a-b-c'`.

<details><summary>Solutions</summary>

```apl
      c←'red' 'green' 'blue'
      ⌈/≢¨c
5
      ⌽c
┌────┬─────┬───┐
│blue│green│red│
└────┴─────┴───┘
      ⌽¨c
┌───┬─────┬────┐
│der│neerg│eulb│
└───┴─────┴────┘
      scores←(90 80)(70 60 50)(100)
      +/¨scores
170 180 100
      1↓∊'-',¨'a' 'b' 'c'
a-b-c
```

</details>

**Next:** [08 · Trains (tacit programming)](../08-trains/README.md)
