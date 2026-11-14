# Run Dyalog APL with Docker

Dyalog publishes an official image on Docker Hub:
[`dyalog/dyalog`](https://hub.docker.com/r/dyalog/dyalog).

> **Quick way:** [`./docker.sh`](docker.sh)
>
> ```sh
> ./docker.sh install   # install/start Docker via Homebrew, pull the image
> ./docker.sh run       # APL session in the terminal (repo mounted at /app)
> ./docker.sh ride      # serve RIDE on localhost:4502
> ```
>
> On Apple Silicon, the script falls back to `--platform linux/amd64` if no
> arm64 image is available. The manual steps follow.

## 1. Install Docker on macOS

Pick one:

- **Docker Desktop:** download from <https://www.docker.com/products/docker-desktop/>,
  or install it with Homebrew:

  ```sh
  brew install --cask docker
  open -a Docker        # start the Docker engine
  ```

- **Colima** (lightweight, no GUI):

  ```sh
  brew install colima docker
  colima start
  ```

Verify:

```sh
docker version
docker run --rm hello-world
```

## 2. Pull the Dyalog image

```sh
docker pull dyalog/dyalog
```

> **Apple Silicon (M1/M2/M3…):** if the pull fails with
> "no matching manifest for linux/arm64", add `--platform linux/amd64`
> to the `pull` and `run` commands. The image then runs under emulation,
> which is slower but works.

## 3. Run an interactive session in the terminal

```sh
docker run -it --rm dyalog/dyalog
```

Type APL at the prompt, and exit with `)off`.

## 4. Use it from RIDE

Start the interpreter with RIDE serving on port 4502:

```sh
docker run -it --rm \
  -p 4502:4502 \
  -e RIDE_INIT=SERVE:*:4502 \
  dyalog/dyalog
```

Then start RIDE (`cd install/ride/ride && npm start`, see [../ride/README.md](../ride/README.md)), choose **Connect**, and
enter host `localhost`, port `4502`.

## 5. Work on files from this repo

Mount the repo into the container so your code persists:

```sh
docker run -it --rm \
  -p 4502:4502 \
  -e RIDE_INIT=SERVE:*:4502 \
  -v "$PWD":/app \
  -w /app \
  dyalog/dyalog
```

Inside APL you can then load files from `/app`, for example
`]load /app/myfile.aplf` or `⎕FIX 'file:///app/myfile.aplf'`.

## Optional: docker compose

`compose.yaml`:

```yaml
services:
  dyalog:
    image: dyalog/dyalog
    stdin_open: true
    tty: true
    ports:
      - "4502:4502"
    environment:
      RIDE_INIT: "SERVE:*:4502"
    volumes:
      - ./:/app
    working_dir: /app
```

```sh
docker compose run --rm --service-ports dyalog
```

## Troubleshooting

- **RIDE can't connect:** check that the container is running
  (`docker ps`) and that port 4502 isn't already in use (`lsof -i :4502`).
- **Licence prompt or exit at start:** read the image's Docker Hub page. Some
  versions require an environment variable to accept the licence.
