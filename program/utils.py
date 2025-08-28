# program/utils.py
from difflib import get_close_matches
from typing import List, Optional

from django.db.models import Q
from program.models import ProgramLevel, Program


def suggest_similar_level_slugs(
    input_slug: str,
    program_slug: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 5,
) -> List[str]:
    """
    Return a small list of similar ProgramLevel slugs to help fix typos.
    Filters candidates by program_slug (if provided) or category (if provided)
    for more relevant hints.
    """
    qs = ProgramLevel.objects.select_related("program")

    if program_slug:
        qs = qs.filter(program__slug=program_slug)
    elif category:
        qs = qs.filter(program__category=category)

    # Build a pool of 'search keys' that users might type
    # (slug is primary; title is a secondary signal)
    all_candidates = list(qs.values_list("slug", flat=True))
    if len(all_candidates) < limit:
        # If list is tiny, just return it as-is (no fuzzy matching needed)
        return all_candidates[:limit]

    # Fuzzy match on slug; if that yields nothing, fall back to titles→slugs
    matches = get_close_matches(input_slug, all_candidates, n=limit, cutoff=0.55)
    if matches:
        return matches

    # Second pass: fuzzy match on titles and then map back to slugs
    title_map = dict(qs.values_list("title", "slug"))
    title_candidates = list(title_map.keys())
    title_hits = get_close_matches(input_slug, title_candidates, n=limit, cutoff=0.55)
    return [title_map[t] for t in title_hits]
