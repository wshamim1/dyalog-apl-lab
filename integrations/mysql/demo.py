"""Demo: analyse a MySQL sales table with APL and write the results back.

1. Creates database `apl_demo` with a `sales` table (sample data) if needed.
2. Loads the table into APL.
3. Runs a few APL analyses (totals per region, top products, running totals).
4. Saves two summaries back to MySQL and reads them with SQL.

Settings come from environment variables (defaults in brackets):

    MYSQL_HOST [127.0.0.1]  MYSQL_PORT [3307]  MYSQL_USER [root]
    MYSQL_PASSWORD [required]  MYSQL_DATABASE [apl_demo]
    DYALOG_HOST [localhost]  DYALOG_PORT [4502]
    APL_EXCHANGE [unset]  optional "host_dir:container_dir" shared folder
                          for fast bulk transfer (see README)

Run:
    install/dyalog/podman.sh ride                       # terminal 1
    MYSQL_PASSWORD=... .venv/bin/python integrations/mysql/demo.py
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import pymysql

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "dyalog_ride"))
from apl_mysql import AplMySQL, AplError  # noqa: E402
from dyalog_client import DyalogClient, DyalogError  # noqa: E402

REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Widget", "Gadget", "Doohickey", "Gizmo", "Thingamajig"]


def seed(conn, db: str) -> None:
    """Create the demo database and a deterministic sales table."""
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}`")
        cur.execute(f"USE `{db}`")
        cur.execute("""CREATE TABLE IF NOT EXISTS sales (
                         id INT AUTO_INCREMENT PRIMARY KEY,
                         sale_date DATE NOT NULL,
                         region VARCHAR(20) NOT NULL,
                         product VARCHAR(30) NOT NULL,
                         qty INT NOT NULL,
                         price DECIMAL(8,2) NOT NULL)""")
        cur.execute("SELECT COUNT(*) FROM sales")
        if cur.fetchone()[0] == 0:
            rng = random.Random(42)
            rows = [(f"2026-{m:02d}-{rng.randint(1, 28):02d}", rng.choice(REGIONS),
                     rng.choice(PRODUCTS), rng.randint(1, 20),
                     rng.choice([4.99, 9.99, 14.5, 19.99, 49.0]))
                    for m in range(1, 7) for _ in range(10)]
            cur.executemany("INSERT INTO sales (sale_date, region, product, qty, price)"
                            " VALUES (%s, %s, %s, %s, %s)", rows)
            print(f"Seeded {len(rows)} rows into {db}.sales")
    conn.commit()


def show(title: str, text: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 60 - len(title)))
    print(text)


def main() -> int:
    password = os.environ.get("MYSQL_PASSWORD")
    if password is None:
        print("Set MYSQL_PASSWORD (and MYSQL_PORT etc. if not the defaults).",
              file=sys.stderr)
        return 2
    db = os.environ.get("MYSQL_DATABASE", "apl_demo")

    conn = pymysql.connect(host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
                           port=int(os.environ.get("MYSQL_PORT", 3307)),
                           user=os.environ.get("MYSQL_USER", "root"),
                           password=password, charset="utf8mb4")
    seed(conn, db)

    try:
        apl = DyalogClient(os.environ.get("DYALOG_HOST", "localhost"),
                           int(os.environ.get("DYALOG_PORT", 4502))).connect()
    except DyalogError as e:
        print(e, file=sys.stderr)
        return 2

    # Optional fast path: "host_dir:container_dir", a folder both can see.
    exchange = os.environ.get("APL_EXCHANGE")
    exchange = tuple(exchange.split(":", 1)) if exchange else None

    with apl:
        b = AplMySQL(apl, conn, exchange=exchange)
        b.run("]box on")

        # 1. MySQL → APL ------------------------------------------------------
        n = b.load("s", "SELECT sale_date, region, product, qty, price, "
                        "qty*price AS amount FROM sales ORDER BY sale_date")
        show(f"Loaded {n} rows into APL namespace s", b.run("s.columns"))

        # 2. APL analysis ------------------------------------------------------
        show("Total revenue  (+/s.amount)", b.run("+/s.amount"))

        show("Orders and revenue per region  (⌸ key)", b.run(
            "byRegion←s.region{⍺,(≢⍵),+/⍵}⌸s.amount\nbyRegion"))

        show("Top 3 products by quantity  (⍒ grade down)", b.run(
            "q←s.product{⍺,+/⍵}⌸s.qty\n3↑q[⍒q[;2];]"))

        b.run("s.month←7↑¨s.sale_date")          # '2026-03-14' → '2026-03'
        show("Revenue per month with running total  (+\\ scan)", b.run(
            "m←s.month{⍺,+/⍵}⌸s.amount\nm,+\\m[;2]"))

        show("Sales over 200  (compress /)", b.run(
            "big←s.amount>200\n(+/big),' of ',(≢big)"))

        # 3. APL → MySQL -------------------------------------------------------
        b.run("Cents←{(⌊0.5+100×⍵)÷100}")            # round to 2 decimals
        b.run("r←⎕NS ⍬ ⋄ r.(region orders revenue)←↓⍉byRegion")
        b.run("r.revenue←Cents r.revenue")
        n1 = b.save("region_summary", "r")

        b.run("mm←⎕NS ⍬ ⋄ mm.(month revenue)←↓⍉m")
        b.run("mm.running←Cents +\\mm.revenue ⋄ mm.revenue←Cents mm.revenue")
        n2 = b.save("monthly_revenue", "mm")

        show(f"Saved region_summary ({n1} rows) — read back with SQL", "")
        for row in b.query(f"SELECT * FROM `{db}`.region_summary ORDER BY revenue DESC"):
            print(row)
        show(f"Saved monthly_revenue ({n2} rows) — read back with SQL", "")
        for row in b.query(f"SELECT * FROM `{db}`.monthly_revenue ORDER BY month"):
            print(row)
    conn.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AplError as e:
        print(f"APL error:\n{e}", file=sys.stderr)
        sys.exit(1)
