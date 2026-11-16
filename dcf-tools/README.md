# Component file viewer and diff

Look inside Dyalog component files (`.dcf`) and see exactly what changed
between two versions: which component, which field, which cell, old value
and new value. You don't need to know APL to use it.

```
$ python3 dcf-tools/dcf.py diff dcf-tools/demo/before dcf-tools/demo/after
customers.dcf
  #   1  changed  char vector
       'Customer master · version 1' → 'Customer master · version 2'
  #   5  changed  nested vector
       [3] 'Berlin' → 'Hamburg'
       [4] 5000 → 7500
  #  13  added    nested vector  (11 'Nia' 'Nairobi' 3000 '2025-03-14')
  10 same, 2 changed, 1 added, 0 removed
orders.dcf
  #   3  changed  namespace
       lines:
         [1;2] 4 → 6
       status: 'open' → 'shipped'
       + shipped: '2026-02-03'
  #   7  changed  namespace
       lines:
         + from [4]: 1 3⍴('Gadget' 1 19.99)
  #  25  removed  namespace  ns(customer date id lines status)
  22 same, 2 changed, 0 added, 1 removed
settings.dcf
  #   1  changed  nested matrix
       [2;2] 0.2 → 0.25
  …
```

## Why

Component files are binary, so the usual tools don't help:

- **git** can't show what changed in a `.dcf`, only that it changed.
- **Python and other languages** can't read them at all: it's Dyalog's own
  format.
- **People who don't know APL** (operations, auditors, data teams) can't
  look inside without someone writing APL for them.

Typical questions this answers: what did last night's batch change? Is the
test copy the same as production? What's actually in component 57?

## Run it

From the repo folder. It uses the `dyalog` container
([install/dyalog](../install/dyalog/README.md)); files can be anywhere on your
Mac.

```sh
dyalog dcf-tools/make-demo.apls                     # once: demo/before and demo/after

python3 dcf-tools/dcf.py view  FILE.dcf             # list the components
python3 dcf-tools/dcf.py view  FILE.dcf 5           # component 5 in full
python3 dcf-tools/dcf.py diff  OLD.dcf NEW.dcf      # two files
python3 dcf-tools/dcf.py diff  OLD_DIR NEW_DIR      # every .dcf in two folders, by name
python3 dcf-tools/dcf.py snapshot FOLDER            # save a copy of FOLDER's .dcf files…
python3 dcf-tools/dcf.py changes  FOLDER            # …and later: what changed since then
python3 dcf-tools/dcf.py dump  FILE.dcf             # everything, as JSON
python3 dcf-tools/dcf.py ddl   FILE.dcf|FOLDER --dialect mysql   # suggested SQL tables

dyalog test dcf-tools                               # the tests
```

`diff` and `changes` exit with **0** when nothing changed and **1** when
something did, so they work in scripts and CI. With a native Dyalog (an Apple
Silicon Mac, or Linux), set `DYALOGSCRIPT=/path/to/dyalogscript` and the
container isn't used.

### In the browser

```sh
.venv/bin/streamlit run dcf-tools/dcf_app.py        # http://localhost:8501
```

- **View:** pick a folder (or upload `.dcf` files), choose a file, and see
  every component: kind, shape, size, when it was written, and a preview.
  Click a row to see the component in full: namespaces as fields, matrices
  as grids, records as tables.
- **Compare:** two files, two folders, or *since a snapshot* (with a
  **Take snapshot now** button). Each changed component lists where, old and
  new. Download the diff as JSON.
- **SQL tables:** suggested `CREATE TABLE` statements for the chosen files, in
  SQLite, MySQL, PostgreSQL or SQL Server, with a table explaining where each
  one comes from. Download as `.sql`.

## Suggested SQL tables (DDL)

Moving component-file data into a database starts with designing the tables.
`ddl` drafts them from what the files actually hold:

```sh
python3 dcf-tools/dcf.py ddl sample-scripts/component-files/data --dialect mysql -o tables.sql
```

```sql
-- orders: orders.dcf components 1–25: one namespace each (25 rows now)
CREATE TABLE orders (
  id INT NOT NULL,
  dcf_component INT NOT NULL,    -- component number in orders.dcf
  customer INT NOT NULL,
  `date` DATE NOT NULL,
  status VARCHAR(10) NOT NULL,
  PRIMARY KEY (id)
) DEFAULT CHARSET=utf8mb4;

-- orders_lines: the 'lines' matrix inside each namespace (3 columns): one row per matrix row
CREATE TABLE orders_lines (
  orders_id INT NOT NULL,        -- the orders row it belongs to
  line_no INT NOT NULL,
  col1 VARCHAR(10) NOT NULL,     -- rename: the data doesn't name it
  col2 INT NOT NULL,
  col3 DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (orders_id, line_no),
  FOREIGN KEY (orders_id) REFERENCES orders (id)
) DEFAULT CHARSET=utf8mb4;
```

