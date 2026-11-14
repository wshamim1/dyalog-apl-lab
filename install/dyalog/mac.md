# Install Dyalog APL on macOS

> **Quick way:** [`./mac.sh`](mac.sh)
> `install` (opens the download page if needed), `check`, `alias`
> (adds `dyalog` to `~/.zshrc`), `run`, `ride` (serves RIDE on port 4502).

## 1. Download

1. Go to <https://www.dyalog.com/download-zone.htm>.
2. Register (free for non-commercial use) and pick the **macOS** installer
   for the latest version.

## 2. Install

1. Open the downloaded `.pkg` / `.dmg` and follow the prompts.
2. You should end up with an app such as `/Applications/Dyalog-<version>.app`.
3. The first time you open it, macOS may block it. If so, go to
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
