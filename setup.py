import nltk
import os
from pathlib import Path

def download_nltk_data():
    # Download required NLTK data
    nltk_data = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet',
        'maxent_ne_chunker',
        'words'
    ]
    
    for package in nltk_data:
        try:
            nltk.data.find(f'tokenizers/{package}')
        except LookupError:
            print(f"Downloading NLTK package: {package}")
            nltk.download(package)

def create_required_directories():
    # Create .streamlit directory if it doesn't exist
    streamlit_dir = Path('.streamlit')
    if not streamlit_dir.exists():
        streamlit_dir.mkdir(parents=True)
        print("Created .streamlit directory")

def main():
    print("Running setup...")
    download_nltk_data()
    create_required_directories()
    print("Setup completed successfully!")

if __name__ == "__main__":
    main() 