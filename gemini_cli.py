# clients/gemini_client.py
import os
from google import genai
import json
import logging

MODEL_NAME = "gemini-2.5-flash" 

def init_gemini_client():
    
    return genai.Client()

def ask_gemini(client, prompt, max_output_tokens=600):
    """
    Send the prompt to Gemini and return plain text.
    We'll attempt to return a string that (ideally) contains JSON to parse.
    """
    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            max_output_tokens=max_output_tokens,
        )
        # Different google-genai versions return different shapes.
        # Try common extraction points:
        if hasattr(resp, "text") and resp.text:
            return resp.text
        # try nested output shape
        try:
            out = resp.output[0].content[0].text
            return out
        except Exception:
            pass
        # fallback to string conversion
        return str(resp)
    except Exception as e:
        logging.exception("Gemini request failed")
        raise
