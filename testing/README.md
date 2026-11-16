# Testing APL code

A small test framework for Dyalog APL: write `*_test.aplf` files, then run
`dyalog test`.

```
$ dyalog test

/app/testing/examples/
  ✅ Vowels_test  (6 checks)

/app/tutorials/03-functions/tests/
  ✅ Fact_test  (5 checks)
  ✅ Hyp_test  (4 checks)
  ✅ Mean_test  (4 checks)
...
14 tests: 14 passed, 0 failed, 0 errors  (0.168 s)
```

## Write a test

Put the test **next to the code**, or in a **`tests/` subfolder** (the code
is then loaded from the folder above). Name it `Something_test.aplf`:

```
my-code/
  Vowels.aplf
  Vowels_test.aplf        ← next to the code
  tests/
    More_test.aplf        ← or in tests/ (code comes from my-code/)
```

Note that `]load folder/*.aplf` also loads matching files from subfolders,
so it loads the tests in `tests/` too. That's harmless: they're just extra
functions in the workspace.

A test is a function with no arguments that makes some checks:

```apl
 Vowels_test
 3 ExpectEq Vowels 'Hello World'      ⍝ expected ExpectEq actual
 0 ExpectEq Vowels ''
 ExpectTrue 0≤Vowels 'xyz'
 11 ExpectError 'Vowels 42'           ⍝ must raise DOMAIN ERROR (11)
```

A dfn works too: `Vowels_test←{3 ExpectEq Vowels 'Hello World'}`.

The [shared library](../lib/README.md) `Lib` is loaded before your code, so
both can call `Lib.Str.Trim` and friends without loading anything.

See [examples/](examples) for a complete example.

## Assertions

| Assertion | Passes when | Example |
| --- | --- | --- |
| `expected ExpectEq actual` | they match exactly (`≡`): same values, shape and type | `120 ExpectEq Fact 5` |
| `ExpectTrue b` | `b` is all 1s | `ExpectTrue 0<Mean x` |
| `ExpectFalse b` | `b` is all 0s | `ExpectFalse 0∊x` |
| `expected ExpectNear actual` | numbers are equal to within 1e¯6 (for floating point) | `3.14159265 ExpectNear ○1` |
| `errnum ExpectError 'expr'` | evaluating `expr` raises that error (`0` or no left argument means any error) | `5 ExpectError '1 2+1 2 3'` |
| `Fail 'message'` | never: records your own failure message | `:If x>10 ⋄ Fail 'too big' ⋄ :EndIf` |

Common error numbers: 2 SYNTAX, 3 INDEX, 4 RANK, 5 LENGTH, 6 VALUE, 11 DOMAIN.

- **A failing check doesn't stop the test.** All failures are listed.
- **Each assertion returns a shy 1 or 0,** so you can write
  `:If ~5 ExpectEq x ⋄ … ⋄ :EndIf`.
- **The expression in `ExpectError`** runs in the test, so it can use the
  test's local variables. It must produce a value.

## What a failure looks like

```
/app/lib/tests/
  ❌ Fails_test
       Fails_test[1]: expected 6, got 5
       Fails_test[2]: expected 5, got 5  (shape ⍬ (scalar) vs 1, depth 0 vs 1)
       Fails_test[3]: expected 'abc', got 'abd'
       Fails_test[4]: expected [1 2 ⋄ 3 4], got [1 2 ⋄ 3 5]
       Fails_test[7]: expected error 11 from: 1 2 Add 1 2 3, got LENGTH ERROR
  💥 Boom_test
       LENGTH ERROR: Mismatched left and right argument shapes  at Boom_test[2] x←1 2+1 2 3

3 tests: 1 passed, 1 failed, 1 errors  (0.02 s)
```

- ✅ passed
- ❌ an assertion failed, with the test name, line, expected and actual
- 💥 the test hit an unexpected APL error

Values that *look* the same but aren't (like `5` and `,5`) get their shapes
spelled out.

## Run tests

```sh
dyalog test                              # everything under the current folder
dyalog test tutorials/03-functions       # one folder (searched recursively)
dyalog test path/to/Vowels_test.aplf     # one test file
```

`dyalog test` exits with **0** if everything passed, **1** if anything failed
or errored, and **2** if the runner itself had a problem. So it works in
scripts and CI:

```sh
dyalog test && echo "all good"
```

From an APL session (terminal or RIDE):

```apl
      ]load /app/testing/Tester.apln
      Tester.Run '/app/testing/examples'        ⍝ prints the report, returns 0 or 1
```

## How it works

For each test file, [Tester.apln](Tester.apln):

1. **Creates a fresh namespace,** so tests don't affect each other.
2. **Copies in the assertions** (`ExpectEq` and the rest).
3. **Loads the code in the folder** (or the parent folder, for a `tests/`
   folder) in dependency order: interfaces (`.apli`), namespaces
   (`.apln`), classes (`.aplc`), then functions and operators (`.aplf`,
   `.aplo`). If one fails (a class whose interface hasn't loaded yet, say),
   it's retried after the others. `.apla` files become variables named
   after the file.
4. **Loads and calls the test,** and collects any failures.

Folders named `node_modules`, `.venv`, `__pycache__`, or starting with `.`
are skipped.

| File | Purpose |
| --- | --- |
| [Tester.apln](Tester.apln) | the framework: `Tester.Run`, the assertions, discovery and loading |
| [run-tests.apls](run-tests.apls) | the script `dyalog test` runs |
| [examples/](examples) | `Vowels.aplf` and its test |

## Tests in this repo

| Folder | Tests |
| --- | --- |
| [tutorials/03-functions/tests](../tutorials/03-functions/tests) | `Fact`, `Hyp`, `Mean` |
| [tutorials/11-tradfns-and-control/tests](../tutorials/11-tradfns-and-control/tests) | `Grade`, `Collatz`, `Stats`, `SafeDiv` |
| [sample-scripts/file-types/tests](../sample-scripts/file-types/tests) | a function, an operator, a namespace, classes with an interface, a class, `.apla` data |
| [examples](examples) | `Vowels` |

**Something the tests caught while writing them:** `Mean ⍬` isn't an error.
`(+/⍬)÷≢⍬` is `0÷0`, which APL defines as 1. `Mean_test` now pins that
down.
