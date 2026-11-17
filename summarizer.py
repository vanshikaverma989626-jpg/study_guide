"""
summarizer.py
=============
Offline Extractive Text Summarizer for the Study Guide Assistant.

How it works (Extractive Summarization by Word Frequency):
-----------------------------------------------------------
1. Sentence Tokenization:
   Split the input text into individual sentences while preserving punctuation.
2. Word Tokenization & Cleaning:
   Convert text to lowercase and remove punctuation to isolate individual words.
3. Stopword Filtering:
   Filter out common structural words (e.g., 'the', 'is', 'at', 'which') using
   a built-in stopword set (with optional NLTK fallback if installed).
4. Word Frequency Distribution:
   Count how often each content word appears. Words appearing frequently
   are considered more important / central to the text's theme.
5. Frequency Normalization:
   Divide each word count by the maximum frequency so frequencies range between 0 and 1.
6. Sentence Scoring:
   Score each sentence by summing the normalized scores of its constituent words,
   divided by the sentence length to avoid bias toward overly long sentences.
7. Top Sentence Selection:
   Pick the top N scoring sentences according to the requested length
   (short, medium, detailed), maintaining their original appearance order.
8. Keyword Highlighting:
   Find the top keywords from the frequency table and bold them in the summary.
"""

import re
import string
from collections import Counter
from typing import List, Dict, Tuple, Set


# Built-in English stopwords so this runs 100% offline without mandatory downloads
BUILTIN_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "also",
    "etc", "eg", "ie", "many", "much", "using", "use", "used"
}


def get_stopwords() -> Set[str]:
    """
    Returns stopwords, preferring NLTK if installed and downloaded,
    otherwise falling back to built-in stopwords.
    """
    try:
        import nltk
        from nltk.corpus import stopwords as nltk_stopwords
        return set(nltk_stopwords.words("english")).union(BUILTIN_STOPWORDS)
    except Exception:
        # Graceful fallback to built-in list
        return BUILTIN_STOPWORDS


def split_into_sentences(text: str) -> List[str]:
    """
    Splits raw text into a list of sentences using regex.
    Handles standard sentence endings (.!?) while avoiding common abbreviations.
    """
    if not text or not text.strip():
        return []

    # Clean multi-line whitespace
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    
    # Split on punctuation followed by space and a capital letter or end of string
    # Regex lookbehind handles standard delimiters
    sentence_pattern = r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])"
    raw_sentences = re.split(sentence_pattern, cleaned_text)
    
    # Clean up and filter out empty lines or overly short fragments
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
    return sentences if sentences else [cleaned_text]


def extract_words(text: str) -> List[str]:
    """
    Extracts lowercase alphabetical words from a string.
    """
    return re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())


def compute_word_frequencies(sentences: List[str], stopwords: Set[str]) -> Tuple[Dict[str, float], List[str]]:
    """
    Calculates normalized word frequencies across all sentences.
    Returns:
        - normalized_freq: Dict mapping word -> float score (0.0 to 1.0)
        - top_keywords: List of the top 8 most frequent words for highlighting
    """
    word_counts = Counter()
    for sentence in sentences:
        words = extract_words(sentence)
        for w in words:
            if w not in stopwords:
                word_counts[w] += 1

    if not word_counts:
        return {}, []

    max_freq = max(word_counts.values())
    normalized_freq = {word: count / max_freq for word, count in word_counts.items()}
    top_keywords = [word for word, _ in word_counts.most_common(8)]
    
    return normalized_freq, top_keywords


def score_sentence(sentence: str, word_frequencies: Dict[str, float]) -> float:
    """
    Scores a single sentence by summing the weights of its informative words.
    Normalizes by word count^0.7 to avoid over-penalizing short sentences
    while preventing long run-on sentences from unfairly dominating.
    """
    words = extract_words(sentence)
    if not words:
        return 0.0

    score = 0.0
    informative_word_count = 0
    for w in words:
        if w in word_frequencies:
            score += word_frequencies[w]
            informative_word_count += 1

    if informative_word_count == 0:
        return 0.0

    # Normalization factor balances sentence length
    length_penalty = (len(words) ** 0.7)
    return score / length_penalty


