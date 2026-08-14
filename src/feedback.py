import os
import csv
import pandas as pd
import joblib
import numpy as np
from preprocess import clean_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDBACK_CSV = os.path.join(BASE_DIR, "data", "user_feedback.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "fake_news_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl")


def record_feedback(text: str, corrected_label: str) -> dict:
    """
    Saves user feedback to user_feedback.csv and fine-tunes Model A.
    """
    if not text or not text.strip():
        return {"status": "error", "message": "Empty text provided."}

    corrected_label = corrected_label.upper()
    if corrected_label not in ["REAL", "FAKE"]:
        return {"status": "error", "message": "Label must be REAL or FAKE."}

    # 1. Append to user_feedback.csv
    file_exists = os.path.exists(FEEDBACK_CSV)
    os.makedirs(os.path.dirname(FEEDBACK_CSV), exist_ok=True)

    cleaned = clean_text(text, strip_meta=True)
    with open(FEEDBACK_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["text", "label", "clean_text"])
        writer.writerow([text.strip(), corrected_label, cleaned])

    # 2. Perform active learning model fine-tuning
    retrain_msg = update_model_with_feedback()

    return {
        "status": "success",
        "message": f"Feedback recorded! Active learning memory bank updated ({corrected_label}).",
        "retrain_info": retrain_msg
    }


def check_feedback_memory(text: str) -> dict:
    """
    Checks if an exact or high-overlap match exists in the user feedback ground-truth memory.
    If found, returns an immediate high-confidence ground-truth override.
    """
    if not os.path.exists(FEEDBACK_CSV):
        return None

    try:
        df = pd.read_csv(FEEDBACK_CSV)
        if len(df) == 0:
            return None

        cleaned_input = clean_text(text, strip_meta=True)
        input_words = set(cleaned_input.split())
        if not input_words:
            return None

        # Check newest feedback first
        for _, row in df.iloc[::-1].iterrows():
            stored_cleaned = str(row.get("clean_text", ""))
            stored_words = set(stored_cleaned.split())
            if not stored_words:
                continue

            # Exact match or high overlap ratio (>= 60%)
            intersection = input_words.intersection(stored_words)
            overlap_ratio = len(intersection) / float(max(len(input_words), len(stored_words)))

            if cleaned_input == stored_cleaned or overlap_ratio >= 0.60:
                label = str(row.get("label", "REAL")).upper()
                return {
                    "matched": True,
                    "prediction": label,
                    "confidence": 99.5,
                    "reasoning": f"🎓 Active Learning Memory Match: Verified by user correction ({label}). The system learned this claim pattern."
                }
    except Exception as e:
        print(f"Feedback memory lookup error: {e}")

    return None


def update_model_with_feedback():
    """
    Loads user feedback samples, applies heavy sample weights (10.0x), and updates Model A.
    """
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
            return "Model files missing."

        if not os.path.exists(FEEDBACK_CSV):
            return "No feedback data available."

        feedback_df = pd.read_csv(FEEDBACK_CSV)
        if len(feedback_df) == 0:
            return "Feedback dataset empty."

        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)

        feedback_df["clean_text"] = feedback_df["clean_text"].fillna("")
        feedback_df["label_encoded"] = feedback_df["label"].map({"FAKE": 1, "REAL": 0})

        # Baseline anchor samples to ensure 2-class representation in batch
        anchor_df = pd.DataFrame([
            {"clean_text": "official government press statement verified news report", "label_encoded": 0},
            {"clean_text": "secret alien underground laboratory reverse engineered technology", "label_encoded": 1}
        ])

        combined_df = pd.concat([anchor_df, feedback_df[["clean_text", "label_encoded"]]], ignore_index=True)

        X_batch = vectorizer.transform(combined_df["clean_text"])
        y_batch = combined_df["label_encoded"].values

        # Heavy sample weights for user feedback (10.0x) so model parameters adjust strongly
        sample_weights = np.ones(len(combined_df))
        sample_weights[2:] = 10.0

        model.fit(X_batch, y_batch, sample_weight=sample_weights)
        joblib.dump(model, MODEL_PATH)

        return f"Successfully retrained Model A on {len(feedback_df)} active learning feedback sample(s)."
    except Exception as e:
        print(f"Active learning update error: {e}")
        return str(e)
