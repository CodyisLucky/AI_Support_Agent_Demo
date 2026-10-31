# Agent setups: pros and cons

Notes for consultations: what each way of running the support agent means for a small business. Prices and results are as of October 2026; check current prices before quoting them.

The shop's side of the agent is the same in every setup: the instructions, the lookups (docs, orders, errors, stock), the safeguards, the honest handoff, and the saved records. Only the model that writes the replies changes. A business can start with one setup and switch later by changing two lines in `agent.env`.

## At a glance

| | Local model (Ollama) | Claude (Anthropic) | OpenAI / Gemini |
|---|---|---|---|
| Cost per message | Nothing. The business pays for the computer and its electricity. | Per word processed. See prices below. | Per word processed. |
| Where shopper messages go | Nowhere. They stay on the shop's computer. | To Anthropic's servers. | To OpenAI's or Google's servers. |
| Answer quality | Depends heavily on the model. The best one tested (Gemma 4 12B) followed the shop's rules in 29 of 30 test replies; the first one tried (Qwen 2.5 7B) in 6 of 30. | Expected to be the strongest. To be measured once the API account exists. | Not tested yet. |
| Speed in the demo | About 3 seconds a reply for Gemma 4 12B on an RTX 3080 Ti; 1 to 20 seconds across the models tested. | Not measured yet. | Not tested yet. |
| What the business needs | A PC with a recent NVIDIA graphics card (12 GB for Gemma 4 12B), left on. | An Anthropic API account and a card on file. | An account with that company. |
| If something breaks | The shop's computer is off or the model is not running. | Anthropic's service is down or the account is out of credit. | The same, at that company. |

In every setup, a failure gives the shopper a plain handoff message with the team's email and a conversation ID, and logs error 508. The shopper never sees an error page.

## Local model (Ollama)

The model runs on the business's own computer. The demo started with Qwen 2.5 7B and then compared five more models. It now uses Gemma 4 12B (`lumen-gemma`), the best of the six. The full test record is in [local-model-tests.md](local-model-tests.md).

**Pros**

- No charge per message and no account to manage.
- Shopper messages, orders, and error logs never leave the building. This is the strongest point for a business that worries about customer data.
- Fast on a gaming-class graphics card.
- Works without an internet connection.

**Cons**

- Free models vary a lot in how well they follow instructions. The weaker ones invent answers the shop's rules forbid, which is the opposite of the "hand off rather than guess" promise. The model has to be chosen and tested, not just installed.
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

**Repeat test (5 runs each, same six questions, 2026-10-30).** The same questions were run five times as written, and five times with a short rules recap added to the end of the instructions. The recap made no real difference, so the model's ability is the limit, not where the rules sit.

| Shopper asked | Followed the rules (as written) | Followed the rules (with recap) |
|---|---|---|
| What did I order last time? | 5 of 5 | 5 of 5 |
| Gel vs. cream cleanser | 0 of 5 (never opened a product file) | 0 of 5 |
| Is the highlighter in stock? | 0 of 5 (always invented a restock or notify-me promise) | 0 of 5 |
| Write me a Python function | 0 of 5 (usually wrote the code) | 1 of 5 |
| I want a refund | 0 of 5 (never handed off) | 0 of 5 |
| Do you ship to Canada? | 0 of 5 (stated "we don't ship to Canada" as fact) | 0 of 5 |

Three failures are worse than a missing handoff, and make good examples for clients:

- **A fake handoff.** The model said "I've handed off your request for a refund to our support team." Nothing was handed off or recorded, and the shopper never got the real contact details or a conversation ID.
- **An invented contact.** It told a shopper to write to support@lumenbeauty.com. The shop's real address is different, so a real refund request would have gone to the wrong place.
- **A broken tool call shown to the shopper.** Twice the reply was literally `off_topic shipping`, text where the model meant to trigger a lookup. Ollama did not recognize it as a call, so it appeared in the chat.

**Safeguard added.** If a reply contains the name of a tool or a fragment of tool-call data, the shop discards it and gives the shopper the plain handoff message instead, and logs error 508. This applies to every model, not only the local one. It catches the broken-reply case only. It does not catch a fake handoff or an invented fact, which look like normal sentences. Only a more capable model, or a check that every answer is backed by a lookup, can address those.

The connection worked every time: lookups ran, safeguards counted tokens, and stopping the model gave the honest handoff. The model was the problem, not the plumbing.

**Comparing six local models (5 runs each of the same six questions, 2026-10-30).** Each model had the same instructions and the same 16,384-token memory, with its publisher's other settings. Every reply was read, not only scored automatically. The per-question results, example replies, and how to rebuild each model are in [local-model-tests.md](local-model-tests.md).

| Model | Download | Followed the rules (of 30) | Typical reply | What went wrong |
|---|---|---|---|---|
| Gemma 4 12B (Google) | 8 GB | **29** | 3 s | Once offered to hand off a refund instead of doing it. No invented facts. |
| Qwen3 8B (Alibaba) | 5 GB | 25 | 6 s | Promised a restock notice for the highlighter in 2 of 5 replies. Once handed off a simple stock question. |
| gpt-oss 20B (OpenAI) | 13 GB | 23 | 5 s | Invented a notification, a reminder, or a restock date in 4 of 5 stock replies. Twice wrote its handoff as raw data, which the safeguard caught. |
| Llama 3.1 8B (Meta) | 5 GB | 23 | 1 s | Rarely opened product files, yet once said "according to the product files". Once imitated the shop's "technical problem" message. Twice leaked tool data, caught. |
| Mistral Small 3.2 24B | 15 GB | 18 | 20 s | Told a refund shopper "you should have received your package by now". Sent another to "the company's customer service". Too big for the graphics card, so slow. |
| Qwen 2.5 7B (Alibaba) | 5 GB | 6 | 1 s | See above. |

Three of the four best models think before they answer. That costs a few seconds a reply and is worth it here, because the failures that matter are invented facts, not slow replies.

The stock question was the hardest. Most models want to offer something after "out of stock", like a notice, a reminder, or a restock date, and the shop has none of these. It's a good live example for clients of a model being helpful in a way the business never agreed to.

The safeguard caught every broken reply in this run. Without it, shoppers would have seen raw data such as `{"name": "hand_off", "parameters": …}`.

**Limits of this test.** These are six questions run five times each, not a full evaluation. Gemma 4's 29 of 30 is a strong result, but it should be checked on more questions, including multi-turn chats, before it's promised to a client. Each model also has its own license terms, and these should be checked before commercial use.

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
