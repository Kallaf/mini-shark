def generate_report(model, history):
    prompt = f"""Summarize the Shark Tank pitch session... \n{history}"""
    response = model.generate_content(prompt)
    return response.text

def format_report(text):
    lines = text.strip().split("\n")
    html = ""
    for line in lines:
        if line.startswith("- "):
            html += f"<li>{line[2:].strip()}</li>"
        elif line.strip() == "":
            html += "<br>"
        else:
            html += f"<h4>{line.strip()}</h4>"
    return f"<div style='padding:1rem;background:#f9f9f9;border-radius:8px;'>{html}</div>"
