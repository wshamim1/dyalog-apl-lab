"""Code map in the browser: pick any folder of APL code, get the report.

    .venv/bin/streamlit run sample-scripts/component-files/code_map_app.py

A thin UI over code-map.py: type a folder path, click Generate, and the full
report (graph, file matrix, Store layer, lineage, findings) appears below,
with a download button. Nothing is written into the scanned folder unless you
tick "Also save".
"""

import importlib.util
import re
import tempfile
import time
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent

# code-map.py has a hyphen in its name, so load it by path
_spec = importlib.util.spec_from_file_location("code_map", HERE / "code-map.py")
code_map = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(code_map)

TOO_MANY = 20_000          # files: past this, scanning gets slow; ask first

st.set_page_config(page_title="APL code map", page_icon="🗺️", layout="wide")
st.title("🗺️ APL code map")
st.caption("Which code touches which component file, how the pieces relate, and what a migration "
           "would need to deal with. Reads the source as text: Dyalog is not needed.")


def scan_folder(folder: Path):
    """Quick look before the real scan: how many files, how many are APL or Python."""
    total = apl = py = 0
    for p in folder.rglob("*"):
        if p.is_file() and not any(x.startswith(".") for x in p.relative_to(folder).parts):
            total += 1
            apl += p.suffix in code_map.APL_EXT
            py += p.suffix == ".py"
            if total > TOO_MANY:
                break
    return total, apl, py


def generate(folder: Path):
    t0 = time.perf_counter()
    m = code_map.build(folder)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "code-map.html"
        _, edges, findings = code_map.render(m, out)
        page = out.read_text(encoding="utf-8")
    return {
        "folder": str(folder), "page": page, "seconds": time.perf_counter() - t0,
        "sources": len(m.code), "actions": len(m.accesses), "edges": len(edges),
        "dcf": sum(1 for d in m.data if code_map.kind_of_node(d) == "dcf"),
        "tables": len(m.tables), "findings": findings,
    }


with st.form("pick"):
    st.session_state.setdefault("folder", str(HERE))
    folder_text = st.text_input("Folder to scan", key="folder",
                                help="Any local folder. ~ works. Subfolders are included; hidden folders are skipped.")
    c1, c2 = st.columns([1, 3])
    save = c2.checkbox("Also save to <folder>/export/code-map.html", value=False)
    go = c1.form_submit_button("Generate report", type="primary", use_container_width=True)

if go:
    folder = Path(folder_text).expanduser().resolve()
    if not folder.is_dir():
        st.session_state.pop("report", None)
        st.error(f"Not a folder: `{folder}`")
        st.stop()
    total, apl, py = scan_folder(folder)
    if total > TOO_MANY and not st.session_state.get("confirm_big") == str(folder):
        st.warning(f"`{folder}` has more than {TOO_MANY:,} files, so the scan may be slow. "
                   "Click Generate again to scan it anyway, or pick a smaller folder.")
        st.session_state["confirm_big"] = str(folder)
        st.stop()
    if apl == 0:
        st.session_state.pop("report", None)
        st.warning(f"No APL source files ({', '.join(sorted(code_map.APL_EXT))}) in `{folder}`. "
                   "The report would be empty.")
        st.stop()
    with st.spinner(f"Reading {apl} APL and {py} Python files…"):
        try:
            st.session_state["report"] = generate(folder)
        except Exception as e:                      # show, don't crash the app
            st.exception(e)
            st.stop()
    if save:
        out = folder / "export" / "code-map.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(st.session_state["report"]["page"], encoding="utf-8")
        st.success(f"Saved `{out}`")

r = st.session_state.get("report")
if not r:
    st.info("Pick a folder and click **Generate report**. The default is the component-files example.")
    st.stop()

st.subheader(Path(r["folder"]).name)
st.caption(f"`{r['folder']}` · scanned in {r['seconds']:.1f}s")
cols = st.columns(5)
for col, (label, value) in zip(cols, [("Source files", r["sources"]), ("File actions", r["actions"]),
                                      ("Relationships", r["edges"]), ("Component files", r["dcf"]),
                                      ("SQL tables", r["tables"])]):
    col.metric(label, value)

if r["findings"]:
    with st.expander(f"Findings ({len(r['findings'])})", expanded=True):
        show = {"warn": st.warning, "ok": st.success, "info": st.info}
        for kind, title, body in r["findings"]:
            text = re.sub(r"<li>", "\n- ", body)
            text = re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&")
            show.get(kind, st.info)(f"**{title}**  \n{text}")

name = re.sub(r"[^\w-]", "-", Path(r["folder"]).name) or "code"
st.download_button("⬇️ Download the report (HTML)", r["page"], file_name=f"code-map-{name}.html",
                   mime="text/html")
st.divider()
# The report escapes everything it takes from the scanned code, so it's safe to embed
st.iframe(r["page"], height=1600)
