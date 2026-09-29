from __future__ import annotations
import re
from dataclasses import dataclass, field
from .llm import grounded_answer
from .rag import KnowledgeBase

EMAIL=re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",re.I)
YES={"yes","y","yeah","yep","please","go ahead","confirm","sure","create it","do it"}
NO={"no","n","nope","cancel","don't","do not","not now"}

@dataclass
class Session:
    email: str|None=None
    state: str="idle"
    pending: dict=field(default_factory=dict)
    tickets: list=field(default_factory=list)

class SmartDeskAgent:
    def __init__(self,kb:KnowledgeBase,tickets): self.kb,self.tickets=kb,tickets; self.sessions={}
    def reset(self,sid): self.sessions.pop(sid,None)
    def respond(self,message,sid="default"):
        s=self.sessions.setdefault(sid,Session()); text=message.strip(); low=text.lower()
        found=EMAIL.search(text)
        if found: s.email=found.group(0).lower()
        if s.state=="confirm":
            if low in YES:
                p=s.pending
                try: ticket=self.tickets.create(s.email,p["title"],p["description"],p["category"],p["priority"])
                except Exception as exc: s.state="idle"; return f"I couldn't submit the ticket right now. {exc} You can try again later."
                s.state="idle"; s.pending={}
                return f"Your ticket {ticket['id']} has been created: {ticket['title']} ({ticket['status']}). Track it here: {ticket['url']}"
            if low in NO: s.state="idle"; s.pending={}; return "Understood. I have not created a ticket."
            return "Please reply yes to create the ticket or no to cancel."
        if s.state=="ticket_email":
            if not s.email: return "Please share your work email address so I can look up tickets."
            s.state="ticket_lookup"; return self._lookup(s)
        if s.state=="create_email":
            if not s.email: return "Please share your work email address so I can associate it with the ticket."
            s.state="confirm"; return self._confirmation(s)
        if s.state=="ticket_select":
            try: idx=int(text)-1
            except ValueError: return "Please choose a ticket by its list number, or say cancel."
            if not 0<=idx<len(s.tickets): return "That number isn't in the list. Please choose one of the listed tickets."
            t=s.tickets[idx]; s.state="idle"
            return f"{t['id']} — {t['title']}\nStatus: {t['status']}\nLatest update: {t.get('comment') or 'No support team updates yet.'}\n{t.get('url','')}"
        if any(x in low for x in ("status of my ticket","status on my ticket","ticket status","check my ticket","updates on my","update on my","my tickets","did anyone look")):
            if not s.email: s.state="ticket_email"; return "I can check that. What work email address did you use for the ticket?"
            return self._lookup(s)
        if any(x in low for x in ("create a ticket","open a ticket","raise a ticket","make a ticket")) and s.pending:
            s.state="confirm"; return self._confirmation(s)
        if low in {"hi","hello","hey","good morning","good afternoon"}: return "Hello! I can help with Northstar IT, HR, onboarding, and payroll guidance, or check a support ticket. What do you need?"
        if low in {"thanks","thank you","no thanks","bye","goodbye"}: return "You're welcome. Let me know if you need help with IT or People Operations."
        answer,hits=self.kb.answer(text)
        if answer:
            generated=grounded_answer(text,hits)
            return (generated or answer)+"\n\nSource: "+", ".join(h.entry["id"] for h in hits[:2])
        category=self._category(text)
        title=self._title(text)
        s.pending={"title":title,"description":f"Employee reported: {text}","category":category,"priority":"Medium"}
        if not s.email:
            s.state="create_email"; return "I don't have enough information in the handbook to answer that confidently. I can prepare a support ticket. What work email should I associate with it?"
        s.state="confirm"; return self._confirmation(s)
    def _confirmation(self,s):
        p=s.pending
        return ("Here is the ticket I will submit:\n" f"Title: {p['title']}\nDescription: {p['description']}\nCategory: {p['category']}\nPriority: {p['priority']}\nEmail: {s.email}\n\n" "Shall I create it? Please reply yes or no.")
    def _lookup(self,s):
        try: items=self.tickets.list_for_email(s.email)
        except Exception as exc: s.state="idle"; return f"I couldn't reach the ticket system. Please try again later. ({exc})"
        s.state="idle"
        if not items: return f"I couldn't find any tickets associated with {s.email}."
        if len(items)>1:
            s.tickets=items; s.state="ticket_select"
            return "I found these tickets:\n"+"\n".join(f"{i+1}. {t['id']} — {t['title']} ({t['status']})" for i,t in enumerate(items))+"\nReply with a number for the latest update."
        t=items[0]
        return f"{t['id']} — {t['title']}\nStatus: {t['status']}\nLatest update: {t.get('comment') or 'No support team updates yet.'}\n{t.get('url','')}"
    @staticmethod
    def _category(text):
        hr={"leave","payroll","salary","benefit","reimbursement","harassment","manager","people","hr","vacation"}
        return "HR" if set(re.findall(r"[a-z]+",text.lower())) & hr else "IT"
    @staticmethod
    def _title(text):
        title=" ".join(text.split())
        return title[:78].rstrip(" .?!") or "Employee support request"

