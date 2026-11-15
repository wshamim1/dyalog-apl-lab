# Jupyter notebooks

The tutorials as **Jupyter notebooks**: read the explanation, run the APL in
the cell below it, change it, and run it again. They use
[Dyalog's Jupyter kernel](https://github.com/Dyalog/dyalog-jupyter-kernel)
in JupyterLab, all inside a container.

## Start

```sh
install/jupyter/jupyter.sh build          # once: Dyalog + JupyterLab image
install/jupyter/jupyter.sh start          # then open the link it prints
```

It prints a link like `http://127.0.0.1:8888/lab?token=…`. Open it, then open
a notebook. They already use the **Dyalog APL** kernel. Press
**Shift+Enter** to run a cell, and stop the server with **Ctrl+C**.

Typing glyphs in JupyterLab: copy them from the
[cheat sheet](../cheatsheet/README.md), or install the Dyalog keyboard layout
(<https://www.dyalog.com/apl-font-keyboard.htm>).

## What's here

| Notebook | Topic |
| --- | --- |
| [00-getting-started](00-getting-started.ipynb) | the session, glyphs, system commands, `]box` |
| [01-basics](01-basics.ipynb) | arithmetic, right to left, variables |
| [02-arrays](02-arrays.ipynb) | `⍳ ⍴ ≢`, reshape, indexing, take/drop |
| [03-functions](03-functions.ipynb) | dfns, `⍺ ⍵`, guards, recursion |
| [04-operators](04-operators.ipynb) | `/ \ ¨ ∘. ⍨ ∘ ⍣ ⍤ ⌸` |
| [05-boolean-selection](05-boolean-selection.ipynb) | comparisons, compress, `⍸ ∊ ⍳ ∪` |
| [06-strings](06-strings.ipynb) | text, `⎕C ⍕ ⍎ ⎕UCS`, split/join |
| [07-nested-arrays](07-nested-arrays.ipynb) | `⊂ ⊃ ≡`, mix/split, records |
| [08-trains](08-trains.ipynb) | tacit forks and atops |
| [09-sorting-searching](09-sorting-searching.ipynb) | `⍋ ⍒`, interval index, counting |
| [10-workspaces-files](10-workspaces-files.ipynb) | `]load`, `⎕NGET ⎕NPUT ⎕CSV ⎕JSON` |
| [11-tradfns-and-control](11-tradfns-and-control.ipynb) | `:If :For :While :Select :Trap` |

They open with the outputs already filled in, as produced by Dyalog 21, so you
can also read them on GitHub without running anything.

### Dyalog's own notebooks

Dyalog publishes 44 more notebooks (MIT licence): arrays, grading and sorting,
tacit techniques, Sudoku, Mandelbrot, a 15-part introductory course, and more.

```sh
install/jupyter/jupyter.sh fetch-dyalog   # downloads them into notebooks/dyalog/
```

They're downloaded rather than copied into this repo (`notebooks/dyalog/` is
git-ignored). On a Mac you'll see 43: two of the originals differ only in
capitalisation, and macOS treats those as the same file name. Two of them,
*Arrays* and *Conway's Game of Life*, were run on Dyalog 21 with no errors.

## How these notebooks are made

The tutorials (`tutorials/NN-*/README.md`) are the source.
[build.py](build.py) converts each one:

- **Prose** becomes markdown cells.
- **Each example** becomes a code cell holding just the input lines.
- **Kept as text, not run:**
  - system commands such as `)save` or `)off` (they would act on the kernel)
  - source listings
  - solutions, which stay folded under **Solutions**
- **The error example** in 00 is tagged `raises-exception`, so "run all"
  doesn't stop there.

Then `jupyter.sh execute` runs every notebook in Dyalog to fill in the
outputs:

```sh
python3 notebooks/build.py                # regenerate from the tutorials
install/jupyter/jupyter.sh execute        # run them all (about 2 minutes)
```

After the last run, **117 of 119** code cells matched the tutorials' recorded
outputs exactly. The two that differ are `]runtime` (a timing, which the
tutorial doesn't show) and one `]load` that the notebook run caught as out of
date in the tutorial, which has since been fixed.

> If you edit a notebook and save it, your changes stay in the `.ipynb`.
> Running `build.py` overwrites the notebooks from the tutorials, so commit
> or copy anything you want to keep first.

## Things worth knowing

- **Where things are:** the repo is mounted at `/app` in the container, so
  notebooks can `]load /app/tutorials/…` just like the tutorials do. Files
  you save under `/app` are your real repo files.
- **Local only:** JupyterLab listens on `127.0.0.1`, so only your computer
  can reach it, and it also needs the token in the link.
- **How the kernel works:** the kernel starts its own Dyalog inside the
  container and talks to it over the RIDE protocol, the same way the Python
  `dyalog_ride` client does.
- **Image setup fixes:**
  - **Launcher name:** the kernel (v2.0.2) looks for a launcher called
    `mapl`, which this Dyalog image doesn't have, so the Dockerfile adds
    that name as a link to `dyalog`.
  - **Clock:** if the image build fails with *"OpenPGP signature
    verification failed … Not live until …"*, the clock in Podman's VM is
    behind (it drifts when the Mac sleeps). Fix it with
    `podman machine ssh "sudo date -u -s '$(date -u '+%Y-%m-%d %H:%M:%S')'"`,
    then build again.
