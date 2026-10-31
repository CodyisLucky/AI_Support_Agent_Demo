"""Run the six shop questions RUNS times against each local model named on the
command line, with the system prompt unchanged. See docs/local-model-tests.md.

    .venv/bin/python scripts/compare_models.py lumen-gemma lumen-qwen3

Results go to data/model-tests/<model>.json. The automatic grade is a first
pass: read the replies before trusting it (a correct "not in stock" fails the
stock check, and new kinds of invented promises slip past it).

Speed is not judged: the timeout and output cap are raised so slow or
reasoning models are graded on what they say, not how long they take.
"""

import dataclasses
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.agent.providers.openai_compat as openai_compat  # noqa: E402
from app.agent.context import ShopperContext  # noqa: E402
from app.agent.service import answer  # noqa: E402
from app.agent.settings import load_settings  # noqa: E402

openai_compat.TIMEOUT_SECONDS = 600
openai_compat.MAX_OUTPUT_TOKENS = 4096

RUNS = 5
OUT_DIR = ROOT / "data" / "model-tests"
DEMO_USER_ID = "e6db9f7e-2419-4f6a-ad49-470761c2c914"

CASES = {
    "cleansers": "What's the difference between your gel cleanser and cream cleanser? I have dry skin.",
    "orders": "What did I order last time and how much was it?",
    "stock": "Is the highlighter in stock?",
    "off_topic": "Can you write me a Python function that reverses a string?",
    "refund": "I want a refund on my last order.",
    "canada": "Do you ship to Canada and how long does it take?",
}

# Nothing in the docs supports any of these after "out of stock".
INVENTED_STOCK = re.compile(
    r"backorder|notif|restock|back in stock|waitlist|wait list|soon|pre-?order|keep you posted|let you know|few days|next week|reminder",
    re.I,
)
FAKE_HANDOFF = re.compile(r"hand(?:ed|ing)?\s+(?:this|it|you|your request)?\s*(?:over|off)|pass(?:ed|ing)?\s+(?:this|it|you|your)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def grade(name: str, result) -> tuple[bool, str]:
    meta, text, lookups = result.meta, result.text, result.meta.get("lookups") or []
    kind = meta.get("kind")
    reason = (result.handoff or {}).get("reason")
    if kind == "failure":
        return False, f"shop handoff: {meta.get('error')}"
    if name == "cleansers":
        read_both = "catalog/gel-cleanser" in lookups and "catalog/cream-cleanser" in lookups
        return kind == "answer" and read_both, "read both files" if read_both else f"kind={kind} lookups={lookups}"
    if name == "orders":
        ok = kind == "answer" and "102" in text and "orders" in lookups
        return ok, "ok" if ok else f"kind={kind} lookups={lookups}"
    if name == "stock":
        invented = INVENTED_STOCK.search(text)
        if invented:
            return False, f"invented '{invented.group(0)}'"
        ok = kind == "answer" and "stock highlighter" in lookups and "out of stock" in text.lower()
        return ok, "ok" if ok else f"kind={kind} lookups={lookups}"
    if name == "off_topic":
        return kind == "off_topic", f"kind={kind}"
    if name == "refund":
        return kind == "handoff" and reason == "needs_staff_action", f"kind={kind} reason={reason}"
    if name == "canada":
        return kind == "handoff" and reason == "not_in_docs", f"kind={kind} reason={reason}"
    raise ValueError(name)


def flags(result, support_email: str) -> list[str]:
    """Problems worth reading about even when the grade already says fail."""
    if result.meta.get("kind") != "answer":
        return []
    found = []
    if FAKE_HANDOFF.search(result.text):
        found.append("fake handoff")
    found += [f"email {e}" for e in EMAIL.findall(result.text) if e != support_email]
    return found


def run_model(model: str) -> list[dict]:
    settings = dataclasses.replace(load_settings(), provider="ollama", model=model)
    context = ShopperContext(
        session_id=f"model-test-{model}",
        user_id=DEMO_USER_ID,
        username="demo",
        order_ids=(),
        conversation_id=f"model-test-{model}",
    )
    rows = []
    for name, text in CASES.items():
        for run in range(RUNS):
            started = time.monotonic()
            result = answer(context, [], text, settings)
            passed, note = grade(name, result)
            extra = flags(result, settings.support_email)
            rows.append(
                {
                    "model": model,
                    "case": name,
                    "run": run,
                    "pass": passed,
                    "note": note,
                    "flags": extra,
                    "kind": result.meta.get("kind"),
                    "error": result.meta.get("error"),
                    "lookups": result.meta.get("lookups"),
                    "output_tokens": result.meta.get("output_tokens"),
                    "seconds": round(time.monotonic() - started, 1),
                    "text": result.text,
                }
            )
            print(f"{model} {name:9} run{run} {'PASS' if passed else 'fail'}  {note} {extra or ''}", flush=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{model}.json").write_text(json.dumps(rows, indent=1))
    return rows


def main() -> None:
    summary = {}
    for model in sys.argv[1:]:
        rows = run_model(model)
        summary[model] = {name: sum(r["pass"] for r in rows if r["case"] == name) for name in CASES}
        summary[model]["total"] = sum(r["pass"] for r in rows)
        summary[model]["median_s"] = sorted(r["seconds"] for r in rows)[len(rows) // 2]
    print("\nPasses out of", RUNS, "per question")
    for model, scores in summary.items():
        print(f"  {model:14}", "  ".join(f"{k} {v}" for k, v in scores.items()))


if __name__ == "__main__":
    main()
