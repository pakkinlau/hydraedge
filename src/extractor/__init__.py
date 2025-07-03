# src/extractor/__init__.py

from sentence_transformers import SentenceTransformer

# load once at import time
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract(text: str):
    """
    Turn a string into a fixed-size numpy array embedding.
    """
    # SentenceTransformer.encode returns a numpy.ndarray
    return embedding_model.encode(text)