| What's in the file | Becomes |
| --- | --- |
| a namespace per component (`orders.dcf`) | one table, a column per field; a matrix field becomes a child table with a foreign key |
| a component of field names, then records (`customers.dcf`) | one table with those column names |
| a 2-column matrix with text keys | a key / value table |
| a numeric or boolean matrix | rows of `(row_no, col_no, value)` |
| a numeric or boolean vector | rows of `(position, value)` |
| anything else (headers, loose text) | `<file>_other`, each component kept whole as JSON, so nothing is lost |

- **Types come from the values:** whole numbers → `INTEGER` (or `BIGINT` when
  large), decimals → `DECIMAL(p,s)` sized to fit, `YYYY-MM-DD` → `DATE`, text →
  `VARCHAR(n)`, nested values → `JSON`. A field missing from some components
  makes a nullable column.
- **Keys:** a unique `id` field becomes the primary key; otherwise the
  component number does. Every table built from components keeps
  `dcf_component`, because other data or code may refer to "component 57".
- **Reserved words** (`date`, `key`, `value`…) are quoted the way each
  database expects.
- **It's a draft.** Rename the generic columns (`col1`…), check the types
  against what the application really allows, and add indexes. Types are
  inferred from the data present now: a column that's always whole numbers
  today might not be tomorrow.

The output was checked by creating the tables in SQLite, MySQL 8.4 and
PostgreSQL 16. SQL Server output follows its syntax (`[date]`, `NVARCHAR`,
`BIT`) but wasn't run against a server.

## How it works

```
dcf.py / dcf_app.py ──► container: dyalogscript dcf.apls ──► DCF.apln
   (paths, snapshots,      your folders mounted read-only      reads with ⎕FSTIE,
    the web page)                                              compares, writes JSON
```

- **APL does the reading.** [DCF.apln](DCF.apln) ties files with `⎕FSTIE`
  (a shared tie, so other users aren't locked out) and never calls
  `⎕FAPPEND`, `⎕FREPLACE` or `⎕FHOLD`. The container also mounts your folders
  read-only.
- **Components are matched by number** (component 5 against component 5).
  Equality is APL's own `≡`, plus one addition: namespaces are compared by
  their contents, because `≡` only says whether two references are the same
  namespace.
- **Differences are explained at the right level:**

  | Both values are | You see |
  | --- | --- |
  | namespaces | fields added, removed and changed (recursively) |
  | vectors | the items that changed, and items added or removed at the end |
  | matrices with the same columns | the cells that changed (`[2;5]`), and rows added or removed |
  | text, or anything else | old → new |

  Positions count from 1, as in APL with `⎕IO←1`.
- **Big values are previewed, not dumped:** 200 items or rows, 50 columns,
  2,000 characters of text. Counts are always exact (e.g. "… and 3,412 more").
  The limits are variables at the top of `DCF.apln`.
- **Values JSON can't hold** (complex numbers, functions inside namespaces)
  are converted: complex numbers become text, and functions are listed by
  name.

### Snapshots

`snapshot FOLDER` copies the folder's `.dcf` files to
`FOLDER/.dcf-snapshots/<date_time>/`. `changes FOLDER` compares the latest
snapshot with the files now (`--since NAME` picks another one). Take
snapshots when nothing is writing, or a copy may catch a write half-way. For
a busy system, snapshot from a backup instead.

## Using it from APL

```apl
      ]load /app/dcf-tools/DCF.apln
      r←DCF.DiffFiles '/app/old/orders' '/app/new/orders'
      r.(same changed added removed)
22 2 0 1
      ↑DCF.Report r
      (DCF.Dump '/app/new/orders').count
24
```

## Limits

- **Matching is by component number.** If components were inserted or
  removed in the middle, everything after shifts and shows as changed.
  Matching by a key field (e.g. customer id) would fix that; it isn't
  implemented yet.
- **Top-level folder only:** `diff OLD_DIR NEW_DIR` and snapshots look at
  `*.dcf` directly in the folder, not in subfolders.
- **Each run starts a container** (about a second), so the viewer caches
  what it has read, by file time and size.

## Files

| File | Purpose |
| --- | --- |
| [DCF.apln](DCF.apln) | the core: `Kind`, `Same`, `Dump`, `DiffFiles`, `DiffFolders`, `Report` |
| [dcf.apls](dcf.apls) | command line inside the container: `view`, `diff`, `dump`, `diffjson` |
| [dcf.py](dcf.py) | command line on your Mac: mounts paths, adds `snapshot` and `changes` |
| [ddl.py](ddl.py) | suggested SQL tables: recognises layouts, infers types, writes DDL in 4 dialects |
| [dcf_app.py](dcf_app.py) | the Streamlit viewer |
| [make-demo.apls](make-demo.apls) | builds `demo/before` and `demo/after` from the sample data |
| [tests/DCF_test.aplf](tests/DCF_test.aplf) | 24 checks: kinds, deep equality, diffs, JSON |