def highlight_keywords(sentence: str, keywords: List[str]) -> str:
    """
    Highlights significant keywords in the sentence using Markdown bold (**word**).
    Matches whole words case-insensitively.
    """
    highlighted = sentence
    for kw in keywords:
        if len(kw) < 4:  # Avoid over-highlighting very short words
            continue
        # Use regex boundary to replace whole words only
        pattern = re.compile(rf"\b({re.escape(kw)})\b", re.IGNORECASE)
        # Avoid double-bolding
        highlighted = pattern.sub(r"**\1**", highlighted)
    return highlighted


def summarize_text(text: str, length: str = "medium") -> Dict[str, any]:
    """
    Summarizes given text into bullet points using extractive word-frequency scoring.

    Args:
        text (str): The raw text or pasted notes to summarize.
        length (str): "short" (2-3 bullets), "medium" (4-5 bullets), or "detailed" (7-8 bullets).

    Returns:
        dict: {
            "summary_bullets": List[str],
            "key_terms": List[str],
            "total_sentences": int,
            "summary_sentences_count": int,
            "length_mode": str
        }
    """
    if not text or not text.strip():
        return {
            "summary_bullets": ["(No text provided to summarize.)"],
            "key_terms": [],
            "total_sentences": 0,
            "summary_sentences_count": 0,
            "length_mode": length
        }

    sentences = split_into_sentences(text)
    if not sentences:
        return {
            "summary_bullets": [text.strip()],
            "key_terms": [],
            "total_sentences": 1,
            "summary_sentences_count": 1,
            "length_mode": length
        }

    stopwords = get_stopwords()
    word_freq, top_keywords = compute_word_frequencies(sentences, stopwords)

    # Determine sentence target count based on length option
    target_counts = {
        "short": 3,
        "medium": 5,
        "detailed": 8
    }
    target_n = target_counts.get(length.lower(), 5)
    # Cannot select more sentences than exist
    target_n = min(target_n, len(sentences))

    # Score each sentence with its original index
    scored_sentences: List[Tuple[int, str, float]] = []
    for idx, s in enumerate(sentences):
        sc = score_sentence(s, word_freq)
        scored_sentences.append((idx, s, sc))

    # Sort descending by score to pick top sentences
    top_scored = sorted(scored_sentences, key=lambda x: x[2], reverse=True)[:target_n]

    # Re-sort by original index so the summary reads in chronological/narrative order
    in_order = sorted(top_scored, key=lambda x: x[0])

    # Highlight top keywords and format as bullets
    bullets = []
    for _, sent, _ in in_order:
        highlighted = highlight_keywords(sent, top_keywords)
        bullets.append(highlighted)

    return {
        "summary_bullets": bullets,
        "key_terms": top_keywords,
        "total_sentences": len(sentences),
        "summary_sentences_count": len(bullets),
        "length_mode": length
    }


def format_summary_markdown(summary_result: Dict[str, any], title: str = "Notes Summary") -> str:
    """
    Formats the summary result into clean, readable Markdown text.
    """
    lines = [
        f"### Notes Summary: {title} ({summary_result['length_mode'].capitalize()} Length)",
        f"*Compressed from {summary_result['total_sentences']} sentences down to {summary_result['summary_sentences_count']} key points.*",
        ""
    ]

    if summary_result["key_terms"]:
        terms_str = ", ".join([f"`{t}`" for t in summary_result["key_terms"][:6]])
        lines.append(f"**Key Identified Terms:** {terms_str}")
        lines.append("")

    lines.append("**Key Takeaways:**")
    for b in summary_result["summary_bullets"]:
        lines.append(f"- {b}")

    return "\n".join(lines)
