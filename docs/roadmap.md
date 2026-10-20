# Roadmap

Step 1 is done: this repo, [README.md](../README.md), and this file. Step 2 has the Lumen Beauty shop, login, and local purchases.

The support model and retrieval approach are deferred to step 6. Product docs and error logs should stay plain files an agent can read either by loading them into a prompt or by retrieving relevant pages.

## Step 2 — Storefront

FastAPI app serving plain HTML.

- Shop, sign-in, create-account, account, cart, and checkout pages are done. The catalog has 25 skincare, makeup, and service items. Cards use a flat color swatch instead of a photo. The visual system for later page work is in [DESIGN.md](../DESIGN.md).
- Login flows: register, sign in, sign out, and view account. Accounts are saved under `data/`. A login is not required to buy.
- A cart is reviewed before checkout. Checkout collects shipping and a card, and accepts any card number except the demo numbers documented in [docs/errors](errors). A shopper can check out as a guest or create an account and save the card. Orders are written to `data/orders.json`. Signed-in orders and the saved card appear on the account page.

**Seeded shopper.** Username `demo`, password `demo-shopper`, created on first launch. Known orders and a known failure wait until the catalog and the error-code step exist.

## Step 3 — Product documentation

Done. [docs/catalog](catalog) has one file per product and service, plus an index and a short guide for the agent. The files are separate from the HTML so step 6 can load them without scraping the storefront.

Each file includes what it is, price and size, ingredients or what a service includes, benefits, drawbacks, when it works, when it does not, how to use it, and shopper questions with answers. Prices and shades in those files match the shop.

## Step 4 — Error logging

Done. [docs/errors](errors) documents each code: what the shopper sees, when it happens, the likely cause, and what to try. The shop writes `data/errors.jsonl`. Each line has `time`, `session_id`, `user_id`, `code`, and a short `detail`.

`session_id` starts on the first page load, stays through sign-in and sign-out, and ends when the browser closes. A later chat can read it from the `lumen_sid` cookie or from `<meta name="shop-session">` and look up that visit's lines.

Codes fire from the flows themselves. **101** is a bad sign-in, **102** is a session that has been idle for 30 minutes (or has no timestamp, or points at a missing account), **201** is the card `4000000000000002`, and **202** is Warm Highlighter, which has no stock. **103**, **203**, and **301** cover a taken username, an empty cart at checkout, and an order this shopper cannot open.

Codes **500**–**507** are the shop or a service it calls, not a mistake in what the shopper typed. They cover an unknown failure, the payment processor being down or timing out, the network being down, an account or order that could not be saved, a card that could not be saved after the order was placed, and account records that could not be read. An unhandled exception is logged as **500**. A failed sign-in for a real account is stored under that account's id. Guest events use `user_id` null. Passwords and full card numbers are not logged.

## Step 5 — Chat window

A popup chat on the storefront. It can send a shopper message and show a reply. Until step 6, the reply can be a stub. Transcripts are saved on disk next to orders so a demo can be replayed.

## Step 6 — Train and connect the agent

Choose the model and whether it sees documentation by full prompt or by retrieval. Connect that choice to the chat window, the product docs, and the error docs.

**What the agent is allowed to see.** It may read this shopper's orders and recent error codes, and it may answer from product and error docs. It must not read another shopper's data. It does not issue refunds or change the account unless a later change adds an explicit action.

**A way out.** If the agent cannot resolve the issue, it writes a local support ticket (user, summary, error codes) instead of inventing a fix.
