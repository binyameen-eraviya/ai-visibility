"""Brand mention detection.

Two passes:
  Pass 1 (string)  -- fast, free, deterministic. Whole-word, case-insensitive
                      matching of each brand name + its aliases. Records the
                      rank (1st brand mentioned = position 1) and the sentence
                      the brand appeared in.
  Pass 2 (LLM)     -- only when Pass 1 finds nothing in a substantial answer
                      (an AI can describe a brand without naming it). The
                      orchestrator batches the prompt fragment from here into
                      its single Gemini call; parse_fuzzy_mentions() maps the
                      result back to MentionResult rows.

A MentionResult is produced for EVERY brand (mentioned True and False) so the
caller can persist mentioned=false rows -- visibility = mentioned_true / runs
depends on those negatives existing.
"""

import re
from dataclasses import dataclass

# An answer at least this long with zero string matches is worth an LLM look.
_MIN_LEN_FOR_FUZZY = 160


@dataclass
class MentionResult:
    brand_id: object
    brand_name: str
    mentioned: bool
    position: int = None  # rank of this brand among all mentioned brands
    context_snippet: str = None


def _terms(brand) -> list:
    """All searchable strings for a brand: its name plus any aliases."""
    terms = [brand.name] if getattr(brand, "name", None) else []
    aliases = getattr(brand, "aliases", None) or []
    terms.extend(a for a in aliases if a)
    # De-dupe case-insensitively, keep longest first so "Stripe Inc" wins over
    # "Stripe" when both would match at the same spot.
    seen = set()
    out = []
    for t in sorted((str(t).strip() for t in terms if str(t).strip()), key=len, reverse=True):
        low = t.lower()
        if low not in seen:
            seen.add(low)
            out.append(t)
    return out


def _first_match(text: str, term: str):
    """Earliest whole-word, case-insensitive match index of term, else None."""
    # (?<!\w) / (?!\w) give whole-word semantics that also work when the term
    # ends in punctuation -- and stop "Stripe" matching inside "Striped".
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.start() if m else None


def _snippet_around(text: str, idx: int, max_len: int = 240) -> str:
    """The sentence containing character `idx` (trimmed)."""
    if idx is None or idx < 0:
        return ""
    # Sentence bounds: nearest .!?\n before and after the match.
    start = max(
        (text.rfind(p, 0, idx) for p in (".", "!", "?", "\n")),
        default=-1,
    )
    ends = [text.find(p, idx) for p in (".", "!", "?", "\n")]
    ends = [e for e in ends if e != -1]
    end = min(ends) + 1 if ends else len(text)
    snippet = text[start + 1:end].strip()
    return snippet[:max_len].strip()


def detect_mentions(answer_text: str, brands: list) -> list:
    """Pass 1: string-match every brand; rank mentions by order of appearance."""
    text = answer_text or ""
    hits = []  # (brand, char_index)
    for brand in brands:
        best = None
        for term in _terms(brand):
            idx = _first_match(text, term)
            if idx is not None and (best is None or idx < best):
                best = idx
        if best is not None:
            hits.append((brand, best))

    # Rank by first appearance; equal indexes keep input order (stable sort).
    hits.sort(key=lambda h: h[1])
    ranked = {id(brand): pos for pos, (brand, _) in enumerate(hits, start=1)}
    positions = {id(brand): idx for brand, idx in hits}

    results = []
    for brand in brands:
        if id(brand) in ranked:
            idx = positions[id(brand)]
            results.append(MentionResult(
                brand_id=brand.id,
                brand_name=brand.name,
                mentioned=True,
                position=ranked[id(brand)],
                context_snippet=_snippet_around(text, idx),
            ))
        else:
            results.append(MentionResult(
                brand_id=brand.id,
                brand_name=brand.name,
                mentioned=False,
            ))
    return results


def needs_llm_fallback(answer_text: str, results: list) -> bool:
    """True when a substantial answer yielded zero string matches."""
    if any(r.mentioned for r in results):
        return False
    return len(answer_text or "") >= _MIN_LEN_FOR_FUZZY


def build_fuzzy_prompt_fragment(brands: list) -> str:
    """Instruction block for the batched LLM call's mention section."""
    names = ", ".join(b.name for b in brands if getattr(b, "name", None))
    return (
        "MENTIONS: Which of these brands are mentioned or clearly referenced in "
        "the answer? Include INDIRECT references (e.g. 'the payment processor "
        "founded by Patrick Collison' refers to Stripe). For each brand give "
        "mentioned (true/false), position (1 = first brand referenced in the "
        "answer, null if not mentioned), and a short context_snippet (the phrase "
        f"that references it, or null).\nBrands: {names}"
    )


def parse_fuzzy_mentions(llm_mentions, brands: list) -> list:
    """Map the LLM's mention list onto a MentionResult per brand.

    llm_mentions: list of {brand_name, mentioned, position, context_snippet}.
    Brands the LLM omits or marks not-mentioned get mentioned=false.
    """
    by_name = {}
    for m in llm_mentions or []:
        if isinstance(m, dict) and m.get("brand_name"):
            by_name[str(m["brand_name"]).strip().lower()] = m

    results = []
    for brand in brands:
        m = by_name.get((brand.name or "").strip().lower())
        if m and bool(m.get("mentioned")):
            pos = m.get("position")
            try:
                pos = int(pos) if pos is not None else None
            except (TypeError, ValueError):
                pos = None
            snippet = m.get("context_snippet")
            results.append(MentionResult(
                brand_id=brand.id,
                brand_name=brand.name,
                mentioned=True,
                position=pos,
                context_snippet=(str(snippet).strip()[:240] if snippet else None),
            ))
        else:
            results.append(MentionResult(
                brand_id=brand.id,
                brand_name=brand.name,
                mentioned=False,
            ))
    return results
