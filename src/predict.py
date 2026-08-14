import os
import joblib
from preprocess import clean_text

class FakeNewsClassifier:
    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
            
        self.model_path = os.path.join(model_dir, "fake_news_model.pkl")
        self.vectorizer_path = os.path.join(model_dir, "tfidf_vectorizer.pkl")
        
        self.model = None
        self.vectorizer = None
        self.load_model()
        
    def load_model(self):
        if not os.path.exists(self.model_path) or not os.path.exists(self.vectorizer_path):
            raise FileNotFoundError(
                "Model files are missing. Please run 'train.py' to generate the files."
            )
        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)
        
    def predict(self, title, text):
        # Combine title and text
        combined = f"{title} {text}"
        
        # Clean text
        clean = clean_text(combined)
        
        if not clean:
            return {
                "prediction": "INVALID INPUT",
                "confidence": 0.0,
                "label_code": -1
            }
            
        # Vectorize
        vectorized = self.vectorizer.transform([clean])
        
        # Predict probability
        probs = self.model.predict_proba(vectorized)[0]
        prediction_code = self.model.predict(vectorized)[0]
        
        # Label mapping (1 is FAKE, 0 is REAL)
        label = "FAKE" if prediction_code == 1 else "REAL"
        confidence = probs[prediction_code] * 100
        
        return {
            "prediction": label,
            "confidence": round(confidence, 2),
            "label_code": int(prediction_code)
        }

if __name__ == "__main__":
    # Quick test if model is present
    try:
        classifier = FakeNewsClassifier()
        result = classifier.predict("Breaking: Alien spaceship lands in Central Park", 
                                    "A giant metallic spacecraft has reportedly landed in New York today, causing massive panic.")
        print(f"Test prediction: {result}")
    except Exception as e:
        print(f"Classifier is not fully initialized yet (run train.py first): {e}")
