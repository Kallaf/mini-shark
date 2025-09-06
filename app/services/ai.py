from app.models.models import ChatSession


def generate_ai_reply(session: ChatSession, user_message: str) -> str:
	name = session.shark.name if session.shark else "Shark"
	return f"{name}: I hear you said '{user_message}'. Let's dive deeper!"
