# ai_model.py

import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


# Load API keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
print("DEBUG GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")
if not SERPER_API_KEY:
    raise ValueError("Missing SERPER_API_KEY in .env")

genai.configure(api_key=GEMINI_API_KEY)


def fetch_sources_from_serper(claim_text: str):
    """
    Use Serper API to get search results for the claim.
    Returns a list of (title, url).
    """
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": claim_text}

    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", [])[:5]:  # take top 5 results
            title = item.get("title", "Untitled")
            link = item.get("link", "")
            results.append((title, link))
        return results
    except Exception as e:
        print(f"Serper error: {e}")
        return []


def verify_claim_with_ai(claim_text: str) -> dict:
    """Fact-check a claim using Gemini AI and Serper sources."""
    # Get sources from Serper
    sources = fetch_sources_from_serper(claim_text)

    sources_list = [{"title": title, "url": url} for title, url in sources]
    sources_text = "\n".join([f"- {title}  {url}" for title, url in sources])

    # Build prompt
    prompt = f"""
    Analyze the truthfulness of this claim: "{claim_text}"

    SOURCES TO CONSIDER:
    {sources_text}

    Provide your response in this exact JSON format (NO markdown, just pure JSON):
    {{
        "result": "Verified|Unverified|Uncertain|Partially true",
        "analysis": "Your detailed analysis here (3-5 sentences)",
        "sources": "Bullet point list of relevant sources {sources_list}"
    }}

    IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting.
    """

    try:
        # Use the correct model
        model = genai.GenerativeModel("gemini-1.5-flash-8b")  # or "gemini-1.0-pro"
        
        response = model.generate_content(prompt)

        # Parse the response - handle markdown formatting
        import json
        import re
        
        response_text = response.text.strip()
        
        # Clean the response - remove markdown code blocks
        if "```json" in response_text:
            # Extract JSON from ```json ... ``` blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text
        elif "```" in response_text:
            # Extract JSON from ``` ... ``` blocks
            json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text
        else:
            json_str = response_text
            
        # Try to parse as JSON
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            # If it's still not valid JSON, try to find JSON object manually
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                # Fallback if JSON parsing completely fails
                parsed = {
                    "result": "Uncertain",
                    "analysis": response_text[:500],
                    "sources": sources_text
                }

        # Ensure we have the expected structure
        result = parsed.get("result", "Uncertain")
        analysis = parsed.get("analysis", "Analysis unavailable.")
        sources_response = parsed.get("sources", "")

        sources_response = parsed.get("sources", "")
        if isinstance(sources_response, str):
            # Convert string back to list of dicts
            final_sources = sources_list
        elif isinstance(sources_response, list):
            final_sources = sources_response
        else:
            final_sources = sources_list

        return {
            "result": result,
            "analysis": analysis,
            "sources": final_sources,
        }

    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "result": "Uncertain",
            "analysis": f"Error during AI processing: {str(e)[:200]}",
            "sources": sources_text,
        }