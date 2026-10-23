import math
import re
from collections import Counter
from typing import Any


def extract_linguistic_features(text: str) -> dict[str, Any]:
    """Extract deterministic, explainable linguistic and statistical features from text.

    Computes:
    - Character and word counts
    - Sentence structure metrics (sentence count, average sentence length)
    - Burstiness (coefficient of variation of sentence lengths)
    - Lexical diversity (Type-Token Ratio - TTR)
    - Repeated n-gram ratio (3-gram repetition)
    - Unigram Shannon token entropy
    """
    clean_text = text.strip()
    char_count = len(clean_text)

    # Word extraction (alphanumeric sequences)
    words = [w.lower() for w in re.findall(r"\b[\w'-]+\b", clean_text)]
    word_count = len(words)

    if word_count == 0:
        return {
            "char_count": char_count,
            "word_count": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0.0,
            "burstiness_score": 0.0,
            "type_token_ratio": 0.0,
            "repeated_ngram_ratio": 0.0,
            "token_entropy": 0.0,
        }

    # Sentence segmentation
    raw_sentences = re.split(r"[.!?]+(?:\s+|$)", clean_text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    sentence_count = max(1, len(sentences))

    # Sentence length in words
    sentence_lengths = [len(re.findall(r"\b[\w'-]+\b", s)) for s in sentences]
    sentence_lengths = [sl for sl in sentence_lengths if sl > 0] or [word_count]

    avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)

    # Burstiness: Coefficient of variation (std dev / mean)
    if len(sentence_lengths) > 1 and avg_sentence_length > 0:
        variance = sum((sl - avg_sentence_length) ** 2 for sl in sentence_lengths) / len(
            sentence_lengths
        )
        std_dev = math.sqrt(variance)
        burstiness_score = round(min(1.0, std_dev / avg_sentence_length), 4)
    else:
        burstiness_score = 0.0

    # Type-Token Ratio (TTR): vocabulary diversity
    unique_words = set(words)
    type_token_ratio = round(len(unique_words) / word_count, 4)

    # Repeated 3-grams
    if word_count >= 3:
        trigrams = [tuple(words[i : i + 3]) for i in range(word_count - 2)]
        total_trigrams = len(trigrams)
        counts = Counter(trigrams)
        repeated_trigram_count = sum(c - 1 for c in counts.values() if c > 1)
        repeated_ngram_ratio = round(repeated_trigram_count / total_trigrams, 4)
    else:
        repeated_ngram_ratio = 0.0

    # Unigram Shannon entropy: H = - sum(p * log2(p))
    word_counts = Counter(words)
    entropy = 0.0
    for count in word_counts.values():
        p = count / word_count
        entropy -= p * math.log2(p)
    token_entropy = round(entropy, 4)

    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "burstiness_score": burstiness_score,
        "type_token_ratio": type_token_ratio,
        "repeated_ngram_ratio": repeated_ngram_ratio,
        "token_entropy": token_entropy,
    }


def build_evidence_signals(
    ai_prob: float | None,
    human_prob: float | None,
    features: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build structured evidentiary indicators from computed metrics and model probabilities.

    Guarantees that every finding reflects actual computed data without fabrication.
    """
    signals: list[dict[str, Any]] = []

    # 1. Primary Model Probability Signal
    if ai_prob is not None and human_prob is not None:
        ai_pct = round(ai_prob * 100, 1)
        human_pct = round(human_prob * 100, 1)
        finding = (
            f"The fine-tuned classification transformer estimated a {ai_pct}% synthetic "
            f"probability versus a {human_pct}% human-authorship probability."
        )
        signals.append({
            "signal": "Transformer Softmax Distribution",
            "metric": f"AI: {ai_pct}% | Human: {human_pct}%",
            "finding": finding,
        })

    # 2. Burstiness / Cadence Signal
    burstiness = features.get("burstiness_score", 0.0)
    avg_len = features.get("avg_sentence_length", 0.0)
    if burstiness < 0.20:
        cadence_finding = (
            f"Low sentence cadence variation ({burstiness:.2f}). Uniform sentence lengths "
            f"(mean {avg_len} words/sentence) are characteristic of unconstrained LLM generation."
        )
    elif burstiness > 0.45:
        cadence_finding = (
            f"High sentence burstiness ({burstiness:.2f}). Varied sentence rhythms and pacing "
            f"(mean {avg_len} words) strongly align with natural human compositional patterns."
        )
    else:
        cadence_finding = (
            f"Moderate sentence variation ({burstiness:.2f}). Sentence structures display "
            f"balanced rhythms without extreme clustering."
        )
    signals.append({
        "signal": "Sentence Rhythm & Burstiness",
        "metric": f"{burstiness:.2f} CV",
        "finding": cadence_finding,
    })

    # 3. Lexical Diversity (Type-Token Ratio)
    ttr = features.get("type_token_ratio", 0.0)
    wc = features.get("word_count", 0)
    if ttr < 0.45 and wc >= 40:
        ttr_finding = (
            f"Restricted vocabulary diversity (TTR {ttr:.2f}). The text reuses a constrained "
            f"set of lexical stems across {wc} analyzed tokens."
        )
    elif ttr > 0.70:
        ttr_finding = (
            f"Rich vocabulary diversity (TTR {ttr:.2f}). High lexical variation across {wc} "
            f"tokens indicates non-repetitive phrasing."
        )
    else:
        ttr_finding = (
            f"Standard vocabulary diversity (TTR {ttr:.2f}). The unique-to-total word ratio "
            f"falls within typical prose boundaries."
        )
    signals.append({
        "signal": "Lexical Diversity (TTR)",
        "metric": f"{ttr:.2f} ratio",
        "finding": ttr_finding,
    })

    # 4. N-gram Repetition
    rep_ngram = features.get("repeated_ngram_ratio", 0.0)
    rep_pct = round(rep_ngram * 100, 1)
    if rep_ngram > 0.08:
        rep_finding = (
            f"Elevated 3-gram repetition ({rep_pct}%). Repeated syntactic sequences detected "
            f"across clauses."
        )
    else:
        rep_finding = (
            f"Low syntactic repetition ({rep_pct}%). Phrases demonstrate natural progression "
            f"without looped n-grams."
        )
    signals.append({
        "signal": "Syntactic Repetition (3-gram)",
        "metric": f"{rep_pct}%",
        "finding": rep_finding,
    })

    # 5. Token Entropy
    entropy = features.get("token_entropy", 0.0)
    signals.append({
        "signal": "Unigram Shannon Entropy",
        "metric": f"{entropy:.2f} bits",
        "finding": (
            "Information density measure of token frequency distribution across the sample."
        ),
    })

    return signals
