"""Cleaning and format checks for text a shopper types into the shop.

Every free-text field passes through `clean_text` before it is checked,
stored, or shown. Passwords are never cleaned, only length-checked.
"""

import re
import unicodedata
import uuid

# Control characters (Cc), invisible formatting such as bidi overrides,
# zero-width spaces, and tag characters (Cf), and lone surrogates (Cs).
# Tag and zero-width characters can hide text from a person reading the
# transcript while a model still reads it.
_STRIPPED_CATEGORIES = {"Cc", "Cf", "Cs"}

MAX_NAME_LENGTH = 80
MAX_EMAIL_LENGTH = 254
MAX_PASSWORD_LENGTH = 128

_CARD_NUMBER = re.compile(r"^[0-9 -]+$")
_CARD_EXPIRY = re.compile(r"^(0[1-9]|1[0-2])\s*/\s*([0-9]{2})$")
_CARD_CVC = re.compile(r"^[0-9]{3,4}$")


def clean_text(raw: str) -> str:
    """Drop invisible and control characters and collapse runs of whitespace."""
    kept = "".join(
        " " if character.isspace() else character
        for character in raw
        if character.isspace() or unicodedata.category(character) not in _STRIPPED_CATEGORIES
    )
    return " ".join(kept.split())


def valid_email(email: str) -> bool:
    if len(email) > MAX_EMAIL_LENGTH or any(c.isspace() for c in email):
        return False
    local, _, domain = email.rpartition("@")
    labels = domain.split(".")
    return bool(local) and len(labels) >= 2 and all(labels)


def valid_card_number(number: str) -> bool:
    if not _CARD_NUMBER.fullmatch(number):
        return False
    return 12 <= sum(character.isdigit() for character in number) <= 19


def normalize_expiry(expiry: str) -> str | None:
    """Return the expiration as MM/YY, or None when it is not in that form."""
    match = _CARD_EXPIRY.fullmatch(expiry)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def valid_cvc(cvc: str) -> bool:
    return bool(_CARD_CVC.fullmatch(cvc))


def valid_order_id(value: str) -> bool:
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False
