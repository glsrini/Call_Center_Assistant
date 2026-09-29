"""Gradio chat application entry point."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
import uuid

import gradio as gr
from langgraph.checkpoint.memory import MemorySaver

from config import settings
from src.agents import create_graph
from src.db import initialize_database
from src.memory import memory_store

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "agent.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
root_log = logging.getLogger()
if not any(getattr(handler, "baseFilename", None) == str(LOG_FILE) for handler in root_log.handlers):
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_log.addHandler(file_handler)
log = logging.getLogger(__name__)
initialize_database()
graph = create_graph(checkpointer=MemorySaver())


def new_session():
    return {"thread_id": str(uuid.uuid4()), "customer_id": None, "pending_query": None, "messages": []}


def respond(message: str, history: list, session: dict):
    session = session or new_session()
    history = history or []
    message = (message or "").strip()
    if not message:
        return history, session, "Enter a message to continue."
    started = time.monotonic()
    log.info("Chat request started session_id=%s", session["thread_id"])
    history = history + [{"role": "user", "content": message}]
    if session.get("pending_query"):
        combined = f"{session['pending_query']}\nCustomer ID is {message}" if message.isdigit() else f"{session['pending_query']}\n{message}"
    else:
        combined = message
    try:
        result = graph.invoke({"message": combined, "customer_id": session.get("customer_id"), "preferences": memory_store.get(session["customer_id"])["music_preferences"] if session.get("customer_id") else []}, {"configurable": {"thread_id": session["thread_id"]}})
        answer = result.get("response", "I could not complete that request.")
        if result.get("pending_verification"):
            session["pending_query"] = message
            answer = result.get("response") or "Please verify your identity. Enter your Customer ID, email address, or phone number."
        elif result.get("customer_id"):
            session["customer_id"] = result["customer_id"]
            session["pending_query"] = None
            if "verified" not in answer.lower() and session.get("pending_query"):
                pass
        history = history + [{"role": "assistant", "content": answer}]
        elapsed = time.monotonic() - started
        log.info(
            "Chat request completed session_id=%s specialists=%s elapsed_seconds=%.2f",
            session["thread_id"],
            ",".join(result.get("calls", [])) or "none",
            elapsed,
        )
        return history, session, f"Completed in {elapsed:.2f}s"
    except Exception:
        log.exception("Chat request failed session_id=%s", session["thread_id"])
        return history + [{"role": "assistant", "content": "I hit an error while handling that request. Please try again."}], session, "Error: request failed"


def reset():
    return [], new_session(), "New conversation ready"


with gr.Blocks(title="Call_Center_Assistant") as demo:
    gr.Markdown("# Call_Center_Assistant\nAsk about the music catalog or your account. Account details require identity verification.")
    chat = gr.Chatbot(type="messages", label="Conversation", height=520)
    status = gr.Markdown("Ready")
    session_state = gr.State(new_session())
    with gr.Row():
        textbox = gr.Textbox(placeholder="Type a message…", label="Message", scale=8, lines=1)
        send = gr.Button("Send", variant="primary", scale=1)
        reset_button = gr.Button("New conversation", scale=1)
    send.click(respond, [textbox, chat, session_state], [chat, session_state, status]).then(lambda: "", None, textbox)
    textbox.submit(respond, [textbox, chat, session_state], [chat, session_state, status]).then(lambda: "", None, textbox)
    reset_button.click(reset, None, [chat, session_state, status])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=settings.port)
