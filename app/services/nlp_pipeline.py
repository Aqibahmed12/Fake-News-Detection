"""
NLP Preprocessing Pipeline
Cleans and extracts features from raw text before ML inference.
"""
import re
import string
import unicodedata
from typing import Dict, Any

# Ordered list of numeric feature names used in both training and inference
NUMERIC_FEATURE_NAMES = [
    "char_count", "word_count", "sentence_count", "avg_word_length",
    "avg_sentence_length", "exclamation_ratio", "question_ratio",
    "caps_word_ratio", "sentiment_compound", "sentiment_pos",
    "sentiment_neg", "sentiment_neu", "flesch_kincaid",
    "flesch_reading_ease", "entity_density", "entity_count",
    "sensational_word_count",
]

# Lazy imports so the module can load even if packages aren't installed yet
_spacy_nlp = None
_vader = None
_stop_words = None


def _get_spacy():
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            try:
                _spacy_nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Fall back to blank English model
                _spacy_nlp = spacy.blank("en")
        except ImportError:
            _spacy_nlp = None
    return _spacy_nlp


def _get_vader():
    global _vader
    if _vader is None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            _vader = SentimentIntensityAnalyzer()
        except ImportError:
            _vader = None
    return _vader


def _get_stop_words():
    global _stop_words
    if _stop_words is None:
        try:
            import nltk
            try:
                from nltk.corpus import stopwords
                _stop_words = set(stopwords.words("english"))
            except LookupError:
                nltk.download("stopwords", quiet=True)
                from nltk.corpus import stopwords
                _stop_words = set(stopwords.words("english"))
        except ImportError:
            _stop_words = set()
    return _stop_words


# ------------------------------------------------------------------
# Text cleaning helpers
# ------------------------------------------------------------------

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+|www\.\S+", " ", text)


def _normalise_unicode(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """Full text cleaning pipeline."""
    text = _strip_html(text)
    text = _strip_urls(text)
    text = _normalise_unicode(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.,!?;:']", " ", text)
    text = _clean_whitespace(text)
    return text


def lemmatise(text: str) -> str:
    """Tokenise, remove stop-words, and lemmatise using spaCy."""
    nlp = _get_spacy()
    stop_words = _get_stop_words()
    if nlp is None:
        # Fallback: simple split
        tokens = [w for w in text.split() if w not in stop_words and len(w) > 2]
        return " ".join(tokens)

    doc = nlp(text[:50_000])  # Limit for safety
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.lemma_) > 2
    ]
    return " ".join(tokens)


# ------------------------------------------------------------------
# Feature extraction
# ------------------------------------------------------------------

def extract_features(text: str) -> Dict[str, Any]:
    """
    Extract numeric features from raw text.
    Returns a dict of feature_name -> value.
    """
    features: Dict[str, Any] = {}
    cleaned = clean_text(text)
    words = cleaned.split()
    sentences = re.split(r"[.!?]+", text)

    # Basic stats
    features["char_count"] = len(text)
    features["word_count"] = len(words)
    features["sentence_count"] = max(len([s for s in sentences if s.strip()]), 1)
    features["avg_word_length"] = (
        sum(len(w) for w in words) / len(words) if words else 0
    )
    features["avg_sentence_length"] = (
        features["word_count"] / features["sentence_count"]
    )

    # Punctuation ratios
    exclamation = text.count("!")
    question = text.count("?")
    caps_words = len(re.findall(r"\b[A-Z]{2,}\b", text))
    features["exclamation_ratio"] = exclamation / max(len(words), 1)
    features["question_ratio"] = question / max(len(words), 1)
    features["caps_word_ratio"] = caps_words / max(len(words), 1)

    # Sentiment (VADER)
    vader = _get_vader()
    if vader:
        scores = vader.polarity_scores(text)
        features["sentiment_compound"] = scores["compound"]
        features["sentiment_pos"] = scores["pos"]
        features["sentiment_neg"] = scores["neg"]
        features["sentiment_neu"] = scores["neu"]
    else:
        features["sentiment_compound"] = 0.0
        features["sentiment_pos"] = 0.0
        features["sentiment_neg"] = 0.0
        features["sentiment_neu"] = 1.0

    # Readability
    try:
        import textstat
        features["flesch_kincaid"] = textstat.flesch_kincaid_grade(text)
        features["flesch_reading_ease"] = textstat.flesch_reading_ease(text)
    except Exception:
        features["flesch_kincaid"] = 0.0
        features["flesch_reading_ease"] = 50.0

    # Named entity density
    nlp = _get_spacy()
    if nlp:
        doc = nlp(text[:50_000])
        features["entity_density"] = len(doc.ents) / max(len(words), 1)
        features["entity_count"] = len(doc.ents)
    else:
        features["entity_density"] = 0.0
        features["entity_count"] = 0

    # Clickbait / sensational cues
    sensational_words = {
        "shocking", "unbelievable", "secret", "exposed", "breaking",
        "exclusive", "bombshell", "scandal", "hoax", "conspiracy",
        "cover-up", "miracle", "outrage", "fake", "fraud", "lie",
    }
    lower_words = set(w.lower().strip(string.punctuation) for w in words)
    features["sensational_word_count"] = len(lower_words & sensational_words)

    return features


def preprocess(text: str) -> Dict[str, Any]:
    """Full preprocessing: clean → lemmatise → extract features."""
    cleaned = clean_text(text)
    lemmatised = lemmatise(cleaned)
    numeric_features = extract_features(text)
    return {
        "cleaned_text": cleaned,
        "lemmatised_text": lemmatised,
        "numeric_features": numeric_features,
    }
