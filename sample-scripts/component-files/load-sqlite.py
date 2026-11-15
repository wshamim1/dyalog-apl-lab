"""Migration steps 3–4: load the exported components into a database, then verify.

    python3 sample-scripts/component-files/load-sqlite.py

Reads export/*.jsonl (written by export-json.apls) and builds
export/components.db, a SQLite database (Python's standard library, no server).
The same code works for SQL Server or MySQL with their Python drivers.

Two layouts, as in migration.md:
  * proper tables for tabular data: customers, orders, order_lines, settings,
    monthly_sales
  * a raw table keeping every component as JSON (nothing lost, even nested data)

Then it checks the database against export/checks.json, the counts and totals
APL computed from the original files. Exits with 1 if anything differs.
"""

import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORT = HERE / "export"
DB = EXPORT / "components.db"


def read_jsonl(name):
    with open(EXPORT / f"{name}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    if not (EXPORT / "checks.json").exists():
        sys.exit("Run export-json.apls first: dyalog sample-scripts/component-files/export-json.apls")
    DB.unlink(missing_ok=True)
    db = sqlite3.connect(DB)

    # Raw layout: every component, as JSON, keyed by file + component number
    db.execute("CREATE TABLE components (file TEXT, component INTEGER, value_json TEXT, "
               "PRIMARY KEY (file, component))")
    for name in ("customers", "orders", "settings"):
        for c in read_jsonl(name):
            db.execute("INSERT INTO components VALUES (?, ?, ?)",
                       (c["file"], c["component"], json.dumps(c["value"], ensure_ascii=False)))

    # customers.dcf: component 1 = header, 2 = field names, 3+ = one record each
    cust = {c["component"]: c["value"] for c in read_jsonl("customers")}
    fields = cust[2]
    db.execute(f"CREATE TABLE customers ({', '.join(fields)})")
    db.executemany(f"INSERT INTO customers VALUES ({', '.join('?' * len(fields))})",
                   [cust[n] for n in sorted(cust) if n >= 3])

    # orders.dcf: one namespace per component → orders + order_lines (normalised)
    db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer INTEGER, date TEXT, status TEXT)")
    db.execute("CREATE TABLE order_lines (order_id INTEGER, line_no INTEGER, product TEXT, "
               "qty INTEGER, price REAL)")
    for c in read_jsonl("orders"):
        o = c["value"]
        db.execute("INSERT INTO orders VALUES (?, ?, ?, ?)", (o["id"], o["customer"], o["date"], o["status"]))
        for i, (product, qty, price) in enumerate(o["lines"], 1):
            db.execute("INSERT INTO order_lines VALUES (?, ?, ?, ?, ?)", (o["id"], i, product, qty, price))

    # settings.dcf: 1 = key/value table, 2 = 3×12 sales matrix, 3 = flags
    sett = {c["component"]: c["value"] for c in read_jsonl("settings")}
    db.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value_json TEXT)")
    db.executemany("INSERT INTO settings VALUES (?, ?)",
                   [(k, json.dumps(v, ensure_ascii=False)) for k, v in sett[1]])
    db.execute("CREATE TABLE monthly_sales (year INTEGER, month INTEGER, amount REAL)")
    db.executemany("INSERT INTO monthly_sales VALUES (?, ?, ?)",
                   [(y, m, amt) for y, row in enumerate(sett[2], 1) for m, amt in enumerate(row, 1)])
    db.commit()

    # Verify against the numbers APL computed from the original files
    want = json.load(open(EXPORT / "checks.json"))
    one = lambda sql: db.execute(sql).fetchone()[0]
    got = {
        "customers": one("SELECT COUNT(*) FROM customers"),
        "credit_total": one("SELECT SUM(credit_limit) FROM customers"),
        "orders": one("SELECT COUNT(*) FROM orders"),
        "order_lines": one("SELECT COUNT(*) FROM order_lines"),
        "order_value": round(one("SELECT SUM(qty * price) FROM order_lines"), 2),
    }
    print(f"Loaded {DB.relative_to(HERE.parent.parent)}")
    for table in ("components", "customers", "orders", "order_lines", "settings", "monthly_sales"):
        print(f"  {table:<14} {one(f'SELECT COUNT(*) FROM {table}'):>4} rows")
    print("\nCheck against the APL totals:")
    ok = True
    for key, expected in want.items():
        match = abs(got[key] - expected) < 1e-9
        ok &= match
        print(f"  {'✅' if match else '❌'} {key:<13} APL {expected:<9} database {got[key]}")
    # Unicode survived?
    names = [r[0] for r in db.execute("SELECT name FROM customers WHERE id IN (3, 4) ORDER BY id")]
    print(f"  {'✅' if names == ['Zoë', 'José'] else '❌'} unicode      {names}")
    ok &= names == ["Zoë", "José"]
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
