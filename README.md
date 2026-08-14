# Fake News Detection Using Machine Learning

An end-to-end Machine Learning and Natural Language Processing (NLP) system designed to detect and classify fake news articles and headlines with high accuracy. 

Built using a classical, explainable machine learning pipeline (TF-IDF + Logistic Regression) and featuring a web interface powered by Streamlit.

---

## 📐 System Architecture

```text
                    ┌──────────────────┐
                    │   News Article   │
                    │  / Headline Input│
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │  Text Cleaning   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │   TF-IDF         │
                    │  Vectorization   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Logistic         │
                    │ Regression Model  │
                    └────────┬─────────┘
                             ↓
                  ┌──────────┴──────────┐
                  ↓                     ↓
             🟢 REAL                 🔴 FAKE
```

### Key Components:
1. **Linguistic Preprocessing:** Lowercasing, removing HTML tags, URLs, numbers, punctuation, and extra spaces.
2. **Feature Extraction (TF-IDF):** Transforms unstructured news text into numerical feature vectors based on word frequencies weighted by corpus-wide importance.
3. **Classification Model:** A Logistic Regression model trained to identify word combination patterns associated with credible journalism (REAL) versus fake news/misinformation (FAKE).
4. **Interactive Dashboard:** Streamlit UI to test real-world headlines/articles in real-time.

---

## 📂 Project Structure

```text
fake-news-detection/
│
├── data/
│   ├── news.csv              # Raw dataset containing articles & labels
│   └── clean_news.csv        # Preprocessed data used for training
│
├── models/
│   ├── fake_news_model.pkl   # Trained Logistic Regression classifier
│   └── tfidf_vectorizer.pkl  # Saved TF-IDF vectorizer parameters
│
├── static/
│   └── confusion_matrix.png  # Heatmap visualization of model evaluations
│
├── src/
│   ├── __init__.py           # Package indicator
│   ├── preprocess.py         # Text cleaning and dataset preprocessing scripts
│   ├── train.py              # Model training, evaluation, and saving scripts
│   └── predict.py            # Object-oriented classification wrapper for inference
│
├── app.py                    # Streamlit interactive web application
├── download_data.py          # Script to fetch Lutz Hamel's dataset automatically
├── requirements.txt          # Python dependency checklist
├── .gitignore                # Folder exclusions for version control
└── README.md                 # Project documentation
```

---

## ⚡ Quick Start & Installation

### 1. Set Up Environment & Install Dependencies
First, set up a virtual environment and install the required libraries:
```bash
# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment (Windows PowerShell)
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Download the Dataset
Automatically download the dataset (~6300 labeled articles) by running:
```bash
python download_data.py
```

### 3. Preprocess Data & Train the Model
Run the training pipeline to preprocess, train the classifier, and save artifacts:
```bash
python src/train.py
```
This will:
* Clean the data
* Fit the TF-IDF vectorizer and train the Logistic Regression classifier
* Output validation metrics (Accuracy, Precision, Recall, F1)
* Save model artifacts under `models/`
* Save a confusion matrix plot under `static/`

### 4. Launch the Streamlit App
Run the local server to interact with the model:
```bash
streamlit run app.py
```

---

## 📈 Model Performance & Evaluation

The system is evaluated on a 20% holdout test set with stratification:

* **Accuracy:** ~91.8%
* **Precision (FAKE):** ~91%
* **Recall (FAKE):** ~93%
* **F1-Score:** ~92%

The confusion matrix visualization is automatically saved to `static/confusion_matrix.png` after running `train.py`.
