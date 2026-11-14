# Run Dyalog APL with Podman

Podman runs the same official image as Docker
([`dyalog/dyalog`](https://hub.docker.com/r/dyalog/dyalog)) without a
background daemon. Most `docker` commands work as-is with `podman`.

> **Quick way:** [`./podman.sh`](podman.sh)
>
> ```sh
> ./podman.sh install   # install Podman via Homebrew, init/start the VM, pull the image
> ./podman.sh run       # APL session in the terminal (repo mounted at /app)
> ./podman.sh ride      # serve RIDE on localhost:4502
> ```
>
> The manual steps follow.

## 1. Install Podman on macOS

```sh
brew install podman
```

(Optional GUI: `brew install --cask podman-desktop`.)

On macOS, containers run inside a small Linux VM. Create it and start it once:

```sh
podman machine init
podman machine start
```

Verify:

```sh
podman version
podman run --rm quay.io/podman/hello
```

After a reboot, run `podman machine start` again.

## 2. Pull the Dyalog image

Use the fully qualified name so Podman knows which registry to use:

```sh
podman pull docker.io/dyalog/dyalog
```

> **Apple Silicon:** if no arm64 image is available, add
> `--platform linux/amd64` to the `pull` and `run` commands.

## 3. Run an interactive session in the terminal

```sh
podman run -it --rm docker.io/dyalog/dyalog
```

Exit with `)off`.

## 4. Use it from RIDE

```sh
podman run -it --rm \
  -p 4502:4502 \
  -e RIDE_INIT=SERVE:*:4502 \
  docker.io/dyalog/dyalog
```

Then start RIDE (`cd install/ride/ride && npm start`, see [../ride/README.md](../ride/README.md)), choose **Connect**, and
enter host `localhost`, port `4502`.

## 5. Work on files from this repo

```sh
podman run -it --rm \
  -p 4502:4502 \
  -e RIDE_INIT=SERVE:*:4502 \
  -v "$PWD":/app:Z \
  -w /app \
  docker.io/dyalog/dyalog
```

The `:Z` suffix handles SELinux labelling on Linux hosts and does no harm on
macOS.

## Optional: use the `docker` command with Podman

```sh
alias docker=podman
```

The compose file in [docker.md](docker.md) also works with
`podman compose run --rm --service-ports dyalog`. That needs
`brew install podman-compose` or Docker Compose installed.

## Troubleshooting

- **`Cannot connect to Podman`:** the VM isn't running. Run
  `podman machine start`.
- **RIDE can't connect:** check `podman ps` and make sure port 4502 is
  published (`-p 4502:4502`).
