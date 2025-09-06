from app.core.config import settings


def simulate_purchase(requested_coins: int) -> tuple[int, int]:
	if requested_coins <= 0:
		raise ValueError("coins must be positive")
	usd = (requested_coins + settings.COINS_PER_USD - 1) // settings.COINS_PER_USD
	return requested_coins, usd
