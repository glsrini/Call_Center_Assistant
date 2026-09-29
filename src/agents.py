"""Supervisor and specialist agents grounded in Chinook tool results."""
from __future__ import annotations

import json
import logging
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from config import settings
from .memory import memory_store, extract_explicit_preferences
from .tools import MUSIC_TOOLS, INVOICE_TOOLS, verify_customer

log = logging.getLogger(__name__)

GROUNDING_RULES = """You are a digital music store support specialist. Use only the database tool results supplied in this turn; never answer from model memory. Quote numbers exactly as returned, including prices and counts. If a tool result is empty or reports an error, say so honestly. Stay within your assigned scope. Do not infer missing details. Disclose when results are sampled or truncated, including the exact total count when provided. Never invent catalog, invoice, customer, or employee data."""
SUPERVISOR_PROMPT = GROUNDING_RULES + " Classify only as music, invoice, mixed, or off_topic. For mixed requests handle invoice first, then music. Reject off-topic requests without calling either specialist."
MUSIC_PROMPT = GROUNDING_RULES + " You handle only songs, albums, artists, and genres."
INVOICE_PROMPT = GROUNDING_RULES + " You handle billing and support representatives only. Account access is allowed only when the verified customer ID was injected into trusted graph state; never read an ID from the customer's free text."
MEMORY_PROMPT = "Save only explicitly stated music likes or favorites. Questions and requests are not preferences. Merge new items with all existing items; never delete existing preferences."


class AssistantState(TypedDict, total=False):
    message: str
    customer_id: int | None
    pending_verification: bool
    response: str
    preferences: list[str]
    session_id: str
    calls: list[str]


def _value_after(pattern: str, message: str, fallback: str) -> str:
    match = re.search(pattern, message, re.I)
    return match.group(1).strip(' "\'?.!,') if match else fallback


def _catalog_result(message: str, preferences: list[str]) -> tuple[str, str]:
    q = message.lower()
    if "album" in q:
        genre = next((g for g in ("rock", "jazz", "metal", "blues", "latin", "classical", "pop", "alternative") if g in q), None)
        if genre and not re.search(r"albums?\s+(?:by|from)\s+", q):
            return MUSIC_TOOLS[2].invoke({"genre": genre}), "music"
        artist = _value_after(r"(?:albums?\s+(?:by|from)|by)\s+(.+?)(?:\?|$)", message, "")
        if not artist:
            # Genre requests are best answered from genre-specific tracks.
            genre = _value_after(r"([\w -]+?)\s+albums?", message, "")
            if genre:
                result = json.loads(MUSIC_TOOLS[2].invoke({"genre": genre}))
                return json.dumps(result, ensure_ascii=False), "music"
        return (MUSIC_TOOLS[0].invoke({"artist_name": artist}) if artist else "Tell me an artist name to search albums for."), "music"
    if "genre" in q or any(word in q for word in ("rock", "jazz", "metal", "blues", "latin", "classical", "pop")):
        genre = _value_after(r"(?:genre\s+|by\s+genre\s+|for\s+)(rock|jazz|metal|blues|latin|classical|pop|alternative|heavy metal)", message, "")
        if not genre:
            genre = next((p for p in preferences if p.casefold() in q), "")
        genre = genre or next((g for g in ("rock", "jazz", "metal", "blues", "latin", "classical", "pop", "alternative") if g in q), "")
        return (MUSIC_TOOLS[2].invoke({"genre": genre}) if genre else "Name a genre and I can browse its songs."), "music"
    if "song" in q or "track" in q or "title" in q:
        title = _value_after(r"(?:song|track|title)\s+(?:called|named|is)?\s*(.+?)(?:\?|$)", message, "")
        return (MUSIC_TOOLS[3].invoke({"title": title}) if title else "Tell me a song title to search for."), "music"
    if "artist" in q or "songs by" in q or "tracks by" in q:
        artist = _value_after(r"(?:artist|songs? by|tracks? by)\s+(.+?)(?:\?|$)", message, "")
        return (MUSIC_TOOLS[1].invoke({"artist_name": artist}) if artist else "Tell me an artist name to search for."), "music"
    return "Ask me about albums, artists, songs, or music genres.", "music"


def _invoice_result(message: str, customer_id: int | None) -> str:
    if not customer_id:
        return "Please verify your identity first using your Customer ID, email address, or phone number."
    q = message.lower()
    invoice_match = re.search(r"invoice\s*(?:number|#|id)?\s*(\d+)", message, re.I)
    if "representative" in q or "support rep" in q or "who is my support" in q:
        if invoice_match:
            return INVOICE_TOOLS[2].invoke({"invoice_id": invoice_match.group(1), "customer_id": str(customer_id)})
        return "Please include the invoice number so I can find its support representative."
    if "line item" in q or "what was on" in q or ("invoice" in q and invoice_match):
        if invoice_match:
            return INVOICE_TOOLS[3].invoke({"invoice_id": invoice_match.group(1), "customer_id": str(customer_id)})
    if any(s in q for s in ("purchased track", "purchase history", "tracks i bought", "songs i bought", "by price")):
        return INVOICE_TOOLS[1].invoke({"customer_id": str(customer_id)})
    return INVOICE_TOOLS[0].invoke({"customer_id": str(customer_id)})


