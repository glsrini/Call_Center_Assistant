from pathlib import Path
from smartdesk.agent import SmartDeskAgent
from smartdesk.rag import KnowledgeBase
from smartdesk.tickets import LocalTickets
from smartdesk.tickets import TicketError

BASE=Path(__file__).resolve().parents[1]

def build(tmp_path):
    kb=KnowledgeBase(BASE/"data"/"knowledge_base.json")
    return SmartDeskAgent(kb,LocalTickets(tmp_path/"tickets.sqlite3")),kb

def test_knowledge_coverage_and_grounded_retrieval(tmp_path):
    agent,kb=build(tmp_path)
    assert len(kb.entries)>=30
    assert {x["category"] for x in kb.entries}>={"IT Support","HR Policies","Onboarding","Payroll & Compensation"}
    answer=agent.respond("How can I reset my password?")
    assert "password" in answer.lower() and "it-01" in answer
    assert kb.answer("What is the office parking reimbursement policy?")[0] is None

def test_unknown_requires_email_confirmation_and_creates_ticket(tmp_path):
    agent,_=build(tmp_path)
    reply=agent.respond("My monitor flickers during video calls.","one")
    assert "email" in reply.lower() and "don't have enough information" in reply.lower()
    reply=agent.respond("jane@example.com","one")
    assert "Shall I create it" in reply and "jane@example.com" in reply
    assert agent.tickets.list_for_email("jane@example.com")==[]
    reply=agent.respond("yes","one")
    assert "created" in reply.lower() and "SD-" in reply

def test_cancel_does_not_create_ticket(tmp_path):
    agent,_=build(tmp_path)
    agent.respond("Unknown printer issue","two")
    agent.respond("sam@example.com","two")
    assert "not created" in agent.respond("no","two")
    assert not agent.tickets.list_for_email("sam@example.com")

def test_status_multiple_selection_and_no_match(tmp_path):
    agent,_=build(tmp_path)
    for title in ("VPN drops every hour","Keyboard is not working"):
        agent.respond(title,"create")
        agent.respond("lee@example.com","create")
        agent.respond("yes","create")
    reply=agent.respond("Check my ticket status","status")
    assert "email" in reply.lower()
    reply=agent.respond("lee@example.com","status")
    assert "1." in reply and "2." in reply
    assert "Status:" in agent.respond("1","status")
    agent.respond("Check my tickets","empty")
    assert "couldn't find" in agent.respond("nobody@example.com","empty")

def test_session_remembers_email_and_separates_sessions(tmp_path):
    agent,_=build(tmp_path)
    agent.respond("Unknown issue","a"); reply=agent.respond("pat@example.com","a")
    assert "pat@example.com" in reply
    assert "work email" in agent.respond("Unknown issue","b").lower()

def test_ticket_api_failures_are_polite(tmp_path):
    class UnavailableTickets:
        def create(self,*args): raise TicketError("ticket service unavailable")
        def list_for_email(self,*args): raise TicketError("ticket service unavailable")
    agent=SmartDeskAgent(KnowledgeBase(BASE/"data"/"knowledge_base.json"),UnavailableTickets())
    agent.respond("My monitor flickers","create-failure")
    agent.respond("jules@example.com","create-failure")
    reply=agent.respond("yes","create-failure")
    assert "try again later" in reply.lower()
    reply=agent.respond("Ticket status for jules@example.com","status-failure")
    assert "try again later" in reply.lower()

def test_optional_llm_failure_uses_retrieved_answer(tmp_path,monkeypatch):
    monkeypatch.setattr("smartdesk.agent.grounded_answer",lambda question,hits: None)
    agent,_=build(tmp_path)
    reply=agent.respond("How do I reset my password?")
    assert "https://help.northstar.example/password" in reply
    assert "it-01" in reply

def test_greeting_is_graceful(tmp_path):
    agent,_=build(tmp_path)
    assert "Hello" in agent.respond("Hi")

