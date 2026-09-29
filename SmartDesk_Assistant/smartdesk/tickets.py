"""GitHub Issues ticket adapter and persistent SQLite demo adapter."""
from __future__ import annotations
import json, os, sqlite3, urllib.error, urllib.parse, urllib.request
from pathlib import Path

class TicketError(RuntimeError): pass

class LocalTickets:
    def __init__(self, db_path="smartdesk_tickets.sqlite3"):
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, title TEXT, description TEXT, category TEXT, priority TEXT, status TEXT, comment TEXT, url TEXT)")
    def create(self, email, title, description, category, priority):
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute("INSERT INTO tickets(email,title,description,category,priority,status,comment,url) VALUES(?,?,?,?,?,'Open','Awaiting triage', '')", (email.lower(),title,description,category,priority))
            n = cur.lastrowid
            db.execute("UPDATE tickets SET url=? WHERE id=?", (f"local://tickets/SD-{n:04d}",n))
        return {"id":f"SD-{n:04d}","title":title,"status":"Open","comment":"Awaiting triage","url":f"local://tickets/SD-{n:04d}"}
    def list_for_email(self,email):
        with sqlite3.connect(self.db_path) as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute("SELECT id,title,status,comment,url,category,priority FROM tickets WHERE lower(email)=? ORDER BY id DESC", (email.lower(),))]

class GitHubTickets:
    def __init__(self, repo, token):
        self.repo, self.token = repo, token
    def _request(self, method, url, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={"Authorization":f"Bearer {self.token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"SmartDesk-Assistant","Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as res: return json.loads(res.read().decode())
        except (urllib.error.URLError, TimeoutError, ValueError) as exc: raise TicketError("GitHub Issues is unavailable. Please try again later.") from exc
    def create(self,email,title,description,category,priority):
        body=f"{description}\n\n---\nEmployee email: {email}\nCategory: {category}\nPriority: {priority}\nCreated by SmartDesk Assistant."
        item=self._request("POST",f"https://api.github.com/repos/{self.repo}/issues",{"title":f"[{category}] {title}","body":body})
        return {"id":f"#{item['number']}","title":item["title"],"status":"Open","comment":"Ticket submitted to the support team.","url":item["html_url"]}
    def list_for_email(self,email):
        query=urllib.parse.quote(f"repo:{self.repo} is:issue {email}")
        results=self._request("GET",f"https://api.github.com/search/issues?q={query}&per_page=100")
        tickets=[]
        for issue in results.get("items",[]):
            if issue.get("pull_request"): continue
            if email.lower() not in issue.get("body","").lower(): continue
            comments=self._request("GET",issue["comments_url"])
            comment=comments[-1].get("body","") if comments else "No support team updates yet."
            tickets.append({"id":f"#{issue['number']}","title":issue["title"],"status":"Closed" if issue["state"]=="closed" else "Open","comment":comment,"url":issue["html_url"]})
        return tickets

def ticket_service():
    repo=os.getenv("GITHUB_TICKETS_REPO","").strip()
    token=os.getenv("GITHUB_TOKEN","").strip()
    if repo and token: return GitHubTickets(repo,token)
    return LocalTickets(os.getenv("SMARTDESK_DB","smartdesk_tickets.sqlite3"))

