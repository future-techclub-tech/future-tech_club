import base64
import hashlib
import hmac
import json
import time


class InvalidOnlyOfficeToken(ValueError):
    pass


def encode_onlyoffice_token(payload, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode('ascii')}.{_base64url_encode(signature)}"


def decode_onlyoffice_token(token, secret):
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_base64url_decode(encoded_header))
        payload = json.loads(_base64url_decode(encoded_payload))
        signature = _base64url_decode(encoded_signature)
    except (AttributeError, ValueError, json.JSONDecodeError) as error:
        raise InvalidOnlyOfficeToken("Malformed token.") from error
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise InvalidOnlyOfficeToken("Unsupported token algorithm.")
    if not isinstance(payload, dict):
        raise InvalidOnlyOfficeToken("Invalid token payload.")
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = hmac.new(
        secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidOnlyOfficeToken("Invalid token signature.")
    now = time.time()
    if "exp" in payload and float(payload["exp"]) <= now:
        raise InvalidOnlyOfficeToken("Token has expired.")
    if "nbf" in payload and float(payload["nbf"]) > now:
        raise InvalidOnlyOfficeToken("Token is not active.")
    return payload


def _base64url_encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
