"""Generate an HTML map of a folder of APL (and Python) code: which code touches
which data files, how, and how the pieces relate.

    python3 sample-scripts/component-files/code-map.py            # this folder
    python3 sample-scripts/component-files/code-map.py some/folder [-o out.html]

Writes export/code-map.html (inside the scanned folder) by default.

It reads the source as text: Dyalog is not needed. It finds
  * every ⎕F… call (create, open, read, write, lock, delete) and the
    component file it acts on, following tie numbers and small wrappers
    such as  Tie←{(Folder,⍵)⎕FTIE 0}
  * native files written with ⎕NPUT or deleted with ⎕NDELETE
  * functions defined, calls between them (Store.Customers…), ⎕FIX loads, tests
  * in Python: files read or written, and the SQL tables built from each export
and, when they exist, export/*.jsonl (what is inside each component) and
export/components.db (tables, columns, rows).

This is Phase 0 of the migration in migration.md: "who reads and writes which
file". The analysis is pattern-based, so treat it as a strong first draft and
check anything surprising against the code.
"""

import argparse
import fnmatch
import html
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

APL_EXT = {".apls", ".aplf", ".apln", ".aplc", ".dyalog"}

# ⎕F… system functions and what they mean
F_OPS = {
    "⎕FCREATE": "create", "⎕FTIE": "open", "⎕FSTIE": "open",
    "⎕FREAD": "read", "⎕FSIZE": "read", "⎕FRDCI": "read", "⎕FRDAC": "read",
    "⎕FAPPEND": "write", "⎕FREPLACE": "write", "⎕FSTAC": "write", "⎕FRESIZE": "write",
    "⎕FHOLD": "lock", "⎕FERASE": "delete", "⎕FDROP": "delete", "⎕FUNTIE": "close",
}
OPENERS = {"⎕FCREATE", "⎕FTIE", "⎕FSTIE", "⎕FERASE"}
ACTION_ORDER = ["create", "delete", "write", "lock", "read", "open", "close"]
F_RE = re.compile("|".join(re.escape(k) for k in sorted(F_OPS, key=len, reverse=True)))
LIT_RE = re.compile(r"'((?:[^']|'')*)'")
NAME_LIT = re.compile(r"^[\w./*-]+$")


# ─── small APL text helpers ──────────────────────────────────────────────────

def strip_comment(line):
    """Code part of a line, and its ⍝ comment (quotes respected)."""
    q = False
    for i, ch in enumerate(line):
        if ch == "'":
            q = not q
        elif ch == "⍝" and not q:
            return line[:i], line[i + 1:].strip()
    return line, ""


def split_diamonds(code):
    out, q, cur = [], False, ""
    for ch in code:
        if ch == "'":
            q = not q
        if ch == "⋄" and not q:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    return out + [cur]


def literals(code):
    return [m.replace("''", "'") for m in LIT_RE.findall(code)]


def file_literals(code):
    """String literals that look like file names (no spaces, not just '.ext')."""
    return [s for s in literals(code) if NAME_LIT.match(s) and not s.startswith(".") and s]


def without_strings(code):
    return LIT_RE.sub("''", code)


def tradfn_name(header):
    """'r←Customers;t' → Customers, 'n←AddOrder order;t' → AddOrder."""
    h = header.split(";")[0]
    h = h.split("←")[-1].strip()
    toks = h.replace("(", " ").replace(")", " ").split()
    if not toks:
        return "?"
    return toks[0] if len(toks) <= 2 else toks[1]


# ─── model ───────────────────────────────────────────────────────────────────

class Model:
    def __init__(self, root):
        self.root = root
        self.files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                            if p.is_file() and not any(x.startswith(".") for x in p.parts))
        self.code = {}            # rel path → info dict
        self.accesses = []        # dicts: code, scope, line, op, action, targets, snippet, comp
        self.calls = []           # dicts: code, scope, line, target ('Store.Customers'), via
        self.loads = []           # dicts: code, line, target (rel path)
        self.data = {}            # node id → info dict (dcf, temp, json, db…)
        self.tables = {}          # SQL table → {sources, columns, rows, builder}
        self.wrappers = {}        # dfn name → (op, prefix var, ext, code file)
        self.namespaces = {}      # ns name → {file, functions: {name: line}}
        self.pipeline = []        # README run order

    # resolve a path expression to node ids
    def resolve(self, path, ext=None):
        if ext and not Path(path).suffix and "*" not in path:
            path += ext
        if path.startswith("/"):
            return [path]
        if "*" in path:
            hits = [f for f in self.files if fnmatch.fnmatch(f, path)]
            return hits or [path]
        if "/" in path:
            return [path]
        hits = [f for f in self.files if Path(f).name == path and not f.endswith(".html")]
        return hits or [path]

    def node(self, nid, **kw):
        n = self.data.setdefault(nid, {"id": nid, "exists": (self.root / nid).exists()
                                       if not nid.startswith("/") else Path(nid).exists()})
        n.update({k: v for k, v in kw.items() if v is not None})
        return n


def kind_of_node(nid):
    if nid.startswith("/"):
        return "temp"
    suf = Path(nid).suffix
    return {".dcf": "dcf", ".jsonl": "json", ".json": "json", ".db": "db"}.get(suf, "file")


# ─── APL analysis ────────────────────────────────────────────────────────────

def apl_scopes(rel, lines):
    """Split a source into scopes: (name, kind, first line no, [(no, text)])."""
    ext = Path(rel).suffix
    if ext == ".aplf":
        name = tradfn_name(strip_comment(lines[0])[0].strip())
        return [(name, "function", 1, list(enumerate(lines, 1)))], None
    if ext not in (".apln", ".aplc", ".dyalog"):
        return [("(script)", "script", 1, list(enumerate(lines, 1)))], None
    scopes, ns, cur, outer = [], None, None, []
    for no, text in enumerate(lines, 1):
        s = text.strip()
        m = re.match(r":(Namespace|Class)\s+(\w+)", s)
        if m:
            ns = m.group(2)
        if s.startswith("∇"):
            if cur is None and len(s) > 1:
                cur = (tradfn_name(s[1:].strip()), "function", no, [(no, text)])
            elif cur is not None:
                cur[3].append((no, text))
                scopes.append(cur)
                cur = None
            continue
        if cur is not None:
            cur[3].append((no, text))
            continue
        m = re.match(r"\s*([A-Za-z_∆][\w∆]*)←\{.*\}\s*(⍝.*)?$", text)
        if m:
            scopes.append((m.group(1), "dfn", no, [(no, text)]))
        else:
            outer.append((no, text))
    if outer:
        scopes.insert(0, ("(namespace)", "namespace", 1, outer))
    return scopes, ns


def header_comments(rel, lines):
    """Leading ⍝ comment lines: the file's own description."""
    out, started = [], False
    for i, text in enumerate(lines):
        s = text.strip()
        if i == 0 and Path(rel).suffix == ".aplf" and not s.startswith("⍝"):
            continue
        if s.startswith(":Namespace") or s.startswith(":Class"):
            continue
        if s.startswith("⍝"):
            out.append(s[1:].strip())
            started = True
        elif started or s:
            break
    return out


