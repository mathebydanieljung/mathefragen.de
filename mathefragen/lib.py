import requests
from django.conf import settings


def validate_with_turnstile(turnstile_token: str) -> bool:
    secret_key = settings.TURNSTILE_SECRET_KEY

    # Turnstile API URL
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    # Daten für die Validierung
    data = {
        'secret': secret_key,
        'response': turnstile_token,
    }

    # Anfrage an die Turnstile API senden
    response = requests.post(url, data=data)
    return response.json()
