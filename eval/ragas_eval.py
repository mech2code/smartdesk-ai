"""Ragas evaluation pipeline for SmartDesk AI RAG flows."""
import json
from pathlib import Path

from datasets import Dataset
from langchain_core.messages import HumanMessage
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from agent.intent_detector import detect_intent
from memory.session import new_session
from rag.confidence import confidence_gate
from rag.retriever import hybrid_search

EVAL_DIR = Path(__file__).parent
DATASET_PATH = EVAL_DIR / "test_dataset.json"
RESULTS_PATH = EVAL_DIR / "results.json"
INTENT_DATASET_PATH = EVAL_DIR / "intent_dataset.json"


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_rag(question: str, domain: str) -> tuple[str, list[str]]:
    chunks, score = hybrid_search(question, domain)
    answer, action = confidence_gate(
        question,
        domain,
        retrieval=(chunks, score),
        use_cache=False,
    )
    if action == "escalate" or not answer:
        answer = "I don't have enough information about that in our knowledge base."
    return answer, chunks


def build_ragas_dataset(samples: list[dict]) -> Dataset:
    questions, answers, contexts, ground_truths = [], [], [], []

    for sample in samples:
        q = sample["question"]
        domain = sample.get("domain", "it")
        gt = sample.get("ground_truth", "")

        answer, chunks = run_rag(q, domain)
        questions.append(q)
        answers.append(answer)
        contexts.append(chunks if chunks else ["No context retrieved."])
        ground_truths.append(gt)

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })


def evaluate_intents() -> float:
    samples = json.loads(INTENT_DATASET_PATH.read_text(encoding="utf-8"))
    correct = 0
    for sample in samples:
        result = detect_intent(
            {
                "messages": [HumanMessage(content=sample["message"])],
                "session": new_session(),
                "intent": None,
            }
        )
        correct += result["intent"] == sample["expected_intent"]
    return round(correct / len(samples), 4) if samples else 0.0


def main():
    print("Loading test dataset...")
    samples = load_dataset()
    answerable = [s for s in samples if s.get("answerable", True)]
    unanswerable = [s for s in samples if not s.get("answerable", True)]
    print(f"  {len(answerable)} answerable samples for Ragas evaluation")

    print("Running RAG pipeline on answerable samples...")
    dataset = build_ragas_dataset(answerable)

    print("Running Ragas metrics...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )

    scores = {
        "faithfulness": round(float(result["faithfulness"]), 4),
        "answer_relevancy": round(float(result["answer_relevancy"]), 4),
        "context_precision": round(float(result["context_precision"]), 4),
    }

    if unanswerable:
        escalated = 0
        for sample in unanswerable:
            _, action = confidence_gate(
                sample["question"],
                sample.get("domain", "it"),
                use_cache=False,
            )
            escalated += action == "escalate"
        scores["escalation_accuracy"] = round(escalated / len(unanswerable), 4)
    scores["ambiguous_intent_accuracy"] = evaluate_intents()

    print("\n=== Ragas Results ===")
    targets = {
        "faithfulness": 0.80,
        "answer_relevancy": 0.75,
        "context_precision": 0.75,
        "escalation_accuracy": 0.90,
        "ambiguous_intent_accuracy": 0.80,
    }
    for metric, score in scores.items():
        status = "PASS" if score >= targets[metric] else "FAIL"
        print(f"  {metric}: {score:.4f}  [{status}]")

    RESULTS_PATH.write_text(json.dumps(scores, indent=2))
    print(f"\nResults saved to {RESULTS_PATH}")
    return scores


if __name__ == "__main__":
    main()
