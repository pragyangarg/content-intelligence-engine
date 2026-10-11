import csv
import json
import logging
import os
import re
from typing import List, Dict, Any, Tuple

from app.evaluation.dataset import get_evaluation_dataset, save_evaluation_dataset
from app.services.vector_store import get_vector_store
from app.services.agentic_rag import get_rag_workflow

logger = logging.getLogger(__name__)


def compute_token_overlap(text1: str, text2: str) -> float:
    """Compute token-level Jaccard similarity / overlap ratio between two strings."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "and", "or",
        "for", "on", "with", "as", "by", "at", "from", "that", "this", "it", "what",
        "how", "which", "does", "do", "did", "can", "could", "will", "would", "be"
    }
    tokens1 = set(re.findall(r"\w+", (text1 or "").lower())) - stopwords
    tokens2 = set(re.findall(r"\w+", (text2 or "").lower())) - stopwords

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return float(intersection / union) if union > 0 else 0.0


def compute_metrics_for_sample(
    question: str,
    ground_truth: str,
    context_list: List[str],
    generated_answer: str
) -> Dict[str, float]:
    """
    Compute Faithfulness, Answer Relevance, Context Relevance, and Context Recall.
    Uses grounded NLP metrics supported locally and aligns with Ragas concepts.
    """
    context_blob = " ".join(context_list).lower()
    answer_clean = generated_answer.lower()
    gt_clean = ground_truth.lower()
    q_clean = question.lower()

    # 1. Faithfulness: proportion of key claims/tokens in answer that appear in retrieved context
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "and", "or", "for", "on", "with", "sources", "according"}
    answer_tokens = set(re.findall(r"\w+", answer_clean)) - stopwords
    context_tokens = set(re.findall(r"\w+", context_blob)) - stopwords

    if answer_tokens and context_tokens:
        supported_tokens = answer_tokens & context_tokens
        faithfulness = round(len(supported_tokens) / len(answer_tokens), 4)
    else:
        faithfulness = 0.5

    # 2. Answer Relevance: semantic/token overlap between question and generated answer
    q_tokens = set(re.findall(r"\w+", q_clean)) - stopwords
    if q_tokens and answer_tokens:
        common_q_ans = q_tokens & answer_tokens
        answer_relevance = round(min(1.0, (len(common_q_ans) / len(q_tokens)) * 1.2), 4)
    else:
        answer_relevance = 0.5

    # 3. Context Relevance: precision of retrieved contexts with respect to the question
    if q_tokens and context_tokens:
        context_relevance = round(min(1.0, (len(q_tokens & context_tokens) / len(q_tokens)) * 1.1), 4)
    else:
        context_relevance = 0.4

    # 4. Context Recall: proportion of ground truth information captured by retrieved context
    gt_tokens = set(re.findall(r"\w+", gt_clean)) - stopwords
    if gt_tokens and context_tokens:
        recalled = gt_tokens & context_tokens
        context_recall = round(len(recalled) / len(gt_tokens), 4)
    else:
        context_recall = 0.4

    return {
        "faithfulness": min(1.0, max(0.0, faithfulness)),
        "answer_relevance": min(1.0, max(0.0, answer_relevance)),
        "context_relevance": min(1.0, max(0.0, context_relevance)),
        "context_recall": min(1.0, max(0.0, context_recall)),
    }


def seed_evaluation_documents(vs) -> int:
    """Ensure benchmark ground truth documents are indexed into vector store."""
    dataset = get_evaluation_dataset()
    indexed_count = 0
    for item in dataset:
        doc_id = item.get("id")
        title = item.get("question")
        docs = item.get("relevant_documents", [])
        content = " ".join(docs)
        if content:
            vs.index_content({
                "id": f"eval_{doc_id}",
                "title": f"Benchmark doc: {title}",
                "content": content,
                "source": "Evaluation Corpus",
                "url": f"https://eval.example.com/{doc_id}",
                "published_at": "2026-03-01",
            })
            indexed_count += 1
    return indexed_count


def evaluate_pipeline(save_output: bool = True) -> Dict[str, Any]:
    """
    Run evaluation comparing:
    Version A (Baseline RAG: Query -> Vector Search -> LLM)
    vs
    Version B (Improved Agentic RAG: Query -> Query Analysis -> Vector Search -> Filtering -> LLM)
    """
    save_evaluation_dataset()
    dataset = get_evaluation_dataset()
    vs = get_vector_store()
    workflow = get_rag_workflow()

    # Pre-seed evaluation docs
    seed_evaluation_documents(vs)

    results_a = []
    results_b = []

    for item in dataset:
        q = item["question"]
        gt = item["ground_truth"]

        # Run Version A (Baseline)
        out_a = workflow.run_baseline(q)
        contexts_a = [d.get("content", "") for d in out_a.get("documents", [])]
        metrics_a = compute_metrics_for_sample(
            question=q,
            ground_truth=gt,
            context_list=contexts_a,
            generated_answer=out_a.get("answer", "")
        )
        results_a.append({
            "id": item["id"],
            "question": q,
            "ground_truth": gt,
            "answer": out_a.get("answer", ""),
            "contexts": contexts_a,
            "metrics": metrics_a,
        })

        # Run Version B (Improved Agentic RAG)
        out_b = workflow.run(q)
        contexts_b = [d.get("content", "") for d in out_b.get("documents", [])]
        metrics_b = compute_metrics_for_sample(
            question=q,
            ground_truth=gt,
            context_list=contexts_b,
            generated_answer=out_b.get("answer", "")
        )
        results_b.append({
            "id": item["id"],
            "question": q,
            "ground_truth": gt,
            "rewritten_query": out_b.get("rewritten_query", ""),
            "answer": out_b.get("answer", ""),
            "contexts": contexts_b,
            "metrics": metrics_b,
        })

    # Compute Aggregate Scores
    def average_metrics(results):
        keys = ["faithfulness", "answer_relevance", "context_relevance", "context_recall"]
        n = len(results)
        if n == 0:
            return {k: 0.0 for k in keys}
        return {
            k: round(sum(r["metrics"][k] for r in results) / n, 4)
            for k in keys
        }

    avg_a = average_metrics(results_a)
    avg_b = average_metrics(results_b)

    summary = {
        "total_samples": len(dataset),
        "version_a_baseline": avg_a,
        "version_b_agentic": avg_b,
        "improvement_percentage": {
            k: round(((avg_b[k] - avg_a[k]) / max(avg_a[k], 0.001)) * 100, 2)
            for k in avg_a
        }
    }

    if save_output:
        base_dir = os.path.dirname(__file__)
        json_path = os.path.join(base_dir, "evaluation_results.json")
        csv_path = os.path.join(base_dir, "evaluation_results.csv")

        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "version_a_baseline_details": results_a,
                "version_b_agentic_details": results_b,
            }, f, indent=2)

        # Save CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Question ID", "Question",
                "Metric",
                "Version A (Baseline)",
                "Version B (Agentic RAG)"
            ])
            for ra, rb in zip(results_a, results_b):
                qid = ra["id"]
                q = ra["question"]
                for m in ["faithfulness", "answer_relevance", "context_relevance", "context_recall"]:
                    writer.writerow([
                        qid, q, m,
                        ra["metrics"][m],
                        rb["metrics"][m]
                    ])
            writer.writerow([])
            writer.writerow(["SUMMARY AVERAGE", "", "", "", ""])
            for m in ["faithfulness", "answer_relevance", "context_relevance", "context_recall"]:
                writer.writerow([
                    "AVERAGE", "-", m,
                    avg_a[m],
                    avg_b[m]
                ])

    return summary


if __name__ == "__main__":
    print("Running RAG Evaluation pipeline (Version A vs Version B)...")
    res = evaluate_pipeline()
    print("Evaluation Summary:")
    print(json.dumps(res, indent=2))

