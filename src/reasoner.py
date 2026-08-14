def combine_predictions(ml_res, news_evidence, fact_evidence):
    """
    Implements the conflict resolution reasoning layer:
    Combines ML prediction with external fact checks and news evidence.
    """
    ml_pred = ml_res["prediction"] # "REAL" or "FAKE"
    ml_conf = ml_res["confidence"]  # Float percentage
    
    # Analyze fact checks for consensus
    fact_verdicts_false = 0
    fact_verdicts_true = 0
    
    for fact in fact_evidence:
        verdict = fact.get("verdict", "").lower()
        if any(term in verdict for term in ["false", "incorrect", "misleading", "pants on fire", "fake"]):
            fact_verdicts_false += 1
        elif any(term in verdict for term in ["true", "correct", "accurate"]):
            fact_verdicts_true += 1
            
    # Analyze news evidence presence
    news_count = len(news_evidence)
    has_tier1_news = any("Tier 1" in art.get("tier", "") for art in news_evidence)
    
    # Conflict Resolution Logic:
    final_verdict = ml_pred
    status = "Verified"
    reasoning = ""
    
    if fact_verdicts_false > 0:
        if ml_pred == "FAKE":
            final_verdict = "FAKE"
            status = "Verified Fake"
            reasoning = f"The ML model predicted FAKE ({ml_conf}%) and external fact-checking databases verify the claim is FALSE."
        else:
            final_verdict = "FAKE"
            status = "Contradicted (Likely Fake)"
            reasoning = "The ML model predicted REAL, but external fact-checking databases confirmed this claim is FALSE. External evidence overrides model."
            
    elif fact_verdicts_true > 0:
        if ml_pred == "REAL":
            final_verdict = "REAL"
            status = "Verified Real"
            reasoning = f"The ML model predicted REAL ({ml_conf}%) and external fact-checking databases confirm the claim is TRUE."
        else:
            final_verdict = "REAL"
            status = "Contradicted (Likely Real)"
            reasoning = "The ML model predicted FAKE, but external fact-checking databases confirm the claim is TRUE. External evidence overrides model."
            
    elif news_count > 0:
        if ml_pred == "REAL":
            final_verdict = "REAL"
            status = "Likely Real"
            reasoning = f"The ML model predicted REAL ({ml_conf}%) and multiple news agencies are currently reporting this event."
        else:
            # ML says FAKE, but there is active news reporting
            if has_tier1_news:
                final_verdict = "UNCERTAIN"
                status = "Conflicting Evidence"
                reasoning = "The ML model flagged structural markers of fake news, but credible Tier-1 news organizations are actively reporting on the topic. Verification is required."
            else:
                final_verdict = "FAKE"
                status = "Likely Fake"
                reasoning = "The ML model flagged this text as FAKE, and while news matches exist, they lack validation from top-tier news agencies."
                
    else:
        # No web evidence found
        if ml_pred == "REAL":
            final_verdict = "REAL"
            status = "Unverified Real"
            reasoning = f"The ML model predicted REAL ({ml_conf}%), but no matching web articles or fact-checks were found to verify this claim."
        else:
            final_verdict = "FAKE"
            status = "Unverified Fake"
            reasoning = f"The ML model predicted FAKE ({ml_conf}%), and no credible web articles support the claim."
            
    return {
        "verdict": final_verdict,
        "status": status,
        "reasoning": reasoning,
        "has_conflict": "Contradicted" in status or "Conflict" in status
    }
