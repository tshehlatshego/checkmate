# app.py

import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

import database as db
from ai_model import verify_claim_with_ai

load_dotenv()

app = Flask(__name__)

# --- API Key Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not GEMINI_API_KEY or not SERPER_API_KEY:
    raise ValueError("Missing API keys. Please check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Init DB
db.init_db()


@app.route('/')
def index():
    return render_template('Main.html')


@app.route('/fact-check', methods=['GET'])
def fact_check_endpoint():
    claim_text = request.args.get('claim')
    if not claim_text:
        return jsonify({"error": "Invalid input. 'claim' parameter is required."}), 400

    # Save to DB
    claim_id = db.create_fact_check(claim_text)

    # Run AI fact-check
    result = verify_claim_with_ai(claim_text)
    analysis = result.get("analysis", "No analysis.")
    verdict = result.get("result", "Uncertain")
    sources_raw = result.get("sources", "")

    # Normalize verdict
    if verdict.lower() == "verified":
        credibility = 90
        verdict_label = "true"
    elif verdict.lower() == "unverified":
        credibility = 40
        verdict_label = "false"
    elif verdict.lower() == "uncertain":
        credibility = 60
        verdict_label = "unclear"
    else:
        credibility = 70
        verdict_label = "partially-true"

    # Format sources into expected structure
    sources = []
    if isinstance(sources_raw, list):
        # If sources is already a list of dictionaries
        for source in sources_raw:
            if isinstance(source, dict):
                sources.append({
                    "title": source.get("title", "Untitled"),
                    "url": source.get("url", source.get("URL", "")),
                    "credibility": "high"
                })
            elif isinstance(source, str):
                # If it's a string, try to parse it
                if "http" in source:
                    parts = source.split("http")
                    if len(parts) >= 2:
                        sources.append({
                            "title": parts[0].replace("-", "").strip(),
                            "url": "http" + parts[1].strip(),
                            "credibility": "high"
                        })
    elif isinstance(sources_raw, str):
        # If sources is a string, split by lines
        for line in sources_raw.split("\n"):
            line = line.strip()
            if line and "http" in line:
                parts = line.split("http")
                if len(parts) >= 2:
                    title = parts[0].replace("-", "").replace("*", "").strip()
                    url = "http" + parts[1].strip()
                    sources.append({
                        "title": title if title else "Source",
                        "url": url,
                        "credibility": "high"
                    })

    # If no sources were parsed, create some fallback
    if not sources:
        sources = [{
            "title": "No sources available",
            "url": "",
            "credibility": "medium"
        }]

    # Update DB
    db.update_fact_check(claim_id, verdict_label, analysis, credibility, str(sources))

    return jsonify({
        "claim": claim_text,
        "verdict": verdict_label,
        "credibilityScore": credibility,
        "summary": analysis,
        "sources": sources,
        "checkedAt": datetime.utcnow().strftime("%d-%m-%Y"),
        "relatedClaims": []
    })


if __name__ == '__main__':
    app.run(debug=True, port=8000)
