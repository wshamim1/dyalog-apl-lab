"""Component file viewer and diff in the browser. No APL knowledge needed.

    .venv/bin/streamlit run dcf-tools/dcf_app.py

View: pick a .dcf file and see every component (what it is, size, when it
was written) and its contents as tables. Compare: two files, two folders, or
a folder against a snapshot, and see exactly what changed: which component,
which field, which cell, old value and new value.

The reading happens in APL (DCF.apln) in the Dyalog container, through
dcf.py. Files are mounted read-only and never changed.
"""

import importlib.util
import json
import tempfile
from pathlib import Path

import sqlite3
import sys

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dcf", HERE / "dcf.py")
dcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dcf)
sys.path.insert(0, str(HERE))
import ddl  # noqa: E402  (dcf-tools/ddl.py)

DEFAULT = HERE.parent / "sample-scripts" / "component-files" / "data"
STATUS = {"changed": "🟡 changed", "added": "🟢 added", "removed": "🔴 removed", "same": "⚪ same"}

st.set_page_config(page_title="Component file viewer", page_icon="🗂️", layout="wide")


# ── data, cached by path + modification time + size ──────────────────────────

def stamp(p):
    s = Path(p).stat()
    return s.st_mtime, s.st_size


@st.cache_data(show_spinner=False, max_entries=64)
def cached_dump(path, _stamp):
    return dcf.dump(path)


@st.cache_data(show_spinner=False, max_entries=32)
def cached_diff(old, new, _stamps):
    return dcf.diff(old, new)


def stamps(*paths):
    out = []
    for p in paths:
        p = Path(p)
        files = sorted(p.glob("*.dcf")) if p.is_dir() else [p]
        out += [(str(f), *stamp(f)) for f in files]
    return tuple(out)


def find_dcfs(folder):
    folder = Path(folder)
    return sorted(f for f in folder.rglob("*.dcf") if dcf.SNAPSHOTS not in f.parts)


def rel(p, folder):
    try:
        return str(Path(p).relative_to(folder))
    except ValueError:
        return str(p)


# ── rendering values ─────────────────────────────────────────────────────────

def is_matrix(v):
    return isinstance(v, list) and v and all(isinstance(r, list) for r in v) \
        and len({len(r) for r in v}) == 1 and not any(isinstance(x, (list, dict)) for r in v for x in r)


def tidy(df):
    """Columns mixing numbers and text become text (tables need one type per column)."""
    for col in df.columns:
        if df[col].map(type).nunique() > 1:
            df[col] = df[col].map(fmt)
    return df


def grid(rows):
    df = tidy(pd.DataFrame(rows))
    df.index = range(1, len(df) + 1)
    df.columns = range(1, len(df.columns) + 1)
    return df


def show_value(v, kind="", key=""):
    """Show a component's value the way it reads best."""
    if isinstance(v, dict):
        fns = v.get("apl_functions")
        fields = {k: x for k, x in v.items() if k != "apl_functions"}
        simple = {k: x for k, x in fields.items() if not isinstance(x, (list, dict)) or
                  (isinstance(x, list) and not any(isinstance(i, (list, dict)) for i in x) and len(x) <= 12)}
        if simple:
            st.dataframe(pd.DataFrame({"field": list(simple), "value": [fmt(x) for x in simple.values()]}),
                         hide_index=True, width="stretch")
        for k, x in fields.items():
            if k not in simple:
                st.markdown(f"**{k}**")
                show_value(x, key=f"{key}.{k}")
        if fns:
            st.caption("Functions in this namespace: " + ", ".join(fns))
    elif is_matrix(v):
        st.dataframe(grid(v), width="stretch")
    elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
        st.dataframe(tidy(pd.DataFrame(v)), width="stretch")
    elif isinstance(v, list) and "boolean" in kind:
        ones = [i for i, x in enumerate(v, 1) if x]
        st.write(f"{len(v)} flags, {len(ones)} set: positions {', '.join(map(str, ones[:200]))}"
                 f"{' …' if len(ones) > 200 else ''}")
    elif isinstance(v, list):
        st.dataframe(pd.DataFrame({"position": range(1, len(v) + 1), "value": [fmt(x) for x in v]}),
                     hide_index=True, width="stretch")
    elif isinstance(v, str):
        st.code(v, language=None)
    else:
        st.write(v)


