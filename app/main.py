import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import (
    authenticate,
    create_user,
    ensure_demo_user,
    find_user_by_id,
    public_user,
    save_card,
    validate_new_account,
)
from app.catalog import format_price, get_item, sections
from app.storage import append_order, get_order, orders_for_user, session_secret

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="Lumen Beauty")
templates.env.filters["price"] = format_price
app.add_middleware(SessionMiddleware, secret_key=session_secret(), https_only=False)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

ensure_demo_user()


def current_user(request: Request) -> dict | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = find_user_by_id(user_id)
    if not user:
        request.session.pop("user_id", None)
        return None
    return public_user(user)


def pop_flash(request: Request) -> dict | None:
    flash = request.session.pop("flash", None)
    return flash if isinstance(flash, dict) else None


def set_flash(request: Request, kind: str, text: str) -> None:
    request.session["flash"] = {"kind": kind, "text": text}


def pop_added(request: Request) -> str | None:
    added = request.session.pop("added", None)
    return added if isinstance(added, str) and added else None


def cart_quantities(request: Request) -> dict[str, int]:
    raw = request.session.get("cart") or {}
    quantities: dict[str, int] = {}
    if not isinstance(raw, dict):
        return quantities
    for item_id, qty in raw.items():
        if get_item(str(item_id)) and isinstance(qty, int) and qty > 0:
            quantities[str(item_id)] = min(qty, 9)
    return quantities


def cart_lines(request: Request) -> list[dict]:
    lines = []
    for item_id, qty in cart_quantities(request).items():
        item = get_item(item_id)
        if not item:
            continue
        lines.append({**item, "qty": qty, "line_cents": item["price_cents"] * qty})
    return lines


def render(request: Request, name: str, **context):
    quantities = cart_quantities(request)
    return templates.TemplateResponse(
        request,
        name,
        {
            "user": current_user(request),
            "flash": pop_flash(request),
            "added": pop_added(request),
            "cart_count": sum(quantities.values()),
            **context,
        },
    )


def remember_order(request: Request, order_id: str) -> None:
    seen = [item for item in request.session.get("order_ids", []) if isinstance(item, str)]
    seen.append(order_id)
    request.session["order_ids"] = seen[-20:]


def card_last4(number: str) -> str:
    compact = "".join(number.split())
    digits = "".join(character for character in compact if character.isdigit())
    source = digits or compact
    return source[-4:]


def blank_checkout() -> dict:
    return {
        "checkout_as": "guest",
        "guest_name": "",
        "guest_email": "",
        "username": "",
        "display_name": "",
        "ship_name": "",
        "ship_line1": "",
        "ship_city": "",
        "ship_region": "",
        "ship_postal": "",
        "pay_with": "saved",
        "card_name": "",
        "card_number": "",
        "card_expiry": "",
        "save_card": False,
    }


def place_order(
    request: Request,
    user: dict | None,
    contact_name: str,
    contact_email: str,
    shipping: dict,
    last4: str,
) -> dict:
    lines = cart_lines(request)
    order = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"] if user else None,
        "guest_name": contact_name,
        "guest_email": contact_email,
        "shipping": shipping,
        "payment": {"last4": last4},
        "lines": [
            {
                "item_id": line["id"],
                "name": line["name"],
                "kind": line["kind"],
                "price_cents": line["price_cents"],
                "qty": line["qty"],
            }
            for line in lines
        ],
        "total_cents": sum(line["line_cents"] for line in lines),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    append_order(order)
    request.session["cart"] = {}
    remember_order(request, order["id"])
    return order


@app.get("/")
def shop(request: Request):
    return render(request, "shop.html", sections=sections())


@app.post("/cart/add")
def add_to_cart(request: Request, item_id: str = Form("")):
    item = get_item(item_id)
    if not item:
        set_flash(request, "error", "That item is not in the shop.")
        return RedirectResponse("/", status_code=303)
    cart = cart_quantities(request)
    cart[item["id"]] = min(cart.get(item["id"], 0) + 1, 9)
    request.session["cart"] = cart
    request.session["added"] = item["name"]
    return RedirectResponse("/", status_code=303)


@app.post("/cart/update")
def update_cart(request: Request, item_id: str = Form(""), quantity: str = Form("1")):
    cart = cart_quantities(request)
    if item_id in cart:
        try:
            qty = int(quantity)
        except ValueError:
            qty = cart[item_id]
        if qty < 1:
            cart.pop(item_id, None)
        else:
            cart[item_id] = min(qty, 9)
        request.session["cart"] = cart
    return RedirectResponse("/cart", status_code=303)


@app.get("/cart")
def view_cart(request: Request):
    lines = cart_lines(request)
    total = sum(line["line_cents"] for line in lines)
    return render(request, "cart.html", lines=lines, total_cents=total)


def checkout_page(request: Request, lines: list[dict], form: dict):
    return render(
        request,
        "checkout.html",
        lines=lines,
        total_cents=sum(line["line_cents"] for line in lines),
        form=form,
    )


def valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1] and " " not in email


@app.get("/checkout")
def checkout_form(request: Request):
    lines = cart_lines(request)
    if not lines:
        set_flash(request, "error", "Your cart is empty.")
        return RedirectResponse("/cart", status_code=303)
    return checkout_page(request, lines, blank_checkout())


