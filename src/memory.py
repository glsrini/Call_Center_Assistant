"""Customer-scoped, additive preference memory."""
from __future__ import annotations

import re
from typing import TypedDict


class UserProfile(TypedDict):
    customer_id: int
    music_preferences: list[str]


class PreferenceStore:
    """Simple in-memory store matching the capstone's namespace contract."""
    def __init__(self):
        self._values: dict[tuple[str, int, str], UserProfile] = {}

    def get(self, customer_id: int) -> UserProfile:
        profile = self._values.get(("memory_profile", customer_id, "user_memory"))
        return {"customer_id": customer_id, "music_preferences": list(profile["music_preferences"])} if profile else {"customer_id": customer_id, "music_preferences": []}

    def merge(self, customer_id: int, preferences: list[str]) -> UserProfile:
        current = self.get(customer_id)
        merged = current["music_preferences"][:]
        keys = {v.casefold() for v in merged}
        for preference in preferences:
            clean = preference.strip()
            if clean and clean.casefold() not in keys:
                merged.append(clean)
                keys.add(clean.casefold())
        if merged != current["music_preferences"]:
            self._values[("memory_profile", customer_id, "user_memory")] = {"customer_id": customer_id, "music_preferences": merged}
        return self.get(customer_id)


def extract_explicit_preferences(message: str) -> list[str]:
    """Conservative local extractor; interrogative requests are never saved."""
    text = message.strip()
    if not re.search(r"\b(i|my)\b", text, re.I) or re.search(r"\?", text):
        return []
    if not re.search(r"\b(love|like|enjoy|favorite|favourite|fan of|prefer)\b", text, re.I):
        return []
    cleaned = re.sub(r"^(?:i\s+(?:really\s+)?(?:love|like|enjoy|prefer)|i'?m\s+a\s+fan\s+of|my\s+(?:favorite|favourite)\s+is)\s+", "", text, flags=re.I)
    cleaned = re.sub(r"[.!]+$", "", cleaned)
    return [part.strip(" ,") for part in re.split(r"\s+and\s+|\s*,\s*", cleaned) if part.strip(" ,")]


memory_store = PreferenceStore()

