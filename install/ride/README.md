# Installing RIDE

RIDE is the IDE for Dyalog APL. It's only a front end: you also need the
Dyalog interpreter. See [`../dyalog`](../dyalog/README.md).

> If you installed the native macOS Dyalog app, RIDE comes with it and you can
> skip this page. Building from source is only needed for the latest RIDE, or
> for using it with Docker/Podman.

## Option 1: Download a release

1. Go to <https://github.com/dyalog/ride/releases>.
2. Download the macOS build (`.dmg` / `.zip`) for your CPU
   (`arm64` for Apple Silicon, `x64` for Intel).
3. Drag **Ride** into `/Applications` and open it. If macOS blocks it, use
   **System Settings → Privacy & Security → Open Anyway**.

## Option 2: Build from source

### Quick way: `install.sh`

From this folder:

```sh
./install.sh            # clone into ./ride, then npm i and npm run css
./install.sh --start    # same, then start RIDE
./install.sh --build    # same, then build a native app under ride/_/
```

The script uses nvm to switch to Node 18.17.0 if nvm is installed. Running it
again updates an existing clone with `git pull`. The cloned `ride/` folder is
git-ignored.

### Manual steps

#### 1. Prerequisites

- **Git:** `xcode-select --install` or `brew install git`
- **Node.js v18.17.0.** This is the version upstream documents. Newer
  versions may work, but if `npm i` or the build fails, switch with
  [nvm](https://github.com/nvm-sh/nvm):

  ```sh
  brew install nvm          # then follow the shell setup it prints
  nvm install 18.17.0
  nvm use 18.17.0
  node -v                   # v18.17.0
  ```

#### 2. Get the source

```sh
cd install/ride
git clone https://github.com/dyalog/ride --depth=1
cd ride
```

#### 3. Install dependencies and run

```sh
npm i              # download dependencies
npm run css        # compile css
npm start          # start Ride (Electron)
```

Or do both steps in one go:

```sh
npm run dev        # compile css and start Ride
```

#### 4. (Optional) Build a standalone app

```sh
npm run build dist # compile css and build native apps under _/ride<version>/
```

Look in `_/` for the macOS `.app` and copy it to `/Applications` if you want
it in Launchpad.

```sh
npm run clean      # remove build output
```

#### 5. Update later

```sh
git pull
npm i
npm run dev
```

## Connecting RIDE to Dyalog

When RIDE opens, it shows a connect dialog:

| Interpreter installed as | In RIDE choose | Settings |
| --- | --- | --- |
| macOS app | **Start** | Interpreter: `/Applications/Dyalog-<version>.app/Contents/Resources/Dyalog/mapl` |
| Docker / Podman container | **Connect** | Host `localhost`, port `4502` |
| `mapl` started by hand with `RIDE_INIT=SERVE:*:4502` | **Connect** | Host `localhost`, port `4502` |

See [`../dyalog/mac.md`](../dyalog/mac.md),
[`../dyalog/docker.md`](../dyalog/docker.md) and
[`../dyalog/podman.md`](../dyalog/podman.md) for how to start each one.

To test it, type `⍳10` and press Enter.

## Troubleshooting

- **`npm i` fails building native modules:** switch to Node 18.17.0 (see
  above), delete `node_modules`, and run `npm i` again.
- **Blank window or missing styles:** run `npm run css` before `npm start`.
- **Connection refused:** the interpreter isn't running or isn't serving
  on port 4502.
