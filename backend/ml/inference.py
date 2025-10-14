# backend/ml/inference.py
from transformers import pipeline
import os
import torch
from typing import Optional, Union

DEFAULT_MODEL = os.getenv("HF_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
_device = 0 if torch.cuda.is_available() else -1
_classifier = None

def get_classifier(model_name: Optional[str] = None):
    global _classifier
    if _classifier is None:
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
    """
    Return a credibility score in range [0,1].
    Accepts one or more text inputs (title, description, etc.).
    """
    # ✅ Join multiple texts if provided
    combined_text = " ".join([t for t in texts if t])

    if not combined_text:
        return 0.0

    clf = get_classifier()
    results = clf(combined_text, truncation=True, max_length=512)

    scores = results[0] if isinstance(results, list) else results
    labels = [s["label"].lower() for s in scores]

    for s in scores:
        lab = s["label"].lower()
        scr = float(s["score"])
        if "credible" in lab or "real" in lab or "true" in lab:
            return scr
        if "fake" in lab or "false" in lab:
            return 1.0 - scr

    if len(scores) == 2:
        return float(scores[1]["score"])
    return max(float(s["score"]) for s in scores)
