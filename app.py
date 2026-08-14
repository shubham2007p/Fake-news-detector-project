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
            "verdict": final_result["verdict"],
            "status_lbl": final_result["status"],
            "reasoning": final_result["reasoning"],
            "has_conflict": final_result["has_conflict"],
            "news_evidence": news_evidence,
            "fact_evidence": fact_evidence
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
