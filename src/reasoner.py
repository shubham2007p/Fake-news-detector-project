def combine_predictions(ml_res, news_evidence, fact_evidence):
    """
    Implements the conflict resolution reasoning layer & Uncertain Logic Gate:
    If a claim lacks a cross-referenceable source on fact-checking repositories
    (e.g., FactCheck.org, AltNews, BOOM) or official Tier 1/2 news/government portals,
    it MUST output UNCERTAIN (Low Confidence) rather than guessing.
    """
    ml_pred = ml_res["prediction"]  # "REAL" or "FAKE"
    ml_conf = ml_res["confidence"]  # Float percentage

    # Analyze fact checks
    fact_verdicts_false = 0
    fact_verdicts_true  = 0
    for fact in fact_evidence:
        verdict = fact.get("verdict", "").lower()
        if any(term in verdict for term in ["false", "incorrect", "misleading", "pants on fire", "fake"]):
            fact_verdicts_false += 1
        elif any(term in verdict for term in ["true", "correct", "accurate"]):
            fact_verdicts_true += 1

    # Analyze news sources
    has_tier1_news = any("Tier 1" in art.get("tier", "") for art in news_evidence)
    has_tier2_news = any("Tier 2" in art.get("tier", "") for art in news_evidence)
    has_credible_sources = (fact_verdicts_false > 0 or fact_verdicts_true > 0 or has_tier1_news or has_tier2_news)

    # ── UNCERTAIN LOGIC GATE ──────────────────────────────────────────────────
    # Rule: If no cross-referenceable source on fact-check repositories or official news portals exists,
    # output UNCERTAIN / Unverified (Low Confidence) rather than guessing.
    if not has_credible_sources:
        return {
            "verdict": "UNCERTAIN",
            "status": "Unverified (Low Confidence)",
            "reasoning": (
                f"No cross-referenceable evidence was found on fact-checking repositories (FactCheck.org, AltNews, BOOM) "
                f"or official news/government portals (PIB, PTI, Reuters, AP, The Hindu). "
                f"The system outputs **UNCERTAIN** rather than guessing."
            ),
            "has_conflict": False
        }

    # ── Verified Decision Tree ─────────────────────────────────────────────────
    if fact_verdicts_false > 0:
        return {
            "verdict": "FAKE",
            "status": "Verified Fake" if ml_pred == "FAKE" else "Contradicted (Likely Fake)",
            "reasoning": (
                f"External fact-checking repositories verified this claim is **FALSE**. "
                f"Fact-check evidence takes absolute priority."
            ),
            "has_conflict": ml_pred != "FAKE"
        }

    if fact_verdicts_true > 0:
        return {
            "verdict": "REAL",
            "status": "Verified Real" if ml_pred == "REAL" else "Contradicted (Likely Real)",
            "reasoning": (
                f"External fact-checking repositories confirmed this claim is **TRUE**. "
                f"Fact-check evidence takes absolute priority."
            ),
            "has_conflict": ml_pred != "REAL"
        }

    if has_tier1_news or has_tier2_news:
        if ml_pred == "REAL":
            return {
                "verdict": "REAL",
                "status": "Likely Real",
                "reasoning": f"Credible news organizations are actively reporting on this event, aligning with the local ML prediction ({ml_conf}%).",
                "has_conflict": False
            }
        else:
            return {
                "verdict": "UNCERTAIN",
                "status": "Conflicting Evidence",
                "reasoning": f"The ML ensemble flagged stylistic/statement concerns, but credible news sources are actively reporting this event. Further verification is required.",
                "has_conflict": True
            }

    return {
        "verdict": "UNCERTAIN",
        "status": "Unverified (Low Confidence)",
        "reasoning": "Lacks sufficient cross-referenceable sources to issue a definitive REAL or FAKE verdict.",
        "has_conflict": False
    }
