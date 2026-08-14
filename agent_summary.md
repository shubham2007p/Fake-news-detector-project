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
  * `clean_text(text, strip_meta=True)`: Lowercases, strips HTML, URLs, punctuation, numbers, **and META_BLOCKLIST label-leakage words**.
  * `preprocess_dataset(input_csv, output_csv)`: Loads raw dataset, cleans and combines title + text, encodes labels, saves preprocessed file.
* **Constants**:
  * `META_BLOCKLIST`: Set of words/phrases that correlate directly with training labels but carry no real journalistic signal: `"fake"`, `"real"`, `"hoax"`, `"satire"`, `"debunked"`, `"misinformation"`, `"misleading"`, `"conspiracy"`, etc. Stripped at **both training and inference time** to prevent label-leakage bias.
  * `_BLOCKLIST_PATTERN`: Compiled regex that matches META_BLOCKLIST words as whole words.

### 3. `src/train.py`
* **Path**: [src/train.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/train.py)
* **Purpose**: Text classification model training pipeline.
* **Key Functions**:
  * `train_model()`: Runs `preprocess_dataset`, splits data (80/20 train/test), fits TF-IDF vectorizer, trains Logistic Regression model, plots confusion matrix, saves to `models/`.
* **Outputs**: `models/fake_news_model.pkl`, `models/tfidf_vectorizer.pkl`, `static/confusion_matrix.png`.

### 5. `src/predict.py`
* **Path**: [src/predict.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/predict.py)
* **Purpose**: Multi-aspect Ensemble Machine Learning inference.
* **Key Classes**:
  * `FakeNewsClassifier`:
    * `load_models()`: Loads **Model A** (`models/fake_news_model.pkl` + `tfidf_vectorizer.pkl`) and **Model B** (`models/liar_model.sav` with `sys.modules['sklearn.linear_model.logistic']` compatibility wrapper).
    * `predict(title, text)`:
      * **Model A (Stylistic Classifier)**: Evaluates article structure and writing style (92.3% accuracy).
      * **Model B (LIAR Statement Classifier)**: Evaluates headline & claim credibility against historical factual statement patterns.
      * **Weighted Combination**: Combines Model B LIAR statement classifier (75%) and Model A stylistics (25%) into a unified top-level prediction, prioritizing statement credibility over raw stylistic tone.
      * **Label Leakage Protection**: Strips `META_BLOCKLIST` artifacts before vectorization.

### 6. `src/web_search.py`
* **Path**: [src/web_search.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/web_search.py)
* **Purpose**: Fetches real-time search evidence and fact-checks. India-aware with 3-pass strategy.
* **Key Functions**:
  * `is_india_query(query)`: Detects India-related queries via 40+ keyword list.
  * `search_news_api(query, limit)`: 3-pass search — Pass 1: NewsAPI filtered to 13 Indian domains; Pass 2: global NewsAPI; Pass 3: direct RSS scrape.
  * `_call_newsapi(query, limit, extra_params)`: Internal NewsAPI helper.
  * `_search_india_rss(query, limit)`: Scrapes RSS from NDTV, The Hindu, HT, Indian Express, ToI, The Print, Scroll.
  * `search_google_factcheck(query)`: Google Fact Check API with Indian fact-checkers in tier system.
  * `get_source_tier(source_name)`: Tier 1 = PTI/IANS/PIB/Reuters/AP. Tier 2 = The Hindu/NDTV/HT/IE/ToI/Mint + AltNews/BOOM/Vishvas/Factly/Newschecker.
* **Constants**: `INDIA_SOURCES` dict (13 domains), `INDIA_RSS_FEEDS` list (7 feeds), `INDIA_KEYWORDS` (40+ terms).

### 7. `src/reasoner.py`
* **Path**: [src/reasoner.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/reasoner.py)
* **Purpose**: Decision engine implementing **The Uncertain Logic Gate** and conflict resolution.
* **Key Rules**:
  * **The Uncertain Logic Gate**: If a claim lacks cross-referenceable evidence on fact-checking repositories (FactCheck.org, AltNews, BOOM, PolitiFact) or official Tier 1/2 news portals (PTI, PIB, Reuters, AP, The Hindu, HT), the system outputs **`UNCERTAIN` / `Unverified (Low Confidence)`** rather than guessing.
  * **Fact-Check Override**: Fact-checking verdicts explicitly override model predictions.

