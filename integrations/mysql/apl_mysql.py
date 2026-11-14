"""Move data between MySQL and a live Dyalog APL session.

    MySQL ──SQL query──► Python ──⎕JSON──► APL namespace (one vector per column)
                                                  │  your APL code
    MySQL ◄──INSERT──── Python ◄──⎕JSON── APL namespace / vector / matrix

Example:

    import pymysql
    from apl_mysql import AplMySQL
    from dyalog_client import DyalogClient

    with DyalogClient() as apl:
        db = pymysql.connect(host="127.0.0.1", port=3307, user="root",
                             password="...", database="apl_demo")
        bridge = AplMySQL(apl, db)
        bridge.load("sales", "SELECT region, amount FROM sales")   # → APL: sales.region, sales.amount
        print(bridge.run("+/sales.amount"))                         # run APL, get text
        bridge.run("t←sales.region{⍺,(≢⍵),+/⍵}⌸sales.amount")
        bridge.run("r←⎕NS ⍬ ⋄ r.(region orders total)←↓⍉t")
        bridge.save("region_summary", "r")                          # → MySQL table
"""

from __future__ import annotations

import datetime as dt
import decimal
import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dyalog_ride"))
from dyalog_client import DyalogClient  # noqa: E402

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")          # SQL + APL-safe
_APL_NAME = re.compile(r"^[A-Za-z_∆⍙][A-Za-z0-9_∆⍙]*$")   # any APL name
# Max characters of (escaped) JSON per line. Dyalog's session input limit is
# ~750 characters per line (see dyalog_client.MAX_LINE_CHARS).
_CHUNK = 650
_OUT_SLICE = 30000     # characters of JSON fetched per call (< ⎕PW 32767)
_EXPORT = "1(⎕JSON⍠'HighRank' 'Split')"


class AplError(Exception):
    """APL code failed. The message is the APL error text."""


def _check_ident(name: str, what: str) -> str:
    if not _IDENT.match(name):
        raise ValueError(f"Invalid {what} {name!r}: use letters, digits and _ "
                         "(and don't start with a digit)")
    return name


def _to_json_value(v):
    """Convert a MySQL value into something JSON (and so APL) understands."""
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, dt.timedelta):
        return v.total_seconds()
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="replace")
    return v


