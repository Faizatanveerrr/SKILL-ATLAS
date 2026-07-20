from model import AnalyzedResource

def rank_resources(
    resources: list[AnalyzedResource],
    resource_type: str | None = None,
    price_type: str | None = None,
    difficulty_level: str | None = None,
    top_n: int | None = None
) -> list[AnalyzedResource]:
    
    filtered = resources

    if resource_type:
        filtered = [r for r in filtered if r.resource_type.lower() == resource_type.lower()]

    if price_type:
        filtered = [r for r in filtered if r.price_type.lower() == price_type.lower()]

    if difficulty_level:
        filtered = [r for r in filtered if r.difficulty_level.lower() == difficulty_level.lower()]

    ranked = sorted(
        filtered,
        key=lambda r: (r.relevance_score * 0.6) + (r.score * 0.4),
        reverse=True
    )

    if top_n:
        ranked = ranked[:top_n]

    return ranked