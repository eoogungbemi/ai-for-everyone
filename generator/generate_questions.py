#!/usr/bin/env python3
"""Generate a bank of everyday AI-literacy quiz questions with a local Ollama model.

The website can't reach Ollama from a visitor's browser (it's hosted on GitHub
Pages), so this runs on your own machine and writes ../questions.json. The site
then draws a random 5 questions from that bank plus its built-in ones.

Every question goes through two checks before it's kept:
  1. Rule checks: exactly 5 distinct options, plain-length text, no
     "all of the above", not a near-duplicate of an existing question.
  2. A judge pass: the model answers its own question blind (options shuffled).
     If it doesn't pick the intended answer, the question is too muddled to keep.

Usage (from the repo root):
    python3 generator/generate_questions.py                 # 4 per topic, llama3.2:3b
    python3 generator/generate_questions.py --per-topic 2 --model gemma4:31b

Needs only the Python standard library and a running Ollama (`ollama serve`).
"""

import argparse
import difflib
import json
import os
import random
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "questions.json"
SCRIPT_JS = ROOT / "script.js"

# Each topic is something an everyday person runs into, phrased as a brief for the model.
TOPICS = [
    "what AI is and is not (it learns patterns from examples; it does not think or feel)",
    "everyday places people already use AI (phones, maps, streaming suggestions, spam filters, voice assistants)",
    "AI chatbots making up facts that sound convincing, and how to double-check them",
    "keeping personal and private information out of AI chatbots",
    "deepfake videos, fake photos and AI-cloned voices",
    "phone and message scams that use AI-cloned voices of family members",
    "bias and unfairness in AI, for example in job or loan decisions",
    "recommendation feeds on social media and video apps, and why they show you what they show you",
    "using AI as a helpful assistant while a human stays in charge of decisions",
    "AI-generated images and text, and how to tell or check if something was made by AI",
]

SYSTEM_PROMPT = """You write quiz questions for a public website that teaches everyday people about AI.
Readers have no technical background. Use short, plain, friendly English (reading age about 12).
No jargon. If a technical word is unavoidable, explain it in brackets.
Each question has exactly ONE clearly correct answer and FOUR wrong answers.
Wrong answers must be believable to a beginner but clearly wrong to someone who knows the basics.
Never use "all of the above", "none of the above", "both", or answers that combine other answers.
Keep each answer under 20 words. The explanation is 1-2 sentences saying why the correct answer is right."""

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "correct_answer": {"type": "string"},
        "wrong_answers": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
        "explanation": {"type": "string"},
    },
    "required": ["question", "correct_answer", "wrong_answers", "explanation"],
}

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"choice": {"type": "integer", "minimum": 1, "maximum": 5}},
    "required": ["choice"],
}

BANNED_OPTION_PATTERNS = re.compile(
    r"\b(all|none) of (the )?(above|these)\b|^both\b|\b[a-e] and [a-e]\b", re.IGNORECASE
)

SIMILARITY_LIMIT = 0.8  # questions more alike than this count as duplicates


# ---------------------------------------------------------------- validation

