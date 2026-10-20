"""Stand-in results for the payment processor and the account store.

A declined card is a shopper outcome (201). The cases here are the shop or a
service it calls failing. Card numbers are matched on digits only.
"""

from app.errors import DECLINED_CARD, card_digits

PROCESSOR_DOWN_CARD = "4000000000000119"
NETWORK_DOWN_CARD = "4000000000000502"
TIMEOUT_CARD = "4000000000000507"
ORDER_SAVE_FAIL_CARD = "4000000000000504"
CARD_SAVE_FAIL_CARD = "4000000000000505"
UNKNOWN_FAILURE_CARD = "4000000000000500"

NETWORK_DOWN_USERNAME = "networkdown"
ACCOUNT_SAVE_FAIL_USERNAME = "storagefail"
ORDERS_READ_FAIL_USERNAME = "recordsdown"


class BackendFault(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(code)


def authorize_card(number: str) -> str:
    """Return the last four digits, or raise when the processor does not approve."""
    digits = card_digits(number)
    last4 = digits[-4:] if len(digits) >= 4 else digits
    detail = f"last4 {last4}" if last4 else "missing number"
    if digits == DECLINED_CARD:
        raise BackendFault("201", detail)
    if digits == PROCESSOR_DOWN_CARD:
        raise BackendFault("501", detail)
    if digits == NETWORK_DOWN_CARD:
        raise BackendFault("502", detail)
    if digits == TIMEOUT_CARD:
        raise BackendFault("507", detail)
    if digits == UNKNOWN_FAILURE_CARD:
        raise RuntimeError("unexpected payment response")
    return last4


def account_store_fault(username: str) -> BackendFault | None:
    key = username.strip().lower()
    if key == NETWORK_DOWN_USERNAME:
        return BackendFault("502", "username networkdown")
    if key == ACCOUNT_SAVE_FAIL_USERNAME:
        return BackendFault("503", "username storagefail")
    return None


def orders_unreadable(username: str) -> bool:
    return username.strip().lower() == ORDERS_READ_FAIL_USERNAME


def order_save_fails(number: str) -> bool:
    return card_digits(number) == ORDER_SAVE_FAIL_CARD


def card_save_fails(number: str) -> bool:
    return card_digits(number) == CARD_SAVE_FAIL_CARD


def code_for_storage(operation: str) -> str:
    if operation.startswith("read"):
        return "506"
    if operation.startswith("write users"):
        return "503"
    if operation.startswith("write orders"):
        return "504"
    return "500"
