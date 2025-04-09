import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured properly. Check your .env file.")
        
    # Pricing (per 1M tokens) - For utils.py
    INPUT_PRICE = 1.10
    CACHED_INPUT_PRICE = 0.55
    OUTPUT_PRICE = 4.40

    # Pricing for tools_api.py (GPT-4o per token)
    GPT4O_INPUT_PRICE_PER_TOKEN = 2.50 / 1_000_000
    GPT4O_CACHED_INPUT_PRICE_PER_TOKEN = 1.25 / 1_000_000
    GPT4O_OUTPUT_PRICE_PER_TOKEN = 10.00 / 1_000_000 