def analyse_apl(m, rel):
    text = (m.root / rel).read_text(encoding="utf-8")
    lines = text.splitlines()
    scopes, ns = apl_scopes(rel, lines)
    comments = header_comments(rel, lines)
    run = next((c.split("Run:", 1)[1].strip() for c in comments if "Run:" in c), None)
    summary = next((c for c in comments if c and "Run:" not in c), "")
    is_test = Path(rel).stem.endswith("_test") or rel.startswith("tests/")
    info = {
        "path": rel, "lang": "APL", "lines": len(lines), "comments": comments,
        "summary": summary, "run": run, "namespace": ns,
        "kind": "test" if is_test else {".apls": "script", ".apln": "namespace",
                                         ".aplf": "function"}.get(Path(rel).suffix, "APL"),
        "scopes": [(s[0], s[1], s[2]) for s in scopes],
        "assertions": len(re.findall(r"\bExpect\w+", text)),
        "pathvars": {},
    }
    # path variables:  dir←here,'data/'   out←here,'export/'   dir←'/tmp/x/'
    code_text = "\n".join(strip_comment(l)[0] for l in lines)     # comments may hold stray quotes
    for mm in re.finditer(r"(\w+)←(?:\w+,)?'([^']*/)'", code_text):
        info["pathvars"][mm.group(1)] = mm.group(2)
    info["glob"] = next((s for s in literals(code_text) if "*" in s), None)
    m.code[rel] = info
    if ns:
        m.namespaces[ns] = {"file": rel, "functions": {s[0]: s[2] for s in scopes
                                                       if s[1] in ("function", "dfn")}}
    # wrappers: one-line dfns around ⎕FTIE/⎕FCREATE/⎕NDELETE
    for name, kind, start, body in scopes:
        if kind != "dfn" and not (kind in ("script", "namespace")):
            continue
        for no, t in body:
            code, _ = strip_comment(t)
            mm = re.match(r"\s*([A-Za-z_∆][\w∆]*)←\{(.*)\}\s*$", code)
            if not mm:
                continue
            body_code = mm.group(2)
            op = next((o for o in ("⎕FTIE", "⎕FCREATE", "⎕FERASE", "⎕NDELETE") if o in body_code), None)
            if op:
                pv = re.search(r"(\w+),⍵", body_code)
                ext = next((s for s in literals(body_code) if s.startswith(".")), None)
                m.wrappers[mm.group(1)] = (op, pv.group(1) if pv else None, ext, rel)
    return info, scopes


def target_paths(m, info, code, line_code, prefix_hint=None, ext=".dcf"):
    """Work out which files a statement names."""
    pv = info["pathvars"]
    words = re.findall(r"[A-Za-z_]\w*", without_strings(code))
    prefix = prefix_hint if prefix_hint is not None else next((pv[w] for w in words if w in pv), "")
    lits = file_literals(code) or file_literals(line_code)
    if lits:
        return [t for lit in lits for t in m.resolve(prefix + lit, ext)]
    if info["glob"]:
        return m.resolve(prefix + info["glob"] if "/" not in info["glob"] else info["glob"])
    return ["(unknown file)"]


def record_apl(m, rel, info, scopes):
    for name, kind, start, body in scopes:
        if kind == "dfn" and name in m.wrappers:
            continue                   # the definition; calls are recorded where used
        current = []                    # files tied in this scope
        for no, t in body:
            code, _ = strip_comment(t)
            if not code.strip():
                continue
            if re.match(r"\s*([A-Za-z_∆][\w∆]*)←\{.*\}\s*$", code) and \
                    re.match(r"\s*([A-Za-z_∆][\w∆]*)", code).group(1) in m.wrappers:
                continue
            snippet = t.strip()
            add = lambda op, action, targets, comp=None: m.accesses.append(dict(
                code=rel, scope=name, line=no, op=op, action=action,
                targets=targets, snippet=snippet, comp=comp))
            # native files
            if "⎕NDELETE" in code:
                pre = next((info["pathvars"][w] for w in re.findall(r"\w+", without_strings(code))
                            if w in info["pathvars"]), "")
                lits = [s for s in file_literals(code) if "." in s]
                if lits:
                    add("⎕NDELETE", "delete", [x for s in lits for x in m.resolve(pre + s)])
            if "⎕NPUT" in code:
                pre = next((info["pathvars"][w] for w in re.findall(r"\w+", without_strings(code))
                            if w in info["pathvars"]), "")
                for s in literals(code):
                    if s.startswith(".") and NAME_LIT.match(s):
                        add("⎕NPUT", "write", m.resolve(pre + "*" + s))
                    elif NAME_LIT.match(s) and "." in s:
                        add("⎕NPUT", "write", m.resolve(pre + s))
            for stmt in split_diamonds(code):
                # wrapper calls:  Tie'customers'   New'orders'
                for w, (op, pvar, ext, wfile) in m.wrappers.items():
                    for mm in re.finditer(r"(?<![\w.])" + re.escape(w) + r"\s*'([^']+)'", stmt):
                        pre = m.code[wfile]["pathvars"].get(pvar, info["pathvars"].get(pvar, "")) if pvar else ""
                        targets = m.resolve(pre + mm.group(1), ext or ".dcf")
                        action = {"⎕NDELETE": "delete", "⎕FERASE": "delete"}.get(op, F_OPS.get(op))
                        add(f"{w} → {op}", action, targets)
                        if op in ("⎕FTIE", "⎕FCREATE"):
                            current = targets
                for mm in F_RE.finditer(stmt):
                    op = mm.group(0)
                    if op in OPENERS:
                        targets = target_paths(m, info, stmt, code)
                        current = targets
                    else:
                        targets = current or ["(unknown file)"]
                    comp = None
                    cm = re.match(r"\s*\w+\s+(\d+)", stmt[mm.end():])
                    if op in ("⎕FREAD", "⎕FREPLACE", "⎕FRDCI") and cm:
                        comp = int(cm.group(1))
                    if op == "⎕FHOLD" and re.match(r"\s*⍬", stmt[mm.end():]):
                        add(op, "lock", targets, comp="release")
                        continue
                    add(op, F_OPS[op], targets, comp)
            # calls into namespaces, and loads
            plain = without_strings(code)
            for ns, nsinfo in m.namespaces.items():
                for mm in re.finditer(r"\b" + re.escape(ns) + r"\.(\w+)", plain):
                    m.calls.append(dict(code=rel, scope=name, line=no, target=f"{ns}.{mm.group(1)}"))
            if info["namespace"] and kind in ("function", "dfn"):
                sib = m.namespaces[info["namespace"]]["functions"]
                for w in set(re.findall(r"(?<![.\w⎕:])([A-Za-z_∆][\w∆]*)", plain)):
                    if w in sib and w != name and no != start:
                        m.calls.append(dict(code=rel, scope=name, line=no,
                                            target=f"{info['namespace']}.{w}", internal=True))
            if "⎕FIX" in code or "]load" in t:
                for s in literals(code) + re.findall(r"\]load\s+(\S+)", t):
                    s = s.split("/")[-1]
                    if Path(s).suffix in APL_EXT:
                        m.loads.append(dict(code=rel, line=no, target=m.resolve(s)[0]))


