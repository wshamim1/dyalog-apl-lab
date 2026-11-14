# 08 · Trains (tacit programming)

A *train* is a function made by placing functions side by side, with no
`⍵` or `⍺`. It's also called *tacit* or *point-free* style.


## The fork: `(f g h)`

Three functions in parentheses make a **fork**:

```
(f g h) ⍵   ≡   (f ⍵) g (h ⍵)
```

The classic example is the average, "sum divided by count":

```apl
      avg←+/÷≢
      avg 1 2 3 4 10
4
```

`(+/ ÷ ≢) ⍵` is `(+/⍵) ÷ (≢⍵)`. Compare it with the dfn `{(+/⍵)÷≢⍵}`.

More forks:

```apl
      range←⌈/-⌊/
      range 3 9 2 7
7
      (⊢,⌽) 1 2 3
1 2 3 3 2 1
```

`range` is max minus min. `(⊢,⌽)` is the argument followed by its reverse.
`⊢` (right tack) returns its argument unchanged, which is very useful in
trains.

## Dyadic forks

With two arguments, each outer function gets both:

```
⍺ (f g h) ⍵   ≡   (⍺ f ⍵) g (⍺ h ⍵)
```

```apl
      3 (+,-) 1
4 2
      5 (⌈-⌊) 2
3
```

## The atop: `(g h)`

Two functions make an **atop**: apply `h`, then `g`:

```
(g h) ⍵   ≡   g (h ⍵)
⍺ (g h) ⍵ ≡   g (⍺ h ⍵)
```

```apl
      (-+/) 1 2 3
¯6
      (⌽⍳) 5
5 4 3 2 1
      (≢∪) 1 2 2 3 3 3
3
      1 2 3 (⌽,) 4 5
5 4 3 2 1
```

- `(-+/)` is the negated sum.
- `(⌽⍳)` counts down.
- `(≢∪)` counts the unique items.
- `⍺ (⌽,) ⍵` joins the arguments, then reverses the result.

## Using constants

A number on the left of a fork acts as a constant:

```apl
      (1+⊢) 1 2 3
2 3 4
      (2×⊢) 1 2 3
2 4 6
```

## Longer trains

Longer trains group from the right in threes: `(a b c d e)` is
`(a b (c d e))`.

```apl
      (⊢-+/÷≢) 1 2 3 4 10
¯3 ¯2 ¯1 0 6
```

That's `⊢ - (+/÷≢)`: each value minus the average.

A train is a function like any other, so it works with operators:

```apl
      (+/÷≢)¨(1 2 3)(4 5 6 7)
2 5.5
```

## Splitting with a train

A very common idiom: split on a separator:

```apl
      split←≠⊆⊢
      ' ' split 'the cat sat'
┌───┬───┬───┐
│the│cat│sat│
└───┴───┴───┘
      ',' split 'a,b,,c'
┌─┬─┬─┐
│a│b│c│
└─┴─┴─┘
```

`⍺ (≠⊆⊢) ⍵` is `(⍺≠⍵)⊆⍵`.

## When to use trains

- Use them for short, reusable "verbs" like `avg`, `range` and `split`.
- If a train gets hard to read, use a dfn instead. Clarity wins.
- To see how a train is parsed, display it with `]box on -trains=tree`:

```apl
      ]box on -trains=tree
Was ON -trains=box
      +/÷≢
  ┌─┼─┐
  / ÷ ≢
┌─┘
+
```

## Exercises

1. Write a train `sq` that squares (hint: `×⍨` or `⊢×⊢`).
2. Write a train that gives the first and last items of a vector.
3. Write `norm` that divides a vector by its sum.
4. Write `isPal` that checks if a string is a palindrome.

<details><summary>Solutions</summary>

```apl
      sq←⊢×⊢
      sq 1 2 3
1 4 9
      firstLast←⊃,⊢/
      firstLast 5 6 7 8
5 8
      norm←⊢÷+/
      norm 1 1 2
0.25 0.25 0.5
      isPal←⊢≡⌽
      isPal 'level'
1
      isPal 'apl'
0
```

`⊢/` reduces with "right", so it returns the last item.

</details>

**Next:** [09 · Sorting and searching](../09-sorting-searching/README.md)
