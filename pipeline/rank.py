from difflib import SequenceMatcher
from model import AnalyzedResource


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().strip().split())


def _titles_similar(a: str, b: str, threshold: float = 0.9) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold


def _combined_score(r: AnalyzedResource) -> float:
    return (r.relevance_score * 0.6) + (r.score * 0.4)


def dedupe_resources(resources: list[AnalyzedResource]) -> list[AnalyzedResource]:
    """
    Removes duplicate resources based on:
      1. Exact URL match (normalized, trailing slash stripped)
      2. Fuzzy title match (catches same content at different URLs)
    When a duplicate is found, keeps whichever has the higher combined score.
    """
    seen_urls: set[str] = set()
    unique: list[AnalyzedResource] = []

    for r in resources:
        url_key = r.url.rstrip("/").lower()

        if url_key in seen_urls:
            continue

        norm_title = _normalize_title(r.title)
        dup_index = None

        for i, existing in enumerate(unique):
            if _titles_similar(norm_title, _normalize_title(existing.title)):
                dup_index = i
                break

        if dup_index is not None:
            existing = unique[dup_index]
            if _combined_score(r) > _combined_score(existing):
                seen_urls.discard(existing.url.rstrip("/").lower())
                unique[dup_index] = r
                seen_urls.add(url_key)
            # else: keep existing, drop r
            continue

        seen_urls.add(url_key)
        unique.append(r)

    return unique


def rank_resources(
    resources: list[AnalyzedResource],
    resource_type: str | None = None,
    price_type: str | None = None,
    difficulty_level: str | None = None,
    min_freshness: float | None = None,
    top_n: int | None = None,
) -> list[AnalyzedResource]:

    filtered = dedupe_resources(resources)

    if resource_type:
        filtered = [r for r in filtered if r.resource_type.lower() == resource_type.lower()]

    if price_type:
        filtered = [r for r in filtered if r.price_type.lower() == price_type.lower()]

    if difficulty_level:
        filtered = [r for r in filtered if r.difficulty_level.lower() == difficulty_level.lower()]

    if min_freshness is not None:
        filtered = [r for r in filtered if r.freshness_score >= min_freshness]

    ranked = sorted(
        filtered,
        key=_combined_score,
        reverse=True,
    )

    if top_n:
        ranked = ranked[:top_n]

    return ranked