# ─── Python analysis ─────────────────────────────────────────────────────────

def analyse_python(m, rel):
    text = (m.root / rel).read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = ""
    mm = re.match(r'\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', text, re.S)
    if mm:
        doc = mm.group(1).strip()
    doc_lines = [l.strip() for l in doc.splitlines()]
    info = {
        "path": rel, "lang": "Python", "lines": len(lines), "kind": "python",
        "comments": [l for l in doc_lines], "summary": doc_lines[0] if doc_lines else "",
        "run": next((l for l in doc_lines if l.startswith("python")), None),
        "scopes": [(mm.group(1), "function", text[:mm.start()].count("\n") + 1)
                   for mm in re.finditer(r"^def (\w+)", text, re.M)],
        "assertions": 0, "namespace": None,
    }
    m.code[rel] = info
    # Path variables:  EXPORT = HERE / "export"
    pvars = {"HERE": ""}
    for mm in re.finditer(r"^(\w+)\s*=\s*(\w+)\s*/\s*\"([^\"]+)\"", text, re.M):
        if mm.group(2) in pvars:
            pvars[mm.group(1)] = pvars[mm.group(2)] + mm.group(3) + ("/" if "." not in mm.group(3) else "")
    for no, t in enumerate(lines, 1):
        for mm in re.finditer(r"(\w+)\s*/\s*f?\"([^\"]+)\"", t):
            if mm.group(1) not in pvars or re.match(r"^\s*\w+\s*=", t) and "." not in mm.group(2):
                continue
            path = pvars[mm.group(1)] + re.sub(r"\{[^}]*\}", "*", mm.group(2))
            if Path(path).suffix == "":
                continue
            action = "write" if path.endswith(".db") else "read"
            targets = m.resolve(path)
            m.accesses.append(dict(code=rel, scope="", line=no, op="open" if action == "read" else "sqlite3",
                                   action=action, targets=targets, snippet=t.strip(), comp=None))
            if re.match(r"^\s*(\w+)\s*=", t):            # DB = EXPORT / "x.db" → the variable
                pvars.setdefault("@" + re.match(r"^\s*(\w+)", t).group(1), path)
    # SQL tables: CREATE TABLE x … and the export each INSERT is fed from
    stems = {Path(f).stem for f in m.files if f.endswith(".jsonl")}
    db = next((v for k, v in pvars.items() if k.startswith("@") and v.endswith(".db")), None)
    for no, t in enumerate(lines, 1):
        for mm in re.finditer(r"CREATE TABLE (\w+)", t):
            tbl = m.tables.setdefault(mm.group(1), {"sources": set(), "db": db})
            if not tbl.get("builder"):
                tbl.update(builder=rel, line=no)
        for mm in re.finditer(r"INSERT INTO (\w+)", t):
            tbl = m.tables.setdefault(mm.group(1), {"sources": set(), "db": db})
            if not tbl.get("builder"):
                tbl.update(builder=rel, line=no)
            for back in range(no - 1, 0, -1):
                found = [s for s in re.findall(r"\"(\w+)\"", lines[back - 1]) if s in stems]
                if found:
                    tbl["sources"].update(found)
                    break
    if "checks.json" in text:
        info["verifies"] = True


# ─── data on disk ────────────────────────────────────────────────────────────

def describe(v):
    if isinstance(v, dict):
        return "namespace", "{" + " ".join(v.keys()) + "}"
    if isinstance(v, str):
        return "text", f"{len(v)} chars"
    if isinstance(v, bool) or isinstance(v, (int, float)):
        return "number", ""
    if isinstance(v, list):
        if v and all(isinstance(r, list) for r in v) and len({len(r) for r in v}) == 1:
            return "matrix", f"{len(v)}×{len(v[0])}"
        if v and all(x in (0, 1) for x in v):
            return "boolean", f"{len(v)}"
        if all(isinstance(x, (int, float)) for x in v):
            return "numeric", f"{len(v)}"
        return "nested", f"{len(v)} items"
    return type(v).__name__, ""


