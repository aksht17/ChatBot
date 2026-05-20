import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from rag_chain import ask_with_context


def _load_jsonl(path):
    examples = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def _term_hit_rate(text, terms):
    terms = [term.lower() for term in terms if term]
    if not terms:
        return None
    text = text.lower()
    hits = sum(1 for term in terms if term in text)
    return hits / len(terms)


def _score_example(example, result):
    answer = result["answer"]
    contexts = result["contexts"]
    context_text = "\n".join(item["text"] for item in contexts)
    source_text = "\n".join(item["source"] for item in contexts)

    answer_term_score = _term_hit_rate(answer, example.get("expected_answer_terms", []))
    source_term_score = _term_hit_rate(source_text, example.get("expected_source_terms", []))
    context_term_score = _term_hit_rate(context_text, example.get("expected_context_terms", []))

    available_scores = [
        score
        for score in [answer_term_score, source_term_score, context_term_score]
        if score is not None
    ]
    overall = sum(available_scores) / len(available_scores) if available_scores else None

    return {
        "question": example["question"],
        "answer": answer,
        "sources": [item["source"] for item in contexts],
        "answer_term_score": answer_term_score,
        "source_term_score": source_term_score,
        "context_term_score": context_term_score,
        "overall_score": overall,
    }


def _maybe_trace_langsmith(example, scored):
    if not os.getenv("LANGSMITH_API_KEY"):
        return

    try:
        from langsmith import traceable
    except Exception:
        print("LangSmith API key found, but langsmith package is not installed.")
        return

    @traceable(name="rag_eval_case")
    def record_eval_case(payload):
        return payload

    record_eval_case({"example": example, "result": scored})


def main():
    parser = argparse.ArgumentParser(description="Evaluate chatbot answer relevance and retrieval quality.")
    parser.add_argument(
        "--data",
        default="eval_questions.example.jsonl",
        help="JSONL file containing questions and expected terms.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output JSON path. Defaults to eval_results_<timestamp>.json.",
    )
    args = parser.parse_args()

    examples = _load_jsonl(args.data)
    results = []
    for index, example in enumerate(examples, 1):
        print(f"Evaluating {index}/{len(examples)}: {example['question']}")
        result = ask_with_context(example["question"])
        scored = _score_example(example, result)
        results.append(scored)
        _maybe_trace_langsmith(example, scored)
        print(f"  overall_score={scored['overall_score']} sources={len(scored['sources'])}")

    scores = [item["overall_score"] for item in results if item["overall_score"] is not None]
    summary = {
        "num_examples": len(results),
        "average_overall_score": sum(scores) / len(scores) if scores else None,
        "results": results,
    }

    output_path = args.out
    if output_path is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"eval_results_{stamp}.json"

    Path(output_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
