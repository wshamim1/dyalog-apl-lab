"""Talk to a running Dyalog APL interpreter over the RIDE protocol.

The interpreter must be serving RIDE, for example:

    install/dyalog/podman.sh ride        # RIDE_INIT=SERVE:*:4502

Usage as a library:

    from dyalog_client import DyalogClient

    with DyalogClient() as apl:
        r = apl.execute("2 3⍴⍳6")
        print(r.output)        # '1 2 3\\n4 5 6'
        print(r.error)         # False

Usage from the command line:

    python integrations/dyalog_ride/dyalog_client.py "+/⍳100"     # run one expression
    python integrations/dyalog_ride/dyalog_client.py              # simple interactive REPL

Protocol reference: https://github.com/Dyalog/ride/blob/master/docs/protocol.md
"""

from __future__ import annotations

import json
import socket
import struct
import subprocess
import sys
import time
from dataclasses import dataclass, field

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 4502

# AppendSessionOutput "type" values (see protocol.md)
OUT_PROMPT = 1          # "undetermined"; used for the continuation prompt
OUT_ECHO_INPUT = 11
OUT_NORMAL_INPUT = 14
OUT_ERROR = 5
_ECHO_TYPES = {OUT_ECHO_INPUT, OUT_NORMAL_INPUT}

# SetPromptType "type" values
PROMPT_NONE = 0
PROMPT_APL = 1          # normal 6-space prompt: ready for the next expression
PROMPT_QUAD = 2         # ⎕ input requested
PROMPT_LINE_EDITOR = 3
PROMPT_QUOTE_QUAD = 4   # ⍞ input requested


class DyalogError(Exception):
    """Connection or protocol problem (not an APL error; those are in Result.error)."""


@dataclass
class Result:
    """Outcome of executing one or more lines of APL."""

    code: str
    output: str = ""
    error: bool = False
    awaiting_input: bool = False   # the code asked for ⎕ or ⍞ input
    timed_out: bool = False
    messages: list = field(default_factory=list, repr=False)  # raw RIDE messages

    def __str__(self) -> str:
        return self.output


