from __future__ import annotations

import re
from typing import List, Tuple, Set, Optional

from presidio_analyzer import EntityRecognizer, Pattern, RecognizerResult, AnalyzerEngine

from classifier.entity_classifier.core.config import CountryConfig
from classifier.entity_classifier.core.prompts import PromptProvider
from classifier.entity_classifier.engine.span_resolver import map_values_to_spans
from classifier.text_generation.text_generation import TextGeneration
from classifier.log import get_logger
from classifier.entity_classifier.core.validation import ValidationProvider


logger = get_logger(__name__)

class BaseCountryAnalyzer(EntityRecognizer):
    """Base analyzer which augments Presidio with LLM-assisted detection and validation.

    This class wires country-specific YAML config, optional regex/builtin recognizers
    (managed outside), and an optional LLM pass. After detection, `post_filter` applies
    thresholds and validator functions declared in YAML.

    Args:
        cfg: Country configuration loaded from YAML
        supported_entities: Entity ids (YAML keys) this analyzer can emit
        enable_pattern: Whether regex-based detection is enabled for this config
        enable_llm: Whether LLM-based detection is enabled for this config
        prompt_provider: Provider for building LLM prompts
        validation: Validation function resolver
        text_gen: Text generation client used for LLM detection
        supported_language: Language code for Presidio
        context: Optional contextual words
    """
    def __init__(
        self,
        cfg: CountryConfig,
        supported_entities: List[str],
        enable_pattern: bool,
        enable_llm: bool,
        prompt_provider: PromptProvider,
        validation: ValidationProvider | None = None,
        text_gen: TextGeneration | None = None,
        supported_language: str = "en",
        context: List[str] | None = None,
    ) -> None:
        super().__init__(
            supported_entities=supported_entities,
            context=context or [],
            supported_language=supported_language,
        )
        self.cfg = cfg
        self._enable_pattern = bool(enable_pattern)
        self._enable_llm = bool(enable_llm)
        self.prompt_provider = prompt_provider
        self.validation = validation or ValidationProvider()
        self.text_gen = text_gen or TextGeneration()
        # Precompute llm-target entity ids
        self._llm_entity_ids: List[str] = []
        for eid, ent in (self.cfg.entities or {}).items():
            if ent.enabled and ent.detect and "llm" in ent.detect.methods:
                self._llm_entity_ids.append(eid)

    @property
    def enabled_entity_ids(self) -> List[str]:
        return [eid for eid, e in self.cfg.entities.items() if e.enabled]

    @property
    def llm_entity_ids(self) -> List[str]:
        return list(self._llm_entity_ids)

    # def _analyze_patterns(self, text: str, target_ids: Optional[Set[str]] = None) -> List[RecognizerResult]:
    #     if not self._enable_pattern or not self.patterns:
    #         return []
    #     results: List[RecognizerResult] = []
    #     for pattern in self.patterns:
    #         logger.info(f"pattern for ent id {pattern}")
    #         if target_ids is not None and pattern.name not in target_ids:
    #             logger.info(f"pattern for ent id {pattern} not in target ids {target_ids}")
    #             continue
    #         try:
    #             logger.info(f"text {text}")
    #             logger.info(f"pattern.regex {pattern.regex}")
    #             test_op = re.findall(pattern.regex, text, re.MULTILINE | re.IGNORECASE)
    #             logger.info(f"test_op {test_op}")
    #             matches = re.finditer(pattern.regex, text, re.MULTILINE | re.IGNORECASE)
    #             logger.info(f"matches {matches}")
    #             for match in matches:
    #                 logger.info(f"match {match}")
    #                 start, end = match.span()
    #                 if start == end:
    #                     continue
    #                 results.append(
    #                     RecognizerResult(
    #                         entity_type=pattern.name,
    #                         start=start,
    #                         end=end,
    #                         score=pattern.score,
    #                     )
    #                 )
    #         except re.error:
    #             continue
    #     logger.info(f"pattern results {results}")
    #     results = EntityRecognizer.remove_duplicates(results)
    #     return results
         

    def _llm_detect_and_validate(self, text: str, target_ids: Optional[Set[str]] = None) -> List[RecognizerResult]:
        """Run LLM detection for the given text and return provisional spans.

        Applies entity id filtering via `target_ids` if provided, maps returned
        values back to spans in `text`, and emits `RecognizerResult` objects with
        a conservative default score which is later filtered by thresholds.
        """
        try:
            use_llm = False
            if not use_llm:
                logger.info(f"use_llm is False - skipping LLM detection")
                return []
            logger.info(f"self._enable_llm {self._enable_llm}")
            if not self._enable_llm or not self._llm_entity_ids:
                return []
            ids = self._llm_entity_ids
            if target_ids is not None:
                ids = [eid for eid in ids if eid in target_ids]
            if not ids:
                return []
            messages = self.prompt_provider.get_detection_messages(text=text, entity_ids=ids)
            det_raw = self.text_gen.generate_entity(messages)
            if not det_raw or not isinstance(det_raw, dict):
                return []
            provisional: List[Tuple[str, int, int]] = map_values_to_spans(det_raw, text, self.cfg)
            results: List[RecognizerResult] = []
            for eid, s, e in provisional:
                results.append(RecognizerResult(entity_type=eid, start=s, end=e, score=0.8))
            return results
        except Exception as e:
            import traceback
            logger.error(f"Error in _llm_detect_and_validate: {traceback.format_exc()}")
            return []

    def post_filter(self, text: str, results: List[RecognizerResult]) -> List[RecognizerResult]:
        """Filter preliminary results by thresholds and optional validators.

        - Enforces per-entity minimum confidence score (if provided in YAML)
        - Invokes validator functions referenced in YAML (module-level or class methods)
        """
        filtered: List[RecognizerResult] = []
        for r in results:
            ent = self.cfg.entities.get(r.entity_type)
            if not ent or not ent.enabled:
                continue
            # thresholds
            min_conf = (ent.detect.thresholds.min_confidence if ent.detect and ent.detect.thresholds else 0.0)
            if r.score is not None and r.score < min_conf:
                continue
            # validator
            fn = ent.validate_fn or (ent.validation.fn if ent.validation else None)
            if fn:
                value = text[r.start:r.end]
                # First, prefer bound method on this analyzer instance if present
                inst_method = getattr(self, fn, None)
                ok = True
                if callable(inst_method):
                    try:
                        ok = bool(inst_method(value, text, self.cfg.country, {}))
                    except TypeError:
                        try:
                            ok = bool(inst_method(value, text))
                        except TypeError:
                            ok = bool(inst_method(value))
                else:
                    ok = self.validation.validate(fn=fn, value=value, text=text, country=self.cfg.country, rules={})
                if not ok:
                    continue
            filtered.append(r)
        return filtered

    def analyze(
        self,
        text: str,
        entities: List[str] = [],
        nlp_artifacts=None,
        regex_flags: int | None = None,
    ) -> List[RecognizerResult]:
        """Primary analyze entrypoint for Presidio integration.

        Currently delegates detection to the LLM flow when enabled, followed by
        `post_filter`. Regex/builtin detection can be added or combined here if needed.
        """
        requested: Optional[Set[str]] = set(entities) if entities else None
        # Determine targets for patterns and LLM
        llm_entity_ids: Set[str] = set(self._llm_entity_ids)
        llm_targets: Optional[Set[str]] = None if requested is None else (requested & llm_entity_ids)
        if self._enable_llm:
            llm_results = self._llm_detect_and_validate(text, target_ids=llm_targets)
        else:
            llm_results = []
        return self.post_filter(text, llm_results)
    

    


