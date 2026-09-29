"""Optional OpenAI-compatible grounded answer generation with retries."""
import json, os, time, urllib.request, urllib.error

def grounded_answer(question, hits):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: return None
    endpoint=os.getenv("OPENAI_BASE_URL","https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    context="\n\n".join(f"[{h.entry['category']}] {h.entry['question']} {h.entry['answer']}" for h in hits)
    payload={"model":os.getenv("OPENAI_MODEL","gpt-4o-mini"),"temperature":0,"messages":[{"role":"system","content":"Answer only with facts explicitly supported by the supplied handbook excerpts. If they do not answer the question, say you do not have enough information. Do not infer policy."},{"role":"user","content":f"Handbook excerpts:\n{context}\n\nEmployee question: {question}"}]}
    for attempt in range(2):
        try:
            req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=15) as res: return json.loads(res.read().decode())["choices"][0]["message"]["content"].strip()
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError):
            if attempt == 0: time.sleep(0.25)
    return None

