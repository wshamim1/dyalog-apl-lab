# Component files (.dcf)

Dyalog's own data files, with sample data, and a working version of the
migration path in `migration.md`: inventory, export, load into a SQL database,
verify, and a data-access layer.

## What component files are

A component file (`.dcf`) is a numbered list of **APL arrays** on disk.
Component 1, 2, 3 and so on can each hold anything: text, a matrix, a nested
record, even a whole namespace. Many older APL systems keep all their data
this way.

| Function | Does |
| --- | --- |
| `t←'name' ⎕FCREATE 0` | create a file, and get a tie number `t` |
| `t←'name' ⎕FTIE 0` | open (tie) an existing file |
| `n←array ⎕FAPPEND t` | add a component; returns its number |
| `⎕FREAD t n` | read component `n` |
| `array ⎕FREPLACE t n` | overwrite component `n` |
| `⎕FSIZE t` | first component, next component, bytes used, size limit |
| `⎕FRDCI t n` | size, user and time of the last write to component `n` |
| `⎕FHOLD t` / `⎕FHOLD ⍬` | lock the file / release it (for safe writing) |
| `⎕FUNTIE t` | close the file |

## The sample data

[make-data.apls](make-data.apls) creates three files in [data/](data), in
styles real legacy systems use:

| File | Components | Style |
| --- | --- | --- |
| `customers.dcf` | 12 | 1 = header text, 2 = field names, 3–12 = one record each `(id name city credit_limit joined)` |
| `orders.dcf` | 25 | one order per component, stored as a **namespace** with a nested matrix of line items |
| `settings.dcf` | 3 | a key/value table, a 3×12 numeric matrix, 100 boolean flags |

## Run it

From the repo folder, in order:

```sh
dyalog sample-scripts/component-files/make-data.apls      # (re)create data/*.dcf
dyalog sample-scripts/component-files/read-data.apls      # a tour of reading them
dyalog sample-scripts/component-files/inventory.apls      # 1. what's in every component
dyalog sample-scripts/component-files/export-json.apls    # 2. export to JSON lines
python3 sample-scripts/component-files/load-sqlite.py     # 3–4. load into SQLite, verify
dyalog sample-scripts/component-files/use-store.apls      # 5. the data-access layer
dyalog test sample-scripts/component-files                #    its tests
```

## The migration path, step by step

### 1. Inventory: what's in there?

```
 file       comp  kind          bytes  JSON ok
 customers     1  text            160  yes
 customers     3  nested 5        280  yes
 orders        1  namespace      2592  yes
 settings      2  numeric 3 12    208  yes
 settings      3  boolean 100     144  yes
40 components in 3 files
```

The **kind** decides the database design: records become tables, namespaces
become tables (or JSON columns), and matrices become tables. **JSON ok** flags
anything `⎕JSON` can't export. Notice that 100 booleans take only 144 bytes:
APL stores them as bits, while most databases use a byte or more each.

### 2. Export: APL writes JSON

Python can't read `.dcf` files (it's Dyalog's own binary format), so APL does
the export, one JSON line per component:

```json
{"component":3,"file":"customers","value":[3,"Zoë","Berlin",5000,"2024-04-22"]}
{"component":1,"file":"orders","value":{"customer":8,"date":"2026-01-12","id":1001,"lines":[["Gizmo",2,49],["Doohickey",3,14.5]],"status":"paid"}}
```

It also writes `export/checks.json`: counts and totals computed in APL from
the original files.

### 3–4. Load into SQL, then verify

[load-sqlite.py](load-sqlite.py) (Python's standard library only) builds
`export/components.db` in both layouts from `migration.md`:

- **Proper tables:** `customers`, `orders` and `order_lines` (normalised
  from the nested line items), `settings`, `monthly_sales`
- **A raw `components` table:** every component as JSON, so nothing is lost

Then it compares the database with the APL totals:

```
  ✅ credit_total  APL 30000     database 30000
  ✅ customers     APL 10        database 10
  ✅ order_lines   APL 50        database 50
  ✅ order_value   APL 5858.9    database 5858.9
  ✅ orders        APL 25        database 25
  ✅ unicode      ['Zoë', 'José']
```

SQLite keeps the example self-contained. For SQL Server or MySQL, the same
code works with their Python drivers (`pyodbc`, `mysql-connector`), changing
only the connection and a few column types.

### 5. Repoint the code: a data-access layer

[Store.apln](Store.apln) is the layer the rest of an application calls,
instead of `⎕FREAD`:

```apl
      Store.Open '/app/sample-scripts/component-files/data'
      (Store.Customer 3).name
Zoë
      (Store.OrdersFor 8).id
1001 1011 1021
```

Callers get namespaces and never see files or component numbers. To move to
SQL, rewrite only `Store`'s function bodies (with SQAPL, like
[integrations/mysql/apl](../../integrations/mysql/apl/README.md)). Everything
that calls `Store` keeps working. `AddOrder` uses `⎕FHOLD` to lock the file
while writing; in SQL that becomes a transaction.

## Files

| File | Purpose |
| --- | --- |
| [make-data.apls](make-data.apls) | creates the sample `data/*.dcf` files |
| [read-data.apls](read-data.apls) | a tour of `⎕FTIE`, `⎕FREAD`, `⎕FSIZE`, `⎕FRDCI` |
| [inventory.apls](inventory.apls) | step 1: kind, size and JSON-safety of every component |
| [export-json.apls](export-json.apls) | step 2: JSON lines + checks, in `export/` |
| [load-sqlite.py](load-sqlite.py) | steps 3–4: load into SQLite, compare with the APL totals |
| [Store.apln](Store.apln), [use-store.apls](use-store.apls) | step 5: the data-access layer and a demo |
| [tests/Store_test.aplf](tests/Store_test.aplf) | tests for `Store` (on its own files in `/tmp`) |
| `data/` | the sample `.dcf` files (small binaries, committed) |
| `export/` | output of steps 2–4 (git-ignored) |
