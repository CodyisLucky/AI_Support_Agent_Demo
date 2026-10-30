# Agent setups: pros and cons

Notes for consultations: what each way of running the support agent means for a small business. Prices and results are as of October 2026; check current prices before quoting them.

The shop's side of the agent is the same in every setup: the instructions, the lookups (docs, orders, errors, stock), the safeguards, the honest handoff, and the saved records. Only the model that writes the replies changes. A business can start with one setup and switch later by changing two lines in `agent.env`.

## At a glance

| | Local model (Ollama) | Claude (Anthropic) | OpenAI / Gemini |
|---|---|---|---|
| Cost per message | Nothing. The business pays for the computer and its electricity. | Per word processed. See prices below. | Per word processed. |
| Where shopper messages go | Nowhere. They stay on the shop's computer. | To Anthropic's servers. | To OpenAI's or Google's servers. |
| Answer quality | Weakest. Breaks shop rules in the demo (below). | Expected to be the strongest. To be measured once the API account exists. | Not tested yet. |
| Speed in the demo | About 1 second a reply on an RTX 3080 Ti. | Not measured yet. | Not tested yet. |
| What the business needs | A PC with a recent NVIDIA graphics card (8 GB or more), left on. | An Anthropic API account and a card on file. | An account with that company. |
| If something breaks | The shop's computer is off or the model is not running. | Anthropic's service is down or the account is out of credit. | The same, at that company. |

In every setup, a failure gives the shopper a plain handoff message with the team's email and a conversation ID, and logs error 508. The shopper never sees an error page.

## Local model (Ollama)

The model runs on the business's own computer. The demo uses Qwen 2.5 with 7 billion parameters, set up as `lumen-qwen` from [ollama/Modelfile](../ollama/Modelfile).

**Pros**

- No charge per message and no account to manage.
- Shopper messages, orders, and error logs never leave the building. This is the strongest point for a business that worries about customer data.
- Fast on a gaming-class graphics card.
- Works without an internet connection.

**Cons**

- Small models follow instructions much less reliably. In the demo they invent answers the shop's rules forbid. That is the opposite of the "hand off rather than guess" promise.
- The computer must stay on and be looked after. If it sleeps, the chat hands every shopper off.
- One graphics card serves a handful of chats at a time, not a busy shop.
- Bigger, more reliable models need a more expensive graphics card.
- A technical trap: Ollama gives a model a short memory (4,096 tokens) by default and silently cuts off anything longer, including the shop's instructions. The demo raises it to 16,384 in the Modelfile.

**What the demo showed (Qwen 2.5 7B, 2026-10-30)**

| Shopper asked | What the shop's rules require | What the local model did |
|---|---|---|
| Difference between the gel and cream cleanser, for dry skin | Read both product files, then answer from them | Answered from search snippets without reading either file, and added a claim of its own |
| What did I order last time? | Look up the shopper's orders | Correct: right items, total, and city |
| Is the highlighter in stock? | Check stock and say no | Said no, then invented a backorder and a notify-me list the shop does not have |
| Write me a Python function | Decline as off topic | Offered to help |
| I want a refund | Hand off to staff | Pointed to a "support form" that does not exist, and did not hand off |
| Do you ship to Canada? | Hand off: shipping is not in the docs | Stated "we do not ship to Canada" as fact |

The connection worked every time: lookups ran, safeguards counted tokens, and stopping the model gave the honest handoff. The model was the problem, not the plumbing. Larger local models are the next thing to try.

## Claude (Anthropic)

The model runs on Anthropic's servers and is paid per use.

**Pros**

- Expected to follow the shop's rules far more reliably: looking things up before answering, declining off-topic requests, and handing off instead of guessing. This is to be confirmed with the same six questions once the API account exists.
- Nothing to install or keep running at the shop.
- Scales from one chat to many with no hardware change.
- Prompt caching (below) makes repeat questions cheaper.

**Cons**

- Costs money on every message. The shop's daily spending caps (`AGENT_DAILY_BUDGET_USD`) limit the risk.
- Shopper messages are sent to Anthropic.
- Needs an internet connection and an API account. A Claude Pro chat subscription does not include API access.

**Prices** (US dollars per million tokens; a token is roughly three-quarters of a word)

| Model | Input | Output | Notes |
|---|---|---|---|
| Claude Opus 5.5 | $4.00 | $20.00 | Most capable. Cached input costs $0.20. |
| Claude Sonnet 5.5 | $2.00 | $10.00 | Middle option. |
| Claude Haiku 5.5 | $0.10 | $0.50 | Cheapest. Test it against the shop's rules before offering it. |

Each reply re-sends the shop's instructions and the chat so far, so input is most of the cost. Caching matters for that reason.

## Why Claude is connected differently

**For clients.** Most AI companies accept requests in the same format OpenAI made popular, so one connection can serve several of them. Anthropic accepts that format too, but only as a testing convenience. Through it, several Claude features that save money or make the agent more reliable are switched off. So the shop talks to Claude in Claude's own format, and uses the shared format for everything else. It's like a travel adapter: the plug fits, but some features of the appliance don't work through it.

**For us.** Anthropic's docs describe its OpenAI-compatible endpoint as "primarily intended to test and compare model capabilities, and is not considered a long-term or production-ready solution". Through that endpoint:

| Feature | Through the compatible endpoint | Native Claude connection |
|---|---|---|
| Prompt caching | Not supported. The full instructions are paid at full price on every lookup round. | Supported. The instructions are written to stay identical so they can be cached. |
| `AGENT_EFFORT` | `reasoning_effort` is ignored. Opus 5.5 always runs at its default, `medium`. | Honored, so `low` makes short support replies faster and cheaper. |
| Temperature | Opus 5.5 rejects any value below 1. | Not sent; tone comes from the instructions. |
| Refusals | Always reported empty, so a refusal looks like a broken reply. | Reported as a refusal, so the log shows the real reason. |
| Cached-token counts | Always empty, so the details line shows no savings. | Reported, so the cost estimate is accurate. |
| Tool-argument checking (`strict`) | Ignored. | Guaranteed to match the tool's schema. |

The native Claude connection also has to handle the model's thinking. Thinking can't be switched off on Opus 5.5, and within one reply its thinking must be sent back unchanged between lookups. New API accounts reject a conversation whose earlier parts were edited. The shop stores earlier turns as plain text, so it stays within that rule.

## OpenAI and Gemini

These are not connected yet. Both will use the same OpenAI-compatible connection as Ollama ([openai_compat.py](../app/agent/providers/openai_compat.py)). That needs an account and a price table for the cost estimate.

"Compatible" still varies from server to server. For example, Ollama ignores the newer `max_completion_tokens` setting and honors only `max_tokens`, and its memory size can't be changed per request. Each new provider should be tested against the same six questions above before it's offered to a client.