def fmt(x):
    if isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        return f"{x:g}" if isinstance(x, float) else str(x)
    return json.dumps(x, ensure_ascii=False)


# ── rendering diffs ──────────────────────────────────────────────────────────

def where(at):
    return f"[{at}]" if not isinstance(at, list) else "[" + ";".join(map(str, at)) + "]"


def flatten(d, prefix=""):
    """A component's detail as rows: where, what, old, new."""
    rows = []
    how = d.get("how")
    if how == "fields":
        for x in d.get("changes", []):
            name = f"{prefix}{x['field']}"
            if x["status"] == "changed" and "detail" in x:
                rows += flatten(x["detail"], name + " ")
            else:
                rows.append((name, x["status"], x.get("old_text", ""), x.get("new_text", "")))
    elif how in ("items", "cells"):
        for x in d.get("changes", []):
            name = f"{prefix}{where(x['at'])}"
            if "detail" in x:
                rows += flatten(x["detail"], name + " ")
            else:
                rows.append((name, "changed", x["old_text"], x["new_text"]))
        more = d.get("changed", 0) - len(d.get("changes", []))
        if more > 0:
            rows.append((prefix.strip() or "…", f"{more} more changed", "", ""))
        if "added" in d:
            rows.append((f"{prefix}from [{d['added_from']}]", "added", "", d["added_text"]))
        if "removed" in d:
            rows.append((f"{prefix}from [{d['removed_from']}]", "removed", d["removed_text"], ""))
    else:
        rows.append((prefix.strip() or "whole value", "changed", d.get("old_text", ""), d.get("new_text", "")))
    return rows


def show_file_diff(r, title=None):
    counts = {k: r.get(k, 0) for k in ("changed", "added", "removed", "same")}
    if title:
        st.markdown(f"#### {title}")
    cols = st.columns(4)
    for col, k in zip(cols, counts):
        col.metric(STATUS[k], counts[k])
    if not r.get("components"):
        st.success("No differences: every component matches.")
        return
    for c in r["components"]:
        label = f"{STATUS[c['status']]}  ·  component {c['component']}  ·  {c.get('kind', '')}"
        with st.expander(label, expanded=c["status"] == "changed"):
            if c["status"] == "changed":
                rows = flatten(c["detail"])
                st.dataframe(pd.DataFrame(rows, columns=["where", "change", "old", "new"]),
                             hide_index=True, width="stretch")
                om, nm = c.get("old_meta", {}), c.get("new_meta", {})
                st.caption(f"written {om.get('written', '?')} → {nm.get('written', '?')} · "
                           f"{om.get('bytes', '?')} → {nm.get('bytes', '?')} bytes")
            elif c["status"] == "added":
                st.write("New component:")
                show_value(c.get("new"), c.get("kind", ""), key=f"add{c['component']}")
            else:
                st.write("Removed component, which held:")
                show_value(c.get("old"), c.get("kind", ""), key=f"rem{c['component']}")


def show_diff(r):
    if "files" in r:
        files = r["files"]
        st.write(" · ".join(f"**{f['name']}.dcf** {STATUS[f['status']]}" for f in files))
        for f in files:
            if f["status"] in ("added", "removed"):
                st.markdown(f"#### {f['name']}.dcf")
                st.info(f"{'New file' if f['status'] == 'added' else 'File removed'}")
            else:
                show_file_diff(f, f"{f['name']}.dcf")
    else:
        show_file_diff(r)
    st.download_button("⬇️ Download the diff (JSON)", json.dumps(r, ensure_ascii=False, indent=1),
                       file_name="dcf-diff.json", mime="application/json")


# ── page ─────────────────────────────────────────────────────────────────────

st.title("🗂️ Component file viewer")
st.caption("Look inside Dyalog component files (.dcf) and see what changed. Read-only: files are never modified.")

