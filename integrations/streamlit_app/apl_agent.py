"""Turn plain-English requests into Dyalog APL and run them.

The model gets one tool, `run_apl`, which executes code in a live Dyalog
session (via integrations/dyalog_ride). It can look at the output or error and
try again, up to `max_steps` times.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dyalog_ride"))
from dyalog_client import DyalogClient  # noqa: E402

SYSTEM_PROMPT = """\
You are an expert Dyalog APL programmer helping someone learn APL.
The user describes what they want in plain English. You write Dyalog APL and
run it with the run_apl tool, then explain the result briefly.

Environment:
- Dyalog APL 21, ⎕IO←1, ]box is on. The session is live: variables and
  functions you define persist between calls and between user messages.
- The repo is mounted read-only at /app (tutorial files under /app/tutorials).

How to work:
- Always run your code with run_apl. Never claim a result you haven't run.
- Prefer short, idiomatic array solutions (primitives, operators, dfns,
  trains) over loops.
- If the run fails, read the error, fix the code and run it again.
- Keep each run small. Define a function on one line, e.g. Avg←{(+/⍵)÷≢⍵}.
- Don't use ⎕ or ⍞ input, ⎕SH/⎕CMD, or anything that writes files.

Answer format (markdown):
1. The final APL code in an ```apl block.
2. One or two sentences explaining how it works, naming the key glyphs.
Don't repeat the output; the user sees it already.
"""

TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_apl",
        "description": (
            "Execute Dyalog APL code in the live session and return what it "
            "printed. Multiple lines run in order and stop at the first error."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Dyalog APL code to run"},
            },
            "required": ["code"],
            "additionalProperties": False,
        },
    },
}]


@dataclass
class Step:
    """One run_apl call made by the model."""
    code: str
    output: str
    error: bool


@dataclass
class Answer:
    text: str
    steps: list[Step] = field(default_factory=list)
    stopped_early: bool = False


def ask(openai_client, model: str, apl: DyalogClient, history: list[dict],
        prompt: str, max_steps: int = 5) -> Answer:
    """Answer `prompt`, running APL as needed.

    history: earlier messages (OpenAI chat format) for follow-up questions.
             It is updated in place with this turn's messages.
    """
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
    history.append({"role": "user", "content": prompt})

    steps: list[Step] = []
    for _ in range(max_steps + 1):
        resp = openai_client.chat.completions.create(
            model=model, messages=history, tools=TOOLS,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []

        assistant = {"role": "assistant", "content": msg.content or ""}
        if tool_calls:
            assistant["tool_calls"] = [{
                "id": tc.id, "type": "function",
                "function": {"name": tc.function.name,
                             "arguments": tc.function.arguments},
            } for tc in tool_calls]
        history.append(assistant)

        if not tool_calls:
            return Answer(text=msg.content or "", steps=steps)

        for tc in tool_calls:
            history.append({"role": "tool", "tool_call_id": tc.id,
                            "content": _run_tool(tc, apl, steps)})

        if len(steps) >= max_steps:
            break

    # Ran out of steps: ask for a final answer without tools.
    history.append({"role": "user", "content":
                    "Stop running code now and give your best final answer."})
    resp = openai_client.chat.completions.create(model=model, messages=history)
    text = resp.choices[0].message.content or ""
    history.append({"role": "assistant", "content": text})
    return Answer(text=text, steps=steps, stopped_early=True)


def _run_tool(tc, apl: DyalogClient, steps: list[Step]) -> str:
    if tc.function.name != "run_apl":
        return f"Unknown tool {tc.function.name!r}. Use run_apl."
    try:
        code = json.loads(tc.function.arguments or "{}").get("code", "")
    except json.JSONDecodeError:
        return "Invalid JSON arguments. Call run_apl with {\"code\": \"...\"}."
    if not code.strip():
        return "Empty code. Pass the APL to run in `code`."

    r = apl.execute(code)
    steps.append(Step(code=code, output=r.output, error=r.error or r.timed_out))
    status = ("ERROR" if r.error else "TIMED OUT" if r.timed_out
              else "INPUT NOT SUPPORTED" if r.awaiting_input else "OK")
    return f"[{status}]\n{r.output or '(no output)'}"
