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
4. **Error logging.** Three-digit error codes for problems a shopper can hit, with logs and documentation an agent can use.
5. **Chat window.** A popup on the storefront that talks to the support agent.
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

The shop is Lumen Beauty, a local beauty store with 25 items: skincare, makeup, a product consultation, and professional makeup. Each card uses a square labeled “photo” instead of an image. Shoppers add items to a cart, then check out with shipping and a card. Any card number is accepted. Guests can buy without an account, or create one during checkout and save the card. Orders are written to `data/orders.json`. Signed-in orders and a saved card appear on the account page. Only the last four characters of a card are stored.
