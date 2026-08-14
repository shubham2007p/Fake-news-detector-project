import re
import string
import pandas as pd

def clean_text(text):
    """
    Cleans raw text data: lowercases, removes HTML, punctuation, special chars, and extra whitespace.
    """
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove HTML tags if any
    text = re.sub(r'<.*?>', '', text)
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove numbers and special characters
    text = re.sub(r'\d+', '', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_dataset(input_csv, output_csv=None):
    """
    Loads dataset, cleans the title and text, combines them, and maps labels.
    """
    print(f"Loading raw data from: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Ensure necessary columns exist
    if 'text' not in df.columns or 'label' not in df.columns:
        raise ValueError("Dataset must contain 'text' and 'label' columns.")
    
    # Fill missing values
    df['title'] = df['title'].fillna("")
    df['text'] = df['text'].fillna("")
    
    # Combine title and text for rich features
    print("Combining title and text...")
    df['combined_text'] = df['title'] + " " + df['text']
    
    # Clean the combined text
    print("Cleaning text (lowercasing, removing punctuation/URLs/numbers)...")
    df['clean_text'] = df['combined_text'].apply(clean_text)
    
    # Filter out empty rows after cleaning
    df = df[df['clean_text'] != ""]
    
    # Encode labels (1 for FAKE, 0 for REAL)
    print("Encoding labels...")
    df['label_encoded'] = df['label'].map({'FAKE': 1, 'REAL': 0})
    
    # Save preprocessed file if output path is provided
    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"Preprocessed data saved to: {output_csv}")
        
    return df

if __name__ == "__main__":
    import os
    # Local test
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_path = os.path.join(base_dir, "data", "news.csv")
    cleaned_path = os.path.join(base_dir, "data", "clean_news.csv")
    if os.path.exists(raw_path):
        preprocess_dataset(raw_path, cleaned_path)
    else:
        print(f"Raw data file not found at: {raw_path}")
