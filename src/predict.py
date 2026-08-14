import os
import sys
import pickle
import joblib

# Setup sys.modules mapping for unpickling legacy scikit-learn models (LIAR model compatibility)
import sklearn.linear_model
sys.modules['sklearn.linear_model.logistic'] = sklearn.linear_model

from preprocess import clean_text, META_BLOCKLIST, _BLOCKLIST_PATTERN


class FakeNewsClassifier:
    """
    Ensemble Classifier combining:
    - Model A: Stylistic Classifier (trained on article body/structure)
    - Model B: Claim Classifier (trained on LIAR benchmark dataset for statement truthfulness)
    """

    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

        self.model_a_path      = os.path.join(model_dir, "fake_news_model.pkl")
        self.vectorizer_a_path = os.path.join(model_dir, "tfidf_vectorizer.pkl")
        self.model_b_path      = os.path.join(model_dir, "liar_model.sav")

        self.model_a      = None
        self.vectorizer_a = None
        self.model_b      = None
        self.load_models()

    def load_models(self):
        # Load Model A (Stylistic Classifier)
        if not os.path.exists(self.model_a_path) or not os.path.exists(self.vectorizer_a_path):
            raise FileNotFoundError(
                "Model A files missing. Run 'train.py' to build fake_news_model.pkl."
            )
        self.model_a      = joblib.load(self.model_a_path)
        self.vectorizer_a = joblib.load(self.vectorizer_a_path)

        # Load Model B (LIAR Claim Classifier)
        if os.path.exists(self.model_b_path):
            try:
                with open(self.model_b_path, "rb") as f:
                    self.model_b = pickle.load(f)
                print("DEBUG: Successfully loaded Model B (LIAR Statement Classifier).")
            except Exception as e:
                print(f"WARNING: Could not load Model B (liar_model.sav): {e}")
                self.model_b = None
        else:
            print("WARNING: Model B (liar_model.sav) not found. Running single-model mode.")
            self.model_b = None

    def predict(self, title, text):
        combined = f"{title} {text}".strip()

        # Detect label-leakage words
        leakage_found = _BLOCKLIST_PATTERN.findall(combined)
        if leakage_found:
            unique_leaked = sorted(set(w.lower() for w in leakage_found))
            print(f"WARNING: Label-leakage words detected and stripped: {unique_leaked}")

        clean = clean_text(combined, strip_meta=True)

        if not clean:
            return {
                "prediction": "INVALID INPUT",
                "confidence": 0.0,
                "label_code": -1,
                "model_a": {"prediction": "INVALID", "confidence": 0.0},
                "model_b": {"prediction": "INVALID", "truth_probability": 0.0},
                "leakage_stripped": leakage_found,
            }

        # ── Model A: Stylistic Analysis ───────────────────────────────────────
        vec_a = self.vectorizer_a.transform([clean])
        probs_a = self.model_a.predict_proba(vec_a)[0]
        code_a = self.model_a.predict(vec_a)[0]
        label_a = "FAKE" if code_a == 1 else "REAL"
        conf_a = probs_a[code_a] * 100

        # ── Model B: Claim / Statement Analysis (LIAR Dataset) ────────────────
        claim_input = title if title else text[:200]
        if self.model_b is not None and claim_input:
            try:
                pred_b_raw = self.model_b.predict([claim_input])[0]
                probs_b = self.model_b.predict_proba([claim_input])[0]
                # Classes: [False, True] -> index 1 is truth probability
                truth_prob_b = probs_b[1] * 100
                is_true_b = str(pred_b_raw).strip().lower() in ["true", "1"]
                label_b = "REAL" if is_true_b else "FAKE"
                conf_b = truth_prob_b if is_true_b else (100.0 - truth_prob_b)
            except Exception as e:
                print(f"Model B inference error: {e}")
                label_b = label_a
                truth_prob_b = conf_a
                conf_b = conf_a
        else:
            label_b = label_a
            truth_prob_b = conf_a if label_a == "REAL" else (100.0 - conf_a)
            conf_b = conf_a

        # ── Primary Focus: Model B Statement Credibility (90%) + Model A Stylistics (10%) ──
        score_a_real = probs_a[0]  # 0 is REAL in Model A
        score_b_real = truth_prob_b / 100.0
        ensemble_real_score = (0.10 * score_a_real) + (0.90 * score_b_real)

        if ensemble_real_score >= 0.5:
            final_pred = "REAL"
            final_conf = ensemble_real_score * 100
        else:
            final_pred = "FAKE"
            final_conf = (1.0 - ensemble_real_score) * 100

        return {
            "prediction": final_pred,
            "confidence": round(final_conf, 2),
            "label_code": 0 if final_pred == "REAL" else 1,
            "model_a": {
                "name": "Stylistic Classifier (Hamel Dataset)",
                "prediction": label_a,
                "confidence": round(conf_a, 2),
            },
            "model_b": {
                "name": "Statement Classifier (LIAR Dataset)",
                "prediction": label_b,
                "truth_probability": round(truth_prob_b, 2),
                "confidence": round(conf_b, 2),
            },
            "leakage_stripped": [w.lower() for w in leakage_found],
        }


if __name__ == "__main__":
    try:
        classifier = FakeNewsClassifier()
        res = classifier.predict(
            "Breaking: NASA discovers water on Mars surface",
            "Scientists at NASA confirmed evidence of liquid water flows on Mars."
        )
        print("Ensemble Prediction Result:", res)
    except Exception as e:
        print("Initialization Error:", e)
