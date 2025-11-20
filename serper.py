# clients/serper_client.py
import os
import requests
from urllib.parse import urlparse

SERPER_URL = "https://google.serper.dev/search"
API_KEY = os.getenv("SERPER_API_KEY")

def serper_search(query, k=6, gl="us", hl="en"):
    """
    Returns a list of results: {title, snippet, link}
    """
    if not API_KEY:
        raise RuntimeError("SERPER_API_KEY not set in environment")

    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "gl": gl,
        "hl": hl,
    }
    resp = requests.post(SERPER_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results = []

    # answer_box -> single high-value snippet
    ab = data.get("answer_box")
    if ab:
        snippet = ab.get("snippet") or ab.get("answer") or ""
        results.append({"title": ab.get("title") or snippet[:60], "snippet": snippet, "link": ab.get("link") or ""})

    # organic results
    organic = data.get("organic", [])
    for item in organic[:k]:
        results.append({
            "title": item.get("title") or item.get("link") or "",
            "snippet": item.get("snippet") or "",
            "link": item.get("link") or ""
        })
    return results

def domain_credibility(url):
    """
    Simple heuristic to tag credibility for the front-end.
    Mark high for .gov, .edu, mainstream news orgs (.bbc., .nytimes., .washingtonpost., etc.)
    This is intentionally conservative and simplistic — replace with a proper classifier if needed.
    """
    if not url:
        return "unknown"
    u = urlparse(url).netloc.lower()
    # high if gov/edu
    if u.endswith(".gov") or u.endswith(".edu"):
        return "high"
    # some common trusted news domains (very small heuristic list)
    trusted = ["nytimes", "bbc", "washingtonpost", "theguardian", "reuters", "apnews", "bbc.co.uk", "cnn"]
    for t in trusted:
        if t in u:
            return "high"
    # org could be medium
    if u.endswith(".org"):
        return "medium"
    # otherwise unknown/low
    return "unknown"
