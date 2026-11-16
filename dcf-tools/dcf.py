"""Component file viewer and diff, for .dcf files anywhere on your machine.

    python3 dcf-tools/dcf.py view FILE.dcf            list the components
    python3 dcf-tools/dcf.py view FILE.dcf 5          show component 5 in full
    python3 dcf-tools/dcf.py diff OLD NEW             compare two files, or two folders
    python3 dcf-tools/dcf.py snapshot FOLDER          copy FOLDER's .dcf files to FOLDER/.dcf-snapshots/<time>/
    python3 dcf-tools/dcf.py changes FOLDER           what changed since the last snapshot
    python3 dcf-tools/dcf.py dump FILE.dcf            everything about a file, as JSON
    python3 dcf-tools/dcf.py ddl FILE.dcf|FOLDER --dialect mysql
                                                      suggest SQL tables (CREATE TABLE) for the data

Python can't read component files (they're Dyalog's own format), so the
reading and comparing happen in APL (DCF.apln) inside the Dyalog container.
The folders holding your files are mounted read-only: nothing is ever
changed. With a native Dyalog, set DYALOGSCRIPT=/path/to/dyalogscript and
the container isn't used.

diff and changes exit with 0 when nothing changed and 1 when something did,
so they also work in scripts and CI.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TOOL = Path(__file__).resolve().parent
IMAGE = os.environ.get("IMAGE", "docker.io/dyalog/dyalog")
SNAPSHOTS = ".dcf-snapshots"


class DcfError(RuntimeError):
    pass


def engine():
    e = os.environ.get("DYALOG_ENGINE")
    if e:
        return e
    for e in ("podman", "docker"):
        if shutil.which(e):
            return e
    raise DcfError("Neither podman nor docker found. Install one (see install/dyalog), "
                   "or set DYALOGSCRIPT to a native dyalogscript.")


def run_apl(args, paths=(), out_dir=None):
    """Run dcf.apls with args. paths: the host paths among args (files or folders),
    which get mounted read-only. Returns (exit code, output text)."""
    local = os.environ.get("DYALOGSCRIPT")
    if local:                                   # native Dyalog: real paths, no container
        cmd = [local, str(TOOL / "dcf.apls"), *args]
    else:
        mounts = {}
        for p in paths:
            p = Path(p).resolve()
            folder = p if p.is_dir() else p.parent
            if folder not in mounts:
                mounts[folder] = f"/data/{len(mounts) + 1}"
        def inside(a):
            p = Path(a).resolve() if a in paths else None
            if p is None:
                if out_dir and Path(a).parent == Path(out_dir):
                    return f"/out/{Path(a).name}"
                return a
            folder = p if p.is_dir() else p.parent
            return mounts[folder] + ("" if p.is_dir() else f"/{p.name}")
        mapped = [inside(a) for a in args]
        vols = []
        for folder, target in mounts.items():
            vols += ["-v", f"{folder}:{target}:ro"]
        if out_dir:
            vols += ["-v", f"{out_dir}:/out"]
        vols += ["-v", f"{TOOL}:/tool:ro"]
        cmd = [engine(), "run", "-i", "--rm", *vols, "--entrypoint", "dyalogscript", IMAGE,
               "/tool/dcf.apls", *mapped]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    # dyalogscript ends lines with a bare \r when not on a terminal
    text = (p.stdout + p.stderr).replace("\r\n", "\n").replace("\r", "\n")
    if not local:                               # show the user's own paths, not the container's
        for folder, target in sorted(mounts.items(), key=lambda m: -len(m[1])):
            text = text.replace(target, str(folder))
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return p.returncode, text.rstrip("\n")


def check_exists(*paths):
    for p in paths:
        if not Path(p).exists():
            raise DcfError(f"not found: {p}")


def _json(cmd, paths):
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "out.json")
        code, text = run_apl([cmd, *map(str, paths), out], paths=list(map(str, paths)), out_dir=tmp)
        if code != 0 or not Path(out).exists():
            raise DcfError(text or f"dcf.apls {cmd} failed (exit {code})")
        return json.loads(Path(out).read_text(encoding="utf-8"))


def dump(file):
    """Everything about one .dcf file: info plus each component (kind, size, time, value)."""
    check_exists(file)
    return _json("dump", [file])


def diff(old, new):
    """Compare two .dcf files, or two folders of them. Returns the structured diff."""
    check_exists(old, new)
    if Path(old).resolve() == Path(new).resolve():
        raise DcfError("Both are the same file or folder.")
    return _json("diffjson", [old, new])


def dcf_files(paths):
    """The .dcf files named by paths (files, or folders: their *.dcf)."""
    out = []
    for p in map(Path, paths):
        check_exists(p)
        out += sorted(p.glob("*.dcf")) if p.is_dir() else [p]
    if not out:
        raise DcfError("no .dcf files found")
    return out


def suggest_ddl(paths, dialect="sqlite"):
    """CREATE TABLE statements suggested for the data in these files. Returns (sql, tables)."""
    sys.path.insert(0, str(TOOL))
    import ddl
    return ddl.ddl([(f.name, dump(f)) for f in dcf_files(paths)], dialect)


def snapshot(folder):
    """Copy the folder's .dcf files into FOLDER/.dcf-snapshots/<time>/. Returns that path.
    Copy when nothing is writing, or the copy may catch a write half-way."""
    folder = Path(folder)
    files = sorted(folder.glob("*.dcf"))
    if not files:
        raise DcfError(f"no .dcf files in {folder}")
    dest = folder / SNAPSHOTS / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest.mkdir(parents=True)
    for f in files:
        shutil.copy2(f, dest / f.name)
    return dest


def snapshots(folder):
    d = Path(folder) / SNAPSHOTS
    return sorted((p for p in d.iterdir() if p.is_dir()), reverse=True) if d.exists() else []


def main():
    ap = argparse.ArgumentParser(description="View and compare Dyalog component files (.dcf).",
                                 epilog="Read-only: files are never changed.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("view", help="list the components, or show one in full")
    v.add_argument("file")
    v.add_argument("component", nargs="?", type=int)
    d = sub.add_parser("diff", help="compare two files, or two folders")
    d.add_argument("old")
    d.add_argument("new")
    s = sub.add_parser("snapshot", help="copy a folder's .dcf files to FOLDER/.dcf-snapshots/<time>/")
    s.add_argument("folder")
    c = sub.add_parser("changes", help="what changed since the last snapshot")
    c.add_argument("folder")
    c.add_argument("--since", help="a snapshot folder name (default: the latest)")
    j = sub.add_parser("dump", help="everything about a file, as JSON")
    j.add_argument("file")
    q = sub.add_parser("ddl", help="suggest SQL tables (CREATE TABLE statements) for the data")
    q.add_argument("paths", nargs="+", metavar="FILE_OR_FOLDER")
    q.add_argument("--dialect", default="sqlite", choices=["sqlite", "mysql", "postgres", "sqlserver"])
    q.add_argument("-o", "--out", help="write to this file instead of the screen")
    a = ap.parse_args()

    try:
        if a.cmd == "view":
            check_exists(a.file)
            args = ["view", a.file] + ([str(a.component)] if a.component is not None else [])
            code, text = run_apl(args, paths=[a.file])
            print(text)
            return 0 if code == 0 else 2
        if a.cmd == "diff":
            check_exists(a.old, a.new)
            code, text = run_apl(["diff", a.old, a.new], paths=[a.old, a.new])
            print(text if code != 0 or text else "no differences")
            return code
        if a.cmd == "snapshot":
            dest = snapshot(a.folder)
            print(f"Saved {len(list(dest.glob('*.dcf')))} files to {dest}")
            return 0
        if a.cmd == "changes":
            snaps = snapshots(a.folder)
            if a.since:
                snaps = [p for p in snaps if p.name == a.since]
            if not snaps:
                raise DcfError(f"no snapshot{' named ' + a.since if a.since else ''} in "
                               f"{Path(a.folder) / SNAPSHOTS}. Make one with: dcf.py snapshot {a.folder}")
            print(f"Changes since snapshot {snaps[0].name}:")
            code, text = run_apl(["diff", str(snaps[0]), a.folder], paths=[str(snaps[0]), a.folder])
            print(text)
            return code
        if a.cmd == "ddl":
            sql, tables = suggest_ddl(a.paths, a.dialect)
            if a.out:
                Path(a.out).write_text(sql, encoding="utf-8")
                print(f"Wrote {len(tables)} tables to {a.out}")
            else:
                print(sql, end="")
            return 0
        if a.cmd == "dump":
            print(json.dumps(dump(a.file), ensure_ascii=False, indent=1))
            return 0
    except DcfError as e:
        print(f"dcf: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
