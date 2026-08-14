# Agent Project Summary & File Map

This document serves as a complete project map and directory registry for the **Fake News Detection** application. It details the purpose, main functions, classes, and dependencies of every key file in the codebase. 

---

## 📁 Directory Structure & File Map

```
fake-news-detection/
├── .env
├── requirements.txt
├── download_data.py
├── app.py
├── README.md
├── agent_summary.md (This file)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── preprocess.py
│   ├── train.py
│   ├── predict.py
│   ├── web_search.py
│   ├── reasoner.py
│   └── llm_reasoner.py
├── templates/
│   └── index.html
└── static/
    ├── confusion_matrix.png
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

---

## 📄 Root Files

### 1. `app.py`
* **Path**: [app.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/app.py)
* **Purpose**: The main Flask application entrypoint containing the backend route definitions.
* **Key Functions/Endpoints**:
  * `home()` (`GET /`): Renders the main dashboard (`templates/index.html`).
  * `predict()` (`POST /predict`): The primary orchestrator. Receives input title/text, runs the local ML model (`FakeNewsClassifier`), performs external API searches, calls Groq LLM reasoning (falls back to local rules-based engine on failure), and returns the final verdict payload.
* **Dependencies**: `src/predict.py`, `src/web_search.py`, `src/reasoner.py`, `src/llm_reasoner.py`, `Flask`.

### 2. `download_data.py`
* **Path**: [download_data.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/download_data.py)
* **Purpose**: Downloads the raw training dataset from GitHub and saves it locally.
* **Key Functions**:
  * `download_dataset()`: Streams and downloads `fake_or_real_news.csv` into `data/news.csv`.
* **Dependencies**: `requests`, `os`.

### 3. `.env`
* **Path**: [.env](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/.env)
* **Purpose**: Contains local API secrets (`GROQ_API_KEY`, optional `NEWS_API_KEY` and `GOOGLE_FACTCHECK_API_KEY`).
* **Dependencies**: Loaded automatically on startup by `src/config.py`.

### 4. `requirements.txt`
* **Path**: [requirements.txt](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/requirements.txt)
* **Purpose**: Python package dependencies.
* **Packages**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `Flask`, `joblib`, `requests`.

---

## 📁 Source Code (`src/`)

### 1. `src/config.py`
* **Path**: [src/config.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/config.py)
* **Purpose**: Dynamically loads environment variables from the `.env` file without needing an external package dependency like `python-dotenv`.
* **Key Functions**:
  * `load_dotenv()`: Parses the key-value pairs in `.env` and assigns them to `os.environ`.

### 2. `src/preprocess.py`
* **Path**: [src/preprocess.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/preprocess.py)
* **Purpose**: Text cleaning and dataset preprocessing.
* **Key Functions**:
  * `clean_text(text)`: Lowercases, strips HTML tags, removes URLs, punctuation, numbers, and trims extra spaces.
  * `preprocess_dataset(input_csv, output_csv)`: Loads raw dataset, cleans and combines title + text, encodes labels (`1` for FAKE, `0` for REAL), and saves preprocessed file.

### 3. `src/train.py`
* **Path**: [src/train.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/train.py)
* **Purpose**: Text classification model training pipeline.
* **Key Functions**:
  * `train_model()`: Runs `preprocess_dataset`, splits data (80/20 train/test), fits a TF-IDF vectorizer, trains a Logistic Regression model, plots the confusion matrix, and saves serialization files to `models/`.
* **Outputs**: `models/fake_news_model.pkl`, `models/tfidf_vectorizer.pkl`, and `static/confusion_matrix.png`.

### 5. `src/predict.py`
* **Path**: [src/predict.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/predict.py)
* **Purpose**: Exposes inference utilities utilizing the pre-trained ML model.
* **Key Classes**:
  * `FakeNewsClassifier`: Encapsulates the joblib loading mechanism and text classification pipeline.
    * `load_model()`: Reads the pickle binary files.
    * `predict(title, text)`: Sanitizes input, applies the TF-IDF transform, gets prediction probabilities, and returns output dictionary with `prediction` label and `confidence`.

### 6. `src/web_search.py`
* **Path**: [src/web_search.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/web_search.py)
* **Purpose**: Fetches real-time search evidence and existing fact-checks.
* **Key Functions**:
  * `search_news_api(query)`: Searches NewsAPI for matching stories; falls back to mock news database if API key is missing.
  * `search_google_factcheck(query)`: Queries Google Fact Check API for matching reviews; falls back to mock database if API key is missing.
  * `get_source_tier(source_name)`: Classifies sources into reliability Tiers (Tier 1 = High, Tier 2 = Medium, Tier 3 = Standard).

### 7. `src/reasoner.py`
* **Path**: [src/reasoner.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/reasoner.py)
* **Purpose**: Local rules-based decision resolver. Used as fallback when the advanced Groq API is not configured or fails.
* **Key Functions**:
  * `combine_predictions(ml_res, news_evidence, fact_evidence)`: Combines ML prediction code with the quantity/reliability of external sources to arrive at final status (e.g. `Contradicted (Likely Fake)`, `Verified Real`).

### 8. `src/llm_reasoner.py`
* **Path**: [src/llm_reasoner.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/llm_reasoner.py)
* **Purpose**: Advanced consensus resolver calling Groq API.
* **Key Functions**:
  * `get_groq_reasoning(title, text, ml_res, news_evidence, fact_evidence)`: Forms prompt incorporating user news content, ML verdict, and web evidence. Requests JSON response from `llama-3.3-70b-versatile` containing the verdict, a professional status label, and a detailed markdown explanation.

---

## 📁 Frontend Assets & Presentation

### 1. `templates/index.html`
* **Path**: [templates/index.html](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/templates/index.html)
* **Purpose**: Dashboard HTML structure. Contains input forms, interactive visual elements for displaying the hybrid status, and grids mapping external evidence metadata.

### 2. `static/css/style.css`
* **Path**: [static/css/style.css](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/static/css/style.css)
* **Purpose**: Styles the dashboard using a sleek, dark layout with neon borders, custom card layouts, responsive layouts, and animations. Also defines custom formatting styles like `.highlight-text` for LLM reasoning indicators.

### 3. `static/js/main.js`
* **Path**: [static/js/main.js](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/static/js/main.js)
* **Purpose**: Front-end interactive handler. Handles AJAX submit actions, loading animations, and renders verdict descriptions dynamically. Converts markdown formatting (`**`, `++`, `` ` ``) in LLM-sourced descriptions into matching HTML tags (`<strong>`, `<span class="highlight-text">`, `<code>`) on load.

---

## 📝 Change Log & Updates

### 2026-08-14 (Antigravity Agent)
* **LLM Reasoning Layer**: Created `src/llm_reasoner.py` and integrated Groq API (`llama-3.3-70b-versatile`) to verify claims against search findings.
* **Environment Configuration**: Added `src/config.py` to parse the `.env` configuration file locally for secrets.
* **Web search API integrations**: Created `src/web_search.py` implementing endpoints for News API & Google Fact Check Tools API.
* **Fallback mechanism**: Added robust fallback logic in `app.py` to ensure local rules-based validation runs if external APIs fail or are unconfigured.
* **UI/UX Refactoring**: Discarded Streamlit, replacing it with a Flask app featuring a custom dashboard displaying news references and fact-checks.

