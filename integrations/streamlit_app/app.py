"""Streamlit UI for Dyalog APL.

Tab 1 "Ask in English": describe what you want; an OpenAI model writes APL,
runs it in Dyalog, fixes errors, and explains the result.
Tab 2 "APL REPL": type APL yourself (no AI, no cost).

Run:
    install/dyalog/podman.sh ride                        # terminal 1
    streamlit run integrations/streamlit_app/app.py      # terminal 2
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "dyalog_ride"))
sys.path.insert(0, str(HERE))

from dyalog_client import (DyalogClient, DyalogError,  # noqa: E402
                           start_container, stop_container)
import apl_agent  # noqa: E402

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

GLYPHS = "← + - × ÷ * ⌈ ⌊ | ! ○ ⍳ ⍴ ≢ , ⍪ ⌽ ⊖ ⍉ ↑ ↓ ⊂ ⊃ ⊆ ∊ ⍷ ∪ ∩ ~ = ≠ < ≤ > ≥ ≡ ∧ ∨ / \\ ⌿ ¨ ⍨ ∘ ⍤ ⍣ ⌸ ⍋ ⍒ ⍸ ⍵ ⍺ ∇ ⋄ ⍝ ¯ ⎕ ⍎ ⍕ ⊢ ⊣".split()

EXAMPLES = [
    "Sum the numbers from 1 to 100",
    "Make a 5×5 multiplication table",
    "Which numbers from 1 to 50 are prime?",
    "Count how often each letter appears in 'mississippi'",
    "Define a function that averages a vector, then use it on 3 1 4 1 5 9",
]

st.set_page_config(page_title="APL Playground", page_icon="⍝", layout="wide")

ss = st.session_state
ss.setdefault("apl", None)              # DyalogClient
ss.setdefault("container_id", None)     # container started by this app
ss.setdefault("llm_history", [])        # OpenAI messages (for follow-ups)
ss.setdefault("chat", [])               # what we display: dicts
ss.setdefault("repl_log", [])           # (code, output, error)
ss.setdefault("repl_code", "")
ss.setdefault("pending_prompt", None)


# ----------------------------------------------------------------- helpers
def connect(host: str, port: int) -> None:
    try:
        ss.apl = DyalogClient(host, port, timeout=20, connect_timeout=15).connect()
    except DyalogError as e:
        ss.apl = None
        st.sidebar.error(str(e))


def disconnect() -> None:
    if ss.apl:
        ss.apl.close()
    ss.apl = None


def run_apl(code: str):
    """Execute code; drop the client if the connection died."""
    try:
        return ss.apl.execute(code)
    except (DyalogError, OSError) as e:
        disconnect()
        st.error(f"Lost the connection to Dyalog: {e}")
        return None


def add_glyph(g: str) -> None:
    ss.repl_code += g


def output_block(text: str, error: bool) -> None:
    if error:
        st.error(text or "(error)", icon="⚠️")
    else:
        st.code(text or "(no output)", language=None)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⍝ APL Playground")

    st.subheader("Dyalog")
    host = st.text_input("Host", "localhost")
    port = st.number_input("Port", 1, 65535, 4502)
    c1, c2 = st.columns(2)
    if ss.apl is None:
        if c1.button("Connect", type="primary", use_container_width=True):
            connect(host, int(port))
            st.rerun()
        if c2.button("Start container", use_container_width=True,
                     help="Runs dyalog/dyalog with Podman, repo mounted read-only at /app"):
            try:
                with st.spinner("Starting Dyalog…"):
                    ss.container_id = start_container(
                        engine="podman", port=int(port), mount=str(REPO_ROOT))
                    connect(host, int(port))
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Couldn't start container: {e}")
    else:
        st.success(f"Connected · Dyalog {ss.apl.version or ''}")
        if c1.button("Reset session", use_container_width=True,
                     help="Clear all variables and functions"):
            run_apl(")clear")
            ss.llm_history, ss.chat, ss.repl_log = [], [], []
            st.rerun()
        if c2.button("Disconnect", use_container_width=True):
            disconnect()
            st.rerun()
    if ss.container_id and st.button("Stop container", use_container_width=True):
        disconnect()
        stop_container(ss.container_id)
        ss.container_id = None
        st.rerun()

    st.subheader("OpenAI")
    api_key = st.text_input("API key", type="password",
                            value=os.environ.get("OPENAI_API_KEY", ""),
                            help="Defaults to $OPENAI_API_KEY. Not stored.")
    model = st.text_input("Model", DEFAULT_MODEL)
    max_steps = st.slider("Max APL runs per question", 1, 10, 5)
    if st.button("Clear chat", use_container_width=True):
        ss.llm_history, ss.chat = [], []
        st.rerun()

if ss.apl is None:
    st.info("Connect to Dyalog in the sidebar. Start it with "
            "`install/dyalog/podman.sh ride`, or click **Start container**.")
    st.stop()

tab_ask, tab_repl = st.tabs(["💬 Ask in English", "⌨️ APL REPL"])

# --------------------------------------------------------------- ask tab
with tab_ask:
    if not ss.chat:
        st.caption("Try one of these:")
        cols = st.columns(len(EXAMPLES))
        for col, ex in zip(cols, EXAMPLES):
            if col.button(ex, use_container_width=True):
                ss.pending_prompt = ex
                st.rerun()

    for item in ss.chat:
        with st.chat_message(item["role"]):
            if item["role"] == "user":
                st.markdown(item["text"])
                continue
            for i, step in enumerate(item.get("steps", []), 1):
                label = f"Run {i}" + (" · error" if step.error else "")
                with st.expander(label, expanded=(i == len(item["steps"]))):
                    st.code(step.code, language=None)
                    output_block(step.output, step.error)
            if item.get("stopped_early"):
                st.warning("Stopped after the maximum number of runs.")
            st.markdown(item["text"])

    prompt = st.chat_input("Describe what you want, e.g. 'average of 3 7 8'")
    prompt = prompt or ss.pending_prompt
    ss.pending_prompt = None

    if prompt:
        if not api_key:
            st.error("Add your OpenAI API key in the sidebar.")
            st.stop()
        from openai import OpenAI  # imported lazily so the REPL works without it

        ss.chat.append({"role": "user", "text": prompt})
        try:
            with st.spinner("Writing and running APL…"):
                ans = apl_agent.ask(OpenAI(api_key=api_key), model, ss.apl,
                                    ss.llm_history, prompt, max_steps=max_steps)
            ss.chat.append({"role": "assistant", "text": ans.text,
                            "steps": ans.steps, "stopped_early": ans.stopped_early})
        except (DyalogError, OSError) as e:
            disconnect()
            ss.chat.append({"role": "assistant", "text": f"⚠️ Lost the connection to Dyalog: {e}"})
        except Exception as e:  # noqa: BLE001  (OpenAI errors, bad model name, ...)
            ss.llm_history.clear()
            ss.chat.append({"role": "assistant", "text": f"⚠️ {type(e).__name__}: {e}"})
        st.rerun()

# -------------------------------------------------------------- REPL tab
with tab_repl:
    st.caption("Type APL directly. Click a glyph to add it. "
               "Shares the same session as the chat.")
    rows = [GLYPHS[i:i + 20] for i in range(0, len(GLYPHS), 20)]
    for r, row in enumerate(rows):
        cols = st.columns(20)
        for c, (col, g) in enumerate(zip(cols, row)):
            col.button(g, key=f"g{r}_{c}", on_click=add_glyph, args=(g,),
                       use_container_width=True)

    with st.form("repl", clear_on_submit=False):
        st.text_area("APL", key="repl_code", height=90,
                     placeholder="e.g.  +/⍳100   or   3 4⍴⍳12")
        submitted = st.form_submit_button("Run ▶", type="primary")
    if submitted and ss.repl_code.strip():
        r = run_apl(ss.repl_code)
        if r is not None:
            ss.repl_log.insert(0, (ss.repl_code, r.output, r.error or r.timed_out))
        st.rerun()

    for code, out, err in ss.repl_log:
        st.code("      " + code.replace("\n", "\n      "), language=None)
        output_block(out, err)
