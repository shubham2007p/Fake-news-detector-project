import os
import json
import requests
import config # Ensures env vars are loaded

def get_groq_reasoning(title, text, ml_res, news_evidence, fact_evidence):
    """
    Calls Groq API to synthesize ML model outputs and web search evidence.
    Returns a unified verdict, status label, and structured explanation.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("WARNING: GROQ_API_KEY not configured. Falling back to local rules engine.")
        return None
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Construct context
    evidence_str = ""
    if news_evidence:
        evidence_str += "\nNEWS ARTICLES FOUND:\n"
        for i, art in enumerate(news_evidence):
            evidence_str += f"{i+1}. Source: {art['source']} ({art['published_at']}) - Tier: {art['tier']}\n"
            evidence_str += f"   Title: {art['title']}\n"
            evidence_str += f"   Description: {art['description']}\n"
            
    if fact_evidence:
        evidence_str += "\nEXISTING FACT-CHECKS FOUND:\n"
        for i, fact in enumerate(fact_evidence):
            evidence_str += f"{i+1}. Fact-Checker: {fact['publisher']} - Tier: {fact['tier']}\n"
            evidence_str += f"   Claim evaluated: {fact['claim_text']}\n"
            evidence_str += f"   Verdict: {fact['verdict']}\n"
            
    if not evidence_str:
        evidence_str = "No matching external news articles or fact-checks found on the web."
        
    system_prompt = (
        "You are an advanced facts-reasoning agent for a Fake News Detection system. "
        "Your task is to analyze user input news, combine it with a local Machine Learning (ML) model prediction "
        "and external web/fact-check evidence, and determine the final verdict.\n\n"
        "Return your response ONLY as a clean JSON object with the following keys:\n"
        '- "verdict": String. Must be exactly "REAL", "FAKE", or "UNCERTAIN".\n'
        '- "status_label": String. A short label summarizing the state (e.g., "Verified Real", "Verified Fake", "Contradicted (Likely Real)", "Contradicted (Likely Fake)", "Unverified Real", "Unverified Fake", "Conflicting Evidence").\n'
        '- "explanation": String. A professional, clear markdown analysis detailing why the verdict was reached, how the ML model outputs align with web evidence, and references to matching sources.\n\n'
        "Guidelines:\n"
        "1. External evidence (fact-checks/Tier-1 news) overrides the local ML model in case of contradictions.\n"
        "2. If no external evidence is found and the ML model is confident, output Unverified Real/Fake.\n"
        "3. If external evidence contradicts the ML model, output a 'Contradicted' status.\n"
        "4. Keep explanations concise, professional, and clear for presentation."
    )
    
    user_content = (
        f"USER NEWS INPUT:\n"
        f"Title: {title}\n"
        f"Body: {text}\n\n"
        f"LOCAL ML MODEL CLASSIFICATION:\n"
        f"Model Prediction: {ml_res['prediction']}\n"
        f"Confidence Score: {ml_res['confidence']}%\n\n"
        f"EXTERNAL SEARCH EVIDENCE:\n"
        f"{evidence_str}"
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed_data = json.loads(content)
            return {
                "verdict": parsed_data.get("verdict", "UNCERTAIN").upper(),
                "status": parsed_data.get("status_label", "Conflicting Evidence"),
                "reasoning": parsed_data.get("explanation", "Reasoning unavailable."),
                "has_conflict": "contradict" in parsed_data.get("status_label", "").lower()
            }
        else:
            print(f"Groq API Error: Status {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception calling Groq API: {e}")
        return None
