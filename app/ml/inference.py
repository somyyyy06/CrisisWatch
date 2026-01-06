# app/ml/inference.py

import os
from typing import Optional

DEFAULT_MODEL = os.getenv(
    "HF_MODEL",
    "distilbert-base-uncased-finetuned-sst-2-english"
)

_classifier = None
_device = None


def get_classifier(model_name: Optional[str] = None):
    global _classifier, _device

    if _classifier is None:
        import torch
        from transformers import pipeline

        _device = 0 if torch.cuda.is_available() else -1
        model_name = model_name or DEFAULT_MODEL

        _classifier = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            return_all_scores=True,
            device=_device,
        )

    return _classifier


def get_credibility_score(*texts: str) -> float:
    combined_text = " ".join(t for t in texts if t)
    if not combined_text:
        return 0.0

    clf = get_classifier()
    results = clf(combined_text, truncation=True, max_length=512)

    scores = results[0] if isinstance(results, list) else results

    for s in scores:
        label = s["label"].lower()
        score = float(s["score"])

        if "credible" in label or "real" in label or "true" in label:
            return score
        if "fake" in label or "false" in label:
            return 1.0 - score

    return max(float(s["score"]) for s in scores)
