# Lumen Beauty error codes for the support agent

Read these files when a shopper reports a problem on the site. Start with [index.md](index.md), then open the file for the code they saw.

The shop writes one JSON line per error to `data/errors.jsonl`. That directory is local and is not committed. Each line has:

- `time` — UTC timestamp
- `session_id` — the browser session, from the first page load until the browser closes
- `user_id` — the account id, or `null` for a guest
- `code` — three digits, matching a file in this folder
- `detail` — a short note, such as an item id or `last4 0002`

The shopper's browser keeps `session_id` in the cookie `lumen_sid`. Signing in or out does not change it. Closing the browser does. A chat request from that browser carries the same cookie, and the page also has `<meta name="shop-session">` with the same value.

Look up `data/errors.jsonl` lines with that `session_id`. That finds what happened in this visit, including errors from before the shopper signed in. Do not use another session's lines. `user_id` still says which account was signed in when the line was written. A guest line has `user_id` null. A failed sign-in for a real account stores that account's id.

The shopper sees the same code in a banner, for example `Error 101`. The wording in the banner matches the "What the shopper sees" section.

Codes 101 through 301 mean the shop understood the request and refused it because of what the shopper did. Codes 500 through 507 mean the shop, the account store, or the payment processor failed. For a 500-series code, do not tell the shopper to correct a typo. Say whether anything was charged or saved, using that code's file. Only 505 places the order.

## How to answer

- Name the code, the likely cause, and what to try from that code's file.
- Do not invent a refund, a price change, or an account change.
- Do not quote a card number. The log stores the last four digits only.
- Product questions still belong in [docs/catalog](../catalog/README.md).
