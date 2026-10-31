# Local model tests

The record behind the choice of Gemma 4 12B as the shop's local model, kept so the other models can be revisited later. [agent-setups.md](agent-setups.md) has the client-facing summary.

## Setup (2026-10-30)

- **Machine:** WSL2 with an RTX 3080 Ti (12 GB, about 10.5 GB free) and 15 GB of RAM. Ollama 0.40.13 as a systemd service.
- **Provider:** the OpenAI-compatible provider, [openai_compat.py](../app/agent/providers/openai_compat.py). The system prompt and tools were unchanged.
- **Models:** each was built from its file in [ollama/](../ollama) with a 16,384-token context window. Qwen 2.5 also had temperature 0.3; the others kept their publishers' sampling settings.
- **Limits during the test:** the timeout was raised to 10 minutes and the output cap to 4,096 tokens, so models were graded on what they said, not their speed.
- **Runs:** each question was a new chat with no history, asked 5 times per model.
- **Script and raw results:** the script is [scripts/compare_models.py](../scripts/compare_models.py). Every reply is saved locally in `data/model-tests/<model>.json`, which is gitignored and not committed.

## The six questions and what counts as a pass

| Question | Pass |
|---|---|
| "What's the difference between your gel cleanser and cream cleanser? I have dry skin." | Reads both `catalog/gel-cleanser` and `catalog/cream-cleanser` before answering |
| "What did I order last time and how much was it?" | Looks up orders and gives the $102.00 total |
| "Is the highlighter in stock?" | Checks stock, says it is out of stock, and adds nothing the docs don't say (no restock, notice, or reminder) |
| "Can you write me a Python function that reverses a string?" | Calls `off_topic` |
| "I want a refund on my last order." | Calls `hand_off` with `needs_staff_action` |
| "Do you ship to Canada and how long does it take?" | Calls `hand_off` with `not_in_docs`, because shipping isn't documented |

Every reply was read as well as auto-graded. One grade was corrected by hand: four of Mistral's stock replies said "not in stock" instead of "out of stock". They were correct and are counted as passes below.

## Results (passes out of 5)

| Model | Base | Download | Cleansers | Orders | Stock | Off topic | Refund | Canada | **Total of 30** | Median reply |
|---|---|---|---|---|---|---|---|---|---|---|
| `lumen-gemma` (default) | `gemma4:12b` | 8.0 GB | 5 | 5 | 5 | 5 | 4 | 5 | **29** | 3.1 s |
| `lumen-qwen3` | `qwen3:8b` | 5.2 GB | 4 | 5 | 1 | 5 | 5 | 5 | **25** | 5.7 s |
| `lumen-gptoss` | `gpt-oss:20b` | 13 GB | 5 | 5 | 1 | 5 | 5 | 2 | **23** | 5.0 s |
| `lumen-llama` | `llama3.1:8b` | 4.9 GB | 1 | 5 | 5 | 5 | 4 | 3 | **23** | 1.0 s |
| `lumen-mistral` | `mistral-small3.2` | 15 GB | 2 | 5 | 4 | 3 | 3 | 1 | **18** | 20.2 s |
| `lumen-qwen` | `qwen2.5:7b` | 4.7 GB | 0 | 5 | 0 | 1 | 0 | 0 | **6** | 1.1 s |

Gemma 4, Qwen3, and gpt-oss think before answering; Ollama returns that thinking separately, so it never reaches the shopper. The largest output for one reply was 1,428 tokens (Qwen3), 878 (Gemma 4), and 767 (gpt-oss); the shop's cap is now 2,048. Mistral is larger than the graphics card, so part of it ran on the processor; three of its replies took over a minute.

## Notes on each model

**Gemma 4 12B: chosen.** Its cleanser answers matched the product files closely, for example "the Fresh Gel Cleanser is intended for oily or combination skin; it can feel tight on dry or barrier-stressed skin". Its stock replies were just "The Warm Highlighter is currently out of stock." It handed off every Canada question. Its one failure was a refund reply that offered a handoff ("I can hand you off to a member of our team") instead of making one. A minor point: one handoff said "I'll have a team member get back to you", which promises more than the shop does.

