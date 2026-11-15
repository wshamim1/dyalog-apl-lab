#!/usr/bin/env python3
"""Turn the tutorials (tutorials/NN-*/README.md) into Jupyter notebooks.

    python3 notebooks/build.py            # writes notebooks/NN-*.ipynb (no outputs yet)
    install/jupyter/jupyter.sh execute    # runs them in Dyalog to fill in the outputs

Each ```apl example block becomes a code cell holding just the input lines
(the 6-space-indented ones); Dyalog produces the outputs when the notebook
runs. Prose becomes markdown cells. Kept as text, not run:
  - blocks with system commands like )save or )off (they'd act on the kernel)
  - blocks with no input lines (e.g. a tradfn's source listing)
  - solutions inside <details>, so they stay folded
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TUT = REPO / "tutorials"
OUT = REPO / "notebooks"
FENCE = re.compile(r"```apl\n(.*?)```", re.S)
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code_cell(src: str, error_expected: bool = False) -> dict:
    meta = {"tags": ["raises-exception"]} if error_expected else {}
    return {"cell_type": "code", "metadata": meta, "source": src,
            "outputs": [], "execution_count": None}


def fix_links(text: str, src_dir: Path) -> str:
    """Rewrite relative links so they work from notebooks/."""
    def repl(m: re.Match) -> str:
        target, anchor = m.group(1), m.group(2) or ""
        if re.match(r"^[a-z]+:", target):              # http:, mailto: …
            return m.group(0)
        abs_path = (src_dir / target).resolve()
        rel_to_repo = abs_path.relative_to(REPO) if REPO in abs_path.parents or abs_path == REPO else None
        if rel_to_repo is None:
            return m.group(0)
        parts = rel_to_repo.parts
        # another tutorial → its notebook
        if len(parts) == 3 and parts[0] == "tutorials" and parts[2] == "README.md":
            return f"]({parts[1]}.ipynb{anchor})"
        if rel_to_repo == Path("tutorials/README.md"):
            return f"](README.md{anchor})"
        return f"]({os.path.relpath(abs_path, OUT)}{anchor})"
    return LINK.sub(repl, text)


def convert(readme: Path) -> dict:
    text = fix_links(readme.read_text(encoding="utf-8"), readme.parent)
    cells: list[dict] = []
    pos = 0
    pending = ""            # markdown waiting to be emitted
    in_details = False

    def flush():
        nonlocal pending
        if pending.strip():
            cells.append(md_cell(pending))
        pending = ""

    for m in FENCE.finditer(text):
        before = text[pos:m.start()]
        pending += before
        # track whether we're inside a <details> (solutions) section
        opens, closes = before.count("<details"), before.count("</details>")
        in_details = (in_details or opens > closes) and not (closes > opens)
        block = m.group(1).rstrip("\n").split("\n")
        # An error display is "XXX ERROR: …", then the failing line (indented
        # like an input) and a caret line: those two are output, not input.
        inputs, outputs, skip = [], [], 0
        for ln in block:
            if skip:
                skip -= 1
                outputs.append(ln)
            elif ln.startswith("      ") and ln.strip():
                inputs.append(ln[6:])
            else:
                outputs.append(ln)
                if re.search(r"\b[A-Z]+ ERROR\b", ln):
                    skip = 2
        static = (not inputs or in_details
                  or any(i.lstrip().startswith(")") for i in inputs)
                  or any(i.lstrip().startswith("]help") for i in inputs))
        if static:
            pending += m.group(0)
        else:
            flush()
            error_expected = any(re.search(r"\b[A-Z]+ ERROR\b", o) for o in outputs)
            cells.append(code_cell("\n".join(inputs), error_expected))
        pos = m.end()
    pending += text[pos:]
    flush()
    return cells


def notebook(cells: list[dict]) -> dict:
    for i, c in enumerate(cells):
        c["id"] = f"c{i:03d}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"name": "dyalog_apl", "display_name": "Dyalog APL", "language": "apl"},
            "language_info": {"name": "apl", "file_extension": ".apl", "mimetype": "text/apl"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }


def main() -> None:
    made = []
    for readme in sorted(TUT.glob("[0-9][0-9]-*/README.md")):
        name = readme.parent.name
        cells = convert(readme)
        if name != "00-getting-started":
            # the tutorials assume boxed display (00 shows how to turn it on)
            cells.insert(1, md_cell("Run this first: it turns on boxed display for nested arrays."))
            cells.insert(2, code_cell("]box on"))
        path = OUT / f"{name}.ipynb"
        path.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n_code = sum(c["cell_type"] == "code" for c in cells)
        made.append(f"  {path.name:<32} {n_code:>3} code cells")
    print("Wrote:\n" + "\n".join(made))


if __name__ == "__main__":
    main()
