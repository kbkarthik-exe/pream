import math
import re
from collections import Counter
from typing import Any

# Standard transitional phrase starters common in machine-generated structured text
TRANSITIONAL_OPENINGS = (
    "furthermore",
    "moreover",
    "additionally",
    "consequently",
    "in conclusion",
    "it is important to note",
    "it is worth noting",
    "overall",
    "specifically",
    "in summary",
    "as a result",
    "however",
    "thus",
    "hence",
    "therefore",
    "in particular",
)


def extract_linguistic_features(text: str) -> dict[str, Any]:
    """Extract deterministic, explainable linguistic and statistical features from text.

    Computes:
    - Character and word counts
    - Sentence structure metrics (sentence count, average sentence length, distributions)
    - Burstiness (coefficient of variation of sentence lengths)
    - Lexical diversity (Type-Token Ratio - TTR)
    - Repeated n-gram ratios (2-gram and 3-gram repetition)
    - Unigram Shannon token entropy
    - Sentence-level pacing analysis
    - Paragraph-level consistency analysis
    - Punctuation distribution & syntactic opening ratios
    - Multi-language script heuristics
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
            "sentence_details": [],
            "paragraph_details": [],
            "paragraph_consistency_score": 1.0,
            "punctuation_metrics": {
                "total_punctuation_count": 0,
                "punctuation_density": 0.0,
                "commas": 0,
                "periods": 0,
                "semicolons": 0,
                "colons": 0,
                "exclamations": 0,
                "questions": 0,
                "hyphens": 0,
            },
            "sentence_length_distribution": {
                "min": 0,
                "max": 0,
                "mean": 0.0,
                "std": 0.0,
                "median": 0.0,
            },
            "syntactic_repetition": {
                "repeated_2gram_ratio": 0.0,
                "repeated_3gram_ratio": 0.0,
                "transitional_starts_ratio": 0.0,
            },
            "language_detection": {
                "script": "unknown",
                "non_latin_ratio": 0.0,
                "warning": None,
            },
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
        variance = 0.0
        std_dev = 0.0
        burstiness_score = 0.0

    sorted_lengths = sorted(sentence_lengths)
    n_sl = len(sorted_lengths)
    if n_sl % 2 == 1:
        median_sl = float(sorted_lengths[n_sl // 2])
    else:
        median_sl = float((sorted_lengths[n_sl // 2 - 1] + sorted_lengths[n_sl // 2]) / 2.0)

    # Sentence details breakdown
    transitional_start_count = 0
    sentence_details: list[dict[str, Any]] = []
    for idx, s in enumerate(sentences, start=1):
        s_words = re.findall(r"\b[\w'-]+\b", s)
        s_wc = len(s_words)
        s_lower = s.lower().strip()
        has_trans = any(s_lower.startswith(prefix) for prefix in TRANSITIONAL_OPENINGS)
        if has_trans:
            transitional_start_count += 1

        cadence_ratio = (
            round(s_wc / avg_sentence_length, 2) if avg_sentence_length > 0 else 1.0
        )
        if cadence_ratio < 0.70:
            cadence_label = "SHORT"
        elif cadence_ratio > 1.35:
            cadence_label = "LONG"
        else:
            cadence_label = "BALANCED"

        punct_count = len(re.findall(r"[,;:\-—?!'\"()]", s))

        sentence_details.append({
            "sentence_index": idx,
            "sentence_idx": idx - 1,
            "text": s[:150] + ("..." if len(s) > 150 else ""),
            "word_count": s_wc,
            "character_count": len(s),
            "char_count": len(s),
            "relative_cadence": cadence_label,
            "cadence_ratio": cadence_ratio,
            "punctuation_count": punct_count,
            "punct_count": punct_count,
            "has_transitional_marker": has_trans,
            "has_transitional_opening": has_trans,
        })

    transitional_starts_ratio = (
        round(transitional_start_count / sentence_count, 4) if sentence_count > 0 else 0.0
    )

    # Paragraph-level segmentation & consistency
    raw_paras = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", clean_text) if p.strip()]
    if not raw_paras:
        raw_paras = [clean_text]

    paragraph_details: list[dict[str, Any]] = []
    para_avg_lens: list[float] = []
    for p_idx, p in enumerate(raw_paras, start=1):
        p_words = [w.lower() for w in re.findall(r"\b[\w'-]+\b", p)]
        p_wc = len(p_words)
        p_sents = [s.strip() for s in re.split(r"[.!?]+(?:\s+|$)", p) if s.strip()]
        p_sc = max(1, len(p_sents))
        p_avg_sl = round(p_wc / p_sc, 2) if p_sc > 0 else 0.0
        para_avg_lens.append(p_avg_sl)

        p_ttr = round(len(set(p_words)) / p_wc, 4) if p_wc > 0 else 0.0
        paragraph_details.append({
            "paragraph_index": p_idx,
            "paragraph_idx": p_idx - 1,
            "text_snippet": p[:100] + ("..." if len(p) > 100 else ""),
            "word_count": p_wc,
            "sentence_count": p_sc,
            "avg_sentence_length": p_avg_sl,
            "avg_sentence_len": p_avg_sl,
            "type_token_ratio": p_ttr,
        })

    # Paragraph consistency score: low variance across paragraphs indicates machine uniformity
    if len(para_avg_lens) > 1:
        mean_p_sl = sum(para_avg_lens) / len(para_avg_lens)
        p_var = sum((sl - mean_p_sl) ** 2 for sl in para_avg_lens) / len(para_avg_lens)
        para_consistency = round(math.sqrt(p_var) / (mean_p_sl + 1e-6), 4)
    else:
        para_consistency = 0.50

    # Type-Token Ratio (TTR): vocabulary diversity
    unique_words = set(words)
    type_token_ratio = round(len(unique_words) / word_count, 4)

    # Repeated 2-grams and 3-grams
    repeated_2gram_ratio = 0.0
    repeated_ngram_ratio = 0.0
    if word_count >= 2:
        bigrams = [tuple(words[i : i + 2]) for i in range(word_count - 1)]
        b_counts = Counter(bigrams)
        rep_bi = sum(c - 1 for c in b_counts.values() if c > 1)
        repeated_2gram_ratio = round(rep_bi / len(bigrams), 4)

    if word_count >= 3:
        trigrams = [tuple(words[i : i + 3]) for i in range(word_count - 2)]
        total_trigrams = len(trigrams)
        counts = Counter(trigrams)
        repeated_trigram_count = sum(c - 1 for c in counts.values() if c > 1)
        repeated_ngram_ratio = round(repeated_trigram_count / total_trigrams, 4)

    # Unigram Shannon entropy: H = - sum(p * log2(p))
    word_counts = Counter(words)
    entropy = 0.0
    for count in word_counts.values():
        p = count / word_count
        entropy -= p * math.log2(p)
    token_entropy = round(entropy, 4)

    # Punctuation distribution
    commas = len(re.findall(r",", clean_text))
    periods = len(re.findall(r"\.", clean_text))
    semicolons = len(re.findall(r";", clean_text))
    colons = len(re.findall(r":", clean_text))
    exclamations = len(re.findall(r"!", clean_text))
    questions = len(re.findall(r"\?", clean_text))
    hyphens = len(re.findall(r"[-—]", clean_text))
    total_punct = commas + periods + semicolons + colons + exclamations + questions + hyphens
    punct_density = round(total_punct / word_count, 4) if word_count > 0 else 0.0

    # Language and script detection heuristics
    latin_chars = len(re.findall(r"[A-Za-z]", clean_text))
    non_latin_chars = len(re.findall(r"[^\x00-\x7F\s\d.,!?;:\"'()\-—]", clean_text))
    total_alpha = latin_chars + non_latin_chars
    non_latin_ratio = round(non_latin_chars / total_alpha, 4) if total_alpha > 0 else 0.0

    lang_warning = None
    if non_latin_ratio > 0.25:
        script_type = "non-latin"
        lang_warning = (
            f"Non-Latin script detected ({non_latin_ratio:.1%}). Neural perplexity models "
            "are trained primarily on English text; non-English distributions may exhibit reduced calibration accuracy."
        )
    elif non_latin_ratio > 0.05:
        script_type = "mixed"
        lang_warning = (
            "Mixed script detected. Verify that non-English segments do not artificially shift perplexity scores."
        )
    else:
        script_type = "latin"

    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "burstiness_score": burstiness_score,
        "type_token_ratio": type_token_ratio,
        "repeated_ngram_ratio": repeated_ngram_ratio,
        "token_entropy": token_entropy,
        "sentence_details": sentence_details[:30],  # Keep up to 30 sentences for display
        "paragraph_details": paragraph_details[:10],
        "paragraph_consistency_score": para_consistency,
        "punctuation_metrics": {
            "total_punctuation_count": total_punct,
            "punctuation_density": punct_density,
            "commas": commas,
            "periods": periods,
            "semicolons": semicolons,
            "colons": colons,
            "exclamations": exclamations,
            "questions": questions,
            "hyphens": hyphens,
        },
        "sentence_length_distribution": {
            "min": min(sentence_lengths),
            "max": max(sentence_lengths),
            "mean": round(avg_sentence_length, 2),
            "std": round(std_dev, 2),
            "median": round(median_sl, 2),
        },
        "syntactic_repetition": {
            "repeated_2gram_ratio": repeated_2gram_ratio,
            "repeated_3gram_ratio": repeated_ngram_ratio,
            "transitional_starts_ratio": transitional_starts_ratio,
        },
        "language_detection": {
            "script": script_type,
            "non_latin_ratio": non_latin_ratio,
            "warning": lang_warning,
        },
    }


def build_evidence_signals(
    ai_prob: float | None,
    human_prob: float | None,
    features: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build structured evidentiary indicators from computed metrics and model probabilities.

    Guarantees that every finding reflects actual computed data without fabrication.
    Includes explicit notice that no single linguistic feature proves AI authorship.
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

    # 4. N-gram Repetition & Syntactic Loops
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

    # 6. Paragraph Consistency & Pacing (New Phase 1 feature)
    p_details = features.get("paragraph_details", [])
    if len(p_details) > 1:
        p_consistency = features.get("paragraph_consistency_score", 0.5)
        if p_consistency < 0.15:
            p_finding = (
                f"High cross-paragraph pacing uniformity (CV {p_consistency:.2f}). "
                "Paragraph lengths and sentence rhythms are systematically balanced across sections."
            )
        else:
            p_finding = (
                f"Dynamic paragraph pacing variation (CV {p_consistency:.2f}). "
                "Paragraph lengths shift naturally across sections, typical of human narrative progression."
            )
        signals.append({
            "signal": "Cross-Paragraph Consistency",
            "metric": f"{p_consistency:.2f} CV",
            "finding": p_finding,
        })

    # 7. Punctuation Distribution & Pacing (New Phase 1 feature)
    p_metrics = features.get("punctuation_metrics", {})
    p_density = p_metrics.get("punctuation_density", 0.0)
    commas = p_metrics.get("commas", 0)
    semicolons = p_metrics.get("semicolons", 0)
    signals.append({
        "signal": "Punctuation Pacing & Density",
        "metric": f"{p_density:.2f} punct/word ({commas} commas, {semicolons} semicolons)",
        "finding": (
            f"Punctuation distribution reveals stylistic cadence ({p_density:.2f} marks per token). "
            "Overly uniform comma and period placement frequently correlates with synthetic generative rhythm."
        ),
    })

    # 8. Epistemic Guard
    signals.append({
        "signal": "Forensic Epistemic Guard",
        "metric": "Corroboration Required",
        "finding": (
            "Individual linguistic indicators (burstiness, entropy, TTR) represent empirical statistical signals, "
            "not definitive proof of AI authorship. Decisions require corroboration with transformer softmax consensus."
        ),
    })

    return signals
