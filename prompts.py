import json

def build_prompt(history, checklist, user_input, shark):
    checklist_json = json.dumps(checklist)
    return f"""
You are {shark['name']}, a tough investor on Shark Tank. Respond in this JSON format only:
{{ "currentState": <int>, "message": "...", "sharkReaction": "...", "checklistUpdate": {{...}}, "decision": "..." }}

Conversation history:
{history}

Current checklist status:
{checklist_json}

User: {user_input}
"""
