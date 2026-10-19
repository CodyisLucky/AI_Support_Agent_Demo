# AI Support Agent Demo

A local storefront used to demonstrate an AI support agent. A shopper can browse fake products and services, sign in, and run into ordinary website problems. A chat window can then answer product questions and troubleshoot those problems from documentation and the shopper's own logs.

Nothing in this project is hosted. The site runs on your machine. Accounts, orders, error logs, chat transcripts, and support tickets are written to a local `data/` directory and are not committed.

## Stack

- Python and FastAPI
- Plain HTML pages for the storefront
- JSON or SQLite on disk for accounts, orders, and logs

The support model and how it reads documentation (full prompt vs retrieval) are chosen in step 6. Steps 1–5 stay model-agnostic. Product docs and error logs are written so either approach can use them later.

## Steps

1. **Repo and starter docs** (this step). Git metadata, this README, and [docs/roadmap.md](docs/roadmap.md).
2. **Storefront.** A barebones HTML shop with fake products and services, login, and generic account flows. Purchases are saved locally.
3. **Product documentation.** Verbose docs for every product and service, written so a support agent can answer shopper questions from them.
4. **Error logging.** Three-digit error codes for problems a shopper can hit, with logs and documentation an agent can use.
5. **Chat window.** A popup on the storefront that talks to the support agent.
6. **Train and connect the agent.** Choose the model and connect it to the docs, logs, and chat window.

See [docs/roadmap.md](docs/roadmap.md) for what each remaining step delivers, including seeded demo data, error correlation, what the agent may read, local tickets, and saved transcripts.

## Run

Not runnable yet. Step 2 adds the FastAPI app and the storefront.
