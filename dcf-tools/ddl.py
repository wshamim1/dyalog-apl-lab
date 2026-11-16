"""Suggest SQL tables (CREATE TABLE statements) for the data in component files.

Used by `dcf.py ddl` and the viewer's SQL tab. Works from DCF.Dump's output:
each component's kind (from APL) and value (as JSON).

Layouts it recognises, per file:
  * namespaces, one per component (orders.dcf)  → one table, a column per field;
    a field holding a matrix (line items) → a child table with a foreign key
  * a field-names component + records (customers.dcf)  → one table with those columns
  * a key/value matrix (2 columns, text keys)   → key / value table
  * a numeric or boolean matrix                  → (row_no, col_no, value)
  * a numeric or boolean vector                  → (position, value)
  * anything else (headers, loose text…)         → <file>_other, as JSON, so nothing is lost

Every table keeps dcf_component, the component number the row came from:
other data or code may refer to "component 57", so don't lose it until
nothing does.

Types are inferred from the values: INTEGER/BIGINT, DECIMAL(p,s), DATE,
TIMESTAMP, VARCHAR(n), TEXT, BOOLEAN, JSON. They're a suggestion: review
them, rename the generic columns (col1, col2…), and decide on indexes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

DIALECTS = {"sqlite": "SQLite", "mysql": "MySQL", "postgres": "PostgreSQL", "sqlserver": "SQL Server"}

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$")
RESERVED = {"order", "key", "value", "date", "user", "group", "select", "table", "index", "desc",
            "from", "to", "time", "timestamp", "position", "level", "size", "type", "name_", "check",
            "default", "primary", "references", "limit", "offset", "range", "rows", "row"}


@dataclass
class Column:
    name: str
    type: tuple                 # logical type: ("integer",) ("decimal", p, s) ("varchar", n) …
    nullable: bool = False
    note: str = ""


@dataclass
class Table:
    name: str
    source: str                 # where the rows come from, in words
    columns: list
    primary_key: list
    foreign_keys: list = field(default_factory=list)   # (columns, table, columns)
    rows: int = 0
    notes: list = field(default_factory=list)


# ── types ────────────────────────────────────────────────────────────────────

def _decimals(v):
    s = repr(float(v))
    if "e" in s or "E" in s:
        return None
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def _width(n):
    for w in (10, 20, 50, 100, 255):
        if n <= w:
            return w
    return None


def infer_type(values, boolean=False):
    """Logical type and nullability for a column's values (None = missing)."""
    present = [v for v in values if v is not None]
    nullable = len(present) < len(values)
    if not present:
        return ("text",), True
    if any(isinstance(v, (list, dict)) for v in present):
        return ("json",), nullable
    strs = [v for v in present if isinstance(v, str)]
    nums = [v for v in present if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if strs and nums:                                    # mixed: keep as text
        w = _width(max(len(str(v)) for v in present))
        return (("varchar", w) if w else ("text",)), nullable
    if strs:
        if all(DATE.match(s) for s in strs):
            return ("date",), nullable
        if all(STAMP.match(s) for s in strs):
            return ("timestamp",), nullable
        w = _width(max(len(s) for s in strs))
        return (("varchar", w) if w else ("text",)), nullable
    if boolean and set(nums) <= {0, 1}:
        return ("boolean",), nullable
    if all(isinstance(v, int) for v in nums):
        return (("bigint",) if max(abs(v) for v in nums) > 2**31 - 1 else ("integer",)), nullable
    scales = [_decimals(v) for v in nums]
    if None in scales or max(scales) > 6:
        return ("double",), nullable
    scale = max(scales)
    digits = max(len(str(int(abs(v)))) for v in nums)
    return ("decimal", min(38, max(10, digits + scale + 2)), scale), nullable


# ── recognising layouts ──────────────────────────────────────────────────────

def _scalar(v):
    return isinstance(v, (str, int, float)) and not isinstance(v, bool)


def _record(v):
    return isinstance(v, list) and len(v) > 0 and all(_scalar(x) or x is None for x in v)


def _names(v):
    return isinstance(v, list) and len(v) > 0 and all(isinstance(x, str) and IDENT.match(x) for x in v)


def _matrix(v):
    return (isinstance(v, list) and len(v) > 0 and all(isinstance(r, list) for r in v)
            and len({len(r) for r in v}) == 1 and len(v[0]) > 0
            and all(_scalar(x) or x is None for r in v for x in r))


def _ranges(ns):
    ns = sorted(ns)
    out, start = [], None
    for i, n in enumerate(ns):
        if start is None:
            start = n
        if i == len(ns) - 1 or ns[i + 1] != n + 1:
            out.append(str(start) if start == n else f"{start}–{n}")
            start = None
    return ", ".join(out)


def _comps(ns):
    ns = list(ns)
    return ("component " if len(ns) == 1 else "components ") + _ranges(ns)


def ident(s):
    s = re.sub(r"\W+", "_", s.strip()).strip("_").lower() or "t"
    return "t_" + s if s[0].isdigit() else s


def _key_column(cols, rows, name="id"):
    """name, if it's a column with a unique, non-empty value in every row."""
    if name not in cols:
        return None
    vals = [r.get(name) for r in rows]
    return name if None not in vals and len(set(map(str, vals))) == len(vals) else None


def tables_for(dump, name):
    """Suggested tables for one file's dump. name: the file name (customers.dcf)."""
    stem = ident(Path(name).stem)
    comps = [c for c in dump["components"]]
    used, tables, taken = set(), [], set()

    def key_first(t):
        k = [c for c in t.columns if c.name in t.primary_key]
        t.columns = k + [c for c in t.columns if c not in k]

    def tname(preferred):
        n = preferred
        i = 2
        while n in taken:
            n = f"{preferred}_{i}"
            i += 1
        taken.add(n)
        return n

    trunc = [c["component"] for c in comps if c.get("truncated")]

    # 1. namespaces, one per component → a table; matrix fields → child tables
    ns = [c for c in comps if isinstance(c["value"], dict)]
    if ns:
        fields = []
        for c in ns:
            fields += [k for k in c["value"] if k not in fields and k != "apl_functions"]
        rows = [c["value"] for c in ns]
        children = [f for f in fields if any(_matrix(r.get(f)) for r in rows)
                    and all(r.get(f) is None or _matrix(r.get(f)) for r in rows)
                    and len({len(r[f][0]) for r in rows if r.get(f)}) == 1]
        t = Table(tname(stem), f"{name} {_comps(c['component'] for c in ns)}: "
                               f"one namespace each", [], [], rows=len(ns))
        t.columns.append(Column("dcf_component", ("integer",), note=f"component number in {name}"))
        for f in fields:
            if f in children:
                continue
            typ, null = infer_type([r.get(f) for r in rows])
            note = "missing in some components" if null and any(f not in r for r in rows) else ""
            t.columns.append(Column(ident(f), typ, null, note))
        key = _key_column(fields, rows)
        t.primary_key = [ident(key)] if key else ["dcf_component"]
        key_first(t)
        if key:
            t.notes.append("dcf_component is kept: other data may refer to orders by component number")
        tables.append(t)
        for f in children:
            mats = [(r.get(key) if key else c["component"], r[f]) for c, r in zip(ns, rows) if r.get(f)]
            ncol = len(mats[0][1][0])
            parent = t.primary_key[0]
            fk = f"{t.name}_{parent}" if parent != "dcf_component" else "dcf_component"
            ch = Table(tname(f"{t.name}_{ident(f)}"), f"the '{f}' matrix inside each namespace "
                       f"({ncol} columns): one row per matrix row", [], [fk, "line_no"],
                       [([fk], t.name, [parent])], rows=sum(len(m) for _, m in mats))
            ptype = next(col.type for col in t.columns if col.name == parent)
            ch.columns += [Column(fk, ptype, note=f"the {t.name} row it belongs to"),
                           Column("line_no", ("integer",), note=f"row number within {f}")]
            for j in range(ncol):
                typ, null = infer_type([row[j] for _, m in mats for row in m])
                ch.columns.append(Column(f"col{j + 1}", typ, null, "rename: the data doesn't name it"))
            tables.append(ch)
        used |= {c["component"] for c in ns}

    # 2. records of the same length, named by a field-names component
    recs = [c for c in comps if c["component"] not in used and _record(c["value"])]
    by_len = {}
    for c in recs:
        by_len.setdefault(len(c["value"]), []).append(c)
    for n, group in by_len.items():
        names = [c for c in group if _names(c["value"])]
        data = [c for c in group if c not in names]
        if not data or (len(data) < 2 and not names):
            continue
        header = names[0] if names and len(data) >= 1 and not all(_names(c["value"]) for c in data) else None
        cols = [ident(x) for x in header["value"]] if header else [f"col{j + 1}" for j in range(n)]
        if len(set(cols)) < len(cols):
            cols = [f"col{j + 1}" for j in range(n)]
        src = f"{name} {_comps(c['component'] for c in data)}: one record each"
        if header:
            src += f"; column names from component {header['component']}"
        t = Table(tname(stem), src, [Column("dcf_component", ("integer",),
                                            note=f"component number in {name}")], [], rows=len(data))
        rows = [dict(zip(cols, c["value"])) for c in data]
        for col in cols:
            typ, null = infer_type([r.get(col) for r in rows])
            t.columns.append(Column(col, typ, null, "" if header else "rename: the data doesn't name it"))
        key = _key_column(cols, rows)
        t.primary_key = [key] if key else ["dcf_component"]
        key_first(t)
        tables.append(t)
        used |= {c["component"] for c in data} | ({header["component"]} if header else set())

    # 3. one table per remaining matrix or vector
    for c in comps:
        if c["component"] in used:
            continue
        v, kind, n = c["value"], c["kind"], c["component"]
        src = f"{name} component {n}: {kind}"
        if kind.endswith("matrix") and isinstance(v, list) and v \
                and all(isinstance(r, list) and len(r) == 2 and isinstance(r[0], str) for r in v) \
                and len({r[0] for r in v}) == len(v):
            typ, null = infer_type([r[1] for r in v])
            t = Table(tname(stem), src + " of keys and values", [
                Column("key", ("varchar", _width(max(len(r[0]) for r in v)) or 255)),
                Column("value", typ, null)], ["key"], rows=len(v))
            t.notes.append(f"from component {n}: keep its number if code looks it up that way")
        elif kind.startswith(("numeric matrix", "boolean matrix")) and _matrix(v):
            typ, null = infer_type([x for r in v for x in r], boolean=kind.startswith("boolean"))
            t = Table(tname(f"{stem}_{n}"), src + f" ({len(v)}×{len(v[0])}): one row per cell", [
                Column("row_no", ("integer",)), Column("col_no", ("integer",)), Column("value", typ, null)],
                ["row_no", "col_no"], rows=len(v) * len(v[0]))
            t.notes.append("long format; a wide table (one column per matrix column) also works "
                           "when the columns have meanings, e.g. months")
        elif kind.startswith(("numeric vector", "boolean vector")) and isinstance(v, list):
            typ, null = infer_type(v, boolean=kind.startswith("boolean"))
            t = Table(tname(f"{stem}_{n}"), src + ": one row per item", [
                Column("position", ("integer",)), Column("value", typ, null)], ["position"], rows=len(v))
        elif kind.startswith("char matrix") and isinstance(v, list):
            t = Table(tname(f"{stem}_{n}"), src + ": one row per line", [
                Column("line_no", ("integer",)), Column("text", infer_type(v)[0])], ["line_no"], rows=len(v))
        else:
            continue
        tables.append(t)
        used.add(n)

    # 4. everything else, as JSON, so nothing is lost
    rest = [c for c in comps if c["component"] not in used]
    if rest:
        t = Table(tname(f"{stem}_other"), f"{name} {_comps(c['component'] for c in rest)}: "
                  f"didn't fit a table, kept whole", [
                      Column("dcf_component", ("integer",)), Column("kind", ("varchar", 50)),
                      Column("value", ("json",))], ["dcf_component"], rows=len(rest))
        for c in rest[:5]:
            t.notes.append(f"component {c['component']}: {c['kind']}, {c['text'][:60]}")
        if len(rest) > 5:
            t.notes.append(f"… and {len(rest) - 5} more")
        tables.append(t)
    if trunc:
        for t in tables:
            t.notes.append(f"types were inferred from previews: components {_ranges(trunc)} are large")
    if dump.get("more"):
        tables[0].notes.append(f"inferred from the first {len(comps)} components; {dump['more']} more not read")
    return tables


# ── SQL ──────────────────────────────────────────────────────────────────────

def sql_type(t, d):
    k = t[0]
    if k == "varchar":
        return {"sqlite": "TEXT", "sqlserver": f"NVARCHAR({t[1]})"}.get(d, f"VARCHAR({t[1]})")
    if k == "decimal":
        return ("NUMERIC" if d in ("sqlite", "postgres") else "DECIMAL") + f"({t[1]},{t[2]})"
    return {
        "integer": {"mysql": "INT", "sqlserver": "INT"},
        "bigint": {"sqlite": "INTEGER"},
        "double": {"sqlite": "REAL", "mysql": "DOUBLE", "postgres": "DOUBLE PRECISION", "sqlserver": "FLOAT"},
        "boolean": {"sqlite": "INTEGER", "sqlserver": "BIT"},
        "date": {"sqlite": "TEXT"},
        "timestamp": {"sqlite": "TEXT", "mysql": "DATETIME", "sqlserver": "DATETIME2"},
        "text": {"sqlserver": "NVARCHAR(MAX)"},
        "json": {"sqlite": "TEXT", "postgres": "JSONB", "sqlserver": "NVARCHAR(MAX)"},
    }.get(k, {}).get(d, k.upper())


def q(name, d):
    if IDENT.match(name) and name.lower() not in RESERVED:
        return name
    return {"mysql": f"`{name}`", "sqlserver": f"[{name}]"}.get(d, f'"{name}"')


def render(tables, dialect="sqlite", title=""):
    d = dialect
    out = [f"-- {title or 'Tables suggested for component file data'}",
           f"-- Dialect: {DIALECTS[d]}. Generated by dcf-tools/ddl.py: a starting point to review,",
           "-- not a final design. Rename generic columns (col1…), check types and add indexes.", ""]
    for t in tables:
        out.append(f"-- {t.name}: {t.source} ({t.rows} row{'s' if t.rows != 1 else ''} now)")
        out += [f"--   note: {n}" for n in t.notes]
        lines = []
        for c in t.columns:
            null = "" if c.nullable else " NOT NULL"
            lines.append((f"  {q(c.name, d)} {sql_type(c.type, d)}{null}", c.note))
        lines.append((f"  PRIMARY KEY ({', '.join(q(k, d) for k in t.primary_key)})", ""))
        for cols, ref, rcols in t.foreign_keys:
            lines.append((f"  FOREIGN KEY ({', '.join(q(x, d) for x in cols)}) "
                          f"REFERENCES {q(ref, d)} ({', '.join(q(x, d) for x in rcols)})", ""))
        out.append(f"CREATE TABLE {q(t.name, d)} (")
        width = max(len(s) for s, _ in lines) + 1
        for i, (s, note) in enumerate(lines):
            s += "," if i < len(lines) - 1 else ""
            out.append(f"{s:<{width}}  -- {note}" if note else s)
        out.append(") DEFAULT CHARSET=utf8mb4;" if d == "mysql" else ");")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def ddl(dumps, dialect="sqlite"):
    """dumps: [(file name, DCF.Dump dict)]. Returns (SQL text, tables)."""
    tables, taken = [], set()
    for name, d in dumps:
        mine, renamed = tables_for(d, name), {}
        for t in mine:
            base, i = t.name, 2
            while t.name in taken:                  # same table name from two files
                t.name = f"{base}_{i}"
                i += 1
            renamed[base] = t.name
            taken.add(t.name)
        for t in mine:                              # keep foreign keys pointing at the right table
            t.foreign_keys = [(c, renamed.get(ref, ref), rc) for c, ref, rc in t.foreign_keys]
        tables += mine
    names = ", ".join(n for n, _ in dumps)
    return render(tables, dialect, f"Tables suggested for {names}"), tables
