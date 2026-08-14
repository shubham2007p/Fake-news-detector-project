import os
import requests
import urllib.parse

# Simple API Configuration
# In a real environment, users can set these as environment variables
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
GOOGLE_FACTCHECK_API_KEY = os.environ.get("GOOGLE_FACTCHECK_API_KEY", "")

def search_news_api(query, limit=5):
    """
    Queries newsapi.org for recent news articles matching the query.
    Returns a list of structured article dicts.
    """
    if not NEWS_API_KEY:
        print("DEBUG: News API Key not configured. Returning mock/empty news results.")
        return get_mock_news(query)
        
    try:
        # Encode query
        encoded_query = urllib.parse.quote(query)
        url = f"https://newsapi.org/v2/everything?q={encoded_query}&sortBy=relevance&pageSize={limit}&apiKey={NEWS_API_KEY}"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            results = []
            for art in articles[:limit]:
                source_name = art.get("source", {}).get("name", "Unknown Source")
                results.append({
                    "source": source_name,
                    "title": art.get("title", ""),
                    "description": art.get("description", ""),
                    "url": art.get("url", ""),
                    "published_at": art.get("publishedAt", "")[:10] if art.get("publishedAt") else "N/A",
                    "tier": get_source_tier(source_name)
                })
            return results
        else:
            print(f"News API Error: Status {response.status_code} - {response.text}")
            return get_mock_news(query)
    except Exception as e:
        print(f"Exception during News API query: {e}")
        return get_mock_news(query)

def search_google_factcheck(query):
    """
    Queries Google Fact Check Tools API for existing fact checks.
    Returns a list of structured fact check dicts.
    """
    if not GOOGLE_FACTCHECK_API_KEY:
        print("DEBUG: Google Fact Check API Key not configured. Returning mock/empty fact checks.")
        return get_mock_fact_checks(query)
        
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={encoded_query}&key={GOOGLE_FACTCHECK_API_KEY}"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            results = []
            for claim in claims[:5]:
                claim_text = claim.get("text", "")
                claimant = claim.get("claimant", "Unknown")
                claim_date = claim.get("claimDate", "")[:10] if claim.get("claimDate") else "N/A"
                
                # Fetch reviews
                reviews = claim.get("claimReview", [])
                for rev in reviews:
                    publisher = rev.get("publisher", {}).get("name", "Unknown Fact Checker")
                    results.append({
                        "claimant": claimant,
                        "claim_text": claim_text,
                        "claim_date": claim_date,
                        "publisher": publisher,
                        "verdict": rev.get("textualRating", "Unrated"),
                        "review_url": rev.get("url", ""),
                        "tier": get_source_tier(publisher)
                    })
            return results
        else:
            print(f"Fact Check API Error: Status {response.status_code} - {response.text}")
            return get_mock_fact_checks(query)
    except Exception as e:
        print(f"Exception during Fact Check API query: {e}")
        return get_mock_fact_checks(query)

def get_source_tier(source_name):
    """
    Evaluates source name and returns Tier 1, Tier 2, or Tier 3.
    """
    s = source_name.lower()
    
    tier_1 = ["reuters", "associated press", "ap news", "bbc", "gov", "official", "who", "cdc", "pib"]
    tier_2 = ["nytimes", "new york times", "republic", "times of india", "ndtv", "indian express", "hindustan times", "the hindu"]
    
    for term in tier_1:
        if term in s:
            return "Tier 1 (High Reliability)"
            
    for term in tier_2:
        if term in s:
            return "Tier 2 (Medium Reliability)"
            
    return "Tier 3 (Standard)"

def get_mock_news(query):
    """
    Mock news database fallback to ensure visual interface works without active keys.
    """
    mock_db = {
        "federal reserve": [
            {
                "source": "Reuters",
                "title": "Federal Reserve Holds Interest Rates Steady, Citing Economic Progress",
                "description": "The Federal Reserve kept interest rates steady on Wednesday, noting inflation is moderating.",
                "url": "https://www.reuters.com/business/finance/fed-holds-rates",
                "published_at": "2026-08-12",
                "tier": "Tier 1 (High Reliability)"
            },
            {
                "source": "BBC News",
                "title": "US Central Bank keeps rates unchanged at close of meeting",
                "description": "The Federal Reserve chose to maintain current rates, citing progress toward its target inflation rate.",
                "url": "https://www.bbc.com/news/business-fed-rates",
                "published_at": "2026-08-12",
                "tier": "Tier 1 (High Reliability)"
            }
        ]
    }
    
    q = query.lower()
    for key, val in mock_db.items():
        if key in q:
            return val
            
    return []

def get_mock_fact_checks(query):
    """
    Mock fact checker data fallback.
    """
    mock_db = {
        "alien": [
            {
                "claimant": "Social Media Posts",
                "claim_text": "Secret military lab reverse engineered alien tech to cure aging.",
                "claim_date": "2026-08-10",
                "publisher": "PolitiFact",
                "verdict": "False / Pants on Fire",
                "review_url": "https://www.politifact.com/factcheck/alien-tech-aging",
                "tier": "Tier 1 (High Reliability)"
            }
        ],
        "space": [
            {
                "claimant": "Social Media Posts",
                "claim_text": "Secret military lab reverse engineered alien tech to cure aging.",
                "claim_date": "2026-08-10",
                "publisher": "PolitiFact",
                "verdict": "False",
                "review_url": "https://www.politifact.com/factcheck/alien-tech-aging",
                "tier": "Tier 1 (High Reliability)"
            }
        ]
    }
    
    q = query.lower()
    for key, val in mock_db.items():
        if key in q:
            return val
            
    return []
