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
# Native macOS app (opens the download page if it isn't installed)
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

## Repository layout

```
install/
  dyalog/     install & run the Dyalog interpreter
    README.md   overview of the options
    mac.md      mac.sh      native macOS app
    docker.md   docker.sh   Docker
    podman.md   podman.sh   Podman
    container.sh            shared logic for docker.sh / podman.sh
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
