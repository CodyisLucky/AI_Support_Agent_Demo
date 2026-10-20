# AI Support Agent Demo

A local storefront used to demonstrate an AI support agent. A shopper can browse fake products and services, sign in, and run into ordinary website problems. A chat window can then answer product questions and troubleshoot those problems from documentation and the shopper's own logs.

Nothing in this project is hosted. The site runs on your machine. Accounts, orders, error logs, chat transcripts, and support tickets are written to a local `data/` directory and are not committed.

## Stack

- Python and FastAPI
- Plain HTML pages for the storefront
- JSON or SQLite on disk for accounts, orders, and logs

The support model and how it reads documentation (full prompt vs retrieval) are chosen in step 6. Steps 1–5 stay model-agnostic. Product docs and error logs are written so either approach can use them later.

## Steps

1. **Repo and starter docs.** Git metadata, this README, and [docs/roadmap.md](docs/roadmap.md).
2. **Storefront.** Lumen Beauty shop with 25 skincare, makeup, and service items. Guests and signed-in shoppers can review a cart and check out locally.
3. **Product documentation.** Done. Agent-facing docs for all 25 products and services are in [docs/catalog](docs/catalog).
4. **Error logging.** Done. Three-digit codes fire from real shop flows and are documented in [docs/errors](docs/errors). Each line in `data/errors.jsonl` has the time, user id, and code.
5. **Chat window.** Done. A Help bubble on every page opens a chat. Replies are a stub until step 6. The visit's transcript is saved in `data/chats.json`.
6. **Train and connect the agent.** Choose the model and connect it to the docs, logs, and chat window.

See [docs/roadmap.md](docs/roadmap.md) for what each remaining step delivers, including seeded demo data, error correlation, what the agent may read, local tickets, and saved transcripts.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If `python3 -m venv .venv` fails because `ensurepip` is missing, create the environment without pip and install pip into it:

```bash
python3 -m venv --without-pip .venv
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

A seeded shopper is created on first launch: username `demo`, password `demo-shopper`. That account has no orders yet. New accounts are written to `data/users.json`, which is gitignored.

## Step 2 status

The shop is Lumen Beauty, a local beauty store with 25 items: skincare, makeup, a product consultation, and professional makeup. Each card uses a square labeled “photo” instead of an image. Shoppers add items to a cart, then check out with shipping and a card. Any card number is accepted except the demo numbers listed on checkout. Guests can buy without an account, or create one during checkout and save the card. Orders are written to `data/orders.json`. Signed-in orders and a saved card appear on the account page. Only the last four characters of a card are stored.

## Step 4 status

Shopper failures write a JSON line to `data/errors.jsonl` with `time`, `session_id`, `user_id`, `code`, and `detail`. The banner shows the same code. Docs for the agent are in [docs/errors](docs/errors).

`session_id` is created on the first page load and stored in the browser cookie `lumen_sid` until the browser closes. It does not change when the shopper signs in or out, so a chat on that visit can be matched to the errors from the same visit. The page exposes the same value in `<meta name="shop-session">`.

- **101** sign-in failed. **102** session expired after 30 minutes idle, a missing timestamp, or a missing account. **103** username already registered.
- **201** card `4000000000000002` declined. **202** Warm Highlighter is out of stock. **203** checkout with an empty cart.
- **301** order link this shopper cannot open.
- **500** unknown shop error, including card `4000000000000500`. **501** payment processor unavailable (`4000000000000119`). **502** network unavailable (`4000000000000502`, or username `networkdown`). **503** account was not saved (`storagefail`, or the user file could not be written). **504** order was not saved (`4000000000000504`). **505** order placed, card not saved (`4000000000000505`). **506** account records could not be loaded (`recordsdown`, or a user or order file could not be read). **507** payment processor timed out (`4000000000000507`).

A signed-out attempt stores `user_id` null, except a failed sign-in for a real account, which stores that account's id. The log does not store passwords or full card numbers.

## Step 5 status

A Help bubble sits at the bottom right of every page. Opening it shows a chat that stays on the page the shopper is already on. Sending a message appends that message and a stub reply: the support agent is not connected yet. Step 6 replaces the stub.

The conversation for the current browser session is stored in `data/chats.json`. It uses the same `session_id` as the error log, so a later agent can read this visit's transcript beside `data/errors.jsonl`. Each shopper message includes the signed-in account id, or null for a guest. Signing out does not start a new chat. Closing the browser does, because the session cookie ends.
