# Install Dyalog APL on macOS

> **Intel Mac?** Dyalog 21.0 for macOS is only available for Apple Silicon
> (ARM). On an Intel Mac, install the container-based `dyalog` command
> instead. It runs the same Dyalog 21.0 (Linux x86_64 build) and feels like
> a normal install:
>
> ```sh
> install/dyalog/install-cli.sh   # once: puts `dyalog` on your PATH
> dyalog                          # APL in the terminal, current folder at /app
> dyalog ride                     # then connect RIDE to localhost:4502
> ```
>
> See [The `dyalog` command](README.md#the-dyalog-command).

> **Quick way:** [`./mac.sh`](mac.sh)
> `install` (opens the download page if needed), `check`, `alias`
> (adds `dyalog` to `~/.zshrc`), `run`, `ride` (serves RIDE on port 4502).

## 1. Download

1. Go to <https://www.dyalog.com/download-zone.htm>.
2. Register (free for non-commercial use) and pick the **macOS** installer
   for the latest version.
3. **Pick the right processor build.** Check which one you have with
   `uname -m`, or **Apple menu → About This Mac**:

   | `uname -m` | Your Mac | Download |
   | --- | --- | --- |
   | `x86_64` | Intel | the **Intel / x86_64** installer |
   | `arm64` | Apple Silicon (M1, M2, …) | the **Apple Silicon / arm64** installer (or Intel, via Rosetta) |

   An Intel Mac **can't** run the Apple Silicon build. Running `dyalog`
   then fails with `Bad CPU type in executable`. If there's no build for
   your Mac, use the container instead (`install/dyalog/podman.sh run`).

## 2. Install

1. Open the downloaded `.pkg` / `.dmg` and follow the prompts.
2. You should end up with an app such as `/Applications/Dyalog-<version>.app`.
   The installer also creates the `dyalog` command (`/usr/local/bin/dyalog`).
3. Check that the build matches your Mac. The output should match `uname -m`:

   ```sh
   lipo -archs /Applications/Dyalog-*.app/Contents/Resources/Dyalog/dyalog
   ```
4. The first time you open it, macOS may block it. If so, go to
   **System Settings → Privacy & Security** and click **Open Anyway**.

## 3. Run

### Option A: bundled RIDE (simplest)

Open **Dyalog** from Launchpad or `/Applications`. It starts the interpreter
and a RIDE window that is already connected.

### Option B: RIDE built from source (`install/ride/ride`, see [../ride/README.md](../ride/README.md))

Find the interpreter binary:

```sh
ls /Applications/Dyalog-*.app/Contents/Resources/Dyalog/mapl
```

**Let RIDE start the interpreter:**

```sh
cd install/ride/ride
npm start
```

In the connect dialog choose **Start**, set the interpreter path to the
`mapl` binary above, then click **Start**.

**Or start the interpreter yourself and connect:**

```sh
RIDE_INIT=SERVE:*:4502 /Applications/Dyalog-<version>.app/Contents/Resources/Dyalog/mapl
```

Then in RIDE choose **Connect**, host `localhost`, port `4502`.

### Option C: terminal only (no RIDE)

```sh
/Applications/Dyalog-<version>.app/Contents/Resources/Dyalog/mapl
```

To make this shorter, add an alias to `~/.zshrc`:

```sh
alias dyalog='/Applications/Dyalog-<version>.app/Contents/Resources/Dyalog/mapl'
```

Exit the session with `)off`.

## Uninstall

Move `/Applications/Dyalog-<version>.app` to the Trash. Settings live in
`~/Library/Preferences/com.dyalog.*` and `~/.dyalog` if you want to remove
those too.