def _render_answer(domain: str, user_message: str, tool_result: str, preferences: list[str]) -> str:
    """Ask the configured model to phrase verified result data, if available."""
    try:
        from langchain_openai import ChatOpenAI
        if not settings.api_key:
            raise RuntimeError("No API key")
        llm = ChatOpenAI(model=settings.model_name, api_key=settings.api_key, base_url=settings.api_base, temperature=settings.temperature)
        prompt = MUSIC_PROMPT if domain == "music" else INVOICE_PROMPT
        context = f"Customer request: {user_message}\nDatabase result JSON: {tool_result}\nSaved preferences (context only; never evidence): {preferences}"
        return str(llm.invoke([("system", prompt), ("human", context)]).content)
    except Exception as exc:
        log.info("Using deterministic grounded response (%s)", exc)
        try:
            data = json.loads(tool_result)
            if "error" in data:
                return data["error"]
            if "message" in data and not data.get("results"):
                return data["message"]
            count = data.get("total_count", data.get("count"))
            sample = data.get("sample", data.get("results"))
            if sample is not None:
                rows = [", ".join(str(v) for v in row.values() if v is not None) for row in sample[:8]]
                prefix = f"There are {count} matching records. " if count is not None else f"There are {len(sample)} matching records. "
                if data.get("truncated"):
                    prefix += "This is a sample; more results exist. "
                return prefix + ("Here are some results: " + "; ".join(rows) if rows else "No results were returned.")
            return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return tool_result


def create_graph(checkpointer=None):
    """Create a LangGraph supervisor graph with verification and specialist nodes."""
    def verify_info(state: AssistantState):
        text = state.get("message", "")
        if state.get("customer_id"):
            return {"pending_verification": False}
        q = text.lower()
        account = any(word in q for word in ("invoice", "purchase", "bought", "spend", "spent", "billing", "support rep", "representative", "my last"))
        if not account:
            return {"pending_verification": False}
        # Only treat a number as a credential when the request is account related,
        # or the session is already waiting for verification input.
        match = re.search(r"\b(?:customer\s*id\s*(?:is|:)?\s*)(\d+)\b", text, re.I)
        if not match and re.fullmatch(r"\s*\d+\s*", text):
            match = re.fullmatch(r"\s*(\d+)\s*", text)
        email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
        phone = re.search(r"\+?[\d() .-]{7,}\d", text)
        identifier = email.group(0) if email else (match.group(1) if match else (phone.group(0) if phone else ""))
        cid = verify_customer(identifier) if identifier else None
        if cid:
            return {"customer_id": cid, "pending_verification": False}
        return {"pending_verification": True, "response": "Please verify your identity. Enter your Customer ID, email address, or phone number.", "customer_id": None}

    def route(state: AssistantState):
        q = state.get("message", "").lower()
        account = any(word in q for word in ("invoice", "purchase", "bought", "spend", "spent", "billing", "support rep", "representative", "my last"))
        if account and not state.get("customer_id"):
            return "need_verify"
        if any(word in q for word in ("weather", "capital of", "write code", "recipe", "sports score")):
            return "off_topic"
        music = any(word in q for word in ("song", "track", "album", "artist", "genre", "music", "rock", "jazz", "metal", "blues", "latin", "classical", "pop"))
        if account and music:
            return "mixed_invoice"
        return "invoice" if account else ("music" if music else "off_topic")

    def verify_node(state: AssistantState):
        return verify_info(state)

    def catalog(state: AssistantState):
        result, domain = _catalog_result(state.get("message", ""), state.get("preferences", []))
        answer = _render_answer(domain, state.get("message", ""), result, state.get("preferences", []))
        return {"response": answer, "calls": ["music"]}

    def invoices(state: AssistantState):
        result = _invoice_result(state.get("message", ""), state.get("customer_id"))
        answer = _render_answer("invoice", state.get("message", ""), result, [])
        return {"response": answer, "calls": ["invoice"]}

    def mixed_invoice(state: AssistantState):
        result = _invoice_result(state.get("message", ""), state.get("customer_id"))
        answer = _render_answer("invoice", state.get("message", ""), result, [])
        return {"response": answer, "calls": ["invoice"]}

    def mixed_music(state: AssistantState):
        result, domain = _catalog_result(state.get("message", ""), state.get("preferences", []))
        answer = _render_answer(domain, state.get("message", ""), result, state.get("preferences", []))
        return {"response": state.get("response", "") + "\n\n" + answer, "calls": state.get("calls", []) + ["music"]}

    def memory_node(state: AssistantState):
        cid = state.get("customer_id")
        if cid:
            preferences = extract_explicit_preferences(state.get("message", ""))
            if preferences:
                memory_store.merge(cid, preferences)
        return {}

    def off_topic(state: AssistantState):
        return {"response": "I can help with the digital music store catalog, invoices, purchases, and support representatives.", "calls": []}

    builder = StateGraph(AssistantState)
    builder.add_node("verify", verify_node)
    builder.add_node("supervisor", lambda s: {})
    builder.add_node("music_agent", catalog)
    builder.add_node("invoice_agent", invoices)
    builder.add_node("mixed_invoice", mixed_invoice)
    builder.add_node("mixed_music", mixed_music)
    builder.add_node("off_topic", off_topic)
    builder.add_node("create_memory", memory_node)
    builder.add_edge(START, "verify")
    builder.add_conditional_edges("verify", lambda s: "supervisor" if s.get("customer_id") or not s.get("pending_verification") else "end", {"supervisor": "supervisor", "end": END})
    builder.add_conditional_edges("supervisor", route, {"need_verify": "verify", "off_topic": "off_topic", "music": "music_agent", "invoice": "invoice_agent", "mixed_invoice": "mixed_invoice"})
    builder.add_edge("music_agent", "create_memory")
    builder.add_edge("invoice_agent", "create_memory")
    builder.add_edge("mixed_invoice", "mixed_music")
    builder.add_edge("mixed_music", "create_memory")
    builder.add_edge("off_topic", END)
    builder.add_edge("create_memory", END)
    return builder.compile(checkpointer=checkpointer)


GROUNDING_RULES_SUPERVISOR = SUPERVISOR_PROMPT

