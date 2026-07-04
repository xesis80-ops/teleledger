"""
Validates Telegram WebApp `initData` per Telegram's official algorithm:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

The frontend sends the raw initData string in the Authorization header:
    Authorization: TelegramWebApp <initData>

We verify the HMAC-SHA256 hash using a secret key derived from the bot token,
then reject stale requests (auth_date older than TELEGRAM_AUTH_MAX_AGE).
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import Profile


def validate_init_data(init_data: str, bot_token: str, max_age: int):
    """Returns the parsed user dict if valid, else raises ValueError."""
    if not init_data:
        raise ValueError("Missing initData")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing hash in initData")

    # Build the data-check-string: all fields except hash, sorted, joined by \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    # secret_key = HMAC-SHA256(bot_token, key="WebAppData")
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid initData signature")

    auth_date = int(parsed.get("auth_date", 0))
    if max_age and (time.time() - auth_date) > max_age:
        raise ValueError("initData has expired")

    user_json = parsed.get("user")
    if not user_json:
        raise ValueError("No user field in initData")

    return json.loads(user_json)


class TelegramInitDataAuthentication(authentication.BaseAuthentication):
    """
    Expects: Authorization: TelegramWebApp <raw_init_data_string>
    On success, attaches request.telegram_user (dict) and returns a Profile
    as request.user equivalent (first element of the auth tuple).
    """

    keyword = "TelegramWebApp"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith(self.keyword):
            return None  # let other auth / permission classes decide

        init_data = header[len(self.keyword):].strip()

        try:
            user_data = validate_init_data(
                init_data, settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_AUTH_MAX_AGE
            )
        except ValueError as exc:
            raise exceptions.AuthenticationFailed(str(exc))

        profile, _ = Profile.objects.get_or_create(
            telegram_id=user_data["id"],
            defaults={"username": user_data.get("username")},
        )
        request.telegram_user = user_data
        return (profile, None)