A follow-up check under the shop's normal limits found a problem the 5-run test missed. Gemma usually asks `read_doc` for `cream-cleanser.md` or `cream-cleanser`, the form shown in the catalog index, instead of the id the tool expects, `catalog/cream-cleanser`. The tool's error makes it retry with the right id, so it normally recovers. But every wrong guess counts toward the shop's limit of 3 invalid tool calls. In 1 of 7 cleanser questions, it used up the limit and the shopper got an unneeded "couldn't load your records" handoff.

**Fixed:** `read_doc` now also accepts the short form the indexes show (`cream-cleanser` → `catalog/cream-cleanser`, `201` → `errors/201`). In 8 more cleanser runs, Gemma read both files every time with no invalid calls. Replies also got quicker, about 5 seconds instead of up to 15, because the retry round is gone.

**Qwen3 8B.** Strong on handoffs and off-topic requests. The stock question tripped it: it offered "Would you like me to notify you when it's available again?" (twice), pointed to "contact our team for more information about restocking", and once handed off a question it could have answered. One cleanser answer read only the gel file. Its handoff explanations mostly said "Please contact our team", which repeats what the shop adds anyway.

**gpt-oss 20B.** Read both cleanser files every time, but invented something after "out of stock" in 4 of 5 replies: setting a notification, adding a reminder, or "an estimated restock date". On Canada, it once called the question off topic, and twice wrote its handoff as raw data, such as `{"explanation":"I'm not finding shipping details…","reason":"not_in_docs",…}`, which the safeguard caught. In a later spot check, it once mixed its reasoning into a tool call so badly that Ollama returned "error parsing tool call" (HTTP 500), which the shop also turns into a handoff.

**Llama 3.1 8B.** Fastest, with clean stock and off-topic replies, though one stock reply added "We recommend checking back later". It mostly answered the cleanser question from search snippets, once saying "According to the Cloud Cream Cleanser and Fresh Gel Cleanser product files" without having read them. Once it imitated the shop's own failure message ("It seems like I've hit a technical problem, and I'm paused for the rest of this chat"), probably after reading error doc 508. Twice it leaked tool-call text, which the safeguard caught. In a spot check, one leak began "it appears that Lumen Beauty ships to Canada", an invented fact.

**Mistral Small 3.2 24B.** The weakest of the new models, and slow on this card. Three cleanser replies skipped the lookups and said it "couldn't find the product details". On refunds it twice looked up the order instead of handing off, once adding "you should have received your package by now". On Canada it said it would "connect you with someone" without doing so, and once sent the shopper to "the company's customer service".

**Qwen 2.5 7B: the first model tried.** It followed the rules only on the orders question. An earlier test also tried adding a short rules recap to the end of the prompt for this model, with no real change: 6 of 30 with the recap against 5 of 30 without. Its failures are listed in [agent-setups.md](agent-setups.md): fake handoffs, an invented support email, and tool calls shown to the shopper.

## Failure types seen across models

- **Invented helpfulness after "out of stock"**, such as a notice, reminder, restock date, or "check back later". This was the most common failure, and the docs never support it.
- **Narrated handoffs:** saying "I'll connect you" or "I can hand you off" without calling `hand_off`. Nothing is recorded and the shopper gets no conversation ID. No code check catches this yet.
- **Tool-call text in the reply:** a tool name or raw JSON. The safeguard in [service.py](../app/agent/service.py) catches it and hands off (error 508).
- **Unparseable tool calls (gpt-oss):** Ollama returns HTTP 500 and the shop hands off (error 508).
- **Answering from search snippets** without reading the product file.

## Rebuilding a removed model

Only `gemma4:12b` and `lumen-gemma` are kept on the machine. To bring another back, for example Qwen3:

```bash
ollama pull qwen3:8b
ollama create lumen-qwen3 -f ollama/lumen-qwen3.Modelfile
.venv/bin/python scripts/compare_models.py lumen-qwen3
```

## Ideas for later

- More questions, including multi-turn chats, error-code questions, and prompt-injection attempts. Gemma's score is from six questions, and one source reports tool-calling issues with Gemma 4.
- Thinking settings: Qwen3 and Gemma 4 can turn thinking off, and gpt-oss has low, medium, and high levels. Speed and accuracy may trade differently.
- A code check for narrated handoffs, the one serious failure the safeguard doesn't cover.
- The same script against Claude once step 6b is connected, for a like-for-like comparison.
- Larger models on a bigger graphics card, if a client's hardware allows.
