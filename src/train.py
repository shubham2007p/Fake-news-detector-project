import os
import sys
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Include src directory in python path
sys.path.append(os.path.dirname(__file__))
from preprocess import clean_text


def train_model():
    """
    Retrains Model A on an augmented, multi-domain dataset combining:
    1. news.csv (~6,300 full length articles)
    2. LIAR benchmark dataset (~12,800 short statement claims)
    Total: ~21,700 samples for robust, non-overfitted stylistic & statement classification.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_csv = os.path.join(base_dir, "data", "news.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "fake_news_model.pkl")
    vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")

    print("Loading Primary News Dataset (news.csv)...")
    if not os.path.exists(raw_csv):
        raise FileNotFoundError(f"Raw news data not found at {raw_csv}.")

    df1 = pd.read_csv(raw_csv)
    df1['combined_text'] = df1['title'].fillna('') + ' ' + df1['text'].fillna('')
    df1['clean'] = df1['combined_text'].apply(lambda t: clean_text(t, strip_meta=True))
    df1['label_encoded'] = df1['label'].map({'FAKE': 1, 'REAL': 0})
    ds1 = df1[['clean', 'label_encoded']]

    # Load Auxiliary LIAR Datasets
    liar_dir = os.path.join(os.path.dirname(base_dir), "Fake_News_Detection")
    liar_files = [
        os.path.join(liar_dir, "train.csv"),
        os.path.join(liar_dir, "test.csv"),
        os.path.join(liar_dir, "valid.csv"),
    ]

    liar_dfs = []
    for path in liar_files:
        if os.path.exists(path):
            print(f"Loading Auxiliary LIAR Dataset: {os.path.basename(path)}...")
            d = pd.read_csv(path)
            if 'Statement' in d.columns and 'Label' in d.columns:
                d['clean'] = d['Statement'].fillna('').apply(lambda t: clean_text(t, strip_meta=True))
                d['label_encoded'] = d['Label'].apply(
                    lambda l: 1 if str(l).strip().upper() in ['FALSE', '0'] else 0
                )
                liar_dfs.append(d[['clean', 'label_encoded']])

    if liar_dfs:
        df_liar = pd.concat(liar_dfs, ignore_index=True)
        df_all = pd.concat([ds1, df_liar], ignore_index=True)
    else:
        df_all = ds1

    # Filter out near-empty strings
    df_all = df_all[df_all['clean'].str.len() > 5].reset_index(drop=True)
    print(f"Total Combined Multi-Domain Corpus: {len(df_all)} samples")

    X = df_all['clean']
    y = df_all['label_encoded']

    # 80/20 train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set size: {len(X_train)} samples")
    print(f"Testing set size: {len(X_test)} samples")

    # Advanced TF-IDF Vectorization with sublinear_tf & ngrams (1, 2)
    print("Vectorizing text (TF-IDF sublinear scaling, ngrams (1,2), max_features=15000)...")
    vectorizer = TfidfVectorizer(
        stop_words='english',
        sublinear_tf=True,
        ngram_range=(1, 2),
        max_features=15000,
        min_df=2
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Regularized Balanced Logistic Regression
    print("Training Balanced Logistic Regression model...")
    model = LogisticRegression(
        C=0.5,
        class_weight='balanced',
        max_iter=1000,
        random_state=42
    )
    model.fit(X_train_vec, y_train)

    # Evaluation
    print("Evaluating model performance...")
    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy across 21.7k multi-domain samples: {acc * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['REAL', 'FAKE']))

    # Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['REAL', 'FAKE'], yticklabels=['REAL', 'FAKE'])
    plt.title('Confusion Matrix - Retrained Model A')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')

    plot_dir = os.path.join(base_dir, "static")
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, "confusion_matrix.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Confusion Matrix saved to: {plot_path}")

    # Save artifacts
    print(f"Saving Model A to {model_path}...")
    joblib.dump(model, model_path)

    print(f"Saving Vectorizer A to {vectorizer_path}...")
    joblib.dump(vectorizer, vectorizer_path)

    print("\nModel A Retraining successfully completed!")


if __name__ == "__main__":
    train_model()
