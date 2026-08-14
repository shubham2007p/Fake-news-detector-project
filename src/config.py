import os

def load_dotenv():
    """
    Manually load .env file variables to avoid installing python-dotenv.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Auto load environment on import
load_dotenv()