def inspect_disk(m):
    for f in m.files:
        p = m.root / f
        if f.endswith(".dcf"):
            m.node(f, size=p.stat().st_size)
    for f in m.files:
        if not f.endswith(".jsonl"):
            continue
        comps = []
        for line in (m.root / f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                k, d = describe(rec.get("value"))
                comps.append({"n": rec.get("component"), "kind": k, "detail": d, "file": rec.get("file")})
        m.node(f, components=len(comps))
        for dcf in m.resolve(f"{Path(f).stem}.dcf"):
            if dcf in m.data:
                m.data[dcf]["contents"] = comps
                m.data[dcf]["export"] = f
    for f in m.files:
        if f.endswith(".db"):
            try:
                con = sqlite3.connect(f"file:{m.root / f}?mode=ro", uri=True)
                for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                    cols = [r[1] for r in con.execute(f"PRAGMA table_info('{t}')")]
                    rows = con.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
                    m.tables.setdefault(t, {"sources": set(), "builder": None, "line": None, "db": f})
                    m.tables[t].update(columns=cols, rows=rows, db=f)
                con.close()
            except sqlite3.Error:
                pass


def read_pipeline(m):
    readme = m.root / "README.md"
    if not readme.exists():
        return
    for t in readme.read_text(encoding="utf-8").splitlines():
        mm = re.match(r"\s*(dyalog|python3?)\s+(?:test\s+)?(\S+)\s*(?:#\s*(.*))?$", t)
        if mm:
            target = mm.group(2).split("/")[-1]
            hit = [c for c in m.code if c.endswith(target) or Path(c).parent.name == target]
            m.pipeline.append({"cmd": t.strip().split("#")[0].strip(), "note": (mm.group(3) or "").strip(),
                               "file": hit[0] if hit and Path(target).suffix else None,
                               "tests": "test" in t.split()[1:2]})


# ─── derived views ───────────────────────────────────────────────────────────

def build(root):
    m = Model(root)
    inspect_disk(m)
    srcs = [f for f in m.files if Path(f).suffix in APL_EXT]
    # namespaces & wrappers first (they're needed to read the callers)
    parsed = {}
    for rel in sorted(srcs, key=lambda f: Path(f).suffix != ".apln"):
        parsed[rel] = analyse_apl(m, rel)
    for rel, (info, scopes) in parsed.items():
        record_apl(m, rel, info, scopes)
    tools = {Path(__file__).name, "code_map_app.py"}          # the map's own code isn't part of the map
    for rel in [f for f in m.files if f.endswith(".py") and Path(f).name not in tools]:
        analyse_python(m, rel)
    for a in m.accesses:
        for t in a["targets"]:
            m.node(t)
    read_pipeline(m)
    return m


def access_matrix(m):
    """{(code, data): {action: [line numbers]}}"""
    mat = defaultdict(lambda: defaultdict(list))
    for a in m.accesses:
        if a["action"] in ("open", "close"):
            continue
        for t in a["targets"]:
            mat[(a["code"], t)][a["action"]].append(a["line"])
    # an open with no other action still counts as touching the file
    for a in m.accesses:
        for t in a["targets"]:
            if a["action"] == "open" and (a["code"], t) not in mat:
                mat[(a["code"], t)]["open"].append(a["line"])
    return mat


def graph_edges(m, mat):
    edges = []
    for (code, data), acts in mat.items():
        writes = any(k in acts for k in ("create", "write", "delete"))
        reads = "read" in acts or "open" in acts
        both = writes and reads and "create" not in acts
        label = " · ".join(a + ("s" if not a.endswith("e") else "s") for a in ACTION_ORDER
                           if a in acts and a not in ("open", "close"))
        label = label.replace("lockss", "locks") or "opens"
        if both or (reads and not writes):
            edges.append(dict(src=data, dst=code, label=label, kind="both" if both else "read"))
        else:
            edges.append(dict(src=code, dst=data, label=label, kind="write"))
    seen = set()
    for c in m.calls:
        if c.get("internal"):
            continue
        ns = c["target"].split(".")[0]
        f = m.namespaces[ns]["file"]
        if f != c["code"] and (f, c["code"]) not in seen:
            seen.add((f, c["code"]))
            edges.append(dict(src=f, dst=c["code"], label="used by", kind="uses"))
    for l in m.loads:
        if (l["target"], l["code"]) not in seen and l["target"] in m.code:
            seen.add((l["target"], l["code"]))
            edges.append(dict(src=l["target"], dst=l["code"], label="loaded by", kind="uses"))
    return edges


def layout(nodes, edges, creators):
    """Layered left-to-right layout: break cycles, longest path, barycentre order."""
    out = defaultdict(list)
    for i, e in enumerate(edges):
        out[e["src"]].append(i)
    indeg = defaultdict(int)
    for e in edges:
        indeg[e["dst"]] += 1
    order = sorted(nodes, key=lambda n: (n not in creators, indeg[n] > 0, n))
    state, back = {}, set()

    def dfs(n):
        state[n] = 1
        for i in out[n]:
            d = edges[i]["dst"]
            if state.get(d) == 1:
                back.add(i)
            elif d not in state:
                dfs(d)
        state[n] = 2
    sys.setrecursionlimit(10000)
    for n in order:
        if n not in state:
            dfs(n)
    layer = {n: 0 for n in nodes}
    for _ in range(len(nodes)):
        changed = False
        for i, e in enumerate(edges):
            if i not in back and layer[e["dst"]] < layer[e["src"]] + 1:
                layer[e["dst"]] = layer[e["src"]] + 1
                changed = True
        if not changed:
            break
    cols = defaultdict(list)
    for n in order:
        cols[layer[n]].append(n)
    pos = {n: i for c in cols.values() for i, n in enumerate(c)}
    for _ in range(4):
        for c in sorted(cols):
            def bary(n):
                ps = [pos[e["src"]] for e in edges if e["dst"] == n and layer[e["src"]] < c] + \
                     [pos[e["dst"]] for e in edges if e["src"] == n and layer[e["dst"]] < c]
                return sum(ps) / len(ps) if ps else pos[n]
            cols[c].sort(key=bary)
            for i, n in enumerate(cols[c]):
                pos[n] = i
    return layer, cols, back


# ─── HTML ────────────────────────────────────────────────────────────────────

E = html.escape
ACT_CLASS = {"create": "w", "write": "w", "delete": "x", "lock": "l", "read": "r", "open": "o", "close": "o"}


def short(nid):
    return nid if nid.startswith("/") else nid


def node_label(m, nid):
    if nid in m.code:
        c = m.code[nid]
        return Path(nid).name, c["kind"]
    d = m.data.get(nid, {})
    k = kind_of_node(nid)
    sub = {"dcf": "component file", "temp": "temp (test)", "json": "export", "db": "SQLite database"}.get(k, "file")
    if d.get("contents"):
        sub += f" · {len(d['contents'])} comps"
    elif d.get("components"):
        sub += f" · {d['components']} lines"
    if not d.get("exists", True) and k != "temp":
        sub += " · missing"
    return Path(nid).name, sub


def svg_graph(m, edges):
    nodes = sorted(set([e["src"] for e in edges] + [e["dst"] for e in edges]))
    creators = {e["src"] for e in edges if "create" in e["label"]}
    layer, cols, back = layout(nodes, edges, creators)
    W, H, GX, GY, PAD = 168, 40, 88, 18, 24
    ncol = max(cols) + 1 if cols else 1
    nrow = max(len(c) for c in cols.values()) if cols else 1
    width = PAD * 2 + ncol * W + (ncol - 1) * GX
    height = PAD * 2 + nrow * (H + GY) - GY + 30
    xy = {}
    for c, ns in cols.items():
        offset = (nrow - len(ns)) * (H + GY) / 2
        for i, n in enumerate(ns):
            xy[n] = (PAD + c * (W + GX), PAD + offset + i * (H + GY))
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Data-flow graph: '
             f'code files, the component files they create, read and write, and the exports '
             f'and database built from them" class="graph">',
             '<defs>']
    for k in ("read", "write", "both", "uses"):
        parts.append(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                     f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
                     f'class="mk-{k}"/></marker>')
    parts.append("</defs><g class=\"edges\">")
    labels = []
    for i, e in enumerate(edges):
        x1, y1 = xy[e["src"]]
        x2, y2 = xy[e["dst"]]
        if layer[e["dst"]] > layer[e["src"]]:
            sx, sy, tx, ty = x1 + W, y1 + H / 2, x2, y2 + H / 2
            dx = (tx - sx) / 2
            d = f"M{sx},{sy} C{sx + dx},{sy} {tx - dx},{ty} {tx},{ty}"
            lx, ly = (sx + tx) / 2, (sy + ty) / 2
        else:                                    # back edge: loop under the nodes
            sx, sy, tx, ty = x1 + W / 2, y1 + H, x2 + W / 2, y2 + H
            low = max(sy, ty) + 34
            d = f"M{sx},{sy} C{sx},{low} {tx},{low} {tx},{ty}"
            lx, ly = (sx + tx) / 2, low - 8
        start = f' marker-start="url(#a-{e["kind"]})"' if e["kind"] == "both" else ""
        parts.append(f'<path d="{d}" class="e e-{e["kind"]}" data-a="{E(e["src"])}" data-b="{E(e["dst"])}"'
                     f'{start} marker-end="url(#a-{e["kind"]})"/>')
        labels.append(f'<text x="{lx:.0f}" y="{ly + 4:.0f}" text-anchor="middle" class="el" '
                      f'data-a="{E(e["src"])}" data-b="{E(e["dst"])}">{E(e["label"])}</text>')
    parts.append("</g><g class=\"labels\">" + "".join(labels) + "</g><g class=\"nodes\">")
    for n in nodes:
        x, y = xy[n]
        title, sub = node_label(m, n)
        cls = "code" if n in m.code else "data " + kind_of_node(n)
        if n not in m.code and not m.data.get(n, {}).get("exists", True) and kind_of_node(n) != "temp":
            cls += " missing"
        parts.append(f'<g class="n {cls}" data-id="{E(n)}" tabindex="0"><title>{E(n)}</title>'
                     f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="7"/>'
                     f'<text x="{x + 12}" y="{y + 17}" class="nt">{E(title)}</text>'
                     f'<text x="{x + 12}" y="{y + 31}" class="ns">{E(sub)}</text></g>')
    parts.append("</g></svg>")
    return "".join(parts)


