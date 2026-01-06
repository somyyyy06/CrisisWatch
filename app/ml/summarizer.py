# app/ml/summarizer.py

from typing import Optional

_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        from transformers import pipeline
        _summarizer = pipeline("summarization", model="t5-small")
    return _summarizer


def generate_summary(
    text: str,
    max_length: int = 100,
    min_length: int = 25
) -> str:
    try:
        summarizer = get_summarizer()
        result = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return result[0]["summary_text"]
    except Exception as e:
        return f"Error: {str(e)}"
