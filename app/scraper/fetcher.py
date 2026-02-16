import requests

def fetch_url(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"Failed to fetch {url}, status {resp.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

