from __future__ import annotations

from typing import Dict, List, Tuple

from classifier.entity_classifier_2.core.config import CountryConfig


def map_values_to_spans(det_raw: Dict[str, List[str]], text: str, cfg: CountryConfig) -> List[Tuple[str, int, int]]:
    """Map LLM-detected values to spans in text.

    Args:
        det_raw: Dictionary where keys are LLM output keys and values are lists of
            extracted strings.
        text: Source text in which spans should be located.
        cfg: Loaded country configuration used to translate output keys to entity ids.

    Returns:
        List of tuples ``(entity_id, start, end)`` representing non-overlapping spans.

    Failure Modes:
        Skips values when spans cannot be located or overlap; unexpected errors are
        logged and skipped.
    """
    # Build mapping from output_key -> entity_id
    key_to_entity: Dict[str, str] = {}
    for eid, ent in cfg.entities.items():
        if not ent.enabled:
            continue
        output_key = (ent.llm.output_key if ent.llm and ent.llm.output_key else eid.replace('-', '_').upper())
        key_to_entity[output_key] = eid

    results: List[Tuple[str, int, int]] = []
    used: List[Tuple[int, int]] = []

    def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return not (a[1] <= b[0] or b[1] <= a[0])

    for out_key, values in (det_raw or {}).items():
        eid = key_to_entity.get(out_key)
        if not eid or not values:
            continue
        for val in values:
            if not isinstance(val, str) or not val.strip():
                continue
            try:
                start = text.find(val)
                if start < 0:
                    continue
                end = start + len(val)
                if any(overlaps((start, end), u) for u in used):
                    continue
                used.append((start, end))
                results.append((eid, start, end))
            except Exception:
                continue
    return results


