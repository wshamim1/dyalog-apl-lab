# 06 · Strings

A string is a vector of characters, so everything you've learnt about
vectors applies to text too.


## Character vectors

Use single quotes. Double a quote to include one:

```apl
      'hello'
hello
      ⍴'hello'
5
      'it''s'
it's
```

A single character is a scalar, so `⍴'a'` prints a blank line. To get a
one-character vector, use `,'a'`:

```apl
      ⍴'a'
      ⍴,'a'
1
```

## Strings are just arrays

```apl
      s←'hello world'
      ⌽s
dlrow olleh
      s[1 2 3 4 5]
hello
      5↑s
hello
      s,'!'
hello world!
      ≢s
11
```

## Upper and lower case: `⎕C`

```apl
      1 ⎕C 'hello'
HELLO
      ⎕C 'HeLLo'
hello
```

`1 ⎕C` makes text upper case, and `⎕C` alone makes it lower case.

## Numbers and text: `⍕` and `⍎`

`⍕` (format) turns anything into text. `⍎` (execute) runs text as APL:

```apl
      ⍕42
42
      'Total: ',⍕3×7
Total: 21
      ⍎'2+3'
5
      ⍎'10 20 30'
10 20 30
```

`⎕VFI` parses numbers safely. It returns a validity mask and the values:

```apl
      ⎕VFI '12 abc 3.5'
┌─────┬────────┐
│1 0 1│12 0 3.5│
└─────┴────────┘
```

## Character codes: `⎕UCS`

```apl
      ⎕UCS 'ABC'
65 66 67
      ⎕UCS 72 105
Hi
```

## Splitting

`(separator≠text)⊆text` splits text into pieces:

```apl
      s←'the quick brown fox'
      (' '≠s)⊆s
┌───┬─────┬─────┬───┐
│the│quick│brown│fox│
└───┴─────┴─────┴───┘
      ','(≠⊆⊢)'a,b,c'
┌─┬─┬─┐
│a│b│c│
└─┴─┴─┘
```

The second form is a *train* (tutorial 08). It does the same thing as a
reusable function.

## Joining

Use `∊` (enlist) to flatten, or catenate with a separator:

```apl
      words←'one' 'two' 'three'
      ∊words
onetwothree
      1↓∊' ',¨words
one two three
```

## Searching

```apl
      'or'⍷'hello world, more words'
0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 0 1 0 0 0
      ⍸'or'⍷'hello world, more words'
8 15 20
```

`⍷` (find) marks where a substring **starts**.

## Replace with `⎕R`

`⎕R` uses regular expressions (PCRE):

```apl
      'world' ⎕R 'APL' ⊢'hello world'
hello APL
      '\d+' ⎕R '#' ⊢'room 101, floor 3'
room #, floor #
```

## Matrices of text

`↑` turns a list of strings into a padded character matrix. `↓` turns a
matrix back into a list:

```apl
      ↑'apple' 'fig' 'banana'
apple
fig
banana
      ↓↑'apple' 'fig' 'banana'
┌──────┬──────┬──────┐
│apple │fig   │banana│
└──────┴──────┴──────┘
```

## Exercises

1. Is `'racecar'` a palindrome? (hint: `≡` and `⌽`)
2. Count the words in `'APL is fun to learn'`.
3. Capitalise the first letter of `'dyalog'`.
4. Turn `'1,2,3,4'` into the number vector `1 2 3 4` and sum it.

<details><summary>Solutions</summary>

```apl
      w←'racecar'
      w≡⌽w
1
      s←'APL is fun to learn'
      ≢(' '≠s)⊆s
5
      w←'dyalog'
      (1 ⎕C 1↑w),1↓w
Dyalog
      +/⍎¨(','≠'1,2,3,4')⊆'1,2,3,4'
10
```

</details>

**Next:** [07 · Nested arrays](../07-nested-arrays/README.md)
