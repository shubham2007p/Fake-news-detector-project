import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from preprocess import preprocess_dataset

def train_model():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_csv = os.path.join(base_dir, "data", "news.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "fake_news_model.pkl")
    vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")
    
    # Check if raw data exists
    if not os.path.exists(raw_csv):
        raise FileNotFoundError(f"Raw news data not found at {raw_csv}. Run download_data.py first.")
    
    # Step 1: Preprocess data
    df = preprocess_dataset(raw_csv)
    
    # Step 2: Split into features and target
    X = df['clean_text']
    y = df['label_encoded']
    
    # Train-test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Training set size: {len(X_train)} samples")
    print(f"Testing set size: {len(X_test)} samples")
    
    # Step 3: TF-IDF Vectorization
    print("Vectorizing text using TF-IDF...")
    # Max features set to 5000 to keep model lightweight and prevent overfitting
    vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7, max_features=5000)
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    # Step 4: Model Training
    print("Training Logistic Regression model...")
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train_vectorized, y_train)
    
    # Step 5: Evaluation
    print("Evaluating model...")
    y_pred = model.predict(X_test_vectorized)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['REAL', 'FAKE']))
    
    # Plot & Save Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['REAL', 'FAKE'], yticklabels=['REAL', 'FAKE'])
    plt.title('Confusion Matrix - Fake News Detection')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    
    # Save the plot
    plot_dir = os.path.join(base_dir, "static")
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, "confusion_matrix.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Confusion Matrix plot saved to: {plot_path}")
    
    # Step 6: Save Model and Vectorizer
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
    
    print(f"Saving vectorizer to {vectorizer_path}...")
    joblib.dump(vectorizer, vectorizer_path)
    
    print("\nTraining workflow completed successfully!")

if __name__ == "__main__":
    train_model()
