"""Small, deterministic hybrid retriever for the bundled employee handbook."""
from __future__ import annotations
import json, math, re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {"a","an","the","to","of","for","is","are","do","i","how","what","my","in","on","and","or","can","it","me","we","you","your","with","this","that","from","be","get"}

@dataclass(frozen=True)
class Hit:
    entry: dict
    score: float

class KnowledgeBase:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.entries = json.loads(self.path.read_text(encoding="utf-8"))
        self.docs = [self._tokens(" ".join((e["question"], e["category"], e["answer"]))) for e in self.entries]
        self.avg_len = sum(map(len, self.docs)) / max(1, len(self.docs))
        df = Counter(t for doc in self.docs for t in set(doc))
        self.idf = {t: math.log(1 + (len(self.docs)-n+0.5)/(n+0.5)) for t,n in df.items()}

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [t for t in TOKEN.findall(text.lower()) if t not in STOP]

    def search(self, query: str, k: int = 4) -> list[Hit]:
        terms = self._tokens(query)
        if not terms: return []
        hits = []
        for e, doc in zip(self.entries, self.docs):
            counts = Counter(doc); score = 0.0
            # BM25 term weighting plus a query-to-question coverage component.
            for term in set(terms):
                f = counts[term]
                if f:
                    score += self.idf.get(term, 0) * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * len(doc) / self.avg_len))
            qterms = set(terms)
            qdoc = set(self._tokens(e["question"]))
            score += 0.65 * len(qterms & qdoc) / max(1, len(qterms))
            if not score: continue
            # Mild phrase reranking gives the question field extra weight.
            normalized = " ".join(terms)
            question = e["question"].lower()
            if normalized and normalized in question: score += 0.5
            hits.append(Hit(e, score))
        return sorted(hits, key=lambda h: h.score, reverse=True)[:k]

    def answer(self, query: str, threshold: float = 0.9) -> tuple[str | None, list[Hit]]:
        hits = self.search(query)
        qterms=set(self._tokens(query))
        if not hits or hits[0].score < threshold:
            return None, hits
        # Generic words in an answer (for example, "office" or "policy") are
        # insufficient evidence by themselves. Require a query term to match
        # the entry's question and at least two terms to match its full record.
        entry=hits[0].entry
        question_terms=set(self._tokens(entry["question"]))
        record_terms=set(self._tokens(" ".join((entry["question"],entry["category"],entry["answer"]))))
        if len(qterms & question_terms)<min(2,len(qterms)) or len(qterms & record_terms)<2:
            return None, hits
        # Keep answer extractive by default; the optional LLM layer receives only these hits.
        return entry["answer"], hits

