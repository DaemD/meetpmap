"""
Download required NLTK data for RAKE
"""
import nltk

print("Downloading NLTK stopwords...")
nltk.download('stopwords', quiet=False)

print("Downloading NLTK punkt...")
nltk.download('punkt', quiet=False)

print("✅ NLTK data downloaded successfully!")