class DyalogClient:
    """A RIDE-protocol client holding one live APL session.

    State (variables, functions) persists between execute() calls, and APL
    errors don't end the session.
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 timeout: float = 30.0, connect_timeout: float = 30.0,
                 reset_on_error: bool = True):
        """
        timeout:        seconds to wait for each line before interrupting it
        reset_on_error: clear the stack after an error, so failed functions
                        don't pile up as suspended (set False to inspect them)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.reset_on_error = reset_on_error
        self._sock: socket.socket | None = None
        self._buf = b""
        self._prompt = PROMPT_NONE
        self.version: str | None = None

    # ------------------------------------------------------------------ setup
    def connect(self) -> "DyalogClient":
        """Open the connection and do the RIDE handshake.

        Retries until connect_timeout, so it can be called right after the
        container starts.
        """
        deadline = time.monotonic() + self.connect_timeout
        last_err: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self._sock = socket.create_connection((self.host, self.port), timeout=5)
                self._handshake()
                return self
            except (OSError, DyalogError) as e:
                last_err = e
                self._close_socket()
                time.sleep(0.5)
        raise DyalogError(
            f"Could not connect to Dyalog at {self.host}:{self.port}: {last_err}\n"
            "Is the interpreter running with RIDE_INIT=SERVE:*:"
            f"{self.port}? Try: install/dyalog/podman.sh ride"
        )

    def _handshake(self) -> None:
        self._send_raw("SupportedProtocols=2")
        self._send_raw("UsingProtocol=2")
        # The interpreter sends its own two handshake strings first.
        for _ in range(2):
            msg = self._recv_raw(timeout=10)
            if not msg.startswith(("SupportedProtocols=", "UsingProtocol=")):
                raise DyalogError(f"Unexpected handshake message: {msg!r}")
        self._send(["Identify", {"apiVersion": 1, "identity": 1}])
        self._send(["Connect", {"remoteId": 2}])
        self._send(["GetWindowLayout", {}])
        # Drain the startup chatter (banner, identify reply) until the prompt.
        self._drain_until_prompt(timeout=self.connect_timeout)

    def close(self) -> None:
        self._close_socket()

    def _close_socket(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
                self._buf = b""

    def __enter__(self) -> "DyalogClient":
        return self.connect()

    def __exit__(self, *exc) -> None:
        self.close()

    # -------------------------------------------------------------- execution
    def execute(self, code: str, timeout: float | None = None) -> Result:
        """Run APL code and return its output.

        Multi-line code is sent one line at a time, waiting for each to
        finish. Execution stops at the first line that errors.
        """
        if self._sock is None:
            raise DyalogError("Not connected. Call connect() first.")
        timeout = self.timeout if timeout is None else timeout
        self._flush()
        result = Result(code=code)
        out: list[str] = []

        # An unclosed { puts the session into multi-line mode, which only a
        # closing } can leave. Catch that here instead of hanging.
        depth = _brace_depth(code)
        if depth > 0:
            result.error = True
            result.output = (f"SYNTAX ERROR: {depth} unclosed '{{' "
                             "(code not run). Add the matching '}'.")
            return result

        for line in code.splitlines() or [""]:
            if not self._execute_line(line, timeout, result, out):
                break
        if self._prompt == PROMPT_LINE_EDITOR:
            # Still inside an unfinished multi-line block: close it.
            result.error = True
            out.append("\n[incomplete multi-line input; block closed]")
            for _ in range(10):
                self._execute_line("}", 5, Result(code="}"), [])
                if self._prompt != PROMPT_LINE_EDITOR:
                    break
        if result.timed_out or result.awaiting_input:
            # Abort the running line / input request and get back to a prompt,
            # so later output can't leak into the next result.
            # ⎕ input is escaped by answering →; ⍞ input and running code by
            # an interrupt.
            if self._prompt == PROMPT_QUAD:
                self._send(["Execute", {"text": "→\n", "trace": 0}])
            else:
                self.interrupt()
            try:
                self._drain_until_prompt(timeout=10)
            except DyalogError:
                pass
            if result.timed_out:
                out.append(f"\n[interrupted after {timeout:g}s]")
            else:
                out.append("\n[input (⎕ or ⍞) is not supported; request cancelled]")
        result.output = "".join(out).strip("\n")
        if self.reset_on_error and (result.error or result.timed_out
                                    or result.awaiting_input):
            self._execute_line(")reset", timeout, Result(code=")reset"), [])
        return result

    def _execute_line(self, line: str, timeout: float, result: Result,
                      out: list[str]) -> bool:
        """Run one line. Returns False if execution should stop."""
        self._send(["Execute", {"text": line + "\n", "trace": 0}])
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                result.timed_out = True
                return False
            msg = self._recv(timeout=remaining)
            if msg is None:
                continue
            result.messages.append(msg)
            name, args = msg[0], (msg[1] if len(msg) > 1 else {})

            if name == "AppendSessionOutput":
                if args.get("type") in _ECHO_TYPES:
                    continue
                if args.get("type") == OUT_ERROR:
                    result.error = True
                text = args.get("result", "")
                if isinstance(text, list):          # older interpreters
                    text = "\n".join(text) + "\n"
                if args.get("type") == OUT_PROMPT and not text.strip():
                    continue                        # continuation prompt "      "
                out.append(text)
            elif name == "HadError":
                result.error = True
                # A prompt follows; keep reading until we see it.
            elif name == "SetPromptType":
                ptype = args.get("type", 0)
                self._prompt = ptype
                if ptype == PROMPT_APL:
                    return not result.error
                if ptype == PROMPT_LINE_EDITOR:
                    return True     # inside a multi-line dfn: send next line
                if ptype in (PROMPT_QUAD, PROMPT_QUOTE_QUAD):
                    result.awaiting_input = True
                    return False
            elif name in ("SysError", "InternalError"):
                result.error = True
                out.append(f"[{name}] {args}\n")
            else:
                self._auto_reply(name, args)

    def interrupt(self) -> None:
        """Interrupt a long-running computation (like Ctrl+Break)."""
        self._send(["StrongInterrupt", {}])

    def reset(self) -> Result:
        """Clear the stack and start with an empty workspace."""
        self.execute(")reset")
        return self.execute(")clear")

    def load(self, path: str) -> Result:
        """Load a .aplf/.apln file (or wildcard) with ]load."""
        return self.execute(f"]load {path}")

    # --------------------------------------------------------------- dialogs
    def _auto_reply(self, name: str, args: dict) -> None:
        """Dismiss dialogs we can't show, so the interpreter doesn't hang."""
        token = args.get("token")
        if name == "OptionsDialog":
            self._send(["ReplyOptionsDialog", {"index": -1, "token": token}])
        elif name == "StringDialog":
            self._send(["ReplyStringDialog",
                        {"value": args.get("defaultValue", ""), "token": token}])
        elif name == "TaskDialog":
            self._send(["ReplyTaskDialog", {"index": -1, "token": token}])
        elif name == "ReplyIdentify":
            self.version = args.get("version")
        # Everything else (OpenWindow, UpdateDisplayName, ...) is ignored.

    def _flush(self) -> None:
        """Discard any messages still queued from earlier work."""
        while (msg := self._recv(timeout=0.02)) is not None:
            self._auto_reply(msg[0], msg[1] if len(msg) > 1 else {})

    def _drain_until_prompt(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._recv(timeout=deadline - time.monotonic())
            if msg is None:
                continue
            name, args = msg[0], (msg[1] if len(msg) > 1 else {})
            if name == "SetPromptType" and args.get("type") == PROMPT_APL:
                return
            self._auto_reply(name, args)
        raise DyalogError("Timed out waiting for the APL prompt")

    # ----------------------------------------------------------------- wire
    def _send_raw(self, payload: str) -> None:
        data = payload.encode("utf-8")
        assert self._sock is not None
        self._sock.sendall(struct.pack(">I", 8 + len(data)) + b"RIDE" + data)

    def _send(self, msg: list) -> None:
        self._send_raw(json.dumps(msg, ensure_ascii=False))

    def _recv_raw(self, timeout: float) -> str:
        """Read one framed message. Raises socket.timeout if none arrives."""
        assert self._sock is not None
        self._sock.settimeout(max(timeout, 0.01))
        while True:
            if len(self._buf) >= 8:
                (length,) = struct.unpack(">I", self._buf[:4])
                if self._buf[4:8] != b"RIDE":
                    raise DyalogError("Bad frame: missing RIDE magic")
                if len(self._buf) >= length:
                    payload = self._buf[8:length]
                    self._buf = self._buf[length:]
                    return payload.decode("utf-8")
            chunk = self._sock.recv(65536)
            if not chunk:
                raise DyalogError("Connection closed by interpreter")
            self._buf += chunk

    def _recv(self, timeout: float) -> list | None:
        """Read one JSON message, or None on timeout."""
        try:
            raw = self._recv_raw(timeout)
        except socket.timeout:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return ["_Raw", {"text": raw}]


def _brace_depth(code: str) -> int:
    """Net count of '{' minus '}' outside strings and comments."""
    depth = 0
    for line in code.splitlines():
        in_quote = False
        for ch in line:
            if ch == "'":
                in_quote = not in_quote       # '' inside a string toggles twice
            elif in_quote:
                continue
            elif ch == "⍝":
                break
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
    return depth


# ---------------------------------------------------------------- container
def start_container(engine: str = "podman", port: int = DEFAULT_PORT,
                    mount: str | None = None, readonly: bool = True,
                    image: str = "docker.io/dyalog/dyalog",
                    name: str | None = None) -> str:
    """Start a detached Dyalog container serving RIDE. Returns the container id.

    mount: host folder to mount at /app (read-only by default).
    """
    cmd = [engine, "run", "-dit", "--rm",
           "-p", f"{port}:{port}", "-e", f"RIDE_INIT=SERVE:*:{port}"]
    if name:
        cmd += ["--name", name]
    if mount:
        cmd += ["-v", f"{mount}:/app" + (":ro" if readonly else "")]
    cmd.append(image)
    return subprocess.run(cmd, check=True, capture_output=True,
                          text=True).stdout.strip()


def stop_container(container_id: str, engine: str = "podman") -> None:
    subprocess.run([engine, "stop", "-t", "2", container_id],
                   check=False, capture_output=True)


# ---------------------------------------------------------------------- CLI
def _repl(client: DyalogClient) -> None:
    print(f"Connected to Dyalog {client.version or ''} at "
          f"{client.host}:{client.port}. Ctrl+D to quit.")
    while True:
        try:
            line = input("      ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        r = client.execute(line)
        if r.output:
            print(r.output)
        if r.awaiting_input:
            print("(input requested: not supported in this REPL)")


def main(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Run APL on a Dyalog RIDE server.")
    p.add_argument("code", nargs="*", help="APL to run (omit for a REPL)")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    a = p.parse_args(argv)

    try:
        with DyalogClient(a.host, a.port, connect_timeout=5) as client:
            if not a.code:
                _repl(client)
                return 0
            r = client.execute(" ".join(a.code))
            if r.output:
                print(r.output)
            return 1 if r.error else 0
    except DyalogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