### 8. `src/llm_reasoner.py`
* **Path**: [src/llm_reasoner.py](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/src/llm_reasoner.py)
* **Purpose**: Groq Llama-3 synthesis layer with **Uncertain Logic Gate & Scare-Word Neutralization**.
* **Key Features**:
  * Enforces the **Uncertain Logic Gate**: Returns `verdict: "UNCERTAIN"` and `status_label: "Unverified (Low Confidence)"` when external cross-referenceable evidence is missing.
  * Enforces **Scare-Word Neutralization**: Prevents panic keywords (`radiation`, `frozen`, `secret clause`, `bioweapon`, `chemtrails`) from triggering false positive `FAKE` verdicts without fact-check evidence.
* **Key Functions**:
  * `get_groq_reasoning(...)`: Builds prompt with optional India-context block (Tier 1/2 sources, Indian fact-checkers). Calls `llama-3.3-70b-versatile`.

---

## 📁 Frontend Assets & Presentation

### 1. `templates/index.html`
* **Path**: [templates/index.html](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/templates/index.html)
* **Purpose**: VeritasAI dashboard. Sidebar (history + model stats + clear history button), input panel (headline + body + sample pills), result panel (verdict hero with donut chart, status bar, AI reasoning, tabbed evidence). Light/dark mode toggle in topbar.

### 2. `static/css/style.css`
* **Path**: [static/css/style.css](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/static/css/style.css)
* **Purpose**: Premium obsidian & zinc monochrome design system with dark and light modes.
  * **Dark Theme Palette**: Pure obsidian & zinc black (`#09090b`, `#121215`, `#18181b`, `#27272a`) — completely free of purple tinting.
  * **Buttons in Dark Theme**: Primary action buttons are solid **white** with deep charcoal black text (`background: #ffffff; color: #09090b;`).
  * **Light Theme Palette**: Refined grayscale zinc off-white (`#f4f4f5`, `#ffffff`, `#e4e4e7`).
  * **Buttons in Light Theme**: Primary action buttons are solid **black/charcoal** with white text (`background: #18181b; color: #ffffff;`).
  * Smooth 0.35s CSS transitions across all cards, panels, inputs, and interactive components.

### 3. `static/js/main.js`
* **Path**: [static/js/main.js](file:///c:/Users/shubh/Downloads/IBM%20project/fake-news-detection/static/js/main.js)
* **Purpose**: Full frontend handler. localStorage search history (50 entries), dark/light theme toggle, animated SVG donut chart, 3-step loading sequence, tabbed evidence, toast notifications, Ctrl+Enter shortcut, sample pills, sidebar toggle, character counter.

---

## 📝 Change Log & Updates

### 2026-08-14 — Session 1
* LLM reasoning via Groq API (`llama-3.3-70b-versatile`).
* Config loader (`src/config.py`), NewsAPI + Google Fact Check integration.
* Local fallback rules engine. Flask app replacing Streamlit.

### 2026-08-14 — Session 2 (UI + India + Monochrome Theme)
* **Monochrome Theme System**: Overhauled color tokens to pure obsidian/zinc blacks (`#09090b`, `#121215`, `#18181b`), eliminating all purple/indigo tinting.
* **Dynamic Inverted Buttons**: Action buttons adapt seamlessly:
  * Dark Mode: White button (`#ffffff`) with black text (`#09090b`).
  * Light Mode: Black button (`#18181b`) with white text (`#ffffff`).
* **Light Mode**: `[data-theme="light"]` soft neutral gray (`#f4f4f5`) + sun/moon toggle + localStorage persistence.
* **Search History**: Sidebar history (localStorage, 50 entries) + Clear History.
* **India-Aware Search**: 3-pass NewsAPI strategy, 13-domain Indian registry, RSS scraping of 7 outlets, expanded tier classifier with Indian fact-checkers.
* **India-Aware LLM**: Injects Indian source hierarchy and fact-checker names into system prompt when `is_india_query()` is True.

### 2026-08-14 — Session 2 (UI + India)
* **Premium UI**: VeritasAI dark design system, donut chart, verdict hero, tabbed evidence, loading sequence.
* **Light Mode**: `[data-theme="light"]` CSS + moon/sun toggle + localStorage persistence.
* **Search History**: Sidebar history (localStorage, 50 entries) + Clear History.
* **India-Aware Search**: 3-pass NewsAPI strategy, 13-domain Indian registry, RSS scraping of 7 outlets, expanded tier classifier with Indian fact-checkers (AltNews, BOOM, Vishvas, Factly, Newschecker).
* **India-Aware LLM**: Injects Indian source hierarchy and fact-checker names into system prompt when `is_india_query()` is True.


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
* **Key Features**:
  * Stepped loading sequence UI animation with simulated step intervals.
  * Markdown-to-HTML formatter with custom bold, code, and highlight tag rendering.
  * Theme toggle persistence via `localStorage`.
  * Keyboard Shortcuts: Pressing `Enter` in the headline input or `Ctrl+Enter` / `Cmd+Enter` in the body textarea instantly submits for analysis.

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

