# Installing Dyalog APL

RIDE (in [`../ride`](../ride)) is only the IDE. It connects to a Dyalog APL
**interpreter**, which has to be installed separately. Pick one option:

| Option | Best for | Guide | Script |
| --- | --- | --- | --- |
| Native macOS app | Apple Silicon Macs; RIDE is bundled | [mac.md](mac.md) | [mac.sh](mac.sh) |
| **`dyalog` command** | Intel Macs, or anyone who wants a `dyalog` command without the app | [below](#the-dyalog-command) | [install-cli.sh](install-cli.sh) |
| Docker | Throwaway, reproducible interpreter | [docker.md](docker.md) | [docker.sh](docker.sh) |
| Podman | Same as Docker, but daemonless / rootless | [podman.md](podman.md) | [podman.sh](podman.sh) |

## The `dyalog` command

A `dyalog` command that works from any folder, running Dyalog in a
container. Use it when the native app isn't an option: Dyalog 21.0 for
macOS is Apple Silicon only, so an Intel Mac can't run it.

```sh
install/dyalog/install-cli.sh      # once: links `dyalog` into /usr/local/bin (or ~/.local/bin)

dyalog                             # APL in this terminal; the current folder is at /app
dyalog hello.apls                  # run an APL script top to bottom, then exit
dyalog MyFn.aplf                   # session with MyFn loaded (runs it if it takes no arguments)
dyalog test [folder|file]          # run *_test.aplf tests (see testing/README.md)
dyalog ride                        # serve RIDE on localhost:4502, then connect RIDE to it
dyalog setup                       # first time: install/start Podman, pull the image
dyalog pull                        # update the image
```

| Setting (env var) | Default | |
| --- | --- | --- |
| `DYALOG_ENGINE` | `podman` if installed, else `docker` | |
| `IMAGE` | `docker.io/dyalog/dyalog` | use `localhost/dyalog-mysql:latest` for the [MySQL functions](../../integrations/mysql/apl/README.md) |
| `RIDE_PORT` | `4502` | |

### Running files

| File | What it contains | `dyalog FILE` does |
| --- | --- | --- |
| `.apls` | **script**: statements, run top to bottom | runs it with `dyalogscript`, then exits with its exit code (0 = OK, 4 = APL error, or `⎕OFF n`) |
| `.aplf` / `.aplo` | **one function / operator** | opens a session with it loaded. A function that takes no arguments runs right away. |
| `.apln` / `.aplc` / `.apli` | **namespace / class / interface** | opens a session with it loaded. A namespace's or class's `Run` is called. |
| `.apla` | **array** in array notation | displays the array (namespaces also as JSON), then exits |
| `.dws` | saved **workspace** (binary) | opens it and runs its `⎕LX` |
| `.dyapp` | **app definition** (`Load …` / `Run …` lines) | boots it: loads the files in order, runs the `Run` lines |

Examples of every type: [sample-scripts/file-types](../../sample-scripts/file-types/README.md).

**In a script, only `⎕←` lines print.** A bare expression is evaluated but not
shown, unlike in the interactive session:

```apl
⍝ hello.apls
⎕←'hello Shamim'          ⍝ prints
'not shown'               ⍝ evaluated, not printed
x←+/⍳100
⎕←'sum: ',⍕x              ⍝ prints "sum: 5050"
```

If the file is inside the current folder, the current folder is mounted, so
a script can read its neighbours (`⊃⎕NGET'/app/data.txt' 1`). Otherwise the
file's own folder is mounted.

Things to know:

- **Your files:** the folder you run `dyalog` from is mounted at `/app`.
  Load code from it with `]load /app/MyFn.aplf`. Files you save under
  `/app` stay on your Mac, while anything else inside the container
  disappears when you quit.
- **Auto-load:** if the folder contains **exactly one** `.aplf`, `.apln` or
  `.dws` file, the Dyalog image loads it at startup (that's the image's own
  behaviour). With none or several, you start with a clear workspace.
- **Uninstall:** `install/dyalog/install-cli.sh --uninstall`. The installer
  only replaces an existing `dyalog` if it's a broken link (like the one a
  removed Mac app leaves behind) or already its own link.
- **Same version:** it's the Linux x86_64 build of Dyalog 21.0, running in
  Podman's Linux VM. On an Intel Mac that runs at full speed, with no
  emulation.

## Scripts

Each script has the same subcommands:

```sh
./mac.sh    install | check | alias | run | ride
./docker.sh install | pull | run | ride
./podman.sh install | pull | run | ride
```

- `install` installs or checks the prerequisites. The macOS app needs a free
  registration to download, so `mac.sh install` opens the download page.
- `run` starts an APL session in your terminal.
- `ride` starts the interpreter serving RIDE on `localhost:4502`. Then open
  RIDE and choose **Connect**.

Example: `./podman.sh install`, then `./podman.sh run`:

![Pulling the Dyalog image with podman.sh install, then starting an APL session with podman.sh run](images/podman-run.png)

`docker.sh` and `podman.sh` both use [container.sh](container.sh). They mount
the repo root at `/app` inside the container. Set `RIDE_PORT` to use a
different port.

All three options can be used with the RIDE you built from source. The
interpreter listens on a port (we use `4502`), and RIDE connects to it.

## Quick check

Once a session is running, try:

```apl
⍳10
+/⍳100
```

You should get `1 2 3 4 5 6 7 8 9 10` and `5050`.

## Licence

Dyalog is free for personal, non-commercial use. Commercial use needs a paid
licence. See <https://www.dyalog.com/prices-and-licences.htm>.
