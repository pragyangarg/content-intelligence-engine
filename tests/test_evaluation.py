import os
import pytest
from app.evaluation.dataset import get_evaluation_dataset, EVALUATION_DATASET
from app.evaluation.evaluator import compute_metrics_for_sample


def test_evaluation_dataset_loads_correctly():
    dataset = get_evaluation_dataset()
    assert len(dataset) >= 20
    for item in dataset:
        assert "question" in item
        assert "ground_truth" in item
        assert "relevant_documents" in item
        assert len(item["relevant_documents"]) > 0


def test_evaluation_pipeline_produces_scores():
    sample = EVALUATION_DATASET[0]
    metrics = compute_metrics_for_sample(
        question=sample["question"],
        ground_truth=sample["ground_truth"],
        context_list=sample["relevant_documents"],
        generated_answer=sample["ground_truth"]
    )

    assert "faithfulness" in metrics
    assert "answer_relevance" in metrics
    assert "context_relevance" in metrics
    assert "context_recall" in metrics

    for key, score in metrics.items():
        assert 0.0 <= score <= 1.0

