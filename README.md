# Learn APL (Dyalog)

Notes, setup scripts and exercises for learning [APL](https://aplwiki.com)
with [Dyalog APL](https://www.dyalog.com).

## What you need

Two things:

1. **Dyalog APL**, the interpreter that runs your code.
2. **RIDE**, the IDE you type into. It connects to the interpreter.

The native macOS app includes both. If you use Docker or Podman, you only get
the interpreter, so you also need RIDE (or you can just use the terminal).

## Quick start

Pick one way to run Dyalog:

```sh
# Intel Mac (or no app): a `dyalog` command that runs Dyalog in a container
install/dyalog/install-cli.sh
dyalog

# Native macOS app, Apple Silicon only (opens the download page if it isn't installed)
install/dyalog/mac.sh install
install/dyalog/mac.sh run

# Docker
install/dyalog/docker.sh install
install/dyalog/docker.sh run

# Podman
install/dyalog/podman.sh install
install/dyalog/podman.sh run
```

`run` starts APL in your terminal. Exit with `)off`.

### Using RIDE with Docker or Podman

```sh
install/dyalog/docker.sh ride       # or podman.sh ride / mac.sh ride
install/ride/install.sh --start     # build and start RIDE from source
```

In RIDE choose **Connect**, host `localhost`, port `4502`.

### Check it works

```apl
⍳10
+/⍳100
```

You should get `1 2 3 4 5 6 7 8 9 10` and `5050`.

## Tutorials

Start with [tutorials/](tutorials/README.md). There are 12 short lessons,
from first steps to control structures, each with exercises.

## Repository layout

```
tutorials/    lessons 00–11 with exercises (start here)
integrations/ connect Dyalog to other systems
  dyalog_ride/  Python client for a live Dyalog session (RIDE protocol)
  streamlit_app/ web UI: plain English → APL with OpenAI, plus a REPL
  mysql/        load MySQL tables into APL, write results back
    apl/          …the same from APL itself (.aplf functions, SQAPL/ODBC)
install/
  dyalog/     install & run the Dyalog interpreter
    README.md   overview of the options
    mac.md      mac.sh      native macOS app
    docker.md   docker.sh   Docker
    podman.md   podman.sh   Podman
    container.sh            shared logic for docker.sh / podman.sh
    dyalog, install-cli.sh  the `dyalog` command (container-based) and its installer
  ride/       build and run RIDE from source
    README.md
    install.sh
```

## Resources

- [Dyalog documentation](https://docs.dyalog.com)
- [APL Wiki](https://aplwiki.com)
- [TryAPL](https://tryapl.org): APL in the browser, nothing to install
- [Learning APL (Dyalog)](https://xpqz.github.io/learnapl)
- [APL Orchard chat](https://apl.chat)
- [RIDE on GitHub](https://github.com/dyalog/ride)
