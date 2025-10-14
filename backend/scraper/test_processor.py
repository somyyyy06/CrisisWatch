# backend/scraper/test_processor.py
from backend.scraper.rss_scraper import fetch_items, fetch_article_text
from backend.scraper.processor import process_and_store
import time

def main_loop():
    items = fetch_items()
    print(f"Found {len(items)} items to check")
    
    successful = 0
    for i, it in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] Processing: {it['title'][:80]}...")
        print(f"URL: {it['link']}")
        
        title, text, url = fetch_article_text(it["link"], it["title"])
        
        # Reduced minimum length from 100 to 50 characters
        if not text or len(text.strip()) < 50:
            print(f"  → Insufficient content extracted ({len(text) if text else 0} chars)")
            continue
            
        print(f"  → Extracted {len(text)} characters")
        
        try:
            row = process_and_store(title, text, url)
            if row:
                print(f"  → ✅ Stored: {row.id} - {row.title[:80]}...")
                successful += 1
            else:
                print(f"  → ⚠️ Duplicate/ignored")
        except Exception as e:
            print(f"  → ❌ Process error: {e}")
        
        time.sleep(1)  # polite delay
    
    print(f"\nSummary: Successfully processed {successful} out of {len(items)} items")

if __name__ == "__main__":
    main_loop()