def normalise(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def is_duplicate(question, existing):
    q = normalise(question)
    return any(difflib.SequenceMatcher(None, q, normalise(e)).ratio() > SIMILARITY_LIMIT for e in existing)


def validate(raw, existing_questions):
    """Turn a model response into a quiz item, or raise ValueError saying why it was rejected."""
    question = str(raw.get("question", "")).strip()
    correct = str(raw.get("correct_answer", "")).strip()
    wrong = [str(w).strip() for w in raw.get("wrong_answers", [])]
    explanation = str(raw.get("explanation", "")).strip()

    if not 15 <= len(question) <= 200:
        raise ValueError("question length out of range")
    if not question.endswith("?"):
        raise ValueError("question does not end with '?'")
    if len(wrong) != 4:
        raise ValueError(f"expected 4 wrong answers, got {len(wrong)}")

    options = [correct] + wrong
    for opt in options:
        if not 2 <= len(opt) <= 140:
            raise ValueError(f"option length out of range: {opt!r}")
        if BANNED_OPTION_PATTERNS.search(opt):
            raise ValueError(f"banned option wording: {opt!r}")
    if len({normalise(o) for o in options}) != 5:
        raise ValueError("options are not all different")
    if not 20 <= len(explanation) <= 320:
        raise ValueError("explanation length out of range")
    if re.search(r"\bcorrect answer\b", explanation, re.IGNORECASE):
        raise ValueError("explanation talks about 'the correct answer' instead of explaining")
    if is_duplicate(question, existing_questions):
        raise ValueError("too similar to an existing question")

    return {"question": question, "options": options, "answer": correct, "explanation": explanation}


def built_in_questions():
    """Question texts already hard-coded in script.js, so we don't generate repeats of them."""
    try:
        return re.findall(r'^\s*question:\s*"(.+)",\s*$', SCRIPT_JS.read_text(encoding="utf-8"), re.MULTILINE)
    except OSError:
        return []


# ---------------------------------------------------------------- Ollama

def ollama_chat(host, model, messages, schema, temperature):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "format": schema,
        "stream": False,
        "options": {"temperature": temperature},
    }).encode()
    req = urllib.request.Request(f"{host}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(json.loads(resp.read())["message"]["content"])


def generate_one(host, model, topic, avoid):
    avoid_text = "\n".join(f"- {q}" for q in avoid[-8:]) or "- (none yet)"
    prompt = (
        f"Write ONE multiple-choice question about: {topic}.\n"
        f"It must be different from these existing questions:\n{avoid_text}"
    )
    return ollama_chat(host, model, [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ], QUESTION_SCHEMA, temperature=0.9)


def judge_agrees(host, model, item):
    """Ask the model to answer the question blind. True if it picks the intended answer."""
    shuffled = random.sample(item["options"], len(item["options"]))
    listing = "\n".join(f"{i}. {opt}" for i, opt in enumerate(shuffled, 1))
    result = ollama_chat(host, model, [
        {"role": "user", "content": f"{item['question']}\n\n{listing}\n\nReply with the number of the single best answer."},
    ], JUDGE_SCHEMA, temperature=0)
    choice = result.get("choice")
    return isinstance(choice, int) and 1 <= choice <= 5 and shuffled[choice - 1] == item["answer"]


# ---------------------------------------------------------------- main

def write_atomically(path, data):
    """Write to a temp file then swap it in, so a crash never leaves a half-written bank."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".questions-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--per-topic", type=int, default=4, help="questions to keep per topic (default 4)")
    parser.add_argument("--max-attempts", type=int, default=6, help="tries per kept question before giving up")
    # 127.0.0.1, not "localhost": localhost can resolve to IPv6 and reach a different
    # Ollama (e.g. one in Docker) that shares port 11434 but has other models.
    parser.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-judge", action="store_true", help="skip the blind-answer check (faster, lower quality)")
    args = parser.parse_args()

    try:
        with urllib.request.urlopen(f"{args.host}/api/tags", timeout=5) as resp:
            installed = {m["name"] for m in json.loads(resp.read())["models"]}
    except (urllib.error.URLError, OSError):
        sys.exit(f"Can't reach Ollama at {args.host}. Start it with `ollama serve` (or open the Ollama app).")
    if args.model not in installed:
        sys.exit(f"Model {args.model!r} isn't on the Ollama at {args.host}. "
                 f"Installed there: {', '.join(sorted(installed)) or 'none'}. Try `ollama pull {args.model}`.")

    existing = built_in_questions()
    bank, rejected = [], 0

    for t_index, topic in enumerate(TOPICS, 1):
        print(f"[{t_index}/{len(TOPICS)}] {topic[:60]}…")
        kept = 0
        for _ in range(args.per_topic * args.max_attempts):
            if kept == args.per_topic:
                break
            try:
                item = validate(generate_one(args.host, args.model, topic, existing), existing)
                if not args.no_judge and not judge_agrees(args.host, args.model, item):
                    raise ValueError("judge picked a different answer")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as err:
                rejected += 1
                print(f"   ✗ rejected: {err}")
                continue
            except urllib.error.URLError as err:
                sys.exit(f"Lost connection to Ollama: {err}")
            item = {"id": f"ai-{len(bank) + 1:03d}", "topic": topic.split(" (")[0], **item, "source": "ai"}
            bank.append(item)
            existing.append(item["question"])
            kept += 1
            print(f"   ✓ {item['question']}")
        if kept < args.per_topic:
            print(f"   ! only kept {kept}/{args.per_topic} for this topic")

    if not bank:
        sys.exit("No questions passed the checks, so the existing bank was left untouched.")

    write_atomically(args.out, {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "count": len(bank),
        "questions": bank,
    })
    print(f"\nKept {len(bank)} questions ({rejected} rejected) → {args.out}")
    print("Please read through the bank before publishing. Small models can still get facts wrong.")


if __name__ == "__main__":
    main()
