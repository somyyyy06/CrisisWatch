# backend/scraper/debug_scraper.py
import requests
from bs4 import BeautifulSoup

def test_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, timeout=10, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for different content patterns
        print("Trying to find paragraphs...")
        paragraphs = soup.find_all('p')
        print(f"Found {len(paragraphs)} <p> tags")
        
        if paragraphs:
            sample_text = ' '.join(p.get_text().strip() for p in paragraphs[:3] if p.get_text().strip())
            print(f"Sample text: {sample_text[:200]}...")
        
        # Check for article-specific tags
        article_content = soup.find('article') or soup.find(class_=lambda x: x and ('article' in x or 'content' in x))
        if article_content:
            print("Found article/content section")
            
        return response.text
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Use a different variable name to avoid conflict
    test_url_address = "https://timesofindia.indiatimes.com/india/unwarranted-india-pulls-up-turkeys-erdogan-over-un-speech-what-triggered-row-turkeys-stand-on-kashmir/articleshow/124160522.cms"
    test_url(test_url_address)  # Now this calls the function correctly