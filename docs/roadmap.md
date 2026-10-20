# Roadmap

Step 1 is done: this repo, [README.md](../README.md), and this file. Step 2 has the Lumen Beauty shop, login, and local purchases.

The support model and retrieval approach are deferred to step 6. Product docs and error logs should stay plain files an agent can read either by loading them into a prompt or by retrieving relevant pages.

## Step 2 — Storefront

FastAPI app serving plain HTML.

- Shop, sign-in, create-account, account, cart, and checkout pages are done. The catalog has 25 skincare, makeup, and service items. Cards use a square labeled “photo” instead of an image.
- Login flows: register, sign in, sign out, and view account. Accounts are saved under `data/`. A login is not required to buy.
- A cart is reviewed before checkout. Checkout collects shipping and a card, and accepts any card number. A shopper can check out as a guest or create an account and save the card. Orders are written to `data/orders.json`. Signed-in orders and the saved card appear on the account page.

**Seeded shopper.** Username `demo`, password `demo-shopper`, created on first launch. Known orders and a known failure wait until the catalog and the error-code step exist.

## Step 3 — Product documentation

Done. [docs/catalog](catalog) has one file per product and service, plus an index and a short guide for the agent. The files are separate from the HTML so step 6 can load them without scraping the storefront.

Each file includes what it is, price and size, ingredients or what a service includes, benefits, drawbacks, when it works, when it does not, how to use it, and shopper questions with answers. Prices and shades in those files match the shop.

## Step 4 — Error logging

Three-digit error codes for problems a shopper can hit on a real site, plus documentation of each code (what the shopper sees, likely cause, what to try).

**Errors the shopper can actually hit.** Codes should fire from real flows, such as a bad login, an expired session, a declined payment, or an out-of-stock item.

**Correlation.** Each log line includes user id, time, and code so a later agent can look up what just happened to the signed-in shopper.

## Step 5 — Chat window

A popup chat on the storefront. It can send a shopper message and show a reply. Until step 6, the reply can be a stub. Transcripts are saved on disk next to orders so a demo can be replayed.

## Step 6 — Train and connect the agent

Choose the model and whether it sees documentation by full prompt or by retrieval. Connect that choice to the chat window, the product docs, and the error docs.

**What the agent is allowed to see.** It may read this shopper's orders and recent error codes, and it may answer from product and error docs. It must not read another shopper's data. It does not issue refunds or change the account unless a later change adds an explicit action.

**A way out.** If the agent cannot resolve the issue, it writes a local support ticket (user, summary, error codes) instead of inventing a fix.
