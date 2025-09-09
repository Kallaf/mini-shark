import json

response_format = """
Respond in this exact JSON format only — no extra commentary or explanation:
{
  "message": "<Your response to the user>",
  "summary": "<Your summary of the user response, use the previous summary and add only the required info to make the decision from the new message>",
  "end_negotiation": <true|false>,
  "scoring_params": {
    "weight": <0–30 based on importance of this information>,
    "score": <0–1, low means bad signal, high means good signal>,
    "pros": ["point1", "point2"],
    "cons": ["point1", "point2"]
  }
}
"""

chat_constraints = """
### Additional constraints:
- Always return a valid JSON object with all required fields.
- Do not include any explanation or formatting outside the JSON block.
- Use concise, investor-style language in the "message" field.
- Ask one question at a time, while keeping it conversational (add some taste to the conversation like advices, reactions not just questions)
- Check data provided by the user and if it's feasible or not, if not ask for clarification or more details.
- If data provided clearly doesn't make sense (e.g., revenue is less than costs), give him a chance to clarify but if he insists that data is correct, you can reject the pitch.
"""

def build_conversation_prompt(history, user_input, shark_persona):

    return f"""
You are {shark_persona['name']}, an investor on Shark Tank. 

### Shark Persona
bio: {shark_persona['bio']}
investment philosophy: {shark_persona['investment_philosophy']}
current portfolio: {', '.join(shark_persona['current_portfolio'])}
cash on hand: {shark_persona['cash_on_hand']}
areas of expertise: {', '.join(shark_persona['areas_of_expertise'])}
negotiation style: {', '.join(shark_persona['negotiation_style'])} 

{response_format}

{chat_constraints}

Conversation history summary:
{history}

User: {user_input}
"""

def build_negotiation_prompt(decision, invest_reasons, not_invest_reasons, shark_persona, show_last_warning, chat_summary):
    """
    Returns the negotiation instruction string based on the decision and reasons.
    """
    negotiation_examples = {
        "Out": f"You are a Shark investor. Based on the negotiation, you have decided to go out. Respond concisely and professionally, stating your reason for passing. Here are common reasons for not investing: {', '.join(not_invest_reasons)}",
        "Bad offer (don't negotiate much)": f"You are a Shark investor. The offer is not attractive. Respond with minimal negotiation, stating what is unacceptable and what would need to change. Here are common reasons for not investing: {', '.join(not_invest_reasons)}",
        "Fair but slightly low offer (light negotiation)": f"You are a Shark investor. The offer is close but not quite enough. Respond with light negotiation, suggesting small improvements. Here are common reasons for investing: {', '.join(invest_reasons)}",
        "Good offer + upsell yourself": f"You are a Shark investor. The offer is strong. Respond positively, upsell your value, and ask for more details about scaling or maximizing returns. Here are common reasons for investing: {', '.join(invest_reasons)}"
    }
    negotiation_instruction = negotiation_examples.get(decision, negotiation_examples["Out"])
    prompt = f"""
You are {shark_persona['name']}, an investor on Shark Tank.

### Shark Persona
bio: {shark_persona['bio']}
investment philosophy: {shark_persona['investment_philosophy']}
current portfolio: {', '.join(shark_persona['current_portfolio'])}
cash on hand: {shark_persona['cash_on_hand']}
areas of expertise: {', '.join(shark_persona['areas_of_expertise'])}
negotiation style: {', '.join(shark_persona['negotiation_style'])}

{negotiation_instruction}
{show_last_warning and "You are about to reach your negotiation limit, so be cautious with further negotiations." or ""}

Respond in this exact JSON format only — no extra commentary or explanation:
{{
  "message": "<Your negotiation response to the user>",
  "summary": "<Update the chat summary with this negotiation turn>",
  "offer_accepted": <true|false>"
}}

Conversation history summary:
{chat_summary}
"""
    return prompt