def badge(action, lines=None):
    t = f' title="lines {", ".join(map(str, sorted(set(lines))))}"' if lines else ""
    return f'<span class="b b-{ACT_CLASS.get(action, "o")}"{t}>{E(action)}</span>'


def anchor(nid):
    return "f-" + re.sub(r"[^\w]", "-", nid)


def link(m, nid):
    name = Path(nid).name if not nid.startswith("/") else nid
    return f'<a href="#{anchor(nid)}">{E(name)}</a>'


def render(m, out_path):
    mat = access_matrix(m)
    edges = graph_edges(m, mat)
    code_files = sorted(m.code, key=lambda f: (["script", "namespace", "function", "test", "python"]
                                               .index(m.code[f]["kind"]) if m.code[f]["kind"] in
                                               ["script", "namespace", "function", "test", "python"] else 9, f))
    data_files = sorted({d for (_, d) in mat}, key=lambda d: (["dcf", "temp", "json", "db", "file"]
                                                              .index(kind_of_node(d)), d))
    fn_count = sum(1 for c in m.code.values() for s in c["scopes"] if s[1] in ("function", "dfn"))
    f_calls = sum(1 for a in m.accesses if a["op"].startswith("⎕F") or "→ ⎕F" in a["op"])

    # ── findings
    findings = []
    layer_ns = [ns for ns, i in m.namespaces.items()
                if any(a["code"] == i["file"] for a in m.accesses)]
    layer_files = {m.namespaces[ns]["file"] for ns in layer_ns}
    if layer_ns:
        direct = defaultdict(int)
        for a in m.accesses:
            if a["code"] not in layer_files and m.code.get(a["code"], {}).get("lang") == "APL" \
                    and (a["op"].startswith("⎕F") or "→ ⎕F" in a["op"]) \
                    and m.code[a["code"]]["kind"] != "test":
                direct[a["code"]] += 1
        if direct:
            items = ", ".join(f"{link(m, c)} ({n})" for c, n in sorted(direct.items(), key=lambda x: -x[1]))
            findings.append(("warn", "Code that bypasses the data-access layer",
                             f"{', '.join(layer_ns)} is the data-access layer, but these files call ⎕F… "
                             f"directly: {items}. In a migration each of these needs to go through "
                             f"{layer_ns[0]} (or be retired) before the storage can change."))
    comps = defaultdict(set)
    for a in m.accesses:
        if isinstance(a["comp"], int):
            for t in a["targets"]:
                comps[(t, a["comp"])].add(a["code"])
    if comps:
        rows = "".join(f"<li>{link(m, t)} component <b>{n}</b>: read by "
                       f"{', '.join(link(m, c) for c in sorted(cs))}</li>"
                       for (t, n), cs in sorted(comps.items()))
        findings.append(("info", "Hard-coded component numbers",
                         "These places read a fixed component number, so they depend on the file's "
                         "layout (the \"component numbers as IDs\" pitfall). A database table must "
                         f"keep that meaning, for example as a header or field-names row:<ul>{rows}</ul>"))
    writers = defaultdict(set)
    holds = defaultdict(set)
    for a in m.accesses:
        for t in a["targets"]:
            if a["action"] in ("write",):
                writers[t].add((a["code"], a["scope"]))
            if a["action"] == "lock":
                holds[t].add((a["code"], a["scope"]))
    unlocked = [(t, c, s) for t, ws in writers.items() for (c, s) in ws
                if (c, s) not in holds[t] and m.code.get(c, {}).get("kind") == "namespace"]
    locked = [(t, c, s) for t, ws in writers.items() for (c, s) in ws if (c, s) in holds[t]]
    if locked:
        findings.append(("ok", "Writes protected with ⎕FHOLD",
                         "; ".join(f"{E(s)} in {link(m, c)} holds {link(m, t)} while writing"
                                   for t, c, s in locked) + ". In SQL this becomes a transaction."))
    if unlocked:
        findings.append(("warn", "Writes in shared code without ⎕FHOLD",
                         "; ".join(f"{E(s)} in {link(m, c)} writes {link(m, t)}" for t, c, s in unlocked)))
    for ns in layer_ns:
        fns = [f for f, _ in m.namespaces[ns]["functions"].items()
               if f not in [w for w in m.wrappers] and f[0].isupper()]
        tested = {c["target"].split(".")[1] for c in m.calls if m.code[c["code"]]["kind"] == "test"}
        used = {c["target"].split(".")[1] for c in m.calls if not c.get("internal")}
        missing = [f for f in fns if f not in tested and f in used]   # internal helpers are tested through their callers
        unused = [f for f in fns if f not in used]
        if missing:
            findings.append(("warn", f"{ns} functions without a test", ", ".join(missing)))
        else:
            findings.append(("ok", f"Every {ns} function is called by a test",
                             ", ".join(fns) + f" — {sum(m.code[c]['assertions'] for c in m.code if m.code[c]['kind'] == 'test')} assertions in total."))
        if unused:
            findings.append(("info", f"{ns} functions only used inside {ns}", ", ".join(unused)))
    miss = [d for d in data_files if not m.data.get(d, {}).get("exists", True) and kind_of_node(d) != "temp"]
    if miss:
        findings.append(("info", "Referenced but not on disk yet",
                         ", ".join(E(d) for d in miss) + ". Usually an output that hasn't been generated."))
    nojson = [d for d, i in m.data.items() if kind_of_node(d) == "dcf" and i.get("exists") and not i.get("contents")]
    if nojson:
        findings.append(("info", "No export found", ", ".join(E(d) for d in nojson) +
                         ": run export-json.apls to see what each component holds."))

    # ── sections
    S = []
    # summary
    stats = [("source files", len(m.code)), ("functions", fn_count), ("file calls", f_calls),
             ("component files", sum(1 for d in m.data if kind_of_node(d) == "dcf")),
             ("SQL tables", len(m.tables))]
    S.append('<div class="stats">' + "".join(f'<div class="stat"><b>{v}</b><span>{E(k)}</span></div>'
                                             for k, v in stats) + "</div>")

    # graph
    S.append('<section id="graph"><h2>How it fits together</h2>'
             '<p class="lede">Data flows left to right. Hover or focus a box to highlight its '
             'connections; click to jump to its details.</p>'
             '<div class="legend"><span class="lg lg-write"></span>creates or writes '
             '<span class="lg lg-read"></span>reads <span class="lg lg-both"></span>reads and writes '
             '<span class="lg lg-uses"></span>uses code <span class="sw code"></span>code '
             '<span class="sw dcf"></span>component file <span class="sw json"></span>export / database</div>'
             f'<div class="scroll">{svg_graph(m, edges)}</div></section>')

    # pipeline
    if m.pipeline:
        steps = "".join(
            f'<li><code>{E(p["cmd"])}</code>{(" " + link(m, p["file"])) if p["file"] else ""}'
            f'<span class="muted">{(" — " + E(p["note"])) if p["note"] else ""}</span></li>'
            for p in m.pipeline)
        S.append(f'<section id="pipeline"><h2>Run order</h2><p class="lede">From the README.</p>'
                 f'<ol class="steps">{steps}</ol></section>')

    # matrix
    def matrix(cols):
      head = "".join(f'<th><a href="#{anchor(d)}">{E(Path(d).name if not d.startswith("/") else d)}</a></th>'
                     for d in cols)
      body = ""
      for c in code_files:
        cells = ""
        touched = False
        for d in cols:
            acts = mat.get((c, d))
            if acts:
                touched = True
                cells += "<td>" + "".join(badge(a, acts[a]) for a in ACTION_ORDER if a in acts) + "</td>"
            else:
                cells += '<td class="empty"></td>'
        if touched:
            body += f'<tr><th>{link(m, c)}</th>{cells}</tr>'
      return (f'<div class="scroll"><table class="matrix"><thead><tr><th></th>{head}'
              f'</tr></thead><tbody>{body}</tbody></table></div>')
    comp_cols = [d for d in data_files if kind_of_node(d) in ("dcf", "temp")]
    other_cols = [d for d in data_files if d not in comp_cols]
    S.append('<section id="matrix"><h2>Who touches which file</h2><p class="lede">Hover a badge for '
             'line numbers.</p><h3>Component files</h3>' + matrix(comp_cols) +
             ('<h3 class="gap">Exports and database</h3>' + matrix(other_cols) if other_cols else "") +
             '</section>')

    # data layer API
    def direct_ops(f, fn):
        ops = defaultdict(set)
        for a in m.accesses:
            if a["code"] == f and a["scope"] == fn and a["action"] not in ("open", "close"):
                for t in a["targets"]:
                    ops[t].add(a["action"])
        return ops

    for ns, nsi in m.namespaces.items():
        rows = ""
        for fn, line in nsi["functions"].items():
            acts = [a for a in m.accesses if a["code"] == nsi["file"] and a["scope"] == fn]
            ops = defaultdict(set)
            for a in acts:
                for t in a["targets"]:
                    if a["action"] not in ("open", "close"):
                        ops[t].add(a["action"])
            used_inside = sorted({c["target"].split(".")[1] for c in m.calls
                                  if c["code"] == nsi["file"] and c["scope"] == fn})
            callers = sorted({(c["code"], c["line"]) for c in m.calls
                              if c["target"] == f"{ns}.{fn}" and not c.get("internal")})
            by_file = defaultdict(list)
            for c, l in callers:
                by_file[c].append(l)
            files_html = "<br>".join(f'{link(m, t)} ' + "".join(badge(x) for x in ACTION_ORDER if x in o)
                                     for t, o in ops.items())
            if not files_html:
                via = [(u, t, o) for u in used_inside for t, o in direct_ops(nsi["file"], u).items()]
                files_html = "<br>".join(f'{link(m, t)} ' + "".join(badge(x) for x in ACTION_ORDER if x in o)
                                         + f' <span class="muted">via {E(u)}</span>' for u, t, o in via) \
                    or '<span class="muted">—</span>'
            rows += (f'<tr><td><code>{E(ns)}.{E(fn)}</code>'
                     f'{"<span class=muted> (helper)</span>" if fn in m.wrappers or fn[0].islower() else ""}</td>'
                     f'<td>{files_html}</td>'
                     f'<td>{", ".join(f"<code>{E(u)}</code>" for u in used_inside) or "<span class=muted>—</span>"}</td>'
                     f'<td>{"<br>".join(f"{link(m, c)} <span class=muted>line {E(", ".join(map(str, ls)))}</span>" for c, ls in by_file.items()) or "<span class=muted>not called from outside</span>"}</td></tr>')
        S.append(f'<section id="api-{E(ns)}"><h2>The {E(ns)} layer</h2><p class="lede">{link(m, nsi["file"])}: '
                 f'what each function touches and who calls it.</p><div class="scroll"><table class="grid">'
                 f'<thead><tr><th>Function</th><th>Files and actions</th><th>Uses</th><th>Called from</th></tr>'
                 f'</thead><tbody>{rows}</tbody></table></div></section>')

    # lineage
    lin = ""
    for d in [x for x in data_files if kind_of_node(x) == "dcf"]:
        info = m.data.get(d, {})
        exp = info.get("export")
        tables = sorted(t for t, ti in m.tables.items() if Path(d).stem in ti["sources"])
        lin += (f'<tr><td>{link(m, d)}</td><td>{link(m, exp) if exp else "<span class=muted>not exported</span>"}</td>'
                f'<td>{" ".join(f"<code>{E(t)}</code>" for t in tables) or "<span class=muted>—</span>"}</td></tr>')
    def built_by(ti):
        if not ti.get("builder"):
            return "—"
        return link(m, ti["builder"]) + f' <span class="muted">line {ti["line"]}</span>'

    if m.tables:
        trows = "".join(
            f'<tr><td><code>{E(t)}</code></td><td>{", ".join(E(c) for c in ti.get("columns", [])) or "<span class=muted>?</span>"}</td>'
            f'<td class="num">{ti.get("rows", "—")}</td><td>{", ".join(E(s) + ".jsonl" for s in sorted(ti["sources"])) or "—"}</td>'
            f'<td>{built_by(ti)}</td></tr>'
            for t, ti in sorted(m.tables.items()))
        S.append('<section id="lineage"><h2>Data lineage: component file → export → SQL tables</h2>'
                 '<div class="scroll"><table class="grid"><thead><tr><th>Component file</th><th>Export</th>'
                 f'<th>Tables</th></tr></thead><tbody>{lin}</tbody></table></div>'
                 '<h3>Tables in the database</h3><div class="scroll"><table class="grid"><thead><tr><th>Table</th>'
                 '<th>Columns</th><th>Rows</th><th>Loaded from</th><th>Built by</th></tr></thead>'
                 f'<tbody>{trows}</tbody></table></div></section>')

    # findings
    if findings:
        S.append('<section id="findings"><h2>Findings for a migration</h2>' + "".join(
            f'<div class="finding {k}"><h3>{E(t)}</h3><div>{b}</div></div>' for k, t, b in findings) + "</section>")

    # per-file details
    cards = ""
    for c in code_files:
        i = m.code[c]
        acc = [a for a in m.accesses if a["code"] == c]
        acc_rows = "".join(
            f'<tr><td class="num">{a["line"]}</td><td>{E(a["scope"])}</td><td>{badge(a["action"])}</td>'
            f'<td><code>{E(a["op"])}</code>{(" comp " + str(a["comp"])) if isinstance(a["comp"], int) else (" (release)" if a["comp"] == "release" else "")}</td>'
            f'<td>{", ".join(link(m, t) if t in m.data else E(t) for t in a["targets"])}</td>'
            f'<td><code class="snip">{E(a["snippet"][:110])}</code></td></tr>' for a in acc)
        fns = [s for s in i["scopes"] if s[1] in ("function", "dfn")]
        calls_out = sorted({x["target"] for x in m.calls if x["code"] == c and not x.get("internal")})
        loads = sorted({x["target"] for x in m.loads if x["code"] == c})
        used_by = sorted({x["code"] for x in m.calls if not x.get("internal") and
                          m.namespaces.get(x["target"].split(".")[0], {}).get("file") == c} |
                         {x["code"] for x in m.loads if x["target"] == c})
        meta = []
        if i.get("run"):
            meta.append(f'<div><span class="k">Run</span><code>{E(i["run"])}</code></div>')
        if fns:
            meta.append('<div><span class="k">Defines</span>' + " ".join(
                f'<code title="line {s[2]}">{E(s[0])}</code>' for s in fns) + "</div>")
        if calls_out:
            meta.append('<div><span class="k">Calls</span>' + " ".join(f"<code>{E(x)}</code>" for x in calls_out) + "</div>")
        if loads:
            meta.append('<div><span class="k">Loads</span>' + " ".join(link(m, x) for x in loads) + "</div>")
        if used_by:
            meta.append('<div><span class="k">Used by</span>' + " ".join(link(m, x) for x in used_by) + "</div>")
        if i.get("assertions"):
            meta.append(f'<div><span class="k">Checks</span>{i["assertions"]} assertions</div>')
        if i.get("verifies"):
            meta.append('<div><span class="k">Verifies</span>compares the database with export/checks.json</div>')
        desc = " ".join(x for x in i["comments"] if x and "Run:" not in x and not x.startswith("python"))
        cards += (f'<article class="card" id="{anchor(c)}"><header><h3>{E(c)}</h3>'
                  f'<span class="tag">{E(i["kind"])}</span><span class="muted">{i["lines"]} lines · {E(i["lang"])}</span></header>'
                  f'<p>{E(desc[:420])}{"…" if len(desc) > 420 else ""}</p><div class="meta">{"".join(meta)}</div>'
                  + (f'<details><summary>{len(acc)} file actions</summary><div class="scroll"><table class="grid small">'
                     f'<thead><tr><th>Line</th><th>In</th><th>Action</th><th>Call</th><th>File</th><th>Code</th></tr></thead>'
                     f'<tbody>{acc_rows}</tbody></table></div></details>' if acc else "")
                  + "</article>")
    S.append(f'<section id="code"><h2>Code files</h2>{cards}</section>')

    # data file cards
    dcards = ""
    for d in data_files:
        i = m.data.get(d, {"exists": True})
        users = defaultdict(set)
        for (c, dd), acts in mat.items():
            if dd == d:
                users[c] |= set(acts)
        urows = " ".join(f'{link(m, c)} ' + "".join(badge(a) for a in ACTION_ORDER if a in acts and a != "close")
                         for c, acts in sorted(users.items()))
        size = f'{i["size"]:,} bytes' if i.get("size") else ""
        status = "" if i.get("exists", True) else '<span class="tag warn">not on disk</span>'
        contents = ""
        if i.get("contents"):
            groups = []
            for comp in i["contents"]:
                sig = (comp["kind"], comp["detail"] if comp["kind"] != "nested" else "")
                if groups and groups[-1]["sig"] == sig:
                    groups[-1]["to"] = comp["n"]
                else:
                    groups.append({"sig": sig, "from": comp["n"], "to": comp["n"], "detail": comp["detail"]})
            contents = '<table class="grid small"><thead><tr><th>Components</th><th>Kind</th><th>Shape / fields</th></tr></thead><tbody>' + "".join(
                f'<tr><td class="num">{g["from"]}{"–" + str(g["to"]) if g["to"] != g["from"] else ""}</td>'
                f'<td>{E(g["sig"][0])}</td><td><code>{E(g["detail"])}</code></td></tr>' for g in groups) + "</tbody></table>"
            contents = f'<p class="muted">Contents, from {link(m, i["export"])}:</p>' + contents
        dcards += (f'<article class="card data-card" id="{anchor(d)}"><header><h3>{E(d)}</h3>'
                   f'<span class="tag t-{kind_of_node(d)}">{E(node_label(m, d)[1].split(" · ")[0])}</span>'
                   f'<span class="muted">{size}</span>{status}</header>'
                   f'<div class="meta"><div><span class="k">Used by</span>{urows}</div></div>{contents}</article>')
    S.append(f'<section id="data"><h2>Data files</h2>{dcards}</section>')

    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in
                  [("graph", "Graph"), ("pipeline", "Run order"), ("matrix", "Matrix"),
                   *[(f"api-{ns}", ns) for ns in m.namespaces], ("lineage", "Lineage"),
                   ("findings", "Findings"), ("code", "Code"), ("data", "Data")])
    page = TEMPLATE.replace("{{TITLE}}", "Code map").replace("{{FOLDER}}", E(m.root.name)) \
        .replace("{{WHEN}}", datetime.now().strftime("%Y-%m-%d %H:%M")).replace("{{NAV}}", nav) \
        .replace("{{BODY}}", "\n".join(S))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return m, edges, findings


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a64;--line:#dedbd2;--card:#ffffff;--soft:#f2f0ea;
--write:#2f6fd6;--read:#8a887f;--both:#8a4fd1;--uses:#1f9a76;--lock:#c27c0e;--del:#c8443a;
--code:#e7effc;--dcf:#fbf0dc;--json:#e5f4ee;--temp:#f1f0ec;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ecebe6;--muted:#9c9a92;
--line:#34343a;--card:#1f1f23;--soft:#27272c;--write:#6ea2ff;--read:#8f8d86;--both:#b88bf2;--uses:#4fc9a2;
--lock:#e2a33c;--del:#ef7468;--code:#1f2c44;--dcf:#3a2f1c;--json:#1b3a31;--temp:#2a2a2e;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ecebe6;--muted:#9c9a92;--line:#34343a;--card:#1f1f23;--soft:#27272c;
--write:#6ea2ff;--read:#8f8d86;--both:#b88bf2;--uses:#4fc9a2;--lock:#e2a33c;--del:#ef7468;--code:#1f2c44;
--dcf:#3a2f1c;--json:#1b3a31;--temp:#2a2a2e;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif,"Apple Symbols","Segoe UI Symbol","DejaVu Sans"}
code{font:12.5px/1.4 ui-monospace,SFMono-Regular,Menlo,"Apple Symbols","DejaVu Sans Mono",monospace}
a{color:inherit;text-decoration-color:var(--line);text-underline-offset:2px}a:hover{text-decoration-color:currentColor}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 64px}
.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;gap:18px;align-items:center;padding-bottom:0;height:48px;overflow-x:auto;white-space:nowrap}
.top strong{font-weight:650}.top nav{display:flex;gap:14px;font-size:13.5px;color:var(--muted)}
.top nav a{text-decoration:none}.top nav a:hover{color:var(--fg)}
h1{font-size:28px;line-height:1.2;margin:36px 0 6px;letter-spacing:-.01em}
h2{font-size:19px;margin:44px 0 6px}h3{font-size:15px;margin:0}
.lede,.muted{color:var(--muted)}.lede{margin:0 0 14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:22px 0 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:24px;font-variant-numeric:tabular-nums}.stat span{color:var(--muted);font-size:13px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.graph{min-width:760px;width:100%;height:auto;display:block;background:var(--card);border:1px solid var(--line);border-radius:12px}
.graph .n rect{stroke:var(--line);stroke-width:1}
.graph .n.code rect{fill:var(--code)}.graph .n.dcf rect{fill:var(--dcf)}
.graph .n.json rect,.graph .n.db rect{fill:var(--json)}.graph .n.temp rect{fill:var(--temp);stroke-dasharray:4 3}
.graph .n.missing rect{stroke-dasharray:4 3;opacity:.7}
.graph .n{cursor:pointer}.graph .n:focus{outline:none}.graph .n:focus rect{stroke:var(--fg)}
.graph .nt{font:600 12.5px system-ui,sans-serif;fill:var(--fg)}.graph .ns{font:11px system-ui,sans-serif;fill:var(--muted)}
.graph .e{fill:none;stroke-width:1.6;transition:opacity .15s}
.e-write{stroke:var(--write)}.e-read{stroke:var(--read);stroke-dasharray:5 4}.e-both{stroke:var(--both)}.e-uses{stroke:var(--uses);stroke-dasharray:2 3}
.mk-write{fill:var(--write)}.mk-read{fill:var(--read)}.mk-both{fill:var(--both)}.mk-uses{fill:var(--uses)}
.graph .el{font:10.5px system-ui,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--card);stroke-width:4px;stroke-linejoin:round;opacity:0;transition:opacity .15s}
.graph.focus .e{opacity:.12}.graph.focus .n{opacity:.35}
.graph.focus .e.on{opacity:1;stroke-width:2.2}.graph.focus .n.on{opacity:1}.graph.focus .el.on{opacity:1}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font-size:13px;color:var(--muted);margin:0 0 10px}
.lg{display:inline-block;width:26px;height:0;border-top:2px solid;vertical-align:middle;margin-right:-8px}
.lg-write{border-color:var(--write)}.lg-read{border-color:var(--read);border-top-style:dashed}.lg-both{border-color:var(--both)}.lg-uses{border-color:var(--uses);border-top-style:dotted}
.sw{display:inline-block;width:14px;height:14px;border-radius:4px;border:1px solid var(--line);vertical-align:-2px;margin-right:-8px}
.sw.code{background:var(--code)}.sw.dcf{background:var(--dcf)}.sw.json{background:var(--json)}
table{border-collapse:collapse;width:100%}
.grid th,.grid td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.grid th{font-size:12.5px;font-weight:600;color:var(--muted)}
.grid.small td,.grid.small th{padding:5px 8px;font-size:13px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.matrix{width:auto;min-width:100%}
.matrix th,.matrix td{padding:7px 9px;border:1px solid var(--line);font-size:13px}
.matrix thead th{background:var(--soft);font-weight:600;white-space:nowrap}
.matrix tbody th{text-align:left;font-weight:500;white-space:nowrap;background:var(--soft)}
.matrix td.empty{background:var(--card)}.matrix td{background:var(--card);white-space:nowrap}
.b{display:inline-block;font-size:11.5px;line-height:1;padding:4px 7px;border-radius:999px;margin:1px 3px 1px 0;border:1px solid transparent}
.b-w{background:color-mix(in srgb,var(--write) 16%,transparent);color:var(--write)}
.b-r{background:color-mix(in srgb,var(--read) 16%,transparent);color:var(--fg)}
.b-l{background:color-mix(in srgb,var(--lock) 18%,transparent);color:var(--lock)}
.b-x{background:color-mix(in srgb,var(--del) 16%,transparent);color:var(--del)}
.b-o{border-color:var(--line);color:var(--muted)}
.gap{margin-top:22px}.matrix{margin-top:8px}
.steps{padding-left:22px}.steps li{margin:4px 0}
.finding{border:1px solid var(--line);border-left:4px solid var(--read);background:var(--card);border-radius:8px;padding:12px 14px;margin:10px 0}
.finding.warn{border-left-color:var(--lock)}.finding.ok{border-left-color:var(--uses)}.finding.info{border-left-color:var(--write)}
.finding h3{margin-bottom:4px}.finding ul{margin:6px 0 0;padding-left:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0;scroll-margin-top:64px}
.card header{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}
.card p{margin:8px 0}
.tag{font-size:11.5px;padding:2px 8px;border-radius:999px;background:var(--soft);border:1px solid var(--line)}
.tag.warn{color:var(--lock)}
.meta{display:grid;gap:6px;font-size:13.5px}.meta .k{display:inline-block;min-width:74px;color:var(--muted)}
.meta code{background:var(--soft);padding:1px 5px;border-radius:4px;margin-right:2px}
details{margin-top:10px}summary{cursor:pointer;color:var(--muted);font-size:13.5px}
.snip{white-space:pre;color:var(--muted)}
footer{margin-top:48px;color:var(--muted);font-size:13px}
@media (max-width:640px){h1{font-size:23px}.meta .k{display:block}}
</style></head>
<body>
<div class="top"><div class="wrap"><strong>{{TITLE}}</strong><nav>{{NAV}}</nav></div></div>
<main class="wrap">
<h1>{{FOLDER}}</h1>
<p class="lede">Generated {{WHEN}} by code-map.py from the source code, the exports and the database.
Pattern-based: a strong first draft, not a proof.</p>
{{BODY}}
<footer>Re-run <code>python3 code-map.py</code> after changing the code to refresh this page.</footer>
</main>
<script>
(function(){
  var g=document.querySelector('.graph'); if(!g) return;
  function on(id){
    g.classList.add('focus');
    var hit={}; hit[id]=1;
    g.querySelectorAll('[data-a]').forEach(function(e){
      var a=e.getAttribute('data-a'),b=e.getAttribute('data-b'),x=(a===id||b===id);
      e.classList.toggle('on',x); if(x){hit[a]=1;hit[b]=1;}
    });
    g.querySelectorAll('.n').forEach(function(n){n.classList.toggle('on',!!hit[n.getAttribute('data-id')]);});
  }
  function off(){g.classList.remove('focus');g.querySelectorAll('.on').forEach(function(e){e.classList.remove('on');});}
  g.querySelectorAll('.n').forEach(function(n){
    var id=n.getAttribute('data-id');
    n.addEventListener('mouseenter',function(){on(id);});
    n.addEventListener('focus',function(){on(id);});
    n.addEventListener('mouseleave',off); n.addEventListener('blur',off);
    n.addEventListener('click',function(){
      var t=document.getElementById('f-'+id.replace(/[^\\w]/g,'-')); if(t) t.scrollIntoView({behavior:'smooth'});
    });
  });
})();
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", nargs="?", default=Path(__file__).resolve().parent, type=Path)
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()
    root = args.folder.resolve()
    out = args.out or root / "export" / "code-map.html"
    m = build(root)
    _, edges, findings = render(m, out)
    print(f"Scanned {len(m.code)} source files, {len(m.accesses)} file actions, "
          f"{len(edges)} relationships, {len(findings)} findings")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