with st.sidebar:
    st.header("Folder")
    st.session_state.setdefault("folder", str(DEFAULT))
    folder = Path(st.text_input("Folder with .dcf files", key="folder").strip()).expanduser()
    up = st.file_uploader("…or upload .dcf files", type=["dcf"], accept_multiple_files=True)
    if up:
        tmp = Path(st.session_state.setdefault("upload_dir", tempfile.mkdtemp(prefix="dcf-upload-")))
        for f in up:
            (tmp / f.name).write_bytes(f.getbuffer())
        st.caption(f"Uploaded to a temporary folder: {', '.join(f.name for f in up)}")
    st.divider()
    st.caption("Reading uses the Dyalog container (or DYALOGSCRIPT, if set). "
               "The first read of a file takes a second or two; after that it's cached.")

if not folder.is_dir():
    st.error(f"Not a folder: `{folder}`")
    st.stop()

files = find_dcfs(folder)
upload_dir = st.session_state.get("upload_dir")
uploads = sorted(Path(upload_dir).glob("*.dcf")) if upload_dir else []
choices = {rel(f, folder): f for f in files} | {f"uploaded: {f.name}": f for f in uploads}
snaps = dcf.snapshots(folder)

view_tab, diff_tab, sql_tab = st.tabs(["🔍 View", "⚖️ Compare", "🧱 SQL tables"])

with view_tab:
    if not choices:
        st.info(f"No .dcf files in `{folder}`. Pick another folder, or upload files in the sidebar.")
    else:
        name = st.selectbox("File", list(choices))
        path = choices[name]
        try:
            with st.spinner(f"Reading {name}…"):
                d = cached_dump(str(path), stamp(path))
        except dcf.DcfError as e:
            st.error(str(e))
            st.stop()
        comps = d["components"]
        latest = max((c["written"] for c in comps), default="—")
        m = st.columns(4)
        m[0].metric("Components", d["count"])
        m[1].metric("Numbered", f"{d['first']} – {d['next'] - 1}" if d["count"] else "—")
        m[2].metric("Size", f"{d['bytes']:,} bytes")
        m[3].metric("Last write", latest)
        if d.get("more"):
            st.warning(f"Showing the first {len(comps)} components; {d['more']} more not loaded.")
        table = pd.DataFrame([{"component": c["component"], "kind": c["kind"],
                               "shape": " × ".join(map(str, c["shape"])) or "—",
                               "bytes": c["bytes"], "written": c["written"], "value": c["text"]}
                              for c in comps])
        st.caption("Click a row to see that component in full.")
        sel = st.dataframe(table, hide_index=True, width="stretch",
                           on_select="rerun", selection_mode="single-row", key=f"tbl-{name}")
        picked = sel.selection.rows[0] if sel and sel.selection.rows else 0
        if comps:
            c = comps[picked]
            st.subheader(f"Component {c['component']}")
            st.caption(f"{c['kind']} · shape {c['shape'] or 'scalar'} · {c['bytes']} bytes · "
                       f"written {c['written']} by user {c['user']}")
            if c.get("truncated"):
                st.warning("Large value: showing the first part only.")
            show_value(c["value"], c["kind"], key=f"v{c['component']}")
            with st.expander("Raw JSON"):
                st.json(c["value"], expanded=False)

