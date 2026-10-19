# Roadmap

Step 1 is done: this repo, [README.md](../README.md), and this file. The app is not built yet.

The support model and retrieval approach are deferred to step 6. Product docs and error logs should stay plain files an agent can read either by loading them into a prompt or by retrieving relevant pages.

## Step 2 — Storefront

FastAPI app serving plain HTML.

- A shop page with fake products and services a shopper can "purchase."
- Login and generic account flows (register, sign in, sign out, view account).
- Accounts and orders saved under `data/` on disk. No hosting.

**Seeded shopper.** Include one local account with known orders and a known failure so a walkthrough is repeatable. Document the username in the README when the account exists.

## Step 3 — Product documentation

Verbose documentation for every product and service offered, written for a support agent: what it is, what it costs, what is included, limits, and common shopper questions. Keep these as files separate from the HTML so step 6 can load them without scraping the storefront.

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
