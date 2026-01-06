# backend/ml/summarizer.py
from transformers import pipeline

# load summarization pipeline once at startup
summarizer = pipeline("summarization", model="t5-small")

def generate_summary(text: str, max_length: int = 100, min_length: int = 25) -> str:
    try:
        result = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return result[0]["summary_text"]
    except Exception as e:
        return f"Error: {str(e)}"
