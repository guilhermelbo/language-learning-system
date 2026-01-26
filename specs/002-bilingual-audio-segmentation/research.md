# Research: Bilingual Text Segmentation

**Date**: 2026-01-25
**Author**: Gemini

## 1. Objective

To identify an effective and efficient method for segmenting a single string of text containing multiple languages (specifically Portuguese and English) into distinct, single-language segments. This is a prerequisite for generating language-specific Text-to-Speech (TTS) audio.

## 2. Key Requirements

- **Accuracy**: Must reliably detect language changes between sentences and, if possible, within sentences.
- **Performance**: The detection and segmentation process should not introduce significant latency to the API response.
- **Simplicity**: The chosen library should be easy to integrate into the existing Python/FastAPI backend with minimal dependencies.

## 3. Candidate Libraries for Language Detection

Several Python libraries were evaluated for language detection.

| Library | Pros | Cons |
| :--- | :--- | :--- |
| **`langdetect`** | - Simple, intuitive API.<br>- Pure Python, no complex dependencies.<br>- Widely used and well-documented. | - Non-deterministic results.<br>- Can be inaccurate on very short or ambiguous text. |
| **`pycld2`** | - Very fast and reliable.<br>- Provides confidence scores.<br>- Maintained by Google. | - Requires C++ compiler for installation (dependency on Compact Language Detector 2). |
| **`fasttext`** | - Highly accurate (state-of-the-art).<br>- Supports a vast number of languages. | - Requires downloading large pre-trained models (e.g., ~1GB).<br>- Can be overkill for this use case. |
| **`spacy-langdetect`** | - Integrates smoothly with the spaCy NLP framework. | - Adds a dependency on spaCy, which might be unnecessary if not already in use. |

## 4. Proposed Segmentation Strategy

A robust strategy involves combining sentence tokenization with language detection.

1.  **Sentence Tokenization**: First, split the input text into a list of sentences. The `nltk` library (`nltk.sent_tokenize`) is the industry standard for this and is highly accurate.
2.  **Iterative Language Detection**: Iterate through the tokenized sentences.
    - Detect the language of the current sentence.
    - If the detected language is the same as the previous sentence, append the text to the current segment.
    - If the detected language is different, close the previous segment and start a new one with the new language.
3.  **Handling Edge Cases**: For very short or ambiguous sentences where detection might fail, the system can default to the language of the previous segment.

## 5. Decision and Rationale

**Decision**: Use the **`langdetect`** library for the initial implementation, combined with sentence tokenization via **`nltk`**.

**Rationale**:

- **Good Starting Point**: `langdetect` provides the best balance of simplicity and "good enough" accuracy for a first iteration. Its ease of installation and use allows for rapid prototyping and validation of the core feature.
- **Mitigating Cons**: The primary drawback of `langdetect` (inaccuracy on short text) is mitigated by our strategy of detecting language on a per-sentence basis rather than per-word.
- **Future-Proofing**: The segmentation logic will be abstracted. If `langdetect` proves insufficient in production, it can be swapped with a more robust alternative like `pycld2` or `fasttext` with minimal changes to the overall application logic.

**Next Steps**: Add `langdetect` and `nltk` to the backend's `requirements.txt`.