with diff_tab:
    mode = st.radio("Compare", ["Two files", "Since a snapshot", "Two folders"], horizontal=True)
    old = new = None
    if mode == "Two files":
        if len(choices) < 2 and not snaps:
            st.info("Need at least two .dcf files: pick a folder with more, or upload some.")
        else:
            snap_files = {f"snapshot {s.name}/{f.name}": f for s in snaps for f in sorted(s.glob("*.dcf"))}
            allc = choices | snap_files
            names = list(allc)
            c1, c2 = st.columns(2)
            a = c1.selectbox("Old", names, index=0)
            b = c2.selectbox("New", names, index=None, placeholder="Pick the file to compare with")
            old, new = allc[a], allc.get(b)
    elif mode == "Since a snapshot":
        c1, c2 = st.columns([3, 1])
        if c2.button("📸 Take snapshot now", width="stretch"):
            try:
                dest = dcf.snapshot(folder)
                st.toast(f"Saved snapshot {dest.name}")
                snaps = dcf.snapshots(folder)
            except dcf.DcfError as e:
                st.error(str(e))
        if not snaps:
            c1.info(f"No snapshots yet. A snapshot copies the folder's .dcf files to "
                    f"`{dcf.SNAPSHOTS}/<time>/`, so you can later see what changed since then.")
        else:
            s = c1.selectbox("Snapshot", [p.name for p in snaps])
            old, new = folder / dcf.SNAPSHOTS / s, folder
            st.caption(f"Comparing snapshot `{s}` with the files in `{folder}` now.")
    else:
        c1, c2 = st.columns(2)
        a = c1.text_input("Old folder", value=str(HERE / "demo" / "before"))
        b = c2.text_input("New folder", value=str(HERE / "demo" / "after"))
        old, new = Path(a).expanduser(), Path(b).expanduser()
        if not (old.is_dir() and new.is_dir()):
            st.warning("Both must be folders. (Make the demo ones with: dyalog dcf-tools/make-demo.apls)")
            old = new = None

    if old and new:
        if Path(old).resolve() == Path(new).resolve():
            st.info("Pick two different files.")
        else:
            try:
                with st.spinner("Comparing…"):
                    r = cached_diff(str(old), str(new), stamps(old, new))
                show_diff(r)
            except dcf.DcfError as e:
                st.error(str(e))

with sql_tab:
    st.caption("Suggested CREATE TABLE statements for the data, worked out from what each component holds. "
               "A starting point for moving the data to a database: review it before using it.")
    if not choices:
        st.info("No .dcf files to work from.")
    else:
        c1, c2 = st.columns([3, 1])
        picked = c1.multiselect("Files", list(choices), default=list(choices))
        dialect = c2.selectbox("Database", list(ddl.DIALECTS), format_func=ddl.DIALECTS.get)
        if picked:
            try:
                with st.spinner("Reading the files…"):
                    dumps = [(Path(choices[n]).name, cached_dump(str(choices[n]), stamp(choices[n])))
                             for n in picked]
            except dcf.DcfError as e:
                st.error(str(e))
                st.stop()
            sql, tables = ddl.ddl(dumps, dialect)
            check, _ = ddl.ddl(dumps, "sqlite")         # prove it's valid SQL: build it in SQLite
            try:
                sqlite3.connect(":memory:").executescript(check)
                st.success(f"{len(tables)} tables · checked: the SQLite version creates without errors")
            except sqlite3.Error as e:
                st.warning(f"SQLite couldn't create the tables: {e}")
            st.dataframe(pd.DataFrame([{"table": t.name, "rows now": t.rows, "from": t.source,
                                        "key": ", ".join(t.primary_key),
                                        "notes": "; ".join(t.notes)} for t in tables]),
                         hide_index=True, width="stretch")
            st.code(sql, language="sql")
            st.download_button("⬇️ Download .sql", sql, file_name=f"dcf-tables-{dialect}.sql", mime="text/plain")
            with st.expander("How the tables are chosen"):
                st.markdown("""
| What's in the file | Becomes |
| --- | --- |
| a namespace per component | one table, a column per field; a matrix field becomes a child table with a foreign key |
| a component of field names, then records | one table with those column names |
| a 2-column matrix with text keys | a key / value table |
| a numeric or boolean matrix | rows of (row_no, col_no, value) |
| a numeric or boolean vector | rows of (position, value) |
| anything else | `<file>_other`, each component kept whole as JSON |

Types come from the values: whole numbers → INTEGER (BIGINT if large), decimals → DECIMAL(p,s),
`YYYY-MM-DD` → DATE, text → VARCHAR(n), nested values → JSON. A column is nullable when some
components lack that field. `dcf_component` keeps each row's component number, since other data
may refer to it.
""")