@app.post("/checkout")
def checkout(
    request: Request,
    checkout_as: str = Form("guest"),
    guest_name: str = Form(""),
    guest_email: str = Form(""),
    username: str = Form(""),
    display_name: str = Form(""),
    password: str = Form(""),
    confirm: str = Form(""),
    ship_name: str = Form(""),
    ship_line1: str = Form(""),
    ship_city: str = Form(""),
    ship_region: str = Form(""),
    ship_postal: str = Form(""),
    pay_with: str = Form("new"),
    card_name: str = Form(""),
    card_number: str = Form(""),
    card_expiry: str = Form(""),
    card_cvc: str = Form(""),
    save_card_choice: str = Form(""),
):
    lines = cart_lines(request)
    if not lines:
        set_flash(request, "error", "Your cart is empty.")
        return RedirectResponse("/cart", status_code=303)
    form = {
        "checkout_as": "account" if checkout_as == "account" else "guest",
        "guest_name": guest_name.strip(),
        "guest_email": guest_email.strip(),
        "username": username.strip(),
        "display_name": display_name.strip(),
        "ship_name": ship_name.strip(),
        "ship_line1": ship_line1.strip(),
        "ship_city": ship_city.strip(),
        "ship_region": ship_region.strip(),
        "ship_postal": ship_postal.strip(),
        "pay_with": "saved" if pay_with == "saved" else "new",
        "card_name": card_name.strip(),
        "card_number": card_number.strip(),
        "card_expiry": card_expiry.strip(),
        "save_card": save_card_choice == "yes",
    }
    user = current_user(request)
    error = None
    if not user and form["checkout_as"] == "guest":
        if not form["guest_name"] or len(form["guest_name"]) > 80:
            error = "Enter the name for this order."
        elif not valid_email(form["guest_email"]):
            error = "Enter an email address for the receipt."
    elif not user:
        error = validate_new_account(form["username"], form["display_name"], password, confirm)
    if not error:
        for value, message in (
            (form["ship_name"], "Enter the name for shipping."),
            (form["ship_line1"], "Enter a street address."),
            (form["ship_city"], "Enter a city."),
            (form["ship_region"], "Enter a state."),
            (form["ship_postal"], "Enter a postal code."),
        ):
            if not value or len(value) > 80:
                error = message
                break
    use_saved = bool(user and user.get("saved_card") and form["pay_with"] == "saved")
    last4 = ""
    expiry = ""
    name_on_card = ""
    if not error and use_saved:
        last4 = user["saved_card"]["last4"]
        expiry = user["saved_card"].get("expiry", "")
        name_on_card = user["saved_card"].get("name", "")
    elif not error:
        if not form["card_number"]:
            error = "Enter a card number. Any number is accepted in this demo."
        elif not form["card_name"]:
            error = "Enter the name on the card."
        elif not form["card_expiry"]:
            error = "Enter the card expiration."
        elif not card_cvc.strip():
            error = "Enter the card security code."
        else:
            last4 = card_last4(form["card_number"])
            expiry = form["card_expiry"]
            name_on_card = form["card_name"]
    if error:
        set_flash(request, "error", error)
        return checkout_page(request, lines, form)

    contact_name = user["display_name"] if user else form["guest_name"]
    contact_email = "" if user else form["guest_email"]
    if not user and form["checkout_as"] == "account":
        user = public_user(create_user(form["username"], form["display_name"], password))
        request.session["user_id"] = user["id"]
        contact_name = user["display_name"]
        contact_email = ""
    if form["save_card"] and user and not use_saved:
        save_card(
            user["id"],
            {"last4": last4, "expiry": expiry, "name": name_on_card},
        )
    order = place_order(
        request,
        user,
        contact_name,
        contact_email,
        {
            "name": form["ship_name"],
            "line1": form["ship_line1"],
            "city": form["ship_city"],
            "region": form["ship_region"],
            "postal": form["ship_postal"],
        },
        last4,
    )
    return RedirectResponse(f"/orders/{order['id']}", status_code=303)


@app.get("/orders/{order_id}")
def order_confirmation(request: Request, order_id: str):
    order = get_order(order_id)
    user = current_user(request)
    visible = order and (
        (user and order.get("user_id") == user["id"])
        or order_id in request.session.get("order_ids", [])
    )
    if not visible:
        set_flash(request, "error", "That order could not be found.")
        return RedirectResponse("/", status_code=303)
    return render(request, "confirmation.html", order=order)


@app.get("/login")
def login_form(request: Request):
    if current_user(request):
        return RedirectResponse("/account", status_code=303)
    return render(request, "login.html", username="")


@app.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form("")):
    user = authenticate(username, password)
    if not user:
        set_flash(request, "error", "That username and password do not match.")
        return render(request, "login.html", username=username.strip())
    request.session["user_id"] = user["id"]
    return RedirectResponse("/account", status_code=303)


@app.get("/register")
def register_form(request: Request):
    if current_user(request):
        return RedirectResponse("/account", status_code=303)
    return render(
        request,
        "register.html",
        username="",
        display_name="",
    )


@app.post("/register")
def register(
    request: Request,
    username: str = Form(""),
    display_name: str = Form(""),
    password: str = Form(""),
    confirm: str = Form(""),
):
    error = validate_new_account(username, display_name, password, confirm)
    if error:
        set_flash(request, "error", error)
        return render(
            request,
            "register.html",
            username=username.strip(),
            display_name=display_name.strip(),
        )
    user = create_user(username, display_name, password)
    request.session["user_id"] = user["id"]
    return RedirectResponse("/account", status_code=303)


@app.get("/account")
def account(request: Request):
    user = current_user(request)
    if not user:
        set_flash(request, "error", "Sign in to view your account.")
        return RedirectResponse("/login", status_code=303)
    return render(request, "account.html", orders=orders_for_user(user["id"]))


@app.post("/logout")
def logout(request: Request):
    cart = request.session.get("cart")
    order_ids = request.session.get("order_ids")
    request.session.clear()
    if cart:
        request.session["cart"] = cart
    if order_ids:
        request.session["order_ids"] = order_ids
    return RedirectResponse("/", status_code=303)
