# Dyalog file types

One small example of each kind of Dyalog source file, and how to run it.
Each file holds **one thing**, named after that thing (`Avg.aplf` defines
`Avg`).

| File | Type | What's in it | `dyalog FILE` |
| --- | --- | --- | --- |
| [Avg.aplf](Avg.aplf) | `.aplf` function | a dfn: average of a vector | session with `Avg` loaded |
| [Hello.aplf](Hello.aplf) | `.aplf` function | a tradfn with no arguments | loads it **and runs it** |
| [Twice.aplo](Twice.aplo) | `.aplo` operator | applies a function twice: `(1∘+)Twice 10` → 12 | session with `Twice` loaded |
| [Stats.apln](Stats.apln) | `.apln` namespace | `Mean`, `Median`, `Range`, `SD`, `Summary`, and a `Run` | loads it, then calls `Stats.Run` |
| [Counter.aplc](Counter.aplc) | `.aplc` class | a counter object with a shared `Run` | loads it, then calls `Counter.Run` |
| [Shape.apli](Shape.apli) | `.apli` interface | `Area` and `Name`, which shapes must provide | (load via `shapes.dyapp`) |
| [Square.aplc](Square.aplc), [Circle.aplc](Circle.aplc) | `.aplc` classes | implement `Shape` | (need `Shape` loaded first: use `shapes.dyapp`) |
| [Grid.apla](Grid.apla) | `.apla` array | a 3×3 matrix in array notation | displays the array |
| [People.apla](People.apla) | `.apla` array | a list of namespaces (`name`, `age`, `city`) | displays it, plus its contents as JSON |
| [demo.dyapp](demo.dyapp) | `.dyapp` app | loads `Stats`, `Avg` and `Twice`, then runs two lines | boots the app |
| [shapes.dyapp](shapes.dyapp) | `.dyapp` app | loads the interface, then both classes, then runs a demo | boots the app |
| [make-workspace.apls](make-workspace.apls) | `.apls` script | builds `demo.dws` from the sources | runs it, then exits |
| `demo.dws` | `.dws` workspace | binary, saved by the script above (not committed) | opens it and runs its `⎕LX` |
| [use-all.apls](use-all.apls) | `.apls` script | loads one file of each type and uses it | runs it, then exits |

Tests for these files are in [tests/](tests). Run them with
`dyalog test sample-scripts/file-types`.

## Try it

```sh
dyalog sample-scripts/file-types/use-all.apls        # everything at once
dyalog sample-scripts/file-types/People.apla         # show an array file
dyalog sample-scripts/file-types/Stats.apln          # session; Stats.Run runs first
dyalog sample-scripts/file-types/shapes.dyapp        # interface + classes, in order

dyalog sample-scripts/file-types/make-workspace.apls # build demo.dws…
dyalog sample-scripts/file-types/demo.dws            # …and open it
```

The session types (`.aplf .aplo .apln .aplc .dws .dyapp`) leave you at the
APL prompt afterwards. Exit with `)off`.

## Loading them from your own code

| Type | In a script or function | In the session |
| --- | --- | --- |
| `.aplf`, `.aplo` | `2⎕FIX 'file:///app/…/Avg.aplf'` | `]load /app/…/Avg.aplf` |
| `.apln`, `.aplc`, `.apli` | `⎕FIX 'file:///app/…/Stats.apln'` | `]load /app/…/Stats.apln` |
| `.apla` | read the lines, drop comments, join with `⋄`, then `⍎` (see `Apla` in [use-all.apls](use-all.apls)) | the same |
| `.dws` | | `)load /app/…/demo.dws` |

`2⎕FIX` is for a file holding a single function or operator. Plain `⎕FIX`
is for script-style files (`:Namespace`, `:Class`, `:Interface`).

## Things these examples show

- **Startup entry point:** when a namespace or class is loaded at startup,
  Dyalog calls its `Run` function, which may take no arguments or the
  command-line arguments. For a class, `Run` must be `:Access Public Shared`.
- **Order matters:** a class that implements an interface needs the
  interface loaded first. Loading `Square.aplc` alone fails with "only
  interfaces can be declared after the base class". A `.dyapp` lists the
  files in the right order.
- **`⎕THIS`:** inside a class's shared method, refer to the class as
  `⎕THIS`, not by its name.
- **Array notation:** `( … )` is a list and `[ … ]` is a matrix. So three
  items in `[ ]` make a 3×1 matrix, not a list of three.
- **`.dyapp` paths** are relative to the `.dyapp` file, so it works wherever
  the folder is.
