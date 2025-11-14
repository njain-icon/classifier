from __future__ import annotations

from typing import List, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer

from classifier.entity_classifier.core.config import CountryConfig
from classifier.entity_classifier.core.prompts import PromptProvider
from classifier.entity_classifier.analyzers.base_analyzer import BaseCountryAnalyzer
from classifier.entity_classifier.analyzers import COUNTRY_ANALYZERS


def build_engine_from_yaml(cfg: CountryConfig) -> AnalyzerEngine:
    """Build a Presidio AnalyzerEngine from a CountryConfig.

    Only builtin+regex recognizers are registered here. LLM detection is handled
    outside Presidio in country analyzers.
    """
    registry = RecognizerRegistry()
    if cfg.use_presidio_defaults:
        registry.load_predefined_recognizers()

    # Register regex recognizers per entity
    for ent_id, ent in (cfg.entities or {}).items():
        if not ent.enabled:
            continue
        if not ent.detect or "regex" not in ent.detect.methods or not ent.detect.regex:
            continue
        patterns: List[Pattern] = []
        for rp in ent.detect.regex.patterns:
            patterns.append(Pattern(name=f"{ent_id}", regex=rp.pattern, score=rp.score))
        context = ent.context_indicators or []
        pr = PatternRecognizer(
            supported_entity=ent_id,
            patterns=patterns,
            context=context,
            name=f"{ent_id}_regex",
        )
        registry.add_recognizer(pr)

    enhancer = LemmaContextAwareEnhancer(
        context_similarity_factor=cfg.enhancer.similarity_factor,
        min_score_with_context_similarity=cfg.enhancer.min_score_with_context,
    )
    return AnalyzerEngine(registry=registry, context_aware_enhancer=enhancer)


def build_engine_from_configs(cfgs: List[CountryConfig]) -> AnalyzerEngine:
    """Build a single AnalyzerEngine by aggregating regex/builtin recognizers from multiple configs.

    - Loads predefined recognizers if any config requests it
    - Adds PatternRecognizers for all regex-defined entities across configs
    """
    registry = RecognizerRegistry()
    if any(cfg.use_presidio_defaults for cfg in cfgs):
        registry.load_predefined_recognizers()

    for cfg in cfgs:
        for ent_id, ent in (cfg.entities or {}).items():
            if not ent.enabled:
                continue
            if not ent.detect or "regex" not in ent.detect.methods or not ent.detect.regex:
                continue
            patterns: List[Pattern] = []
            for rp in ent.detect.regex.patterns:
                patterns.append(Pattern(name=f"{ent_id}", regex=rp.pattern, score=rp.score))
            context = ent.context_indicators or []
            pr = PatternRecognizer(
                supported_entity=ent_id,
                patterns=patterns,
                context=context,
                name=f"{ent_id}_regex",
            )
            registry.add_recognizer(pr)

    # Use enhancer settings from the first config as baseline
    first = cfgs[0]
    enhancer = LemmaContextAwareEnhancer(
        context_similarity_factor=first.enhancer.similarity_factor,
        min_score_with_context_similarity=first.enhancer.min_score_with_context,
    )
    return AnalyzerEngine(registry=registry, context_aware_enhancer=enhancer)


def build_patterns_from_yaml(cfg: CountryConfig, analyzer: AnalyzerEngine) -> List[Pattern]:
    for ent_id, ent in (cfg.entities or {}).items():
        patterns = []
        if not ent.enabled or not ent.detect:
            continue
        if "regex" not in ent.detect.methods or not ent.detect.regex:
            continue
        for rp in ent.detect.regex.patterns:
            patterns.append(Pattern(name=f"{ent_id}", regex=rp.pattern, score=rp.score))
        # Define recognizer with the defined pattern
        
        recognizer = PatternRecognizer(
            supported_entity=ent_id,
            name=f"{'_'.join(ent_id.split(' '))}_recognizer",
            patterns=patterns,
            context=ent.context_indicators,
        )
        analyzer.registry.add_recognizer(recognizer)

    return analyzer


def build_supported_entities(cfg: CountryConfig) -> List[str]:
    supported: List[str] = []
    for ent_id, ent in (cfg.entities or {}).items():
        if not ent.enabled or not ent.detect:
            continue
        if any(m in ent.detect.methods for m in ("regex", "llm")):
            supported.append(ent_id)
    return supported


def build_enable_flags(cfg: CountryConfig) -> Tuple[bool, bool]:
    enable_pattern = False
    enable_llm = False
    for _, ent in (cfg.entities or {}).items():
        if not ent.enabled or not ent.detect:
            continue
        if "regex" in ent.detect.methods and getattr(ent.detect, "regex", None) and getattr(ent.detect.regex, "patterns", None):
            enable_pattern = True
        if "llm" in ent.detect.methods:
            enable_llm = True
    return enable_pattern, enable_llm


def build_country_recognizer(cfg: CountryConfig) -> BaseCountryAnalyzer:
    #analyzer = build_patterns_from_yaml(cfg, analyzer)
    supported_entities = build_supported_entities(cfg)
    enable_pattern, enable_llm = build_enable_flags(cfg)
    prompt_provider = PromptProvider(cfg)
    analyzer_cls = COUNTRY_ANALYZERS.get(cfg.country.upper(), BaseCountryAnalyzer) or BaseCountryAnalyzer
    cnt_analyzer = analyzer_cls(
        cfg=cfg,
        supported_entities=supported_entities,
        enable_pattern=enable_pattern,
        enable_llm=enable_llm,
        prompt_provider=prompt_provider,
    )
    return cnt_analyzer
