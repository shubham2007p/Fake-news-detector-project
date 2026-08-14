import os
import json
import requests
import config  # Ensures env vars are loaded
from web_search import is_india_query

def get_groq_reasoning(title, text, ml_res, news_evidence, fact_evidence):
    """
    Calls Groq API to synthesize ML model outputs and web search evidence.
    Returns a unified verdict, status label, and structured explanation.
    Injects India-specific context when the query is about India.
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

    # ── Build evidence string ──────────────────────────────────────────────────
    evidence_str = ""
    if news_evidence:
        evidence_str += "\nNEWS ARTICLES FOUND:\n"
        for i, art in enumerate(news_evidence):
            evidence_str += f"{i+1}. Source: {art['source']} ({art['published_at']}) - Reliability: {art['tier']}\n"
            evidence_str += f"   Title: {art['title']}\n"
            evidence_str += f"   Summary: {art['description']}\n"

    if fact_evidence:
        evidence_str += "\nEXISTING FACT-CHECKS FOUND:\n"
        for i, fact in enumerate(fact_evidence):
            evidence_str += f"{i+1}. Fact-Checker: {fact['publisher']} - Reliability: {fact['tier']}\n"
            evidence_str += f"   Claim: {fact['claim_text']}\n"
            evidence_str += f"   Verdict: {fact['verdict']}\n"

    if not evidence_str:
        evidence_str = "No matching external news articles or fact-checks found on the web."

    # ── Detect India context ───────────────────────────────────────────────────
    query_text = f"{title} {text}"
    india_context_block = ""
    if is_india_query(query_text):
        india_context_block = (
            "\n\nINDIA CONTEXT NOTE:\n"
            "This query relates to Indian news. Apply these additional guidelines:\n"
            "- Tier 1 Indian sources: PTI, IANS, ANI, PIB (Press Information Bureau), Doordarshan.\n"
            "- Tier 2 Indian sources: The Hindu, Hindustan Times, NDTV, Indian Express, Times of India, "
            "Mint, Business Standard, The Print, The Wire, Scroll, India Today, Tribune.\n"
            "- Authoritative Indian fact-checkers: AltNews, BOOM Live, Vishvas News, Factly, "
            "Newschecker, The Quint WebQoof.\n"
            "- WhatsApp forwards, regional tabloids, and anonymous social media posts should be "
            "treated as extremely low reliability.\n"
            "- Consider Indian political, social, and legal context when assessing plausibility.\n"
        )

    # ── System prompt ──────────────────────────────────────────────────────────
    system_prompt = (
        "You are the Chief Fact Verification & Intelligence Officer for a state-of-the-art Fake News Detection system. "
        "Your duty is to deliver a SHARP, DEFINITIVE VERDICT ('REAL' or 'FAKE') whenever possible by synthesizing 4 signals:\n"
        "1. External Web Search & Fact-Check Evidence (highest authority if available).\n"
        "2. Model B (LIAR Statement Credibility) — evaluates structural truthfulness of claims.\n"
        "3. Model A (Stylistic Classifier) — evaluates surface writing tone (secondary hint only).\n"
        "4. Your 70-Billion Parameter World Knowledge Base — evaluate historical facts, real-world events, and physical/logical plausibility.\n\n"
        "CRITICAL DECISION & CONFLICT RESOLUTION DIRECTIVES:\n"
        "- MAKE A SHARP DECISION: Avoid defaulting to 'UNCERTAIN'. Only output 'UNCERTAIN' if evidence is genuinely split 50/50 or evaluating an unverified private rumor.\n"
        "- MODEL CONFLICT RESOLUTION: If Model A says REAL (e.g. 51.4%) while Model B says FAKE (e.g. 65%), RECONCILE THE CONFLICT! Explain that Model B's statement truthfulness classifier flags the claim's core structure, overriding Model A's weak 51% stylistics. Issue a clear verdict (e.g. FAKE) based on Model B + World Knowledge + Web Evidence.\n"
        "- SEARCH EVIDENCE INTEGRATION: When web articles match from credible outlets (Times of India, Reuters, The Hindu, AP, ANI), explicitly cite them to confirm REAL. If fact-checkers (AltNews, BOOM, FactCheck.org) flag it as false, confirm FAKE.\n"
        "- WORLD KNOWLEDGE FALLBACK: If web search returns 0 articles, use your deep world knowledge. If a claim asserts impossible sci-fi events ('nano-chips in currency', 'aliens in UP', 'radiation in cold water'), immediately classify as FAKE and explain why. If it states well-known verified history or current events, classify as REAL.\n\n"
        "Return your response ONLY as a clean JSON object with keys:\n"
        '- "verdict": "REAL", "FAKE", or "UNCERTAIN".\n'
        '- "status_label": Short string (e.g. "Verified Real", "Verified Fake", "Contradicted (Likely Fake)", "High-Confidence Fake", "Likely Real").\n'
        '- "explanation": Clear, sharp markdown analysis explaining the conflict resolution, web/world knowledge evidence, and final conclusion.\n'
        + india_context_block
    )

    model_a_info = ml_res.get("model_a", {"prediction": ml_res.get("prediction", "UNKNOWN"), "confidence": ml_res.get("confidence", 0)})
    model_b_info = ml_res.get("model_b", {"prediction": ml_res.get("prediction", "UNKNOWN"), "truth_probability": ml_res.get("confidence", 0)})

    user_content = (
        f"USER NEWS INPUT:\n"
        f"Title: {title}\n"
        f"Body: {text}\n\n"
        f"LOCAL ML ENSEMBLE SIGNALS:\n"
        f"- Weighted Ensemble Verdict: {ml_res['prediction']} ({ml_res['confidence']}% confidence)\n"
        f"- Model A (Stylistic Classifier): {model_a_info['prediction']} ({model_a_info['confidence']}% confidence)\n"
        f"- Model B (LIAR Statement Classifier): {model_b_info['prediction']} ({model_b_info['truth_probability']}% truth score)\n\n"
        f"EXTERNAL SEARCH EVIDENCE:\n"
        f"{evidence_str}"
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result  = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed  = json.loads(content)
            return {
                "verdict":      parsed.get("verdict", "UNCERTAIN").upper(),
                "status":       parsed.get("status_label", "Conflicting Evidence"),
                "reasoning":    parsed.get("explanation", "Reasoning unavailable."),
                "has_conflict": "contradict" in parsed.get("status_label", "").lower()
            }
        else:
            print(f"Groq API Error {response.status_code}: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"Groq API exception: {e}")
        return None
