from pathlib import Path
from smartdesk.agent import SmartDeskAgent
from smartdesk.rag import KnowledgeBase
from smartdesk.tickets import ticket_service

def main():
    agent=SmartDeskAgent(KnowledgeBase(Path(__file__).parent/"data"/"knowledge_base.json"),ticket_service())
    sid="cli"
    print("SmartDesk Assistant — enter 'quit' to exit.")
    while True:
        try: text=input("You: ")
        except (EOFError,KeyboardInterrupt): print(); break
        if text.strip().lower() in {"quit","exit"}: break
        print("SmartDesk: "+agent.respond(text,sid)+"\n")
if __name__=="__main__": main()

