from __future__ import annotations
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from smartdesk.agent import SmartDeskAgent
from smartdesk.rag import KnowledgeBase
from smartdesk.tickets import ticket_service

ROOT=Path(__file__).resolve().parent
agent=SmartDeskAgent(KnowledgeBase(ROOT/"data"/"knowledge_base.json"),ticket_service())
PAGE="""<!doctype html><html><head><meta charset=utf-8><title>SmartDesk Assistant</title><style>body{font:16px system-ui;max-width:850px;margin:3rem auto;padding:0 1rem;background:#f5f7fb;color:#182230}h1{color:#165d8f}.chat{background:white;border:1px solid #dce3ec;border-radius:12px;padding:1rem;min-height:60vh}.msg{white-space:pre-wrap;padding:.8rem;margin:.6rem 0;border-radius:9px}.user{background:#e8f2fb}.bot{background:#f0f3f7}form{display:flex;gap:.5rem;margin-top:1rem}input{flex:1;padding:.9rem;border:1px solid #bdc8d6;border-radius:8px}button{background:#165d8f;color:white;border:0;padding:.8rem 1.2rem;border-radius:8px}</style></head><body><h1>SmartDesk Assistant</h1><p>Northstar IT, HR, onboarding, payroll, and support ticket help.</p><main class=chat id=chat></main><form id=form><input id=message autocomplete=off placeholder="Ask a question or check a ticket" required><button>Send</button></form><script>let sid=localStorage.smartdeskSession||(localStorage.smartdeskSession=crypto.randomUUID());const chat=document.querySelector('#chat');function add(text,who){let d=document.createElement('div');d.className='msg '+who;d.textContent=text;chat.appendChild(d);chat.scrollTop=chat.scrollHeight}document.querySelector('#form').onsubmit=async e=>{e.preventDefault();let m=document.querySelector('#message'),text=m.value;m.value='';add(text,'user');let data=new URLSearchParams({message:text,session:sid});let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:data});add(await r.text(),'bot')};add('Hello! I can answer from the employee handbook or help with support tickets.','bot');</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(PAGE.encode())
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0")); form=parse_qs(self.rfile.read(n).decode()); msg=form.get("message",[""])[0]; sid=form.get("session",["default"])[0]
        result=agent.respond(msg,sid)
        self.send_response(200); self.send_header("Content-Type","text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(result.encode())
    def log_message(self,fmt,*args): pass

if __name__=="__main__":
    host=os.getenv("HOST","127.0.0.1"); port=int(os.getenv("PORT","7860"))
    print(f"SmartDesk Assistant listening on http://{host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()

