import os
import sys

# Include src/ directory in python path first
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment configuration
import config
from flask import Flask, render_template, request, jsonify

from predict import FakeNewsClassifier
from web_search import search_news_api, search_google_factcheck
from reasoner import combine_predictions
from llm_reasoner import get_groq_reasoning

app = Flask(__name__)

# Initialize classifier
try:
    classifier = FakeNewsClassifier()
except Exception as e:
    print(f"WARNING: Classifier could not be loaded. Please run 'train.py' first: {e}")
    classifier = None

@app.route('/')
def home():
    # Make sure static directory exists
    static_dir = os.path.join(app.root_path, 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Check if confusion matrix exists
    cm_exists = os.path.exists(os.path.join(static_dir, 'confusion_matrix.png'))
    return render_template('index.html', cm_exists=cm_exists)

@app.route('/predict', methods=['POST'])
def predict():
    global classifier
    if classifier is None:
        try:
            classifier = FakeNewsClassifier()
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Model not loaded. Run training script. Error: {str(e)}"
            }), 500

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    title = data.get('title', '').strip()
    text = data.get('text', '').strip()
    
    if not title and not text:
        return jsonify({"status": "error", "message": "Please enter a headline or content body"}), 400
        
    try:
        # Step 0: Active Learning Ground-Truth Memory Check
        from feedback import check_feedback_memory
        full_input = (title + " " + text).strip()
        mem_res = check_feedback_memory(full_input)

        if mem_res:
            print(f"DEBUG: Active Learning Memory Match -> {mem_res['prediction']}")
            return jsonify({
                "status": "success",
                "prediction": mem_res["prediction"],
                "confidence": mem_res["confidence"],
                "model_a": {"name": "Active Learning Memory", "prediction": mem_res["prediction"], "confidence": mem_res["confidence"]},
                "model_b": {"name": "Active Learning Ground-Truth", "prediction": mem_res["prediction"], "truth_probability": mem_res["confidence"]},
                "verdict": mem_res["prediction"],
                "status_lbl": f"Verified {mem_res['prediction'].capitalize()} (User Taught)",
                "reasoning": mem_res["reasoning"],
                "has_conflict": False,
                "news_evidence": [],
                "fact_evidence": []
            })

        # Step 1: Run local ML model
        ml_result = classifier.predict(title, text)
        
        # Determine query for web search
        search_query = title if title else text[:100]
        
        # Step 2: Query External APIs
        news_evidence = search_news_api(search_query)
        fact_evidence = search_google_factcheck(search_query)
        
        # Step 3: Try Advanced LLM Reasoning first
        final_result = get_groq_reasoning(title, text, ml_result, news_evidence, fact_evidence)
        
        # Step 4: Fall back to local rules-based engine if Groq is unconfigured/fails
        if final_result is None:
            print("Using local rules-based resolution engine...")
            final_result = combine_predictions(ml_result, news_evidence, fact_evidence)
        
        return jsonify({
            "status": "success",
            "prediction": ml_result["prediction"],
            "confidence": ml_result["confidence"],
            "model_a": ml_result.get("model_a"),
            "model_b": ml_result.get("model_b"),
            "verdict": final_result["verdict"],
            "status_lbl": final_result["status"],
            "reasoning": final_result["reasoning"],
            "has_conflict": final_result["has_conflict"],
            "news_evidence": news_evidence,
            "fact_evidence": fact_evidence
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/feedback', methods=['POST'])
def feedback():
    """Active Learning: Receives user correction (REAL or FAKE) and updates Model A parameters."""
    from feedback import record_feedback
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    text = data.get("text", "").strip()
    label = data.get("label", "").strip()

    if not text or not label:
        return jsonify({"status": "error", "message": "Missing text or label"}), 400

    res = record_feedback(text, label)

    # Reload classifier model weights
    global classifier
    try:
        classifier = FakeNewsClassifier()
    except Exception as e:
        print(f"Classifier reload warning: {e}")

    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
