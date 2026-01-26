from typing import List, TypedDict
import nltk
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# --- Data Structure ---
class Segment(TypedDict):
    text: str
    lang: str

# --- NLTK Downloader ---
def download_nltk_data():
    """Checks for and downloads the 'punkt' tokenizer if not present."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK 'punkt' tokenizer...")
        nltk.download('punkt')
        print("'punkt' tokenizer downloaded.")

# --- Initialization ---
download_nltk_data()

# --- Core Service ---
def segment_text(text: str) -> List[Segment]:
    """
    Segments a given text into a list of single-language segments.

    Args:
        text: The input text string, potentially containing multiple languages.

    Returns:
        A list of Segment objects, where each segment contains text of a
        single, consistent language.
    """
    if not text or not text.strip():
        return []

    sentences = nltk.sent_tokenize(text)
    
    if not sentences:
        return []

    segments: List[Segment] = []
    current_segment_text = ""
    current_lang = None

    for sentence in sentences:
        try:
            lang = detect(sentence)
        except LangDetectException:
            # If language cannot be detected, assume it's the same as the current segment
            lang = current_lang if current_lang else 'en' # Default to english if no context

        if current_lang is None:
            # First sentence
            current_lang = lang
            current_segment_text = sentence
        elif lang == current_lang:
            # Language is the same, append sentence
            current_segment_text += " " + sentence
        else:
            # Language changed, finalize previous segment and start a new one
            if current_segment_text:
                segments.append({"text": current_segment_text.strip(), "lang": current_lang})
            
            current_lang = lang
            current_segment_text = sentence

    # Add the last running segment
    if current_segment_text:
        segments.append({"text": current_segment_text.strip(), "lang": current_lang})

    return segments