class AplMySQL:
    """Bridge between a pymysql connection and a DyalogClient session.

    Data travels as JSON. By default it's typed into the session over RIDE
    in ~650-character lines (no setup, but only ~6 KB/s). For bigger data,
    pass exchange=(host_dir, container_dir): a folder both sides can see
    (e.g. mounted into the container read-write). JSON is then written to a
    file there and read with ⎕NGET/⎕NPUT, which is near-instant.
    """

    def __init__(self, apl: DyalogClient, conn,
                 exchange: tuple[str, str] | None = None):
        self.apl = apl
        self.conn = conn
        self.exchange = None
        if exchange:
            host_dir, apl_dir = exchange
            Path(host_dir).mkdir(parents=True, exist_ok=True)
            self.exchange = (Path(host_dir), apl_dir.rstrip("/"))
        self.run("⎕PW←32767")      # so ⎕JSON output is never wrapped

    # ------------------------------------------------------------- APL side
    def run(self, code: str) -> str:
        """Run APL code and return its output. Raises AplError on failure."""
        r = self.apl.execute(code)
        if r.error or r.timed_out or r.awaiting_input:
            raise AplError(r.output or "APL execution failed")
        return r.output

    def get(self, expr: str):
        """Evaluate an APL expression and return it as Python data.

        Namespaces become dicts, vectors become lists, matrices become lists
        of rows, and ⎕NULL becomes None.
        """
        if self.exchange:
            host_file, apl_file = self._exchange_file("out")
            try:
                self.run(f"(⊂{_EXPORT} {expr})⎕NPUT'{apl_file}' 1")
                return json.loads(host_file.read_text(encoding="utf-8"))
            finally:
                host_file.unlink(missing_ok=True)
        # Output wider than ⎕PW (max 32767) would wrap, so fetch in slices.
        self.run(f"⍙out←{_EXPORT} {expr}")
        n = int(self.run("≢⍙out"))
        parts = [self.run(f"⍙out[{i}+⍳{min(_OUT_SLICE, n - i)}]")
                 for i in range(0, n, _OUT_SLICE)]
        self.run("⎕EX'⍙out'")
        return json.loads("".join(parts))

    def put(self, name: str, value) -> None:
        """Assign Python data (dict/list/number/str) to an APL variable."""
        if not _APL_NAME.match(name):
            raise ValueError(f"Invalid APL name {name!r}")
        text = json.dumps(value, ensure_ascii=False, default=_to_json_value)
        if self.exchange:
            host_file, apl_file = self._exchange_file("in")
            host_file.write_text(text, encoding="utf-8")
            try:
                self.run(f"{name}←0 ⎕JSON⊃⎕NGET'{apl_file}'")
            finally:
                host_file.unlink(missing_ok=True)
            return
        # Send the JSON in chunks so no single line gets huge. Split before
        # escaping so a doubled quote is never cut in half.
        lines = ["⍙json←''"]
        i = 0
        while i < len(text):
            size = _CHUNK
            while True:
                piece = text[i:i + size].replace("'", "''")
                if len(piece) <= _CHUNK or size <= 1:
                    break
                size //= 2          # lots of quotes: escaped text grew
            lines.append(f"⍙json,←'{piece}'")
            i += size
        lines.append(f"{name}←0 ⎕JSON ⍙json ⋄ ⎕EX'⍙json'")
        # One call per line: measured ~10 ms per line, whereas sending the
        # lines as one multi-line batch was ~15x slower.
        for line in lines:
            self.run(line)

    def _exchange_file(self, kind: str) -> tuple[Path, str]:
        name = f"apl_mysql_{kind}_{uuid.uuid4().hex}.json"
        host_dir, apl_dir = self.exchange
        return host_dir / name, f"{apl_dir}/{name}"

    # ----------------------------------------------------------- MySQL side
    def load(self, name: str, sql: str, params=None) -> int:
        """Run a SELECT and store the result in APL as a namespace.

        Each column becomes a vector: SELECT city, pop … → name.city, name.pop.
        Column names must be valid APL names, so alias them if needed
        (SELECT `first name` AS first_name …). Also sets name.columns.
        Returns the number of rows.
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        for c in cols:
            _check_ident(c, "column name (alias it in SQL)")
        data = {c: [_to_json_value(r[i]) for r in rows] for i, c in enumerate(cols)}
        self.put(name, data)
        self.put("⍙cols", cols)
        self.run(f"{name}.columns←⍙cols ⋄ ⎕EX'⍙cols'")
        return len(rows)

    def save(self, table: str, expr: str, mode: str = "replace") -> int:
        """Write an APL namespace of equal-length column vectors to a table.

        mode="replace": drop and recreate the table (column types inferred).
        mode="append":  insert into an existing table.
        Returns the number of rows written.
        """
        _check_ident(table, "table name")
        if mode not in ("replace", "append"):
            raise ValueError("mode must be 'replace' or 'append'")
        data = self.get(expr)
        if not isinstance(data, dict):
            raise ValueError(f"{expr!r} must be a namespace with one vector per "
                             "column, e.g. r←⎕NS ⍬ ⋄ r.(a b)←…")
        data.pop("columns", None)
        cols = [_check_ident(c, "column name") for c in data]
        # A column of single characters comes back as one string ("abc").
        values = [list(v) if isinstance(v, str) else
                  (v if isinstance(v, list) else [v]) for v in data.values()]
        n = len(values[0]) if values else 0
        if any(len(v) != n for v in values):
            raise ValueError("All columns must have the same length: "
                             + ", ".join(f"{c}={len(v)}" for c, v in zip(cols, values)))

        rows = list(zip(*values))
        qcols = ", ".join(f"`{c}`" for c in cols)
        with self.conn.cursor() as cur:
            if mode == "replace":
                defs = ", ".join(f"`{c}` {_sql_type(v)}" for c, v in zip(cols, values))
                cur.execute(f"DROP TABLE IF EXISTS `{table}`")
                cur.execute(f"CREATE TABLE `{table}` ({defs})")
            if rows:
                marks = ", ".join(["%s"] * len(cols))
                cur.executemany(f"INSERT INTO `{table}` ({qcols}) VALUES ({marks})",
                                [tuple(_flatten(x) for x in r) for r in rows])
        self.conn.commit()
        return len(rows)

    def query(self, sql: str, params=None) -> list[dict]:
        """Run SQL and return rows as dicts (handy for checking results)."""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                self.conn.commit()
                return []
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]


def _flatten(x):
    """Values must be scalars for SQL; join nested lists (e.g. char lists)."""
    if isinstance(x, list):
        return "".join(map(str, x)) if all(isinstance(i, str) for i in x) else json.dumps(x)
    return x


def _sql_type(values: list) -> str:
    vals = [v for v in values if v is not None]
    if vals and all(isinstance(v, bool) for v in vals):
        return "BOOLEAN"
    if vals and all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
        return "BIGINT"
    if vals and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        return "DOUBLE"
    longest = max((len(_flatten(v)) if isinstance(v, (str, list)) else len(str(v))
                   for v in vals), default=0)
    return "VARCHAR(255)" if longest <= 255 else "TEXT"
