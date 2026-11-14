# Dyalog RIDE integration

A Python client that drives a live Dyalog APL session over the RIDE
protocol. Other integrations (Streamlit UI, MCP server, Kafka) build on it.
See the [integrations index](../README.md).

## `dyalog_client.py`

A client for the **RIDE protocol**, the same connection the RIDE IDE uses. It
keeps one live APL session, so variables and functions persist between
calls, and APL errors don't end the session.

It uses only the Python standard library (Python 3.10+), so there's nothing
to install.

### 1. Start Dyalog serving RIDE

```sh
install/dyalog/podman.sh ride        # or docker.sh ride / mac.sh ride
```

### 2a. Use it from the command line

```sh
python3 integrations/dyalog_ride/dyalog_client.py "+/⍳100"     # run one expression
python3 integrations/dyalog_ride/dyalog_client.py              # interactive REPL
```

### 2b. Use it from Python

```python
from dyalog_client import DyalogClient

with DyalogClient() as apl:                 # localhost:4502
    r = apl.execute("2 3⍴⍳6")
    print(r.output)       # 1 2 3
                          # 4 5 6
    apl.execute("x←10")
    print(apl.execute("x×⍳3").output)        # 10 20 30

    r = apl.execute("1 2+1 2 3")
    print(r.error)        # True
    print(r.output)       # LENGTH ERROR: Mismatched left and right argument shapes ...
```

Or start a container from Python. It mounts a folder read-only at `/app`:

```python
from dyalog_client import DyalogClient, start_container, stop_container

cid = start_container(engine="podman", port=4599, mount="/path/to/repo")
try:
    with DyalogClient(port=4599) as apl:
        apl.load("/app/tutorials/03-functions/Fact.aplf")
        print(apl.execute("Fact 5").output)   # 120
finally:
    stop_container(cid)
```

### API

| Method | What it does |
| --- | --- |
| `DyalogClient(host, port, timeout=30, reset_on_error=True)` | create a client (`connect()` or use `with`) |
| `execute(code, timeout=None) -> Result` | run one or more lines; stops at the first error |
| `load(path)` | `]load` a `.aplf` file or wildcard |
| `reset()` | clear the stack and the workspace |
| `interrupt()` | stop a running computation |
| `start_container(...)` / `stop_container(id)` | run a detached Dyalog container serving RIDE |

`Result` has these fields:

- `output`: the text APL printed
- `error`: whether an APL error happened
- `timed_out`
- `awaiting_input`
- `messages`: the raw RIDE messages, for debugging

### Behaviour

- **Errors:** `error=True`, with the APL message in `output`. The stack is
  cleared afterwards so failed functions don't pile up. Pass
  `reset_on_error=False` if you want to inspect them.
- **Long-running code:** after `timeout` seconds, the line is interrupted
  and `timed_out=True`.
- **Input (`⎕` / `⍞`):** not supported. The request is cancelled and
  `awaiting_input=True`.
- **Multi-line dfns and control structures** (`F←{` … `}`, `:If` … `:EndIf`)
  can be sent as several lines. An unclosed `{` is caught before sending
  and reported as a `SYNTAX ERROR`, because otherwise the session would wait
  forever for the closing `}`.
- **Dialogs** the interpreter opens are dismissed automatically.

### Safety

The client runs whatever code it's given, and APL can run shell commands
(`⎕SH`) inside the container. Keep it in a container, and mount the repo
read-only (`start_container` does that by default).
